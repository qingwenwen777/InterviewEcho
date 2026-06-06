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


async def _build_interviewer_system_prompt(role, question, expected_points, conversation_history, target_next_question, difficulty, knowledge_points, force_next_instruction):
    """Run RAG retrieval and assemble the interviewer system prompt.

    Shared by both the blocking and streaming response generators so the prompt
    stays identical regardless of transport.
    """
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

    return prompt_manager.get_interviewer_prompt(
        role=role,
        question=question,
        expected_points=expected_points,
        conversation_history=conversation_history,
        target_next_question=target_next_question,
        difficulty=difficulty,
        knowledge_points=knowledge_points,
        force_next_instruction=force_next_instruction,
        rag_context=rag_context,
    )


def _extract_partial_json_string(buffer: str, key: str):
    """Incrementally pull a string field out of an in-progress JSON object.

    Returns (value, complete). ``value`` is the decoded partial string, or None
    if the field has not started yet. ``complete`` is True once the closing
    quote has been parsed. Designed to be called repeatedly on a growing buffer
    while a JSON response streams in.
    """
    marker = f'"{key}"'
    key_idx = buffer.find(marker)
    if key_idx == -1:
        return None, False

    i = key_idx + len(marker)
    n = len(buffer)
    while i < n and buffer[i] in " \t\r\n":
        i += 1
    if i >= n or buffer[i] != ":":
        return None, False
    i += 1
    while i < n and buffer[i] in " \t\r\n":
        i += 1
    if i >= n or buffer[i] != '"':
        return None, False
    i += 1  # first char of the value

    escapes = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\", "/": "/", "b": "\b", "f": "\f"}
    out = []
    while i < n:
        c = buffer[i]
        if c == "\\":
            if i + 1 >= n:
                break  # incomplete escape; wait for more
            nxt = buffer[i + 1]
            if nxt == "u":
                if i + 6 <= n:
                    try:
                        out.append(chr(int(buffer[i + 2:i + 6], 16)))
                    except ValueError:
                        pass
                    i += 6
                    continue
                break  # incomplete \uXXXX; wait for more
            out.append(escapes.get(nxt, nxt))
            i += 2
            continue
        if c == '"':
            return "".join(out), True
        out.append(c)
        i += 1
    return "".join(out), False


async def generate_llm_response(role, question, expected_points, conversation_history, target_next_question, difficulty="medium", knowledge_points="", force_next_instruction=""):
    """
    Generate conversational follow-up or next question using AI logic.
    Returns: {"action": "FOLLOW_UP" | "MOVE_NEXT" | "CLOSE", "text": "..."}
    """
    system_prompt = await _build_interviewer_system_prompt(
        role, question, expected_points, conversation_history,
        target_next_question, difficulty, knowledge_points, force_next_instruction,
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
        if "面试结束" in (force_next_instruction or ""):
            return {
                "action": "CLOSE",
                "text": "【面试结束】谢谢你刚才的补充。本轮模拟面试到这里结束，接下来我会结合你的整体回答生成评估报告。"
            }
        return {
            "action": "MOVE_NEXT",
            "text": "抱歉，刚才信号有点不好。我们直接看下一个话题： " + target_next_question
        }


async def generate_llm_response_stream(role, question, expected_points, conversation_history, target_next_question, difficulty="medium", knowledge_points="", force_next_instruction=""):
    """Streaming variant of :func:`generate_llm_response`.

    Async generator yielding event dicts:
      - {"type": "delta", "text": "<new fragment of the spoken text>"}
      - {"type": "done", "action": "...", "text": "<full spoken text>"}

    The model returns a JSON object ``{thought, action, text}``; only the value
    of ``text`` is streamed to the candidate. On any failure a single ``done``
    event with a graceful fallback is emitted so callers always terminate.
    """
    is_closing_turn = "面试结束" in (force_next_instruction or "")
    fallback_text = (
        "【面试结束】谢谢你刚才的补充。本轮模拟面试到这里结束，接下来我会结合你的整体回答生成评估报告。"
        if is_closing_turn
        else "抱歉，刚才信号有点不好。我们直接看下一个话题： " + target_next_question
    )
    try:
        system_prompt = await _build_interviewer_system_prompt(
            role, question, expected_points, conversation_history,
            target_next_question, difficulty, knowledge_points, force_next_instruction,
        )

        stream = await asyncio.wait_for(
            client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[{"role": "system", "content": system_prompt}],
                response_format={"type": "json_object"},
                stream=True,
            ),
            timeout=LLM_CALL_TIMEOUT_SECONDS,
        )

        buffer = ""
        emitted = 0
        async for event in stream:
            choices = getattr(event, "choices", None)
            if not choices:
                continue
            delta = choices[0].delta.content if choices[0].delta else None
            if not delta:
                continue
            buffer += delta
            current_text, _complete = _extract_partial_json_string(buffer, "text")
            if current_text is not None and len(current_text) > emitted:
                yield {"type": "delta", "text": current_text[emitted:]}
                emitted = len(current_text)

        action = "MOVE_NEXT"
        text = ""
        try:
            data = json.loads(buffer)
            action = data.get("action", "MOVE_NEXT")
            text = data.get("text", "")
        except Exception:
            # Fall back to whatever we managed to extract while streaming.
            text, _ = _extract_partial_json_string(buffer, "text")
            text = text or ""
        if not text:
            text = fallback_text if is_closing_turn else "好了，我们进行下一个话题。"
        yield {"type": "done", "action": "CLOSE" if is_closing_turn else action, "text": text}
    except Exception as e:
        print(f"Error streaming LLM: {type(e).__name__}: {e}")
        yield {"type": "done", "action": "CLOSE" if is_closing_turn else "MOVE_NEXT", "text": fallback_text}

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


def _string_list(value, limit: int = 8) -> list[str]:
    if not isinstance(value, list):
        return []
    result = []
    for item in value[:limit]:
        if isinstance(item, str):
            text = item.strip()
        elif isinstance(item, dict):
            text = " / ".join(str(part).strip() for part in item.values() if str(part).strip())
        else:
            text = str(item).strip()
        if text:
            result.append(text[:220])
    return result


async def parse_resume_profile(text: str) -> dict:
    """
    Use the configured OpenAI-compatible LLM to turn raw resume text into a
    compact profile snapshot. Returns a safe fallback if the LLM is unavailable.
    """
    raw = (text or "").strip()
    if not raw:
        return {
            "summary": "",
            "skills": [],
            "education": [],
            "experience": [],
            "projects": [],
            "headline": "",
            "target_role": "",
        }

    prompt_text = raw[:9000]
    fallback = {
        "summary": prompt_text[:500],
        "skills": [],
        "education": [],
        "experience": [],
        "projects": [],
        "headline": "",
        "target_role": "",
    }

    try:
        response = await _create_chat_completion(
            timeout_seconds=30,
            model=settings.LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是招聘场景的简历信息抽取助手。请从候选人简历中提取可用于模拟面试的资料，"
                        "不要编造。只输出 JSON：summary 字符串；headline 字符串；target_role 字符串；"
                        "skills、education、experience、projects 均为字符串数组。summary 控制在 120 字以内，"
                        "每个数组最多 8 条，每条适合面试官快速阅读。"
                    ),
                },
                {"role": "user", "content": prompt_text},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        content = (response.choices[0].message.content or "").strip()
        data = json.loads(content)
        if not isinstance(data, dict):
            return fallback
        return {
            "summary": str(data.get("summary") or fallback["summary"]).strip()[:700],
            "headline": str(data.get("headline") or "").strip()[:160],
            "target_role": str(data.get("target_role") or "").strip()[:80],
            "skills": _string_list(data.get("skills"), 12),
            "education": _string_list(data.get("education"), 6),
            "experience": _string_list(data.get("experience"), 8),
            "projects": _string_list(data.get("projects"), 8),
        }
    except Exception as e:
        print(f"[parse_resume_profile] LLM error: {type(e).__name__}: {e}")
        return fallback

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


def _stringify_study_task(task) -> str:
    if isinstance(task, str):
        return task
    if isinstance(task, dict):
        title = task.get("title") or task.get("type") or ""
        note = task.get("note") or task.get("description") or ""
        return "：".join(part for part in [title, note] if part) or "完成一项针对性练习"
    return "完成一项针对性练习"


def _normalize_weak_area(area) -> dict:
    if isinstance(area, dict):
        name = area.get("area") or area.get("title") or area.get("name") or "待加强领域"
        return {
            "area": name,
            "severity": area.get("severity") or "中",
            "diagnosis": area.get("diagnosis") or area.get("note") or str(name),
        }
    if isinstance(area, str):
        return {"area": area, "severity": "中", "diagnosis": area}
    return {"area": "待加强领域", "severity": "中", "diagnosis": "建议结合报告详情继续复盘。"}


def _normalize_study_plan(data: dict) -> dict:
    if not isinstance(data, dict):
        data = {}

    fallback_weeks = [
        {
            "week": 1,
            "focus": "夯实核心基础",
            "tasks": ["复盘本次薄弱题目并整理关键概念", "补齐一个高频知识点的原理图谱", "完成一次 20 分钟口述练习"],
        },
        {
            "week": 2,
            "focus": "强化工程实践",
            "tasks": ["阅读一篇官方文档并写 150 字总结", "用小 Demo 验证一个工程化知识点", "整理项目中可量化的技术亮点"],
        },
        {
            "week": 3,
            "focus": "提升表达结构",
            "tasks": ["准备 STAR 结构项目案例", "录制 3 分钟技术讲解并复盘", "把复杂问题拆成背景、方案、结果三段"],
        },
        {
            "week": 4,
            "focus": "模拟面试冲刺",
            "tasks": ["完成一轮同岗位限时模拟", "复盘错题并更新答案模板", "总结 5 个可追问的项目细节"],
        },
    ]

    weak_areas = data.get("weak_areas") if isinstance(data.get("weak_areas"), list) else []
    quick_wins = data.get("quick_wins") if isinstance(data.get("quick_wins"), list) else []
    raw_plan = data.get("plan") if isinstance(data.get("plan"), list) else []

    normalized_weeks = []
    for index, fallback in enumerate(fallback_weeks):
        raw = raw_plan[index] if index < len(raw_plan) and isinstance(raw_plan[index], dict) else {}
        raw_tasks = raw.get("tasks") if isinstance(raw.get("tasks"), list) else []
        tasks = [_stringify_study_task(task) for task in raw_tasks[:3]]
        while len(tasks) < 3:
            tasks.append(fallback["tasks"][len(tasks)])
        normalized_weeks.append(
            {
                "week": raw.get("week") or fallback["week"],
                "focus": raw.get("focus") or fallback["focus"],
                "tasks": tasks,
            }
        )

    return {
        **data,
        "weak_areas": [_normalize_weak_area(area) for area in weak_areas[:3]],
        "quick_wins": [_stringify_study_task(item) for item in quick_wins[:3]]
        or ["完成一次同岗位限时复盘", "整理 3 个高频追问答案", "用 10 分钟复述本次最弱知识点"],
        "plan": normalized_weeks,
    }


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
                {"role": "user", "content": "请根据上述评估结果，按约定 JSON 格式输出学习计划。plan 必须且只能包含 4 个 week，每个 week 给出 3 个 tasks；weak_areas 最多 3 个，quick_wins 3 个。"},
            ],
            temperature=0.5,
            response_format={"type": "json_object"},
        )
        content = (response.choices[0].message.content or "").strip()
        data = json.loads(content)
        data = _normalize_study_plan(data)
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
