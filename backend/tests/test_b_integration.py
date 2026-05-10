import asyncio
import json
import os
import sys

# 确保脚本能找到 backend 目录下的模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import SessionLocal
from db import models
from routers.interview import end_interview

async def run_integration_test():
    db = SessionLocal()
    try:
        # 1. 确保数据库中有一个测试用户
        user = db.query(models.User).filter(models.User.id == 1).first()
        if not user:
            user = models.User(id=1, username="test_b_user", password_hash="dummy_hash")
            db.add(user)
            db.commit()

        # 2. 创建一场测试用的虚拟面试
        interview = models.Interview(user_id=1, role="Java后端开发工程师", status="in_progress")
        db.add(interview)
        db.commit()
        db.refresh(interview)

        # 3. 创建一条假的用户消息（假装用户刚刚回答完问题）
        msg = models.Message(
            interview_id=interview.id, 
            sender="user", 
            content="嗯，HashMap 是基于数组加链表实现的，然后在 JDK 1.8 之后引入了红黑树优化。"
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)

        # 4. 强行把 mock 数据注入到 A 同学负责的 voice_metrics 表中
        mock_file_path = os.path.join(os.path.dirname(__file__), "mock_voice_metrics.json")
        with open(mock_file_path, "r", encoding="utf-8") as f:
            mock_data = json.load(f)[0]  # 取第一条 mock 数据
        
        vm = models.VoiceMetrics(
            interview_id=interview.id,
            message_id=msg.id,
            wpm=mock_data["wpm"],
            pause_ratio=mock_data["pause_ratio"],
            filler_total=mock_data["filler_total"],
            pitch_std=mock_data["pitch_std"],
            raw_json=json.dumps(mock_data)
        )
        db.add(vm)
        db.commit()

        print(f"✅ 假数据注入成功！生成的 Interview ID: {interview.id}")
        print("⏳ 正在调用 end_interview 接口...")
        print("   （后台将同时触发原有的【内容评估】和我们新写的【表达分析】大模型，请等待 5-10 秒钟）")

        # 5. 直接调用你刚刚修改好的业务路由函数！
        result = await end_interview(interview_id=interview.id, db=db, user_id=1)
        
        print("\n🎉 测试成功！最终合并生成的报告数据如下：")
        
        # 提取并打印我们最关心的字段
        eval_data = result.get("evaluation", {})
        print(f"\n▶ 综合表达分 (被我们的引擎覆盖): {eval_data.get('expression_score')}")
        print(f"  - 语速子分: {eval_data.get('speech_rate_score')}")
        print(f"  - 清晰度子分: {eval_data.get('clarity_score')}")
        print(f"  - 自信度子分: {eval_data.get('confidence_score')}")
        
        print("\n▶ 个性化建议 (Recommendations):")
        print(eval_data.get('recommendations'))

    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_integration_test())