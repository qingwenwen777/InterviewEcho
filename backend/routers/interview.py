from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
import asyncio
import uuid
import shutil
import tempfile
from services.stt_service import stt_service
from services.audio_analysis import analyze_audio
from services.repo_analyzer import analyze_repo
from services.tts_service import TTSServiceError, get_tts_options, synthesize_interviewer_audio
from core.config import settings
from core.llm_service import (
    generate_llm_response,
    generate_llm_response_stream,
    evaluate_full_interview,
    polish_text,
    generate_repo_questions,
    generate_resume_questions,
    generate_resume_match_report,
    generate_study_plan,
    _normalize_round_reviews,
)
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List
import json
import os
import random
import re
import hashlib
from db import models, schemas
from db.database import SessionLocal, get_db
from datetime import datetime

router = APIRouter()

VOICE_POLISH_TIMEOUT_SECONDS = 8.0

def _safe_json_loads(value, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def _evaluation_payload(interview: models.Interview, eval_record: models.Evaluation, messages: list | None = None) -> dict:
    report_data = _safe_json_loads(eval_record.report_json, {})
    repo_context = _safe_json_loads(interview.repo_context, None)
    custom_questions = _safe_json_loads(interview.custom_questions, None)
    round_reviews = report_data.get("round_reviews") or []
    if not round_reviews and messages:
        round_reviews = _normalize_round_reviews(messages, [])

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
        "round_reviews": round_reviews,
        "resume_match": report_data.get("resume_match"),
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


def _normalize_url(value: str) -> str:
    return (value or "").strip().rstrip("/")


def _summary_matches_url(summary: dict, url: str) -> bool:
    if not isinstance(summary, dict):
        return False
    target = _normalize_url(url)
    if not target:
        return False
    candidates = [
        summary.get("url", ""),
        f"https://github.com/{summary.get('full_name', '')}",
    ]
    return any(_normalize_url(candidate) == target for candidate in candidates if candidate)


def _profile_snapshot_for_interview(db: Session, user_id: int) -> dict:
    profile = db.query(models.UserProfile).filter(models.UserProfile.user_id == user_id).first()
    if not profile:
        return {}
    snapshot = {
        "headline": profile.headline or "",
        "target_role": profile.target_role or "",
        "summary": profile.resume_summary or "",
        "skills": _safe_json_loads(profile.skills, []),
        "education": _safe_json_loads(profile.education, []),
        "experience": _safe_json_loads(profile.experience, []),
        "projects": _safe_json_loads(profile.projects, []),
        "resume_excerpt": (profile.resume_text or "")[:2400],
    }
    has_resume_signal = any(
        snapshot.get(key)
        for key in ("headline", "target_role", "summary", "skills", "education", "experience", "projects", "resume_excerpt")
    )
    return snapshot if has_resume_signal else {}


def _candidate_context_for_prompt(db: Session, user_id: int) -> str:
    profile_snapshot = _profile_snapshot_for_interview(db, user_id)
    lines = []
    if profile_snapshot:
        if profile_snapshot.get("summary"):
            lines.append(f"简历摘要：{profile_snapshot['summary']}")
        skills = profile_snapshot.get("skills") or []
        if skills:
            lines.append("技能关键词：" + "、".join(str(item) for item in skills[:10]))
        experience = profile_snapshot.get("experience") or []
        if experience:
            lines.append("经历亮点：" + "；".join(str(item) for item in experience[:4]))
        profile_projects = profile_snapshot.get("projects") or []
        if profile_projects:
            lines.append("简历项目：" + "；".join(str(item) for item in profile_projects[:3]))
    return "\n".join(lines)[:2600]


def _knowledge_points_for_prompt(db: Session, interview: models.Interview, user_id: int) -> str:
    candidate_context = _candidate_context_for_prompt(db, user_id)
    if not candidate_context:
        return interview.knowledge_points or "[]"
    return (
        f"{interview.knowledge_points or '[]'}\n\n"
        "【候选人长期资料】\n"
        f"{candidate_context}\n"
        "请在自我介绍、项目经历、场景题中自然参考这些信息，避免机械复述简历。"
    )


_QUESTION_NOISE_RE = re.compile(r"[\s\W_]+", re.UNICODE)
MAIN_QUESTION_CATEGORIES = {"business_scenario", "project", "resume", "problem_solving", "behavioral"}
QUESTION_MESSAGE_SOURCES = {"question_bank", "github_repo", "resume_profile", "fallback"}


def _is_main_question_message(message: models.Message) -> bool:
    action = getattr(message, "action", None)
    source = getattr(message, "source", None)
    if action:
        return action == "MOVE_NEXT" and source in QUESTION_MESSAGE_SOURCES
    return (message.category or "") in MAIN_QUESTION_CATEGORIES


def _is_follow_up_message(message: models.Message) -> bool:
    action = getattr(message, "action", None)
    if action:
        return action == "FOLLOW_UP"
    return (message.category or "").endswith("_FOLLOW_UP")


def _normalize_question_text(value: str) -> str:
    text = (value or "").lower()
    text = re.sub(
        r"(感谢你的回答|你已经|不过我想|我想进一步问一下|接下来|下一题|好的|请问|能否|能不能|一下|哪些|什么)",
        "",
        text,
    )
    return _QUESTION_NOISE_RE.sub("", text)


def _char_bigrams(text: str) -> set[str]:
    if len(text) < 2:
        return {text} if text else set()
    return {text[i : i + 2] for i in range(len(text) - 1)}


def _question_similarity(left: str, right: str) -> float:
    left_norm = _normalize_question_text(left)
    right_norm = _normalize_question_text(right)
    if not left_norm or not right_norm:
        return 0.0
    if left_norm in right_norm or right_norm in left_norm:
        return min(len(left_norm), len(right_norm)) / max(len(left_norm), len(right_norm))
    left_set = _char_bigrams(left_norm)
    right_set = _char_bigrams(right_norm)
    return len(left_set & right_set) / max(1, len(left_set | right_set))


def _question_was_asked(question: str, ai_messages: list, question_id: str = "") -> bool:
    if question_id and any(getattr(m, "question_id", None) == question_id for m in ai_messages):
        return True
    if not question:
        return False
    return any(
        question in (m.content or "") or _question_similarity(question, m.content or "") >= 0.72
        for m in ai_messages
    )


def _is_repeated_ai_question(text: str, ai_messages: list) -> bool:
    if not text:
        return False
    return any(_question_similarity(text, m.content or "") >= 0.62 for m in ai_messages[-5:])


def _with_forced_question(text: str, question: str, repo_name: str = "") -> str:
    text = (text or "").strip()
    if not question or question in text:
        return text
    if text and text[-1] not in "。！？!?":
        text += "。"
    if question.startswith("在你的项目"):
        return f"{text} {question}" if text else question
    prefix = f"接下来我想针对你的 GitHub 项目 {repo_name} 深挖一个具体问题：" if repo_name else "接下来我想针对你的 GitHub 项目深挖一个具体问题："
    return f"{text} {prefix}{question}" if text else f"{prefix}{question}"


def _with_forced_resume_question(text: str, question: str) -> str:
    text = (text or "").strip()
    if not question or question in text:
        return text
    if text and text[-1] not in "。！？!?":
        text += "。"
    prefix = "接下来我想针对你的简历深挖一个具体问题："
    return f"{text} {prefix}{question}" if text else f"{prefix}{question}"


def _first_question_message(question: str) -> str:
    return f"好的，感谢你的自我介绍。我们进入第一题：{question}"


def _is_skip_or_boundary_answer(content: str) -> bool:
    text = (content or "").strip().lower()
    compact = "".join(text.split())
    if not compact:
        return False
    phrases = [
        "不会",
        "不知道",
        "不清楚",
        "没听过",
        "不了解",
        "想不出来",
        "答不上来",
        "跳过",
        "下一个",
        "下一题",
        "过吧",
        "过了",
        "你问过了",
        "问过了",
        "别问了",
        "换一个",
        "pass",
        "skip",
        "next",
    ]
    if any(phrase in compact for phrase in phrases):
        return True
    return compact in {"过", "不会了", "不知道了"}


def _max_follow_ups_for_interview(total_rounds: int) -> int:
    if total_rounds <= 2:
        return max(0, settings.INTERVIEW_SHORT_ROUNDS_MAX_FOLLOW_UPS)
    return max(0, settings.INTERVIEW_MAX_FOLLOW_UPS_PER_QUESTION)


def _closing_message() -> str:
    return "【面试结束】谢谢你刚才的补充。本轮模拟面试到这里结束，接下来我会结合你的整体回答生成评估报告。"


def _normalize_closing_text(text: str) -> str:
    cleaned = (text or "").strip()
    if not cleaned:
        return _closing_message()
    if not cleaned.startswith("【面试结束】"):
        cleaned = f"【面试结束】{cleaned}"
    return cleaned


def _move_next_message(question: str, skipped: bool = False) -> str:
    if skipped:
        return f"好的，这个点先跳过。下一题：{question}"
    return f"好的，我们进入下一题：{question}"

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

def _questions_file_for_role(role_key: str) -> str:
    backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(os.path.dirname(backend_path), "knowledge-base", role_key, "questions.json")


def _load_role_questions(role_key: str) -> list[dict]:
    questions_file = _questions_file_for_role(role_key)
    if not os.path.exists(questions_file):
        return []
    try:
        with open(questions_file, "r", encoding="utf-8") as f:
            questions = json.load(f)
            return questions if isinstance(questions, list) else []
    except Exception:
        return []


def _custom_questions_for_interview(interview: models.Interview) -> list[dict]:
    if not interview.custom_questions:
        return []
    try:
        questions = json.loads(interview.custom_questions)
        return questions if isinstance(questions, list) else []
    except Exception:
        return []


def _repo_key_for_question(question_obj: dict) -> str:
    if not isinstance(question_obj, dict):
        return "__github_repo__"
    return (
        str(question_obj.get("repo") or "").strip()
        or str(question_obj.get("section") or "").strip()
        or "__github_repo__"
    )


def _is_resume_custom_question(question_obj: dict) -> bool:
    if not isinstance(question_obj, dict):
        return False
    return (
        str(question_obj.get("source") or "").strip() == "resume_profile"
        or str(question_obj.get("category") or "").strip() == "resume"
        or str(question_obj.get("section") or "").strip().startswith("简历")
    )


def _is_github_custom_question(question_obj: dict) -> bool:
    if not isinstance(question_obj, dict) or _is_resume_custom_question(question_obj):
        return False
    return (
        str(question_obj.get("source") or "").strip() == "github_repo"
        or bool(str(question_obj.get("repo") or "").strip())
        or "项目经历·" in str(question_obj.get("section") or "")
    )


def _repo_keys_for_custom_questions(custom_questions: list[dict]) -> list[str]:
    keys = []
    for question in custom_questions:
        if not _is_github_custom_question(question):
            continue
        key = _repo_key_for_question(question)
        if key not in keys:
            keys.append(key)
    return keys


def _repo_round_count_for_custom_questions(custom_questions: list[dict]) -> int:
    return len(_repo_keys_for_custom_questions(custom_questions))


def _resume_round_count_for_custom_questions(custom_questions: list[dict]) -> int:
    return 1 if any(_is_resume_custom_question(question) for question in custom_questions) else 0


def _effective_total_rounds(interview: models.Interview) -> int:
    base_rounds = interview.total_rounds or 6
    custom_questions = _custom_questions_for_interview(interview)
    return base_rounds + _repo_round_count_for_custom_questions(custom_questions) + _resume_round_count_for_custom_questions(custom_questions)


def _question_source(question_obj: dict, stage: str) -> str:
    if isinstance(question_obj, dict) and question_obj.get("source"):
        return str(question_obj["source"])
    if stage == "resume" or _is_resume_custom_question(question_obj):
        return "resume_profile"
    if isinstance(question_obj, dict) and question_obj.get("repo"):
        return "github_repo"
    if stage == "project" and isinstance(question_obj, dict) and "项目经历·" in str(question_obj.get("section", "")):
        return "github_repo"
    return "question_bank"


def _stable_question_id(question_obj: dict, stage: str) -> str:
    if isinstance(question_obj, dict):
        for key in ("question_id", "id"):
            value = question_obj.get(key)
            if value:
                return str(value)
    source = _question_source(question_obj, stage)
    repo_key = _repo_key_for_question(question_obj)
    question_text = (question_obj.get("question") or "") if isinstance(question_obj, dict) else ""
    raw = f"{source}|{stage}|{repo_key}|{question_text}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
    return f"{source}:{stage}:{digest}"


def _with_question_identity(question_obj: dict, stage: str) -> dict:
    question_copy = dict(question_obj or {})
    question_copy["source"] = _question_source(question_copy, stage)
    question_copy["question_id"] = _stable_question_id(question_copy, stage)
    return question_copy


def _question_points(question_obj: dict) -> list[str]:
    if not isinstance(question_obj, dict):
        return []
    points = question_obj.get("key_points") or question_obj.get("expected_points") or []
    return points if isinstance(points, list) else []


def _expected_points_for_main_question(role_key: str, interview: models.Interview, main_question: models.Message | None) -> str:
    if not main_question:
        return "技术准确性、实践经验"

    text = main_question.content or ""
    candidates = _custom_questions_for_interview(interview) + _load_role_questions(role_key)
    best_question = None
    best_score = 0.0
    for candidate in candidates:
        candidate = _with_question_identity(candidate, candidate.get("category", "project") if isinstance(candidate, dict) else "project")
        if getattr(main_question, "question_id", None) and candidate.get("question_id") == main_question.question_id:
            best_question = candidate
            best_score = 1.0
            break
        question_text = candidate.get("question", "") if isinstance(candidate, dict) else ""
        if not question_text:
            continue
        score = 1.0 if question_text in text else _question_similarity(question_text, text)
        if score > best_score:
            best_question = candidate
            best_score = score

    if best_question and best_score >= 0.62:
        points = _question_points(best_question)
        if points:
            return "、".join(str(point) for point in points)
    return "技术准确性、实践经验"


def _repo_display_name(question_obj: dict) -> str:
    repo = (question_obj.get("repo") or "").strip() if isinstance(question_obj, dict) else ""
    if repo:
        return repo.split("/")[-1] or repo
    section = (question_obj.get("section") or "").strip() if isinstance(question_obj, dict) else ""
    if "·" in section:
        return section.rsplit("·", 1)[-1].strip()
    return repo


def _with_repo_project_context(question_obj: dict) -> dict:
    question_copy = dict(question_obj or {})
    question_text = (question_copy.get("question") or "").strip()
    repo_name = _repo_display_name(question_copy)
    if question_text and repo_name and "你的项目" not in question_text and repo_name not in question_text:
        question_copy["question"] = f"在你的项目“{repo_name}”中，{question_text}"
    return question_copy


def _fallback_question_for_stage(stage: str, ai_msgs: list) -> dict:
    fallbacks = {
        "business_scenario": [
            "请结合一个真实业务场景，说明你会如何拆解问题、评估风险并推进落地？",
            "如果线上出现一个影响用户体验的问题，你会如何定位优先级并组织排查？",
        ],
        "project": [
            "请选一个你最熟悉的项目模块，讲讲它的核心设计、权衡以及你后续会如何优化？",
            "围绕你做过的一个项目，说明一次具体的技术取舍以及最终效果。",
        ],
        "resume": [
            "请结合你简历中最能代表岗位匹配度的一段经历，说明你的个人职责、技术选择和最终结果。",
            "你简历里有哪些能力点是本岗位最需要的？请用一个具体经历证明它。",
        ],
        "problem_solving": [
            "请选一个你熟悉的核心技术点，讲清楚它的底层原理、适用场景和常见坑。",
            "如果一个系统性能突然下降，你会从哪些指标和链路开始排查？",
        ],
        "behavioral": [
            "请讲一次你和他人在技术方案上意见不一致的经历，你是如何沟通和推进的？",
            "请讲一次你面对不熟悉问题时的处理过程，包括你如何学习、验证和复盘。",
        ],
    }
    for question in fallbacks.get(stage, fallbacks["behavioral"]):
        if not _question_was_asked(question, ai_msgs):
            return _with_question_identity({"question": question, "key_points": ["结构化表达", "具体经历", "复盘能力"], "source": "fallback"}, stage)
    return _with_question_identity({"question": "我们换一个角度，请结合一个具体经历说明你的判断、行动和复盘。", "key_points": ["结构化表达", "具体经历", "复盘能力"], "source": "fallback"}, stage)


def _select_unasked_question(role_key: str, stage: str, difficulty: str, knowledge_points: list[str], ai_msgs: list) -> dict:
    search_scopes = [
        (difficulty, knowledge_points),
        (difficulty, None),
        ("中等", None),
        ("简单", None),
        ("困难", None),
    ]
    seen_scopes = set()
    for diff, points in search_scopes:
        scope_key = (diff, tuple(points or []))
        if scope_key in seen_scopes:
            continue
        seen_scopes.add(scope_key)
        potential = get_questions_by_category(role_key, stage, diff, points)
        potential = [_with_question_identity(q, stage) for q in potential]
        available = [q for q in potential if not _question_was_asked(q.get("question", ""), ai_msgs, q.get("question_id", ""))]
        if available:
            return random.choice(available)
    return _fallback_question_for_stage(stage, ai_msgs)


def get_questions_by_category(role_key: str, category: str, difficulty: str = "medium", knowledge_points: List[str] = None):
    # Map role key to actual JSON file

    diff_map = {"简单": "easy", "中等": "medium", "困难": "hard"}
    target_diff = diff_map.get(difficulty, "medium")

    try:
        all_questions = _load_role_questions(role_key)
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

    # v3/v6: 如果用户提供了 GitHub 项目链接或简历资料，生成定制深挖题。
    repo_context_json = None
    custom_questions_json = None
    all_custom_questions = []
    resume_deepdive_rounds = 0
    repo_deepdive_rounds = 0

    profile_snapshot = _profile_snapshot_for_interview(db, user_id)
    if profile_snapshot:
        resume_questions = await generate_resume_questions(data.role, profile_snapshot)
        if resume_questions:
            all_custom_questions.extend(resume_questions)
            resume_deepdive_rounds = _resume_round_count_for_custom_questions(resume_questions)
            print(f"[start_interview] generated {len(resume_questions)} resume deep-dive questions")

    repo_urls = (data.repo_urls or [])[:3]   # 最多 3 个
    if repo_urls:
        preview_summaries = data.repo_summaries or []
        print(f"[start_interview] preparing {len(repo_urls)} repos...")
        repo_summaries = []
        for url in repo_urls:
            if not url or not url.strip():
                continue
            summary = next((item for item in preview_summaries if _summary_matches_url(item, url)), None)
            if summary:
                print(f"[start_interview] reuse preview summary: {summary.get('full_name', url)}")
            else:
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
        repo_deepdive_rounds = _repo_round_count_for_custom_questions(all_custom_questions)
        if repo_deepdive_rounds:
            print(f"[start_interview] generated {repo_deepdive_rounds} repo deep-dive rounds")

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
    profile_note = "我也会结合你在用户中心保存的简历资料来观察匹配度。" if profile_snapshot else ""
    resume_round_note = f"你已保存简历资料，我会额外增加 {resume_deepdive_rounds} 轮简历深挖。" if resume_deepdive_rounds else ""
    repo_round_note = f"你选择了 GitHub 项目深挖，我会额外增加 {repo_deepdive_rounds} 轮，每个项目 1 题。" if repo_deepdive_rounds else ""
    greeting = f"你好，我是你的{data.role}面试官。很高兴见到你。本次常规面试共设定为 {data.total_rounds} 轮提问。{resume_round_note}{repo_round_note}{profile_note}在正式开始前，请先做一个简单的自我介绍。"
    ai_msg = models.Message(
        interview_id=new_interview.id,
        sender="ai",
        content=greeting,
        category="introduction",
        round_index=0,
        question_id="introduction",
        action="INTRO",
        source="system",
    )
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
    responses = [schemas.MessageResponse.model_validate(message) for message in messages]
    if interview.status == "completed":
        for message in reversed(responses):
            if message.sender == "ai":
                message.is_final = True
                break
    return responses

@router.get("/{interview_id}/evaluation", response_model=schemas.EvaluationDetail)
def get_evaluation(interview_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    eval_record = db.query(models.Evaluation).join(models.Interview).filter(
        models.Evaluation.interview_id == interview_id,
        models.Interview.user_id == user_id
    ).first()
    if not eval_record:
        raise HTTPException(status_code=404, detail="Evaluation not found or unauthorized")

    messages = db.query(models.Message).filter(
        models.Message.interview_id == interview_id
    ).order_by(models.Message.created_at.asc()).all()
    return schemas.EvaluationDetail(**_evaluation_payload(eval_record.interview, eval_record, messages))

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


def _sse(payload: dict) -> str:
    """Serialise a Server-Sent Events data frame."""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.post("/{interview_id}/message/stream")
async def send_message_stream(interview_id: int, msg: schemas.MessageSend, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    """Streaming counterpart of :func:`send_message`.

    Streams the interviewer reply as Server-Sent Events so the frontend can
    render the answer progressively instead of waiting for the full response.

    Event frames (JSON in the SSE ``data:`` field):
      - {"type": "user", "message": {...}}            # echoes the saved user message
      - {"type": "delta", "text": "<fragment>"}        # incremental reply text
      - {"type": "done", "message": {...}, "is_final": bool}
      - {"type": "error", "detail": "..."}
    """
    ctx = _load_turn_context(interview_id, msg.content, db, user_id, None)
    interview = ctx["interview"]
    user_msg = ctx["user_msg"]
    user_payload = schemas.MessageResponse.model_validate(user_msg).model_dump(mode="json")

    plan = _plan_interview_turn(ctx, db, user_id)

    async def event_stream():
        try:
            yield _sse({"type": "user", "message": user_payload})

            # Deterministic transitions do not need token streaming, but we
            # still emit the text as a single delta so the frontend rendering
            # path stays identical.
            if plan["is_intro_move"]:
                llm_resp = {"action": "MOVE_NEXT", "text": _first_question_message(plan["target_next_text"])}
                yield _sse({"type": "delta", "text": llm_resp["text"]})
            elif plan["force_transition"]:
                llm_resp = {"action": "MOVE_NEXT", "text": _move_next_message(plan["target_next_text"], skipped=plan["skipped_or_boundary"])}
                yield _sse({"type": "delta", "text": llm_resp["text"]})
            else:
                action = "MOVE_NEXT"
                full_text = ""
                async for ev in generate_llm_response_stream(
                    role=interview.role,
                    question=plan["last_main_q"].content,
                    expected_points=plan["expected_points"],
                    conversation_history=plan["history_str"],
                    target_next_question=plan["target_next_text"],
                    difficulty=interview.difficulty,
                    knowledge_points=plan["knowledge_points"],
                    force_next_instruction=plan["force_next"],
                ):
                    if ev["type"] == "delta":
                        yield _sse({"type": "delta", "text": ev["text"]})
                    elif ev["type"] == "done":
                        action = ev.get("action", "MOVE_NEXT")
                        full_text = ev.get("text", "")
                llm_resp = {"action": action, "text": full_text}

                # Project-deepdive forcing may append a question that was not part
                # of the streamed text; surface the appended remainder as a delta.
                before_text = llm_resp["text"]
                llm_resp = _postprocess_llm_resp(llm_resp, plan, ctx["ai_msgs"])
                if llm_resp["text"] != before_text:
                    if llm_resp["text"].startswith(before_text):
                        remainder = llm_resp["text"][len(before_text):]
                        if remainder:
                            yield _sse({"type": "delta", "text": remainder})
                    else:
                        # Text was fully replaced (repeated follow-up guard).
                        yield _sse({"type": "replace", "text": llm_resp["text"]})

            response, _ai_msg, final_is_ended = _finalize_ai_turn(db, ctx, plan, llm_resp)
            yield _sse({
                "type": "done",
                "message": response.model_dump(mode="json"),
                "is_final": final_is_ended,
            })
        except Exception as e:
            print(f"[send_message_stream] error: {type(e).__name__}: {e}")
            db.rollback()
            yield _sse({"type": "error", "detail": "生成回复时出现问题，请重试。"})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )


@router.get("/tts/options")
def tts_options(user_id: int = Depends(get_current_user_id)):
    return get_tts_options()


@router.post("/{interview_id}/messages/{message_id}/tts", response_model=schemas.TTSResponse)
async def synthesize_message_tts(
    interview_id: int,
    message_id: int,
    data: schemas.TTSRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    interview = db.query(models.Interview).filter(
        models.Interview.id == interview_id,
        models.Interview.user_id == user_id,
    ).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found or unauthorized")

    message = db.query(models.Message).filter(
        models.Message.id == message_id,
        models.Message.interview_id == interview_id,
        models.Message.sender == "ai",
    ).first()
    if not message:
        raise HTTPException(status_code=404, detail="AI message not found")

    try:
        return await synthesize_interviewer_audio(
            message.content or "",
            voice=data.voice or "mimo_default",
            speed=data.speed or "normal",
            style=data.style or "calm",
        )
    except TTSServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def _voice_upload_root() -> str:
    if settings.VOICE_UPLOAD_DIR:
        return settings.VOICE_UPLOAD_DIR
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads", "voice"))


def _persist_voice_upload(interview_id: int, file: UploadFile) -> tuple[str, str]:
    extension = os.path.splitext(file.filename or "")[1].lower()
    if extension not in {".webm", ".wav", ".mp3", ".m4a", ".mp4", ".ogg"}:
        extension = ".webm"
    target_dir = os.path.join(_voice_upload_root(), str(interview_id))
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, f"voice_{uuid.uuid4()}{extension}")
    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return target_path, file.content_type or ""


def _store_voice_metrics(db: Session, interview_id: int, message_id: int, audio_path: str, stt_result: dict) -> None:
    existing = db.query(models.VoiceMetrics).filter(models.VoiceMetrics.message_id == message_id).first()
    if existing:
        return
    metrics = analyze_audio(audio_path, stt_result)
    if metrics is None:
        print(f"[voice_metrics] skip (audio too short or empty) for interview={interview_id}")
        return
    vm = models.VoiceMetrics(
        interview_id=interview_id,
        message_id=message_id,
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
    print(f"[voice_metrics] saved for interview={interview_id}, message={message_id}, wpm={metrics['wpm']}")


def _has_ai_reply_after(db: Session, interview_id: int, user_msg_id: int) -> bool:
    return db.query(models.Message).filter(
        models.Message.interview_id == interview_id,
        models.Message.sender == "ai",
        models.Message.id > user_msg_id,
    ).first() is not None


def _store_voice_reply_fallback(db: Session, interview_id: int, user_id: int, user_msg_id: int) -> None:
    if _has_ai_reply_after(db, interview_id, user_msg_id):
        return

    interview = db.query(models.Interview).filter(
        models.Interview.id == interview_id,
        models.Interview.user_id == user_id,
    ).first()
    role_text = interview.role if interview else "目标岗位"
    fallback_text = (
        "刚才生成追问时出现了短暂异常，我们先继续保持面试节奏。"
        f"下一题：请结合{role_text}的实际工作场景，说明一次你定位并解决技术问题的过程。"
    )
    previous_ai = db.query(models.Message).filter(models.Message.interview_id == interview_id, models.Message.sender == "ai").order_by(models.Message.created_at.asc()).all()
    previous_rounds = [message for message in previous_ai if _is_main_question_message(message)]
    fallback_question = _with_question_identity({"question": fallback_text, "source": "fallback"}, "problem_solving")
    ai_msg = models.Message(
        interview_id=interview_id,
        sender="ai",
        content=fallback_text,
        category="voice_fallback",
        round_index=len(previous_rounds) + 1,
        question_id=fallback_question["question_id"],
        action="MOVE_NEXT",
        source="fallback",
    )
    db.add(ai_msg)
    db.commit()
    print(f"[voice_reply_job] fallback AI message saved for interview={interview_id}, user_message={user_msg_id}")


async def _run_voice_reply_job(interview_id: int, user_id: int, user_msg_id: int, audio_path: str, stt_result: dict):
    db = SessionLocal()
    try:
        user_msg = db.query(models.Message).filter(
            models.Message.id == user_msg_id,
            models.Message.interview_id == interview_id,
            models.Message.sender == "user",
        ).first()
        if not user_msg:
            print(f"[voice_reply_job] user message not found: {user_msg_id}")
            return

        try:
            polished = await asyncio.wait_for(
                polish_text(user_msg.content or ""),
                timeout=VOICE_POLISH_TIMEOUT_SECONDS,
            )
            if polished and polished != user_msg.content:
                user_msg.content = polished
                stt_result = {**(stt_result or {}), "text": polished}
                db.commit()
        except asyncio.TimeoutError:
            print(f"[voice_reply_job] polish timeout after {VOICE_POLISH_TIMEOUT_SECONDS}s; using raw transcript")
        except Exception as e:
            print(f"[voice_reply_job] polish failed: {type(e).__name__}: {e}")

        try:
            await process_message_logic(interview_id, user_msg.content or "", db, user_id, user_msg=user_msg)
        except Exception as e:
            print(f"[voice_reply_job] AI reply failed: {type(e).__name__}: {e}")
            db.rollback()
            try:
                _store_voice_reply_fallback(db, interview_id, user_id, user_msg_id)
            except Exception as fallback_error:
                db.rollback()
                print(f"[voice_reply_job] fallback save failed: {type(fallback_error).__name__}: {fallback_error}")

        try:
            _store_voice_metrics(db, interview_id, user_msg_id, audio_path, stt_result)
        except Exception as e:
            print(f"[voice_metrics] analyze failed: {type(e).__name__}: {e}")
            db.rollback()
    finally:
        db.close()


@router.post("/{interview_id}/voice", response_model=schemas.VoiceResponse)
async def upload_voice(
    interview_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    interview = db.query(models.Interview).filter(models.Interview.id == interview_id, models.Interview.user_id == user_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found or unauthorized")

    audio_path, mime_type = _persist_voice_upload(interview_id, file)
    stt_result = stt_service.transcribe_detailed(audio_path, mime_type=mime_type)
    if not stt_result or not stt_result.get("text"):
        try:
            os.remove(audio_path)
        except OSError:
            pass
        raise HTTPException(status_code=400, detail="语音转录失败，请重试或手动输入")

    transcript = stt_result["text"].strip()
    user_msg = models.Message(
        interview_id=interview_id,
        sender="user",
        content=transcript,
        audio_path=audio_path,
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    background_tasks.add_task(_run_voice_reply_job, interview_id, user_id, user_msg.id, audio_path, stt_result)
    return schemas.VoiceResponse(
        transcription=transcript,
        user_message=schemas.MessageResponse.model_validate(user_msg),
        ai_message=None,
        reply_status="processing",
    )

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

def _load_turn_context(interview_id: int, content: str, db: Session, user_id: int, user_msg: models.Message | None):
    """Steps 1-3: fetch interview, persist the user message, and summarise history.

    Shared by the blocking and streaming message handlers.
    """
    interview = db.query(models.Interview).filter(models.Interview.id == interview_id, models.Interview.user_id == user_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found or unauthorized")

    messages_before_user = db.query(models.Message).filter(models.Message.interview_id == interview_id).order_by(models.Message.created_at.asc()).all()
    ai_msgs_before_user = [m for m in messages_before_user if m.sender == "ai"]
    current_main_before_user = None
    for m in ai_msgs_before_user[1:]:
        if _is_main_question_message(m):
            current_main_before_user = m

    if user_msg is None:
        user_msg = models.Message(
            interview_id=interview_id,
            sender="user",
            content=content,
            round_index=current_main_before_user.round_index if current_main_before_user else 0,
            parent_question_id=current_main_before_user.id if current_main_before_user else None,
            action="ANSWER",
            source="candidate",
        )
        db.add(user_msg)
        db.commit()
        db.refresh(user_msg)
    else:
        content = user_msg.content or content
        if not user_msg.action:
            user_msg.round_index = current_main_before_user.round_index if current_main_before_user else 0
            user_msg.parent_question_id = current_main_before_user.id if current_main_before_user else None
            user_msg.action = "ANSWER"
            user_msg.source = "candidate"
            db.commit()
            db.refresh(user_msg)

    messages = db.query(models.Message).filter(models.Message.interview_id == interview_id).order_by(models.Message.created_at.asc()).all()
    ai_msgs = [m for m in messages if m.sender == "ai"]

    main_questions_asked = []
    current_follow_up_count = 0
    for m in ai_msgs[1:]:
        if _is_main_question_message(m):
            main_questions_asked.append(m)
            current_follow_up_count = 0
        elif _is_follow_up_message(m):
            current_follow_up_count += 1

    question_count = len(main_questions_asked)
    base_rounds = interview.total_rounds or 6
    custom_questions = _custom_questions_for_interview(interview)
    repo_rounds = _repo_round_count_for_custom_questions(custom_questions)
    resume_rounds = _resume_round_count_for_custom_questions(custom_questions)
    n = base_rounds + repo_rounds + resume_rounds

    return {
        "interview": interview,
        "user_msg": user_msg,
        "content": content,
        "messages": messages,
        "ai_msgs": ai_msgs,
        "main_questions_asked": main_questions_asked,
        "current_follow_up_count": current_follow_up_count,
        "question_count": question_count,
        "base_rounds": base_rounds,
        "repo_rounds": repo_rounds,
        "resume_rounds": resume_rounds,
        "n": n,
    }


def _store_closing_turn(db: Session, interview: models.Interview, interview_id: int):
    """Persist the closing message once the round budget is exhausted."""
    interview.status = "completed"
    interview.end_time = interview.end_time or datetime.utcnow()
    ai_msg = models.Message(
        interview_id=interview_id,
        sender="ai",
        content=_closing_message(),
        category="closing",
        action="CLOSE",
        source="system",
    )
    db.add(ai_msg)
    db.commit()
    db.refresh(ai_msg)
    response = schemas.MessageResponse.model_validate(ai_msg)
    response.is_final = True
    return response, ai_msg


def _plan_interview_turn(ctx: dict, db: Session, user_id: int) -> dict:
    """Steps 4-5: decide stage, target question, and forcing instructions.

    Returns a plan dict consumed by both the blocking and streaming generators.
    """
    interview = ctx["interview"]
    messages = ctx["messages"]
    ai_msgs = ctx["ai_msgs"]
    main_questions_asked = ctx["main_questions_asked"]
    current_follow_up_count = ctx["current_follow_up_count"]
    question_count = ctx["question_count"]
    base_rounds = ctx["base_rounds"]
    repo_rounds = ctx["repo_rounds"]
    resume_rounds = ctx["resume_rounds"]
    n = ctx["n"]
    skipped_or_boundary = _is_skip_or_boundary_answer(ctx["content"])

    # 4. Determine Stage & Next Target
    # v5 节奏：用户设置的 total_rounds 只计算常规题；GitHub 项目深挖按仓库数额外追加。
    #   有 GitHub 深挖时：scenario → 每个项目 1 题 → problem_solving → behavioral
    #   无 GitHub 深挖时：scenario → problem_solving → behavioral
    custom_questions_list = _custom_questions_for_interview(interview)
    has_resume = _resume_round_count_for_custom_questions(custom_questions_list) > 0
    has_repo = _repo_round_count_for_custom_questions(custom_questions_list) > 0
    has_custom = has_resume or has_repo
    if has_custom:
        scenario_end = max(1, base_rounds // 3)
        resume_end = min(n, scenario_end + resume_rounds)
        project_end = min(n, resume_end + repo_rounds)
        remaining_regular_rounds = max(0, base_rounds - scenario_end)
        solving_rounds = max(1, remaining_regular_rounds // 2) if remaining_regular_rounds else 0
        solving_end = min(n, project_end + solving_rounds)
        if question_count < scenario_end:
            current_stage = "business_scenario"
        elif question_count < resume_end:
            current_stage = "resume"
        elif question_count < project_end:
            current_stage = "project"
        elif question_count < solving_end:
            current_stage = "problem_solving"
        else:
            current_stage = "behavioral"
    else:
        # 3 段分布
        scenario_end = max(1, base_rounds // 3)
        solving_end = scenario_end + max(1, base_rounds // 3)
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

    if current_stage == "resume" and has_resume:
        resume_questions = [
            _with_question_identity(q, "resume")
            for q in custom_questions_list
            if _is_resume_custom_question(q)
        ]
        available_resume = [
            q for q in resume_questions
            if not _question_was_asked(q.get("question", ""), ai_msgs, q.get("question_id", ""))
        ]
        if available_resume:
            target_q_obj = available_resume[0]
        else:
            target_q_obj = _select_unasked_question(role_key, "resume", interview.difficulty, kp_list, ai_msgs)
    elif current_stage == "project" and has_repo:
        # 项目深挖题走强制队列：按生成顺序挑第一道未问过的，避免面试官模型跳过 GitHub 内容。
        custom_questions_list = [
            _with_question_identity(q, "project")
            for q in custom_questions_list
            if _is_github_custom_question(q)
        ]
        asked_repo_keys = {
            _repo_key_for_question(q)
            for q in custom_questions_list
            if _question_was_asked(q.get("question", ""), ai_msgs, q.get("question_id", ""))
        }
        available_custom = [
            q for q in custom_questions_list
            if _repo_key_for_question(q) not in asked_repo_keys
            and not _question_was_asked(q.get("question", ""), ai_msgs, q.get("question_id", ""))
        ]
        if available_custom:
            target_q_obj = _with_repo_project_context(available_custom[0])
        else:
            # 定制问完了，降级到静态 project 题库
            target_q_obj = _select_unasked_question(role_key, "project", interview.difficulty, kp_list, ai_msgs)
    else:
        target_q_obj = _select_unasked_question(role_key, current_stage, interview.difficulty, kp_list, ai_msgs)

    # 5. Prepare LLM Context
    history_str = ""
    for m in messages[-6:]:  # Last 3 rounds
        role_name = "面试官" if m.sender == "ai" else "候选人"
        history_str += f"{role_name}: {m.content}\n"

    last_main_q = main_questions_asked[-1] if main_questions_asked else None

    force_next = ""
    max_follow_ups = _max_follow_ups_for_interview(n)
    follow_up_limit_reached = bool(last_main_q) and current_follow_up_count >= max_follow_ups
    force_transition = skipped_or_boundary
    if skipped_or_boundary:
        force_next = "【系统指令：强制切换】候选人已表达不会、跳过或指出问题重复。必须结束当前问题，不要重复追问同一个知识点，直接进入下一题。"
    elif follow_up_limit_reached:
        force_next = "【系统指令：追问上限】当前主题目的追问次数已到上限。请自然总结候选人刚才的回答，然后进入下一题；不要继续围绕同一个知识点追问。"
    if current_stage == "project" and has_repo and not skipped_or_boundary:
        repo_name = target_q_obj.get("repo", "")
        force_next = f"【系统指令：GitHub 项目深挖】必须结束当前话题并切换到项目深挖。下一题必须围绕候选人的 GitHub 仓库{repo_name}，并且必须用清晰句式自然问出：{target_q_obj.get('question', '')}"
    if current_stage == "resume" and has_resume and not skipped_or_boundary:
        force_next = f"【系统指令：简历深挖】必须结束当前话题并切换到简历深挖。下一题必须明确引用候选人简历中的具体信息，并且必须用清晰句式自然问出：{target_q_obj.get('question', '')}"

    # Check if this is the absolute last round
    is_final_move = False
    if question_count >= n:
        is_final_move = True
        target_next_text = _closing_message()
        force_next = (
            "【系统指令：面试结束】这是最后一轮。请先用一句话承接候选人刚才的回答，"
            "再明确说明本轮模拟面试已结束并将生成评估报告。禁止再提出任何新问题、追问或引导后续对话。"
            "输出的 text 必须以【面试结束】开头。"
        )
    else:
        target_next_text = target_q_obj["question"]

    return {
        "current_stage": current_stage,
        "has_custom": has_custom,
        "has_repo": has_repo,
        "has_resume": has_resume,
        "target_q_obj": target_q_obj,
        "history_str": history_str,
        "last_main_q": last_main_q,
        "force_next": force_next,
        "force_transition": force_transition,
        "follow_up_limit_reached": follow_up_limit_reached,
        "skipped_or_boundary": skipped_or_boundary,
        "is_intro_move": last_main_q is None,
        "is_final_move": is_final_move,
        "target_next_text": target_next_text,
        "knowledge_points": _knowledge_points_for_prompt(db, interview, user_id),
        "expected_points": _expected_points_for_main_question(role_key, interview, last_main_q),
    }


def _postprocess_llm_resp(llm_resp: dict, plan: dict, ai_msgs: list) -> dict:
    """Apply closing, project-deepdive forcing, and repeated-follow-up guards."""
    if plan["is_final_move"]:
        llm_resp["action"] = "CLOSE"
        llm_resp["text"] = _normalize_closing_text(llm_resp.get("text", ""))
        return llm_resp

    if plan["current_stage"] == "resume" and plan.get("has_resume"):
        llm_resp["action"] = "MOVE_NEXT"
        llm_resp["text"] = _with_forced_resume_question(
            llm_resp.get("text", ""),
            plan["target_next_text"],
        )

    if plan["current_stage"] == "project" and plan.get("has_repo"):
        llm_resp["action"] = "MOVE_NEXT"
        llm_resp["text"] = _with_forced_question(
            llm_resp.get("text", ""),
            plan["target_next_text"],
            plan["target_q_obj"].get("repo", ""),
        )
    repeated_follow_up = (
        llm_resp.get("action") == "FOLLOW_UP"
        and _is_repeated_ai_question(llm_resp.get("text", ""), ai_msgs)
    )
    if repeated_follow_up:
        llm_resp["action"] = "MOVE_NEXT"
        llm_resp["text"] = _move_next_message(plan["target_next_text"], skipped=False)
    return llm_resp


def _finalize_ai_turn(db: Session, ctx: dict, plan: dict, llm_resp: dict):
    """Steps 7-8: persist the AI message and build the response model."""
    interview = ctx["interview"]
    question_count = ctx["question_count"]
    n = ctx["n"]

    final_is_ended = False
    # End only on the explicit closing plan, or on the legacy MOVE_NEXT/CLOSE
    # signal after the configured main-question budget has been exhausted.
    if plan.get("is_final_move") or (question_count >= n and llm_resp["action"] in {"MOVE_NEXT", "CLOSE"}):
        final_is_ended = True
        interview.status = "completed"
        interview.end_time = interview.end_time or datetime.utcnow()
        db.commit()

    msg_category = plan["current_stage"]
    if llm_resp["action"] == "FOLLOW_UP":
        msg_category = f"{plan['current_stage']}_FOLLOW_UP"
    elif plan.get("is_final_move"):
        msg_category = "closing"

    is_follow_up = llm_resp["action"] == "FOLLOW_UP"
    last_main_q = plan.get("last_main_q")
    target_q_obj = plan.get("target_q_obj") or {}
    round_index = getattr(last_main_q, "round_index", None) if is_follow_up and last_main_q else question_count + 1
    parent_question_id = last_main_q.id if is_follow_up and last_main_q else None
    if is_follow_up:
        parent_qid = getattr(last_main_q, "question_id", "") if last_main_q else "unknown"
        follow_index = ctx["current_follow_up_count"] + 1
        question_id = f"{parent_qid}:followup:{follow_index}"
        source = "llm_follow_up"
    elif plan.get("is_final_move"):
        round_index = None
        question_id = "closing"
        source = "system_closing"
    else:
        question_id = target_q_obj.get("question_id")
        source = target_q_obj.get("source")

    ai_msg = models.Message(
        interview_id=interview.id,
        sender="ai",
        content=llm_resp["text"],
        category=msg_category,
        round_index=round_index,
        question_id=question_id,
        parent_question_id=parent_question_id,
        action=llm_resp["action"],
        source=source,
    )
    db.add(ai_msg)
    db.commit()
    db.refresh(ai_msg)

    response = schemas.MessageResponse.model_validate(ai_msg)
    response.is_final = final_is_ended
    return response, ai_msg, final_is_ended


async def process_message_logic(interview_id: int, content: str, db: Session, user_id: int, user_msg: models.Message | None = None):
    ctx = _load_turn_context(interview_id, content, db, user_id, user_msg)
    interview = ctx["interview"]
    user_msg = ctx["user_msg"]

    plan = _plan_interview_turn(ctx, db, user_id)

    # 6. Generate AI Response
    if plan["is_intro_move"]:
        llm_resp = {"action": "MOVE_NEXT", "text": _first_question_message(plan["target_next_text"])}
    elif plan["force_transition"]:
        llm_resp = {"action": "MOVE_NEXT", "text": _move_next_message(plan["target_next_text"], skipped=plan["skipped_or_boundary"])}
    else:
        llm_resp = await generate_llm_response(
            role=interview.role,
            question=plan["last_main_q"].content,
            expected_points=plan["expected_points"],
            conversation_history=plan["history_str"],
            target_next_question=plan["target_next_text"],
            difficulty=interview.difficulty,
            knowledge_points=plan["knowledge_points"],
            force_next_instruction=plan["force_next"],
        )
        llm_resp = _postprocess_llm_resp(llm_resp, plan, ctx["ai_msgs"])

    response, _ai_msg, _final = _finalize_ai_turn(db, ctx, plan, llm_resp)
    return response, user_msg.id

async def _build_and_store_evaluation(interview_id: int, db: Session) -> dict | None:
    interview = db.query(models.Interview).filter(models.Interview.id == interview_id).first()
    if not interview:
        return None
    existing_eval = db.query(models.Evaluation).filter(
        models.Evaluation.interview_id == interview_id
    ).first()
    if existing_eval:
        messages = db.query(models.Message).filter(
            models.Message.interview_id == interview_id
        ).order_by(models.Message.created_at.asc()).all()
        if interview.status != "completed":
            interview.status = "completed"
            interview.end_time = interview.end_time or datetime.utcnow()
            db.commit()
            db.refresh(existing_eval)
        return {
            "message": "Interview already evaluated.",
            "evaluation": _evaluation_payload(interview, existing_eval, messages),
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

    voice_messages = db.query(models.Message).filter(
        models.Message.interview_id == interview_id,
        models.Message.sender == "user",
        models.Message.audio_path.isnot(None),
    ).all()
    for message in voice_messages:
        if message.audio_path and os.path.exists(message.audio_path):
            try:
                _store_voice_metrics(
                    db,
                    interview_id,
                    message.id,
                    message.audio_path,
                    {"text": message.content or "", "segments": [], "language": settings.WHISPER_LANGUAGE or "zh"},
                )
            except Exception as e:
                print(f"[end_interview] voice metric backfill failed for message={message.id}: {type(e).__name__}: {e}")
                db.rollback()
    
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

    # 2.6 简历匹配度分析
    # 将“简历是否被回答支撑”显式写进报告，避免简历资料只停留在提问 prompt 中。
    try:
        profile_snapshot = _profile_snapshot_for_interview(db, interview.user_id)
        resume_match = await generate_resume_match_report(interview.role, profile_snapshot, messages)
        if resume_match:
            evaluation_data["resume_match"] = resume_match
    except Exception as e:
        print(f"[end_interview] resume_match failed (non-fatal): {type(e).__name__}: {e}")

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


async def _run_evaluation_job(interview_id: int):
    db = SessionLocal()
    try:
        result = await _build_and_store_evaluation(interview_id, db)
        if result is None:
            print(f"[evaluation_job] interview not found: {interview_id}")
    except Exception as e:
        print(f"[evaluation_job] failed for interview={interview_id}: {type(e).__name__}: {e}")
        db.rollback()
        interview = db.query(models.Interview).filter(models.Interview.id == interview_id).first()
        if interview:
            interview.status = "evaluation_failed"
            db.commit()
    finally:
        db.close()


@router.get("/history", response_model=List[schemas.EvaluationSummary])
def get_interview_history(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    # Include completed evaluations and interviews whose report job is still running.
    results = (
        db.query(models.Interview, models.Evaluation)
        .outerjoin(models.Evaluation, models.Evaluation.interview_id == models.Interview.id)
        .filter(
            models.Interview.user_id == user_id,
            or_(
                models.Evaluation.id.isnot(None),
                models.Interview.status.in_(["evaluating", "evaluation_failed"]),
            ),
        )
        .order_by(func.coalesce(models.Evaluation.created_at, models.Interview.end_time, models.Interview.start_time).desc())
        .all()
    )

    return [
        schemas.EvaluationSummary(
            id=interview.id,
            role=interview.role,
            difficulty=interview.difficulty,
            total_score=evaluation.total_score if evaluation else None,
            status="completed" if evaluation else (interview.status or "in_progress"),
            created_at=evaluation.created_at if evaluation else (interview.end_time or interview.start_time),
        )
        for interview, evaluation in results
    ]


@router.get("/{interview_id}/evaluation/status")
def get_evaluation_status(interview_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    interview = db.query(models.Interview).filter(models.Interview.id == interview_id, models.Interview.user_id == user_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found or unauthorized")

    eval_record = db.query(models.Evaluation).filter(models.Evaluation.interview_id == interview_id).first()
    if eval_record:
        messages = db.query(models.Message).filter(
            models.Message.interview_id == interview_id
        ).order_by(models.Message.created_at.asc()).all()
        return {
            "interview_id": interview_id,
            "status": "completed",
            "retryable": False,
            "evaluation": _evaluation_payload(interview, eval_record, messages),
        }

    status = interview.status or "in_progress"
    return {
        "interview_id": interview_id,
        "status": status,
        "retryable": status in {"evaluation_failed", "completed"},
        "message": "评估报告正在生成中。" if status == "evaluating" else "评估报告尚未生成。",
    }


@router.post("/{interview_id}/end")
async def end_interview(
    interview_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    interview = db.query(models.Interview).filter(models.Interview.id == interview_id, models.Interview.user_id == user_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found or unauthorized")

    existing_eval = db.query(models.Evaluation).filter(
        models.Evaluation.interview_id == interview_id
    ).first()
    if existing_eval:
        messages = db.query(models.Message).filter(
            models.Message.interview_id == interview_id
        ).order_by(models.Message.created_at.asc()).all()
        if interview.status != "completed":
            interview.status = "completed"
            interview.end_time = interview.end_time or datetime.utcnow()
            db.commit()
            db.refresh(existing_eval)
        return {
            "message": "Interview already evaluated.",
            "status": "completed",
            "evaluation": _evaluation_payload(interview, existing_eval, messages),
        }

    if interview.status == "evaluating":
        return {
            "message": "Evaluation already running.",
            "status": "evaluating",
            "interview_id": interview_id,
        }

    interview.status = "evaluating"
    interview.end_time = interview.end_time or datetime.utcnow()
    db.commit()
    background_tasks.add_task(_run_evaluation_job, interview_id)

    return {
        "message": "Evaluation started.",
        "status": "evaluating",
        "interview_id": interview_id,
    }
