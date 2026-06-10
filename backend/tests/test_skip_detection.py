from routers.interview import _is_skip_or_boundary_answer


def test_contextual_unknown_condition_is_not_skip():
    answer = (
        "嗯，对于一个比例固定为 16:9 的响应式视频组件，"
        "如果事先不知道父容器的宽度，我一般会优先使用 CSS 的 aspect-ratio 属性实现。"
    )

    assert not _is_skip_or_boundary_answer(answer)


def test_explicit_inability_or_skip_is_detected():
    assert _is_skip_or_boundary_answer("这题我不知道")
    assert _is_skip_or_boundary_answer("我不会了")
    assert _is_skip_or_boundary_answer("跳过吧")
    assert _is_skip_or_boundary_answer("pass")
