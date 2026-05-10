from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
import uuid
import shutil
import tempfile
from services.stt_service import stt_service
from services.audio_analysis import analyze_audio
from services.repo_analyzer import analyze_repo
from core.llm_service import generate_llm_response, evaluate_full_interview, polish_text, generate_repo_questions, generate_study_plan
from sqlalchemy.orm import Session
from typing import List
import json
import os
import random
from db import models, schemas
from db.database import get_db
from datetime import datetime

router = APIRouter()

def _safe_json_loads(value, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def _evaluation_payload(interview: models.Interview, eval_record: models.Evaluation) -> dict:
    report_data = _safe_json_loads(eval_record.report_json, {})
    repo_context = _safe_json_loads(interview.repo_context, None)
    custom_questions = _safe_json_loads(interview.custom_questions, None)

    return {
        "interview_id": eval_record.interview_id,
        "role": interview.role,
        "content_score": eval_record.content_score or 0,
        "expression_score": eval_record.expression_score or 0,
        "business_scenario_score": eval_record.business_scenario_score or 0,
        "problem_solving_score": eval_record.problem_solving_score or 0,
        "total_score": eval_record.total_score or 0,
        "speech_rate_score": eval_record.speech_rate_score or 0,
        "clarity_score": eval_record.clarity_score or 0,
        "confidence_score": eval_record.confidence_score or 0,
        "expression_metrics": report_data.get("expression_metrics"),
        "repo_context": repo_context,
        "custom_questions": custom_questions,
        "study_plan": report_data.get("study_plan"),
        "highlights": report_data.get("highlights", report_data.get("strengths", [])),
        "weaknesses": report_data.get("weaknesses", []),
        "recommendations": eval_record.recommendations or report_data.get("improvement_suggestions", "继续加油！"),
        "scores": report_data.get("scores"),
        "report_json": report_data,
        "created_at": eval_record.created_at,
    }

ROLES = [
    {
        "id": 1, 
        "name": "Java后端开发工程师", 
        "key": "java-backend", 
        "icon": "☕", 
        "desc": "重点考察自动装配、JVM、并发编程等", 
        "gradient": "from-orange-400 to-red-500"
    },
    {
        "id": 2, 
        "name": "Web前端开发工程师", 
        "key": "web-frontend", 
        "icon": "🌐", 
        "desc": "重点考察Vue/React原理、性能优化、事件循环等", 
        "gradient": "from-blue-400 to-indigo-600"
    },
    {
        "id": 3, 
        "name": "Python算法工程师", 
        "key": "python-algorithm", 
        "icon": "🐍", 
        "desc": "重点考察机器学习模型、数据结构、模型调优等", 
        "gradient": "from-green-400 to-emerald-600"
    }
]

def get_questions_by_category(role_key: str, category: str, difficulty: str = "medium", knowledge_points: List[str] = None):
    # Map role key to actual JSON file
    backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    questions_file = os.path.join(os.path.dirname(backend_path), "knowledge-base", role_key, "questions.json")
    
    if not os.path.exists(questions_file):
        return []

    diff_map = {"简单": "easy", "中等": "medium", "困难": "hard"}
    target_diff = diff_map.get(difficulty, "medium")

    try:
        with open(questions_file, "r", encoding="utf-8") as f:
            all_questions = json.load(f)
            
        potential = []
        for q in all_questions:
            if q.get("category") == category and q.get("difficulty") == target_diff:
                # Optional section filter
                if knowledge_points:
                    if q.get("section") in knowledge_points:
                        potential.append(q)
                else:
                    potential.append(q)
        return potential
    except:
        return []

def get_random_starting_question(role_name: str, difficulty: str = "medium", knowledge_points: List[str] = None):
    # This is a fallback/legacy function, we now prefer get_questions_by_category
    role_info = next((r for r in ROLES if r["name"] == role_name), None)
    role_key = role_info["key"] if role_info else "java-backend"
    
    # Always start with Scenario for the first actual question
    questions = get_questions_by_category(role_key, "business_scenario", difficulty, knowledge_points)
    if not questions:
        # Fallback to any if scenario not found
        backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        questions_file = os.path.join(os.path.dirname(backend_path), "knowledge-base", role_key, "questions.json")
        try:
            with open(questions_file, "r", encoding="utf-8") as f:
                questions = json.load(f)
        except:
            return "请谈谈你对该岗位的理解。"
            
    return random.choice(questions) if questions else "请谈谈你对该岗位的理解。"

@router.get("/roles")
def get_roles():
    return ROLES

from fastapi import Header

def get_current_user_id(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")
    try:
        # Expected format: "Bearer fake-token-1"
        token = authorization.split(" ")[1] if " " in authorization else authorization
        user_id_str = token.replace("fake-token-", "")
        return int(user_id_str)
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid Authorization Token")

@router.post("/repo/analyze")
async def analyze_repo_endpoint(data: schemas.RepoAnalyzeRequest, user_id: int = Depends(get_current_user_id)):
    """前端粘贴 GitHub URL 后立即预览抓取结果。"""
    if not data.url or not data.url.strip():
        raise HTTPException(status_code=400, detail="URL 不能为空")

    summary = await analyze_repo(data.url)
    if summary is None:
        raise HTTPException(
            status_code=400,
            detail="无法抓取该仓库。请确认：1) 仓库是公开的 GitHub 仓库；2) URL 格式为 https://github.com/owner/repo；3) 网络连接正常。"
        )
    return summary


@router.post("/start", response_model=schemas.InterviewResponse)
async def start_interview(data: schemas.InterviewStart, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    knowledge_points_json = json.dumps(data.knowledge_points) if data.knowledge_points else "[]"

    # v3: 如果用户提供了 GitHub 项目链接，抓取摘要 + 生成定制问题
    repo_context_json = None
    custom_questions_json = None
    repo_urls = (data.repo_urls or [])[:3]   # 最多 3 个
    if repo_urls:
        print(f"[start_interview] analyzing {len(repo_urls)} repos...")
        repo_summaries = []
        all_custom_questions = []
        for url in repo_urls:
            if not url or not url.strip():
                continue
            summary = await analyze_repo(url)
            if summary is None:
                print(f"[start_interview] skip invalid repo: {url}")
                continue
            repo_summaries.append(summary)
            # 为每个 repo 生成 3-5 个定制问题
            questions = await generate_repo_questions(data.role, summary)
            all_custom_questions.extend(questions)

        if repo_summaries:
            repo_context_json = json.dumps(repo_summaries, ensure_ascii=False)
        if all_custom_questions:
            custom_questions_json = json.dumps(all_custom_questions, ensure_ascii=False)
            print(f"[start_interview] generated {len(all_custom_questions)} custom questions total")

    new_interview = models.Interview(
        user_id=user_id,
        role=data.role,
        difficulty=data.difficulty,
        knowledge_points=knowledge_points_json,
        total_rounds=data.total_rounds,
        status="in_progress",
        repo_context=repo_context_json,
        custom_questions=custom_questions_json,
    )
    db.add(new_interview)
    db.commit()
    db.refresh(new_interview)

    # Round 0: Only Introduction request (First sentence, no questions yet)
    greeting = f"你好，我是你的{data.role}面试官。很高兴见到你。本次面试共设定为 {data.total_rounds} 轮提问。在正式开始前，请先做一个简单的自我介绍。"
    ai_msg = models.Message(interview_id=new_interview.id, sender="ai", content=greeting, category="introduction")
    db.add(ai_msg)
    db.commit()

    return new_interview

@router.get("/roles/{role_key}/sections")
def get_role_sections(role_key: str):
    # Dynamic extraction of sections from consolidated questions.json
    backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    questions_file = os.path.join(os.path.dirname(backend_path), "knowledge-base", role_key, "questions.json")
    
    sections = set()
    if os.path.exists(questions_file):
        try:
            with open(questions_file, "r", encoding="utf-8") as f:
                questions = json.load(f)
                for q in questions:
                    if "section" in q:
                        sections.add(q["section"])
        except Exception as e:
            print(f"Error extracting sections for {role_key}: {e}")
    
    # Return as a sorted list
    return sorted(list(sections))

@router.get("/{interview_id}/messages", response_model=List[schemas.MessageResponse])
def get_interview_messages(interview_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    interview = db.query(models.Interview).filter(models.Interview.id == interview_id, models.Interview.user_id == user_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found or unauthorized")
    
    messages = db.query(models.Message).filter(models.Message.interview_id == interview_id).order_by(models.Message.created_at.asc()).all()
    return messages

@router.get("/{interview_id}/evaluation", response_model=schemas.EvaluationDetail)
def get_evaluation(interview_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    eval_record = db.query(models.Evaluation).join(models.Interview).filter(
        models.Evaluation.interview_id == interview_id,
        models.Interview.user_id == user_id
    ).first()
    if not eval_record:
        raise HTTPException(status_code=404, detail="Evaluation not found or unauthorized")

    return schemas.EvaluationDetail(**_evaluation_payload(eval_record.interview, eval_record))

@router.post("/polish")
async def polish_transcription(data: dict, user_id: int = Depends(get_current_user_id)):
    """
    Endpoint to add punctuation to raw transcription.
    """
    text = data.get("text", "")
    if not text:
        return {"text": ""}
    
    polished_text = await polish_text(text)
    return {"text": polished_text}

@router.post("/{interview_id}/message", response_model=schemas.MessageResponse)
async def send_message(interview_id: int, msg: schemas.MessageSend, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    # 纯文本模式下，我们不需要提取 user_msg.id，直接用占位符忽略即可
    ai_msg_resp, _ = await process_message_logic(interview_id, msg.content, db, user_id)
    return ai_msg_resp

@router.post("/{interview_id}/voice", response_model=schemas.VoiceResponse)
async def upload_voice(
    interview_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    # 1. Save uploaded file to temporary location
    temp_dir = tempfile.gettempdir()
    file_extension = os.path.splitext(file.filename)[1] if file.filename else ".webm"
    temp_file_path = os.path.join(temp_dir, f"voice_{uuid.uuid4()}{file_extension}")

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 2. Whisper 详细转写（一次调用，结果同时给 polish 和 analyze 使用，避免重复跑模型）
        whisper_result = stt_service.transcribe_detailed(temp_file_path)
        if not whisper_result or not whisper_result.get("text"):
            raise HTTPException(status_code=400, detail="语音转录失败，请重试或手动输入")
        raw_transcript = whisper_result["text"]

        # 3. AI Polish for punctuation and homophone correction
        transcript = await polish_text(raw_transcript)

        # 4. Process the polished text as a message
        ai_msg_resp, user_msg_id = await process_message_logic(interview_id, transcript, db, user_id)

        # 5. 表达分析特征落库（A 部分实现，契约 §2.1）
        # 失败不影响用户对话主流程，仅记录日志
        try:
            metrics = analyze_audio(temp_file_path, whisper_result)
            if metrics is not None:
                vm = models.VoiceMetrics(
                    interview_id=interview_id,
                    message_id=user_msg_id,
                    duration_sec=metrics["duration_sec"],
                    wpm=metrics["wpm"],
                    pause_ratio=metrics["pause_ratio"],
                    long_pause_count=metrics["long_pause_count"],
                    filler_total=metrics["filler_total"],
                    pitch_mean=metrics["pitch_mean"],
                    pitch_std=metrics["pitch_std"],
                    volume_mean=metrics["volume_mean"],
                    volume_std=metrics["volume_std"],
                    raw_json=json.dumps(metrics, ensure_ascii=False),
                )
                db.add(vm)
                db.commit()
                print(f"[voice_metrics] saved for interview={interview_id}, message={user_msg_id}, wpm={metrics['wpm']}")
            else:
                print(f"[voice_metrics] skip (audio too short or empty) for interview={interview_id}")
        except Exception as e:
            print(f"[voice_metrics] analyze failed: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

        return schemas.VoiceResponse(transcription=transcript, ai_message=ai_msg_resp)

    finally:
        # 6. Cleanup
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except:
                pass

async def process_message_logic(interview_id: int, content: str, db: Session, user_id: int):
    # 1. Fetch interview context
    interview = db.query(models.Interview).filter(models.Interview.id == interview_id, models.Interview.user_id == user_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found or unauthorized")

    # 2. Save User Message
    user_msg = models.Message(interview_id=interview_id, sender="user", content=content)
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)  

    # 3. Analyze History
    messages = db.query(models.Message).filter(models.Message.interview_id == interview_id).order_by(models.Message.created_at.asc()).all()
    ai_msgs = [m for m in messages if m.sender == "ai"]
    
    main_questions_asked = []
    current_follow_up_count = 0
    
    for m in ai_msgs[1:]: 
        if m.category and "FOLLOW_UP" not in m.category:
            main_questions_asked.append(m)
            current_follow_up_count = 0
        else:
            current_follow_up_count += 1

    question_count = len(main_questions_asked)
    n = interview.total_rounds or 6

    # 4. Determine Stage & Next Target
    # v4 新逻辑：4 段式覆盖赛题要求的全部题型
    #   有 GitHub 深挖时：scenario → project → problem_solving → behavioral
    #   无 GitHub 深挖时：scenario → problem_solving → behavioral
    custom_questions_list = []
    if interview.custom_questions:
        try:
            custom_questions_list = json.loads(interview.custom_questions)
        except Exception:
            custom_questions_list = []

    has_custom = len(custom_questions_list) > 0
    if has_custom:
        # 4 段分布，n>=4 时每段都有；n<4 时压缩不问行为
        scenario_end = max(1, n // 4)
        project_end = scenario_end + max(1, n // 4)
        solving_end = project_end + max(1, n // 4)
        if question_count < scenario_end:
            current_stage = "business_scenario"
        elif question_count < project_end:
            current_stage = "project"
        elif question_count < solving_end:
            current_stage = "problem_solving"
        else:
            current_stage = "behavioral"
    else:
        # 3 段分布
        scenario_end = max(1, n // 3)
        solving_end = scenario_end + max(1, n // 3)
        if question_count < scenario_end:
            current_stage = "business_scenario"
        elif question_count < solving_end:
            current_stage = "problem_solving"
        else:
            current_stage = "behavioral"

    # If we are in the middle of a question, we might want the next one ready
    role_info = next((r for r in ROLES if r["name"] == interview.role), None)
    role_key = role_info["key"] if role_info else "java-backend"
    kp_list = json.loads(interview.knowledge_points) if interview.knowledge_points else []

    # Logic for picking the "Next Target"
    asked_titles = [m.content.split("接下来，")[-1] for m in main_questions_asked]  # Simple heuristic

    if current_stage == "project" and has_custom:
        # 优先从定制问题里挑未问过的
        available_custom = [q for q in custom_questions_list if q.get("question") not in asked_titles]
        if available_custom:
            target_q_obj = random.choice(available_custom)
        else:
            # 定制问完了，降级到静态 project 题库
            potential_next = get_questions_by_category(role_key, "project", interview.difficulty, kp_list)
            available_next = [q for q in potential_next if q["question"] not in asked_titles]
            target_q_obj = random.choice(available_next if available_next else potential_next) if potential_next else {"question": "继续谈谈你的项目经验吧。", "key_points": []}
    else:
        potential_next = get_questions_by_category(role_key, current_stage, interview.difficulty, kp_list)

        # 降级 1：若带难度过滤后没题（典型场景：behavioral 题库难度分布不全），去掉 knowledge_points 过滤
        if not potential_next and kp_list:
            potential_next = get_questions_by_category(role_key, current_stage, interview.difficulty, None)

        # 降级 2：换一种难度兜底（优先 medium）
        if not potential_next:
            for fallback_diff in ["中等", "简单", "困难"]:
                potential_next = get_questions_by_category(role_key, current_stage, fallback_diff, None)
                if potential_next:
                    break

        available_next = [q for q in potential_next if q["question"] not in asked_titles]
        target_q_obj = random.choice(available_next if available_next else potential_next) if potential_next else {"question": "请继续。", "key_points": []}
    
    # 5. Prepare LLM Context
    history_str = ""
    for m in messages[-6:]: # Last 3 rounds
        role_name = "面试官" if m.sender == "ai" else "候选人"
        history_str += f"{role_name}: {m.content}\n"

    last_main_q = main_questions_asked[-1] if main_questions_asked else ai_msgs[0]
    
    force_next = ""
    if current_follow_up_count >= 2:
        force_next = "【系统指令：强制切换】当前话题已追问满 2 次，请务必结束当前话题，给出一个简短评价并过渡到下一个问题。"

    # Check if this is the absolute last round
    is_final_move = False
    if question_count >= n:
        is_final_move = True
        target_next_text = "面试即将结束，请做一个结语。"
        force_next = "【系统指令：面试结束】请给出一个礼貌的结束语表示感谢。禁止再提出任何新问题或引导后续对话内容。"
    else:
        target_next_text = target_q_obj["question"]

    # 6. Generate AI Response
    llm_resp = await generate_llm_response(
        role=interview.role,
        question=last_main_q.content,
        expected_points="技术准确性、实践经验", # Can be more dynamic if we store key_points
        conversation_history=history_str,
        target_next_question=target_next_text,
        difficulty=interview.difficulty,
        knowledge_points=interview.knowledge_points,
        force_next_instruction=force_next
    )

    # 7. Update State
    final_is_ended = False
    # Only end if we have asked exactly N main questions AND the AI says MOVE_NEXT (meaning no more follow-ups for the last question)
    if question_count >= n and llm_resp["action"] == "MOVE_NEXT":
        final_is_ended = True
        interview.status = "completed"
        db.commit()

    # Save AI Message
    # Category tag: "Main" vs "FollowUp"
    msg_category = current_stage
    if llm_resp["action"] == "FOLLOW_UP":
        msg_category = f"{current_stage}_FOLLOW_UP"

    ai_msg = models.Message(
        interview_id=interview_id,
        sender="ai",
        content=llm_resp["text"],
        category=msg_category
    )
    db.add(ai_msg)
    db.commit()
    db.refresh(ai_msg)

    # 8. Format Response for Schema
    # MessageResponse expects id, sender, content, created_at, and is_final.
    response = schemas.MessageResponse.model_validate(ai_msg)
    response.is_final = final_is_ended
    
    # 返回值为 Tuple，包含新生成的 user_msg 的主键 ID
    return response, user_msg.id

@router.get("/history", response_model=List[schemas.EvaluationSummary])
def get_interview_history(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    # Fetch completed interviews for the specific user
    results = db.query(models.Evaluation).join(models.Interview).filter(
        models.Interview.user_id == user_id,
        models.Interview.status == "completed"
    ).order_by(models.Evaluation.created_at.desc()).all()
    
    return [
        schemas.EvaluationSummary(
            id=e.interview_id,
            role=e.interview.role,
            difficulty=e.interview.difficulty,
            total_score=e.total_score,
            created_at=e.created_at
        ) for e in results
    ]

@router.post("/{interview_id}/end")
async def end_interview(interview_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    interview = db.query(models.Interview).filter(models.Interview.id == interview_id, models.Interview.user_id == user_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found or unauthorized")

    existing_eval = db.query(models.Evaluation).filter(
        models.Evaluation.interview_id == interview_id
    ).first()
    if existing_eval:
        if interview.status != "completed":
            interview.status = "completed"
            interview.end_time = interview.end_time or datetime.utcnow()
            db.commit()
            db.refresh(existing_eval)
        return {
            "message": "Interview already evaluated.",
            "evaluation": _evaluation_payload(interview, existing_eval),
        }

    # 1. Gather all messages for evaluation
    messages = db.query(models.Message).filter(models.Message.interview_id == interview_id).order_by(models.Message.created_at.asc()).all()
    
    # 2. Call Real LLM Evaluator (Async). The evaluator itself has a hard timeout
    # and returns a fallback report if the model service is unavailable.
    evaluation_data = await evaluate_full_interview(messages, role=interview.role)
    if not isinstance(evaluation_data, dict):
        evaluation_data = {}
    for score_key in [
        "content_score",
        "expression_score",
        "business_scenario_score",
        "problem_solving_score",
        "total_score",
    ]:
        evaluation_data.setdefault(score_key, 0.0)

    from evaluation.expression_evaluator import score_expression
    
    # 从数据库查出所有的 voice_metrics 并反序列化
    voice_records = db.query(models.VoiceMetrics).filter(models.VoiceMetrics.interview_id == interview_id).all()
    metrics_list = []
    for r in voice_records:
        if r.raw_json:
            try:
                metrics_list.append(json.loads(r.raw_json))
            except Exception:
                pass
                
    # 调用打分引擎。表达分析也可能访问 LLM，失败时不阻塞报告落库。
    try:
        expr_result = score_expression(metrics_list, interview.role)
    except Exception as e:
        print(f"[end_interview] expression scoring failed (non-fatal): {type(e).__name__}: {e}")
        expr_result = None
    
    # 声明这三个子分，如果全程无语音输入，默认都是 0.0
    speech_rate_score = 0.0
    clarity_score = 0.0
    confidence_score = 0.0
    
    # 如果打分引擎返回了有效数据（说明本场面试使用了语音回答）
    if expr_result:
        # 覆盖原来 evaluate_full_interview 瞎猜的 expression_score
        evaluation_data["expression_score"] = expr_result.get("expression_score", evaluation_data.get("expression_score", 0))
        
        speech_rate_score = expr_result.get("speech_rate_score", 0.0)
        clarity_score = expr_result.get("clarity_score", 0.0)
        confidence_score = expr_result.get("confidence_score", 0.0)
        
        # 将我们引擎生成的个性化点评追加到最终的综合建议后面
        fb = expr_result.get("feedback", {})
        extra_feedback = f"\n\n【表达分析建议】\n- 语速：{fb.get('speech_rate', '')}\n- 清晰度：{fb.get('clarity', '')}\n- 自信度：{fb.get('confidence', '')}"
        evaluation_data["recommendations"] = evaluation_data.get("recommendations", "") + extra_feedback
        
        # 将完整的前端图表渲染所需结构存在 evaluation_data 中，后面会 dump 进 report_json
        evaluation_data["expression_metrics"] = expr_result

        # 因为 expression_score 被覆盖了，必须重新计算整场面试的总分 total_score
        active_scores = [
            evaluation_data.get("content_score", 0),
            evaluation_data.get("expression_score", 0),
            evaluation_data.get("business_scenario_score", 0),
            evaluation_data.get("problem_solving_score", 0)
        ]
        valid_scores = [float(s) for s in active_scores if s is not None and float(s) > 0]
        if valid_scores:
            evaluation_data["total_score"] = round(sum(valid_scores) / len(valid_scores), 1)

    # -------------------------------------------------------------
    # 2.5 生成学习计划
    # 失败不阻塞主流程
    try:
        study_plan = await generate_study_plan(interview.role, evaluation_data, messages)
        if study_plan:
            evaluation_data["study_plan"] = study_plan
    except Exception as e:
        print(f"[end_interview] study_plan failed (non-fatal): {type(e).__name__}: {e}")

    # 3. Save Evaluation to DB（upsert：已有则更新，避免重复结束面试时报 IntegrityError）
    eval_record = db.query(models.Evaluation).filter(
        models.Evaluation.interview_id == interview_id
    ).first()

    fields = {
        "content_score": evaluation_data.get("content_score", 0),
        "expression_score": evaluation_data.get("expression_score", 0),
        "business_scenario_score": evaluation_data.get("business_scenario_score", 0),
        "problem_solving_score": evaluation_data.get("problem_solving_score", 0),
        "total_score": evaluation_data.get("total_score", 0),
        # V2 新增的三个子字段
        "speech_rate_score": speech_rate_score,
        "clarity_score": clarity_score,
        "confidence_score": confidence_score,
        "report_json": json.dumps(evaluation_data, ensure_ascii=False),
        "recommendations": evaluation_data.get("recommendations", ""),
    }

    if eval_record is None:
        eval_record = models.Evaluation(interview_id=interview_id, **fields)
        db.add(eval_record)
    else:
        for k, v in fields.items():
            setattr(eval_record, k, v)
    interview.status = "completed"
    interview.end_time = interview.end_time or datetime.utcnow()
    db.commit()
    db.refresh(eval_record)
    
    return {
        "message": "Interview ended and evaluated successfully.",
        "evaluation": _evaluation_payload(interview, eval_record),
    }
