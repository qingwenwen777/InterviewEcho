"""
B 的本地调试脚本 -- 演示如何用 mock 数据测试 score_expression()

用法（在 backend 目录下执行）：
    cd backend
    python tests/test_expression_evaluator.py

预期输出：
    实现完成前：会抛 NotImplementedError（这是正常的，证明骨架对接成功）
    实现完成后：打印 ExpressionScore dict 的内容

工作流：
    1. 先跑一次，看到 NotImplementedError -> 说明环境 OK
    2. 去 evaluation/expression_evaluator.py 实现 score_expression
    3. 再跑此脚本 -> 看到打印出的评分结果
    4. 反复改 rubric 阈值 + 跑此脚本，直到分数符合预期
    5. 接入到 routers/interview.py 的 end_interview
"""
import json
import os
import sys
from pprint import pprint

# 让 import 能找到上层包（backend/）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.expression_evaluator import score_expression


def main():
    # 1. 加载 mock 数据（A 已经准备好的 3 条样例）
    mock_path = os.path.join(os.path.dirname(__file__), "mock_voice_metrics.json")
    with open(mock_path, "r", encoding="utf-8") as f:
        metrics_list = json.load(f)

    print("[OK] 加载 mock 数据成功，共 {} 条用户语音回答".format(len(metrics_list)))
    print("     样例 1 transcript: {}...".format(metrics_list[0]['transcript'][:30]))
    print("     样例 1 wpm: {}".format(metrics_list[0]['wpm']))
    print("     样例 1 filler_total: {}".format(metrics_list[0]['filler_total']))
    print()

    # 2. 调用你要实现的函数
    print("[..] 调用 score_expression()...")
    try:
        result = score_expression(metrics_list, role="Java后端开发工程师")
    except NotImplementedError:
        print("[XX] score_expression 还未实现 -- 这是正常的，去 expression_evaluator.py 写代码吧！")
        return

    # 3. 校验返回结构是否符合契约 §2.2
    print("[OK] 函数返回成功！结果如下：")
    print()
    pprint(result, width=100)
    print()

    # 4. 简单的契约校验
    required_keys = {
        "speech_rate_score", "clarity_score", "confidence_score",
        "expression_score", "metrics_summary", "feedback", "per_message"
    }
    missing = required_keys - set(result.keys())
    if missing:
        print("[!!] 返回结果缺少字段（参见契约 2.2）: {}".format(missing))
    else:
        print("[OK] 返回结构符合契约 2.2")

    # 5. 测试边界情况
    print()
    print("[..] 测试空列表（用户全程文字作答）...")
    empty_result = score_expression([], role=None)
    if empty_result is None:
        print("[OK] 空列表返回 None，符合契约 4.5")
    else:
        print("[!!] 空列表应返回 None，实际返回: {}".format(empty_result))


if __name__ == "__main__":
    main()
