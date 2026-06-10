import json
import random
import sys
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from routers import interview


class Msg(SimpleNamespace):
    pass


def _patch_candidate_context():
    interview._knowledge_points_for_prompt = lambda db, it, user_id: it.knowledge_points or "[]"


def _ctx(interview_obj, ai_msgs, main_questions, question_count, content="answer"):
    return {
        "interview": interview_obj,
        "messages": [*ai_msgs, Msg(sender="user", category=None, content=content)],
        "ai_msgs": ai_msgs,
        "main_questions_asked": main_questions,
        "current_follow_up_count": 0,
        "question_count": question_count,
        "base_rounds": interview_obj.total_rounds or 6,
        "repo_rounds": interview._repo_round_count_for_custom_questions(
            interview._custom_questions_for_interview(interview_obj)
        ),
        "resume_rounds": interview._resume_round_count_for_custom_questions(
            interview._custom_questions_for_interview(interview_obj)
        ),
        "n": interview._effective_total_rounds(interview_obj),
        "content": content,
    }


def test_repo_deepdive_adds_extra_rounds_and_asks_one_question_per_repo():
    _patch_candidate_context()
    random.seed(0)
    custom_questions = [
        {
            "question": "如何让健康检查 URL 配置化？",
            "expected_points": ["环境变量", "配置文件"],
            "repo": "owner/Golive",
            "section": "项目经历·Golive",
        },
        {
            "question": "如果直播间消息量翻倍，你会先改哪条链路？",
            "expected_points": ["链路拆分", "压测"],
            "repo": "owner/Golive",
            "section": "项目经历·Golive",
        },
        {
            "question": "你会如何设计后台权限模型？",
            "expected_points": ["RBAC", "最小权限"],
            "repo": "owner/AdminPanel",
            "section": "项目经历·AdminPanel",
        },
    ]
    interview_obj = SimpleNamespace(
        role="Web前端开发工程师",
        difficulty="中等",
        knowledge_points="[]",
        total_rounds=3,
        custom_questions=json.dumps(custom_questions, ensure_ascii=False),
    )
    intro = Msg(sender="ai", category="introduction", content="intro")

    assert interview._effective_total_rounds(interview_obj) == 5

    first_plan = interview._plan_interview_turn(_ctx(interview_obj, [intro], [], 0), None, 1)
    assert first_plan["is_intro_move"]
    assert first_plan["current_stage"] == "business_scenario"

    scenario = Msg(sender="ai", category="business_scenario", content=first_plan["target_next_text"])
    project_one_plan = interview._plan_interview_turn(
        _ctx(interview_obj, [intro, scenario], [scenario], 1),
        None,
        1,
    )
    assert project_one_plan["current_stage"] == "project"
    assert project_one_plan["target_next_text"].startswith("在你的项目“Golive”中")
    assert project_one_plan["target_q_obj"]["source"] == "github_repo"
    assert project_one_plan["target_q_obj"]["question_id"]

    project_one = Msg(
        sender="ai",
        category=None,
        content="paraphrased project question",
        action="MOVE_NEXT",
        source="github_repo",
        question_id=project_one_plan["target_q_obj"]["question_id"],
        round_index=2,
    )
    project_two_plan = interview._plan_interview_turn(
        _ctx(interview_obj, [intro, scenario, project_one], [scenario, project_one], 2),
        None,
        1,
    )
    assert project_two_plan["current_stage"] == "project"
    assert project_two_plan["target_next_text"].startswith("在你的项目“AdminPanel”中")

    project_two = Msg(sender="ai", category="project", content=project_two_plan["target_next_text"])
    regular_plan = interview._plan_interview_turn(
        _ctx(interview_obj, [intro, scenario, project_one, project_two], [scenario, project_one, project_two], 3),
        None,
        1,
    )
    assert regular_plan["current_stage"] == "problem_solving"


def test_follow_up_limit_uses_llm_path_and_current_question_points():
    _patch_candidate_context()
    random.seed(0)
    question = next(
        item
        for item in interview._load_role_questions("java-backend")
        if item.get("question") == "介绍一下 JVM 的运行时数据区（内存布局）？"
    )
    interview_obj = SimpleNamespace(
        role="Java后端开发工程师",
        difficulty="中等",
        knowledge_points=json.dumps(["JVM原理"], ensure_ascii=False),
        total_rounds=6,
        custom_questions=None,
    )
    intro = Msg(sender="ai", category="introduction", content="intro")
    main = Msg(sender="ai", category="problem_solving", content=f"好的，我们进入下一题：{question['question']}")
    follow = Msg(sender="ai", category="problem_solving_FOLLOW_UP", content="追问：Full GC 怎么排查？")
    ctx = _ctx(interview_obj, [intro, main, follow], [main], 1)
    ctx["current_follow_up_count"] = 1

    plan = interview._plan_interview_turn(ctx, None, 1)

    assert plan["follow_up_limit_reached"]
    assert not plan["force_transition"]
    assert "堆 (Heap)" in plan["expected_points"]
    assert plan["target_next_text"] != question["question"]


def test_configured_project_round_keys_allow_multiple_questions_per_repo():
    _patch_candidate_context()
    custom_questions = [
        {
            "question": "First repo deep dive?",
            "expected_points": ["ownership"],
            "repo": "owner/Golive",
            "source": "github_repo",
            "section": "项目经历·Golive",
            "repo_round_key": "owner/Golive:round:1",
        },
        {
            "question": "Second repo deep dive?",
            "expected_points": ["tradeoff"],
            "repo": "owner/Golive",
            "source": "github_repo",
            "section": "项目经历·Golive",
            "repo_round_key": "owner/Golive:round:2",
        },
    ]
    interview_obj = SimpleNamespace(
        role="Web前端开发工程师",
        difficulty="中等",
        knowledge_points="[]",
        total_rounds=1,
        custom_questions=json.dumps(custom_questions, ensure_ascii=False),
    )
    intro = Msg(sender="ai", category="introduction", content="intro")
    scenario = Msg(sender="ai", category="business_scenario", content="scenario", action="MOVE_NEXT")

    assert interview._repo_round_count_for_custom_questions(custom_questions) == 2
    assert interview._effective_total_rounds(interview_obj) == 3

    first_project_plan = interview._plan_interview_turn(
        _ctx(interview_obj, [intro, scenario], [scenario], 1),
        None,
        1,
    )
    assert first_project_plan["current_stage"] == "project"
    assert first_project_plan["target_q_obj"]["question"] == "在你的项目“Golive”中，First repo deep dive?"

    project_one = Msg(
        sender="ai",
        category="project",
        content=first_project_plan["target_q_obj"]["question"],
        action="MOVE_NEXT",
        source="github_repo",
        question_id=first_project_plan["target_q_obj"]["question_id"],
        round_index=2,
    )
    second_project_plan = interview._plan_interview_turn(
        _ctx(interview_obj, [intro, scenario, project_one], [scenario, project_one], 2),
        None,
        1,
    )
    assert second_project_plan["current_stage"] == "project"
    assert second_project_plan["target_q_obj"]["question"] == "在你的项目“Golive”中，Second repo deep dive?"


def test_resume_round_keys_count_requested_resume_rounds():
    resume_questions = [
        {
            "question": "Resume deep dive 1?",
            "source": "resume_profile",
            "category": "resume",
            "resume_round_key": "resume:round:1",
        },
        {
            "question": "Resume deep dive 2?",
            "source": "resume_profile",
            "category": "resume",
            "resume_round_key": "resume:round:2",
        },
    ]

    assert interview._resume_round_count_for_custom_questions(resume_questions) == 2
    assert interview._resume_round_count_for_custom_questions([{**resume_questions[0], "resume_round_key": ""}]) == 1


def test_final_round_uses_natural_closing_plan():
    _patch_candidate_context()
    interview_obj = SimpleNamespace(
        role="Java后端开发工程师",
        difficulty="中等",
        knowledge_points="[]",
        total_rounds=1,
        custom_questions=None,
    )
    main = Msg(
        sender="ai",
        category="problem_solving",
        content="介绍一下 JVM 的运行时数据区（内存布局）？",
        action="MOVE_NEXT",
        source="question_bank",
        round_index=1,
    )
    plan = interview._plan_interview_turn(_ctx(interview_obj, [main], [main], 1), None, 1)

    assert plan["is_final_move"]
    assert plan["target_next_text"].startswith("【面试结束】")
    assert "承接候选人刚才的回答" in plan["force_next"]
    assert "禁止再提出任何新问题" in plan["force_next"]


def test_final_round_can_ask_one_follow_up_before_closing():
    _patch_candidate_context()
    interview_obj = SimpleNamespace(
        role="Web前端开发工程师",
        difficulty="中等",
        knowledge_points="[]",
        total_rounds=3,
        custom_questions=None,
    )
    q1 = Msg(sender="ai", category="business_scenario", content="场景题", action="MOVE_NEXT", source="question_bank", round_index=1)
    q2 = Msg(sender="ai", category="problem_solving", content="技术题", action="MOVE_NEXT", source="question_bank", round_index=2)
    q3 = Msg(sender="ai", category="problem_solving", content="最后一题", action="MOVE_NEXT", source="question_bank", round_index=3)

    plan = interview._plan_interview_turn(_ctx(interview_obj, [q1, q2, q3], [q1, q2, q3], 3), None, 1)

    assert not plan["is_final_move"]
    assert plan["is_final_budget_pending"]
    assert plan["target_next_text"].startswith("【面试结束】")
    assert "FOLLOW_UP" in plan["force_next"]


def test_final_round_closes_after_follow_up_answer():
    _patch_candidate_context()
    interview_obj = SimpleNamespace(
        role="Web前端开发工程师",
        difficulty="中等",
        knowledge_points="[]",
        total_rounds=3,
        custom_questions=None,
    )
    q1 = Msg(sender="ai", category="business_scenario", content="场景题", action="MOVE_NEXT", source="question_bank", round_index=1)
    q2 = Msg(sender="ai", category="problem_solving", content="技术题", action="MOVE_NEXT", source="question_bank", round_index=2)
    q3 = Msg(sender="ai", category="problem_solving", content="最后一题", action="MOVE_NEXT", source="question_bank", round_index=3)
    follow = Msg(sender="ai", category="problem_solving_FOLLOW_UP", content="最后追问", action="FOLLOW_UP", source="llm_follow_up", round_index=3)
    ctx = _ctx(interview_obj, [q1, q2, q3, follow], [q1, q2, q3], 3)
    ctx["current_follow_up_count"] = 1

    plan = interview._plan_interview_turn(ctx, None, 1)

    assert plan["is_final_move"]
    assert not plan["is_final_budget_pending"]
    assert plan["target_next_text"].startswith("【面试结束】")


def test_final_postprocess_marks_close_and_keeps_end_marker():
    plan = {"is_final_move": True, "current_stage": "behavioral", "has_custom": False}
    response = interview._postprocess_llm_resp(
        {"action": "FOLLOW_UP", "text": "谢谢你的回答，本轮模拟面试到这里结束，接下来会生成评估报告。"},
        plan,
        [],
    )

    assert response["action"] == "CLOSE"
    assert response["text"] == interview._closing_message()


def test_final_budget_postprocess_separates_follow_up_from_close():
    plan = {
        "is_final_move": False,
        "is_final_budget_pending": True,
        "current_stage": "behavioral",
        "has_resume": False,
        "has_repo": False,
        "follow_up_limit_reached": False,
        "target_next_text": interview._closing_message(),
    }
    follow = interview._postprocess_llm_resp(
        {"action": "FOLLOW_UP", "text": "能否补充说明 !important 失效的场景？"},
        dict(plan),
        [],
    )
    close = interview._postprocess_llm_resp(
        {"action": "MOVE_NEXT", "text": "【面试结束】这些情况你有了解吗？"},
        dict(plan),
        [],
    )

    assert follow["action"] == "FOLLOW_UP"
    assert close["action"] == "CLOSE"
    assert close["text"] == interview._closing_message()


def test_follow_up_limit_is_hard_guard():
    plan = {
        "is_final_move": False,
        "is_final_budget_pending": False,
        "current_stage": "problem_solving",
        "has_resume": False,
        "has_repo": False,
        "follow_up_limit_reached": True,
        "target_next_text": "下一道题",
    }
    response = interview._postprocess_llm_resp(
        {"action": "FOLLOW_UP", "text": "我再追问一个问题？"},
        plan,
        [],
    )

    assert response["action"] == "MOVE_NEXT"
    assert "下一道题" in response["text"]


def test_follow_up_category_uses_last_main_question_category():
    plan = {
        "current_stage": "behavioral",
        "last_main_q": Msg(category="problem_solving"),
    }

    assert interview._follow_up_category_for_plan(plan) == "problem_solving_FOLLOW_UP"


def test_closing_message_has_explicit_marker():
    assert interview._closing_message().startswith("【面试结束】")


def test_structured_message_fields_drive_round_classification():
    main = Msg(category=None, action="MOVE_NEXT", source="question_bank")
    follow_up = Msg(category=None, action="FOLLOW_UP", source="llm_follow_up")

    assert interview._is_main_question_message(main)
    assert interview._is_follow_up_message(follow_up)


if __name__ == "__main__":
    test_repo_deepdive_adds_extra_rounds_and_asks_one_question_per_repo()
    test_follow_up_limit_uses_llm_path_and_current_question_points()
    test_configured_project_round_keys_allow_multiple_questions_per_repo()
    test_resume_round_keys_count_requested_resume_rounds()
    test_final_round_uses_natural_closing_plan()
    test_final_round_can_ask_one_follow_up_before_closing()
    test_final_round_closes_after_follow_up_answer()
    test_final_postprocess_marks_close_and_keeps_end_marker()
    test_final_budget_postprocess_separates_follow_up_from_close()
    test_follow_up_limit_is_hard_guard()
    test_follow_up_category_uses_last_main_question_category()
    test_closing_message_has_explicit_marker()
    test_structured_message_fields_drive_round_classification()
    print("interview planning tests passed")
