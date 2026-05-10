import os
import json
import asyncio
from openai import AsyncOpenAI
from core.config import settings
from core.prompts import prompt_manager
from services.rag_service import rag_service

def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


LLM_CALL_TIMEOUT_SECONDS = _env_float("LLM_CALL_TIMEOUT_SECONDS", 45.0)
LLM_REPORT_TIMEOUT_SECONDS = _env_float("LLM_REPORT_TIMEOUT_SECONDS", 60.0)
LLM_STUDY_PLAN_TIMEOUT_SECONDS = _env_float("LLM_STUDY_PLAN_TIMEOUT_SECONDS", 30.0)
LLM_RAG_TIMEOUT_SECONDS = _env_float("LLM_RAG_TIMEOUT_SECONDS", 8.0)


# Initialize the OpenAI-compatible client
client = AsyncOpenAI(
    api_key=settings.LLM_API_KEY,
    base_url=settings.LLM_BASE_URL,
    timeout=LLM_CALL_TIMEOUT_SECONDS,
    max_retries=1,
)


async def _create_chat_completion(timeout_seconds: float | None = None, **kwargs):
    """Call the LLM with a hard timeout so one slow request cannot freeze FastAPI."""
    return await asyncio.wait_for(
        client.chat.completions.create(**kwargs),
        timeout=timeout_seconds or LLM_CALL_TIMEOUT_SECONDS,
    )


async def generate_llm_response(role, question, expected_points, conversation_history, target_next_question, difficulty="medium", knowledge_points="", force_next_instruction=""):
    """
    Generate conversational follow-up or next question using AI logic.
    Returns: {"action": "FOLLOW_UP" | "MOVE_NEXT", "text": "..."}
    """
    # 1. Query RAG for expert context
    # Use the current question and the last user message as query for better relevance
    last_user_msg = ""
    if isinstance(conversation_history, list):
        for msg in reversed(conversation_history):
            if isinstance(msg, dict) and msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break
    elif isinstance(conversation_history, str):
        # Extract the last "候选人" (Candidate) message from the formatted string
        lines = conversation_history.strip().split("\n")
        for line in reversed(lines):
            if "候选人:" in line:
                last_user_msg = line.split("候选人:")[-1].strip()
                break
            
    rag_query = f"{question} {last_user_msg}"
    rag_context = await rag_service.query_context_async(rag_query)

    # 2. Get system prompt template
    system_prompt = prompt_manager.get_interviewer_prompt(
        role=role,
        question=question,
        expected_points=expected_points,
        conversation_history=conversation_history,
        target_next_question=target_next_question,
        difficulty=difficulty,
        knowledge_points=knowledge_points,
        force_next_instruction=force_next_instruction,
        rag_context=rag_context
    )
    
    try:
        response = await _create_chat_completion(
            model=settings.LLM_MODEL,
            messages=[{"role": "system", "content": system_prompt}],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        return {
            "action": data.get("action", "MOVE_NEXT"),
            "text": data.get("text", "好了，我们进行下一个话题。")
        }
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return {
            "action": "MOVE_NEXT",
            "text": "抱歉，刚才信号有点不好。我们直接看下一个话题： " + target_next_question
        }

async def polish_text(text: str):
    """
    Add punctuation and fix minor typos in transcribed text.
    """
    if not text.strip():
        return text
        
    try:
        response = await _create_chat_completion(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": "你是一个专业的语音转文字校对专家。你的任务是对面试者的语音转录结果进行微调：1. 加入恰当的中文标点符号。2. 修正明显的谐音错误或技术词错误（例如将“加瓦”修正为“Java”）。3. **保留**原句的所有信息、语气词和口语化倾向（如“呃”、“那个”、“然后”等），不要进行任何润色或改写。4. 保持最小限度的修改，只做必要的纠错和标点添加。直接返回处理后的文本。"},
                {"role": "user", "content": text}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error polishing text: {e}")
        return text

async def generate_repo_questions(role: str, repo_summary: dict) -> list[dict]:
    """
    根据 GitHub 仓库摘要，让 LLM 生成 3-5 个定制的项目深挖问题。

    Args:
        role: 岗位名
        repo_summary: services.repo_analyzer.analyze_repo() 的返回值

    Returns:
        问题列表，每条包含 question / expected_points / tech_focus
        如 LLM 调用失败或格式错误则返回空列表（不阻塞主流程）
    """
    if not repo_summary:
        return []

    system_prompt = prompt_manager.get_repo_question_prompt(role, repo_summary)
    if not system_prompt:
        print("[generate_repo_questions] prompt template empty, skip")
        return []

    try:
        response = await _create_chat_completion(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "请根据上述项目资料生成 3-5 条深挖问题，按约定 JSON 格式输出。"},
            ],
            temperature=0.7,
            response_format={"type": "json_object"},
        )
        content = (response.choices[0].message.content or "").strip()
        data = json.loads(content)
        questions = data.get("questions", [])
        if not isinstance(questions, list):
            print(f"[generate_repo_questions] unexpected format: {data}")
            return []

        # 给每条加上 source 标记，便于下游识别是"定制问题"
        for q in questions:
            q["source"] = "github_repo"
            q["repo"] = repo_summary.get("full_name", "")
            # 统一字段：让其能直接进 questions.json 格式
            q.setdefault("category", "project")
            q.setdefault("difficulty", "medium")
            q.setdefault("section", f"项目经历·{repo_summary.get('name', '')}")
            q.setdefault("key_points", q.get("expected_points", []))

        print(f"[generate_repo_questions] generated {len(questions)} questions for {repo_summary.get('full_name')}")
        return questions
    except json.JSONDecodeError as e:
        print(f"[generate_repo_questions] JSON parse error: {e}; content: {content[:200] if 'content' in dir() else 'N/A'}")
        return []
    except Exception as e:
        print(f"[generate_repo_questions] LLM error: {type(e).__name__}: {e}")
        return []


async def generate_study_plan(role: str, evaluation_data: dict, history: list) -> dict | None:
    """
    根据面试评估结果 + 对话历史，让 LLM 生成分周学习计划 + 资源推荐 + 快速收益项。

    Args:
        role: 岗位名
        evaluation_data: evaluate_full_interview 返回的 dict
        history: 面试完整消息列表（models.Message 对象）

    Returns:
        {
            "weak_areas": [...],
            "plan": [...],
            "quick_wins": [...]
        }
        或 None（LLM 失败）
    """
    # 精选对话片段：只取用户回答 + 对应面试官问题，最多 8 轮
    excerpt_parts = []
    round_count = 0
    for m in history:
        if m.sender == "ai" and m.category and "FOLLOW_UP" not in m.category:
            excerpt_parts.append(f"[面试官] {m.content}")
            round_count += 1
        elif m.sender == "user":
            excerpt_parts.append(f"[候选人] {m.content}")
        if round_count >= 8:
            break
    transcript_excerpt = "\n".join(excerpt_parts) if excerpt_parts else "（暂无对话）"

    system_prompt = prompt_manager.get_study_plan_prompt(role, evaluation_data, transcript_excerpt)
    if not system_prompt:
        print("[generate_study_plan] prompt template empty, skip")
        return None

    try:
        response = await _create_chat_completion(
            timeout_seconds=LLM_STUDY_PLAN_TIMEOUT_SECONDS,
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "请根据上述评估结果，按约定 JSON 格式输出学习计划。"},
            ],
            temperature=0.5,
            response_format={"type": "json_object"},
        )
        content = (response.choices[0].message.content or "").strip()
        data = json.loads(content)
        # 简单校验结构
        if not isinstance(data.get("plan"), list):
            print(f"[generate_study_plan] unexpected format: missing 'plan' list")
            return None
        print(f"[generate_study_plan] generated plan with {len(data.get('plan', []))} weeks, {len(data.get('weak_areas', []))} weak areas")
        return data
    except json.JSONDecodeError as e:
        print(f"[generate_study_plan] JSON parse error: {e}")
        return None
    except Exception as e:
        print(f"[generate_study_plan] LLM error: {type(e).__name__}: {e}")
        return None


# ================= 评分辅助工具 =================

_ROLE_NAME_TO_KEY = {
    "Java后端开发工程师": "java-backend",
    "Web前端开发工程师": "web-frontend",
    "Python算法工程师": "python-algorithm",
}

_EXCELLENT_ANSWERS_MAX_CHARS = 6000  # 避免 prompt 超限


def _load_excellent_answers_for_role(role: str) -> str:
    """
    读取该岗位的优秀回答范例 Markdown 文件。
    按岗位映射到 knowledge-base/<role_key>/interview_excellent_answers.md。
    """
    role_key = _ROLE_NAME_TO_KEY.get(role, "")
    if not role_key:
        return "（未找到该岗位的优秀回答范例文件）"

    kb_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..",
        "knowledge-base", role_key, "interview_excellent_answers.md"
    ))
    if not os.path.exists(kb_path):
        return f"（{role} 的优秀回答范例文件不存在：{kb_path}）"

    try:
        with open(kb_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content[:_EXCELLENT_ANSWERS_MAX_CHARS]
    except Exception as e:
        return f"（读取优秀回答范例失败：{e}）"


async def _rag_retrieve_for_evaluation(history: list, top_k: int = 3) -> str:
    """
    对候选人回答较长的 2-3 轮，用 RAG 检索对应的优秀答案片段。
    Returns: 拼接好的相关优秀答题片段字符串
    """
    # 收集候选人回答长度排名前 3 的消息
    user_msgs = [m for m in history if m.sender == "user"]
    user_msgs.sort(key=lambda m: len(m.content or ""), reverse=True)
    top_msgs = user_msgs[:3]
    if not top_msgs:
        return ""

    all_snippets = []
    try:
        # 懒导入避免循环依赖
        from services.rag_service import rag_service
        for msg in top_msgs:
            # 以候选人回答为 query 检索相关优秀答案
            snippet = await rag_service.query_context_async(msg.content[:200], k=top_k)
            if snippet and snippet not in all_snippets:
                all_snippets.append(f"--- 相关参考答案 ---\n{snippet}")
    except Exception as e:
        print(f"[rag_retrieve_for_evaluation] error: {e}")
        return ""

    return "\n\n".join(all_snippets[:3])


def _build_fallback_evaluation(history: list, role: str = "", reason: str = "") -> dict:
    """Create a conservative report when the model evaluator is unavailable."""
    user_answers = [
        (m.content or "").strip()
        for m in history
        if getattr(m, "sender", "") == "user" and (m.content or "").strip()
    ]
    answer_count = len(user_answers)
    total_chars = sum(len(answer) for answer in user_answers)
    substantive_count = sum(1 for answer in user_answers if len(answer) >= 40)

    if total_chars == 0:
        scores = {
            "content_score": 0.0,
            "expression_score": 0.0,
            "business_scenario_score": 0.0,
            "problem_solving_score": 0.0,
        }
        total_score = 0.0
        highlights = ["面试流程已结束，但没有可评估的候选人回答。"]
        weaknesses = ["缺少有效回答内容，无法进行技术、表达和场景能力判断。"]
    else:
        depth = min(total_chars / 1200.0, 1.0)
        coverage = min(answer_count / 6.0, 1.0)
        substance = min(substantive_count / 4.0, 1.0)
        scores = {
            "content_score": round(45 + depth * 30 + substance * 15, 1),
            "expression_score": round(50 + min(total_chars / 700.0, 1.0) * 25, 1),
            "business_scenario_score": round(40 + coverage * 15 + substance * 25, 1),
            "problem_solving_score": round(40 + depth * 20 + substance * 25, 1),
        }
        valid_scores = [value for value in scores.values() if value > 0]
        total_score = round(sum(valid_scores) / len(valid_scores), 1) if valid_scores else 0.0
        highlights = [
            f"本场面试已记录 {answer_count} 条候选人回答，可用于基础复盘。",
            "系统保留了完整对话，后续可以重新生成更精细的模型评估。",
        ]
        weaknesses = [
            "本次模型评估服务响应超时，当前为兜底评估，细粒度技术判断可能不完整。",
            "建议结合原始对话重点复盘回答的结构、关键术语和业务落地细节。",
        ]

    recommendations = (
        "本次报告由系统兜底生成：后端评估模型在限定时间内没有返回结果，"
        "为了避免历史记录丢失，系统先保存基础评分和复盘建议。"
        "服务恢复后，可以重新结束该场面试来覆盖为完整模型评估。"
    )
    if reason:
        recommendations += f"\n\n技术原因：{reason}"

    return {
        **scores,
        "total_score": total_score,
        "highlights": highlights,
        "weaknesses": weaknesses,
        "recommendations": recommendations,
        "evaluation_mode": "fallback",
        "fallback_reason": reason,
        "answer_count": answer_count,
        "answer_chars": total_chars,
        "role": role,
    }


async def evaluate_full_interview(history: list, role: str = ""):
    """
    Generate the final evaluation report for the complete interview.

    Args:
        history: 消息列表
        role: 岗位名（用于注入岗位差异化评估标准）
    """
    # 1. Build a rich transcript with categories and context
    transcript_parts = []
    for m in history:
        if m.sender == "ai":
            category_text = f"【分类: {m.category}】" if m.category else ""
            transcript_parts.append(f"面试官: {m.content} {category_text}")
        else:
            transcript_parts.append(f"面试者: {m.content}")

    transcript = "\n".join(transcript_parts)

    # 2. 获取岗位特定评估标准
    from core.role_criteria import get_role_criteria
    role_specific_criteria = get_role_criteria(role)

    # 3. 加载该岗位的"优秀回答范例"作为评分参照
    excellent_answers_context = _load_excellent_answers_for_role(role)

    # 4. 用 RAG 检索候选人回答对应的优秀答案片段（只对用户回答较长的轮次）
    try:
        rag_hits = await asyncio.wait_for(
            _rag_retrieve_for_evaluation(history, top_k=3),
            timeout=LLM_RAG_TIMEOUT_SECONDS,
        )
        if rag_hits:
            excellent_answers_context = (
                excellent_answers_context
                + "\n\n【RAG 检索到的相关优秀答题片段】\n"
                + rag_hits
            )
    except Exception as e:
        print(f"[evaluate_full_interview] RAG retrieve failed (non-fatal): {e}")

    # 5. Get system prompt with the new structure
    system_prompt = prompt_manager.get_evaluator_prompt(
        interview_transcript=transcript,
        excellent_answers_context=excellent_answers_context,
        role=role,
        role_specific_criteria=role_specific_criteria,
    )
    
    try:
        response = await _create_chat_completion(
            timeout_seconds=LLM_REPORT_TIMEOUT_SECONDS,
            model=settings.LLM_MODEL,
            messages=[{"role": "system", "content": system_prompt}],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        
        # 3. Process the evaluations to get the average
        evals = data.get("evaluations", [])
        scores = {
            "content_score": [],
            "expression_score": [],
            "business_scenario_score": [],
            "problem_solving_score": []
        }
        
        for e in evals:
            for k in scores.keys():
                val = e.get(k)
                if val is not None and isinstance(val, (int, float)):
                    scores[k].append(val)
        
        # Calculate averages for non-null values
        final_scores = {}
        for k, v in scores.items():
            final_scores[k] = round(sum(v) / len(v), 1) if v else 0.0
            
        # Total score is average of the averages
        active_averages = [v for v in final_scores.values() if v > 0]
        total_score = round(sum(active_averages) / len(active_averages), 1) if active_averages else 0.0
        
        summary = data.get("overall_summary", {})
        
        return {
            "content_score": final_scores["content_score"],
            "expression_score": final_scores["expression_score"],
            "business_scenario_score": final_scores["business_scenario_score"],
            "problem_solving_score": final_scores["problem_solving_score"],
            "total_score": total_score,
            "highlights": summary.get("strengths", []),
            "weaknesses": summary.get("weaknesses", []),
            "recommendations": summary.get("recommendations", "继续努力！")
        }
        
    except Exception as e:
        print(f"Error generating report: {type(e).__name__}: {e}")
        return _build_fallback_evaluation(history, role=role, reason=f"{type(e).__name__}: {e}")
