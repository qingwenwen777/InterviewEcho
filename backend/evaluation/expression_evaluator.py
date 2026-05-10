"""
表达评分聚合 - B 负责实现。

入参：A 产出的 VoiceMetrics 列表（一场面试所有用户语音回答）
出参：ExpressionScore dict（参见 docs/expression_module_contract.md §2.2）

约定：
- 评分 rubric 写在 expression_rubric.md
- 填充词清单从 filler_words 模块 import，禁止硬编码
- metrics_list 为空 → 返回 None
- 单条 metrics 缺字段 → 跳过该条，不抛错
"""

import json
import asyncio
import threading
import os
from typing import Optional
from collections import Counter

from core.llm_service import _create_chat_completion
from core.config import settings
from core.prompts import prompt_manager
from evaluation.filler_words import FILLER_WORDS

def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


EXPRESSION_LLM_TIMEOUT_SECONDS = _env_float("LLM_EXPRESSION_TIMEOUT_SECONDS", 25.0)
EXPRESSION_THREAD_TIMEOUT_SECONDS = EXPRESSION_LLM_TIMEOUT_SECONDS + 5.0


def clamp(value: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
    """辅助函数：将数值硬性限制在 [min_val, max_val] 区间内"""
    return max(min_val, min(value, max_val))


async def _async_evaluate_semantics(metrics_list: list[dict]) -> dict:
    """异步调用大模型进行语义和情感的批量分析"""
    prompt = prompt_manager.get_expression_evaluator_prompt()
    
    # 组装 LLM 需要的极简 JSON 数组格式
    input_data = []
    for idx, m in enumerate(metrics_list):
        input_data.append({
            "message_id": m.get("message_id", idx + 1),  # 若缺少 message_id，默认给一个自增序号
            "transcript": m.get("transcript", ""),
            "wpm": m.get("wpm", 0.0),
            "pause_ratio": m.get("pause_ratio", 0.0),
            "filler_total": m.get("filler_total", 0),
            "pitch_std": m.get("pitch_std", 0.0)
        })
        
    try:
        response = await _create_chat_completion(
            timeout_seconds=EXPRESSION_LLM_TIMEOUT_SECONDS,
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(input_data, ensure_ascii=False)}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"调用 LLM 进行表达分析时出错: {e}")
        return {}


def run_async_in_thread(coro) -> dict:
    """
    黑科技：在单独的线程中安全地运行异步代码。
    解决同步函数 score_expression 在 FastAPI 异步环境调用时引发的 "Event loop already running" 冲突。
    """
    result = {}
    exception = None

    def runner():
        nonlocal result, exception
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(coro)
            loop.close()
        except Exception as e:
            exception = e

    t = threading.Thread(target=runner, daemon=True)
    t.start()
    t.join(timeout=EXPRESSION_THREAD_TIMEOUT_SECONDS)

    if t.is_alive():
        print(f"表达分析 LLM 超过 {EXPRESSION_THREAD_TIMEOUT_SECONDS:.0f}s 未返回，已跳过语义增强评分。")
        return {}

    if exception:
        print(f"线程执行异步 LLM 任务失败: {exception}")
    return result


def score_expression(
    metrics_list: list[dict],
    role: Optional[str] = None,
) -> Optional[dict]:
    """
    Args:
        metrics_list: A 的 analyze_audio() 返回值列表
        role: 岗位名（可选，不同岗位语速期待不同）

    Returns:
        ExpressionScore dict 或 None（无语音输入）
    """
    if not metrics_list:
        return None
        
    # 1. 过滤不合规的无效数据，防崩溃保护
    valid_metrics = [m for m in metrics_list if "transcript" in m and "wpm" in m]
    if not valid_metrics:
        return None

    # 2. 批量调用大模型进行深度的语义与情感分析
    llm_result = run_async_in_thread(_async_evaluate_semantics(valid_metrics))
    
    # 将 LLM 结果转为以 message_id 为 key 的字典，方便 O(1) 快速读取
    per_message_llm = {}
    for item in (llm_result.get("per_message_analysis") or []):
        msg_id = item.get("message_id", 0)
        per_message_llm[msg_id] = item

    # 3. 初始化全局状态累加器
    total_wpm = 0.0
    total_pause_ratio = 0.0
    total_filler_count = 0
    total_pitch_std = 0.0
    
    total_wpm_score = 0.0
    total_clarity_score = 0.0
    total_confidence_score = 0.0
    
    all_filler_words = Counter()
    results_per_message = []

    # 4. 逐题计算打分 (结合物理规则与大模型评分)
    for idx, m in enumerate(valid_metrics):
        msg_id = m.get("message_id", idx + 1)
        wpm = m.get("wpm", 0.0)
        pause_ratio = m.get("pause_ratio", 0.0)
        filler_total = m.get("filler_total", 0)
        pitch_std = m.get("pitch_std", 0.0)
        volume_std = m.get("volume_std", 0.0)

        # ---------------- 维度一：语速 (Speech Rate) ----------------
        if 180 <= wpm <= 240:
            wpm_score = 100.0
        elif wpm < 180:
            wpm_score = 100.0 - ((180.0 - wpm) / 10.0) * 5.0
        else:
            wpm_score = 100.0 - ((wpm - 240.0) / 10.0) * 5.0
        wpm_score = clamp(wpm_score)

        # ---------------- 维度二：清晰度 (Clarity) ----------------
        # 物理连贯性基础扣分
        clarity_physical = 100.0 - max(0.0, pause_ratio - 0.2) * 100.0 * 2.0 - filler_total * 2.0
        clarity_physical = clamp(clarity_physical)
        
        # 提取大模型的语义通顺度 (若异常则给默认值 70)
        llm_item = per_message_llm.get(msg_id, {})
        clarity_semantic = llm_item.get("clarity_semantic_score", 70.0)
        
        # 加权融合
        clarity_score = clamp(clarity_physical * 0.6 + clarity_semantic * 0.4)

        # ---------------- 维度三：自信度 (Confidence) ----------------
        # 声音稳定性基础扣分
        confidence_physical = 100.0 - max(0.0, pitch_std - 15.0) * 1.5 - max(0.0, volume_std - 0.02) * 100.0 * 5.0
        confidence_physical = clamp(confidence_physical)

        # 提取大模型的用词笃定感
        confidence_semantic = llm_item.get("confidence_semantic_score", 70.0)

        # 加权融合
        confidence_score = clamp(confidence_physical * 0.4 + confidence_semantic * 0.6)

        # 记录单题结果
        results_per_message.append({
            "message_id": msg_id,
            "wpm": round(wpm, 1),
            "clarity": round(clarity_score, 1),
            "confidence": round(confidence_score, 1)
        })

        # --- 累加供全局使用 ---
        total_wpm += wpm
        total_pause_ratio += pause_ratio
        total_filler_count += filler_total
        total_pitch_std += pitch_std

        total_wpm_score += wpm_score
        total_clarity_score += clarity_score
        total_confidence_score += confidence_score

        # 统计本题填充词分布 (遵守契约，严格过滤不合规词汇)
        fillers = m.get("filler_words", [])
        for f in fillers:
            if f.get("word") in FILLER_WORDS:
                all_filler_words[f["word"]] += f.get("count", 1)
            
    # 5. 全局聚合计算
    num_msgs = len(valid_metrics)
    avg_wpm = total_wpm / num_msgs
    avg_pause_ratio = total_pause_ratio / num_msgs
    
    avg_wpm_score = total_wpm_score / num_msgs
    avg_clarity_score = total_clarity_score / num_msgs
    avg_confidence_score = total_confidence_score / num_msgs
    
    # 最终的三大维度平均分
    expression_score = (avg_wpm_score + avg_clarity_score + avg_confidence_score) / 3.0
    
    # 综合评估面板需要的其他次要指标
    avg_pitch_std = total_pitch_std / num_msgs
    pitch_stability = clamp(1.0 - (avg_pitch_std / 30.0), 0.0, 1.0)  # 将基频波动映射到 0~1 的稳定性指数
    
    top_fillers = [{"word": k, "count": v} for k, v in all_filler_words.most_common(5)]
    
    # 提取个性化反馈建议，配置降级方案
    overall_llm = llm_result.get("overall_analysis") or {}
    feedback = {
        "speech_rate": overall_llm.get("feedback_speech_rate", f"您的平均语速为 {round(avg_wpm)} 字/分钟，节奏控制得当。"),
        "clarity": overall_llm.get("feedback_clarity", "逻辑表达基本清晰，继续保持。"),
        "confidence": overall_llm.get("feedback_confidence", "发声较为稳定，请继续保持专业与自信。")
    }

    # 6. 返回满足契约结构的最终大数据字典
    return {
        "speech_rate_score": round(avg_wpm_score, 1),
        "clarity_score": round(avg_clarity_score, 1),
        "confidence_score": round(avg_confidence_score, 1),
        "expression_score": round(expression_score, 1),
        "metrics_summary": {
            "avg_wpm": round(avg_wpm, 1),
            "avg_pause_ratio": round(avg_pause_ratio, 3),
            "total_filler_count": total_filler_count,
            "top_filler_words": top_fillers,
            "pitch_stability": round(pitch_stability, 2)
        },
        "feedback": feedback,
        "per_message": results_per_message
    }
