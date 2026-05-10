# 表达分析模块 - 接口契约文档

> 本文档是 A、B 两人协作开发"表达分析"模块的唯一接口约定。
> 任何对契约的修改必须双方 sign-off 后再更新本文件。

- **赛题来源**：A05《AI 模拟面试与能力提升软件》3)b 表达分析
- **赛题原文**：集成语音识别与情感分析技术，评估语速、清晰度、自信度等表达表现
- **负责人**：A（音频特征 & 声学指标）/ B（情感语义 & 评分报告）
- **版本**：v1.0 (2026-04-18)

---

## 1. 模块边界

```
┌──────────────────┐  audio file   ┌─────────────────────┐  VoiceMetrics  ┌────────────────────────┐
│ frontend         │ ───────────►  │ A: audio_analysis   │ ─────────────► │ DB: voice_metrics 表   │
│ InterviewRoom    │               │ + Whisper detailed  │                │ (每条用户语音一行)     │
└──────────────────┘               └─────────────────────┘                └───────────┬────────────┘
                                                                                      │
                                                                  metrics_list[]      │ end_interview 时拉出
                                                                                      ▼
┌──────────────────┐  ExpressionScore   ┌──────────────────────────┐
│ frontend         │ ◄────────────────  │ B: expression_evaluator  │
│ ReportView       │                    │ + LLM 情感分析 + rubric  │
└──────────────────┘                    └──────────────────────────┘
```

---

## 2. 核心数据契约

### 2.1 VoiceMetrics（A 产出 → B 消费）

**单条用户语音回答的特征。** A 通过 `analyze_audio()` 返回此结构。

```python
{
    "duration_sec": float,          # 音频总时长（秒）
    "transcript": str,              # Whisper 原始文本（未 polish）
    "segments": [                   # Whisper 带时间戳分段
        {"start": float, "end": float, "text": str}
    ],

    # —— 语速维度 ——
    "wpm": float,                   # 字/分钟（中文统一按字算）
    "char_count": int,              # 有效字符数（去标点空格）

    # —— 清晰度维度 ——
    "pause_ratio": float,           # 0~1，静音时长 / 总时长
    "long_pause_count": int,        # > 1.5s 的停顿次数
    "filler_words": [               # 填充词明细
        {"word": "嗯", "count": 3}
    ],
    "filler_total": int,            # 填充词总次数

    # —— 自信度维度（声学） ——
    "pitch_mean": float,            # 基频均值 (Hz)
    "pitch_std": float,             # 基频标准差（抖动）
    "volume_mean": float,           # RMS 音量均值
    "volume_std": float,            # 音量标准差
}
```

**异常返回**：当音频 < 3 秒 或 Whisper 转写为空 → 返回 `None`。调用方负责跳过。

### 2.2 ExpressionScore（B 产出 → 报告 API & 前端）

**整场面试聚合后的表达评分。** B 通过 `score_expression()` 返回此结构。

```python
{
    "speech_rate_score": float,     # 0~100
    "clarity_score": float,         # 0~100
    "confidence_score": float,      # 0~100
    "expression_score": float,      # 三者加权（覆盖原 evaluation.expression_score）

    "metrics_summary": {            # 整场聚合指标（前端卡片展示）
        "avg_wpm": float,
        "avg_pause_ratio": float,
        "total_filler_count": int,
        "top_filler_words": [{"word": str, "count": int}],
        "pitch_stability": float,   # 0~1
    },

    "feedback": {                   # 文字反馈（前端文本展示）
        "speech_rate": str,
        "clarity": str,
        "confidence": str,
    },

    "per_message": [                # 每题子分（前端画曲线）
        {"message_id": int, "wpm": float, "clarity": float, "confidence": float}
    ]
}
```

**异常返回**：当 `metrics_list` 为空（用户全程文字作答）→ 返回 `None`。前端显示"本场未使用语音作答"。

---

## 3. 函数签名（必须严格遵守）

### A 实现

```python
# backend/services/audio_analysis.py
def analyze_audio(audio_path: str, whisper_result: dict) -> dict | None:
    """
    Args:
        audio_path: 临时音频文件路径
        whisper_result: stt_service.transcribe_detailed() 的完整返回（避免重复转写）
    Returns:
        VoiceMetrics dict (§2.1) 或 None（音频太短/转写失败）
    """
```

### B 实现

```python
# backend/evaluation/expression_evaluator.py
def score_expression(
    metrics_list: list[dict],
    role: str | None = None,
) -> dict | None:
    """
    Args:
        metrics_list: A 产出的 VoiceMetrics 列表（一场面试所有用户回答）
        role: 岗位名（可选，不同岗位语速期待不同）
    Returns:
        ExpressionScore dict (§2.2) 或 None（无语音输入）
    """
```

---

## 4. 关键约定（避免撞车的 8 条）

### 4.1 `process_message_logic` 返回值改造（B 负责）

现状：`async def process_message_logic(...) -> MessageResponse`
**改为**：`async def process_message_logic(...) -> tuple[MessageResponse, int]`，第二个元素是 `user_msg.id`。

调用方 `upload_voice` 拿到 user_msg_id 后写 `voice_metrics.message_id`。

### 4.2 Whisper 只转写一次

`upload_voice` 流程：
1. 调 `stt_service.transcribe_detailed(path)` → 拿 `whisper_result`
2. `polish_text(whisper_result["text"])` → 文字 polish
3. `analyze_audio(path, whisper_result)` → 提特征（**复用结果，不重转**）

### 4.3 wpm 统一按"字/分钟"

中文按字计数，英文按 1 词≈2 字折算。rubric 阈值参考：
- 180~260 字/分钟：正常
- < 150 或 > 300：偏离

### 4.4 填充词清单单点定义

清单只在 `backend/evaluation/filler_words.py` 中定义。A 的 `audio_analysis` 和 B 的 `expression_evaluator` 都从此处 import，**禁止各自硬编码**。

### 4.5 异常路径

| 场景                | A 行为    | B 行为           |
| ------------------- | --------- | ---------------- |
| 音频 < 3 秒         | 返回 None | —                |
| Whisper 转写为空    | 返回 None | —                |
| metrics_list 为空   | —         | 返回 None        |
| 单条 metrics 缺字段 | —         | 跳过该条，不抛错 |

`upload_voice` 看到 A 返回 None 就**不写 voice_metrics 表**（但仍然走正常对话流程，不阻塞用户）。

### 4.6 数据库 migration

项目无 Alembic。新增表/字段：
- 改 `models.py`（SQLAlchemy 定义）
- 改 `init_db.sql`（首次建库）
- 写 `sql/migration_v2_voice.sql`（已有库的增量升级）

A、B 拉代码后各自跑一次 migration_v2_voice.sql。

### 4.7 实时 vs 结束时

表达评分**只在 `end_interview` 时聚合一次**，前端面试中**不展示**实时分。
- 好处：A 不用提供任何实时分接口
- 前端面试页无需改动

### 4.8 临时音频是否保留（建议）

当前 `upload_voice` 用完即删。建议改为持久化到 `backend/uploads/voice/{interview_id}/{message_id}.webm`，路径写入 `messages.audio_path`（字段已存在）。

**阶段一可不做**，等核心链路跑通再加。

---

## 5. RACI

| 文件                                           | A 改动                       | B 改动      |
| ---------------------------------------------- | ---------------------------- | ----------- |
| `services/audio_analysis.py`（新）             | ✅ 全权                       | ❌           |
| `services/stt_service.py`                      | ✅ 加 `transcribe_detailed()` | ❌           |
| `evaluation/__init__.py`（新）                 | 共享空文件                   | 共享空文件  |
| `evaluation/filler_words.py`（新）             | 只读 import                  | ✅ 维护清单  |
| `evaluation/expression_evaluator.py`（新）     | ❌                            | ✅ 全权      |
| `evaluation/expression_rubric.md`（新）        | 评审                         | ✅ 主笔      |
| `db/models.py`                                 | 评审                         | ✅ 加表+字段 |
| `db/schemas.py`                                | ❌                            | ✅           |
| `sql/init_db.sql`                              | ❌                            | ✅           |
| `sql/migration_v2_voice.sql`（新）             | ❌                            | ✅           |
| `routers/interview.py` `upload_voice`          | ✅ 接入特征落库               | 评审        |
| `routers/interview.py` `end_interview`         | ❌                            | ✅ 接入评分  |
| `routers/interview.py` `process_message_logic` | 评审                         | ✅ 改返回值  |
| `frontend/views/ReportView.vue`                | ❌                            | ✅           |
| `tests/mock_voice_metrics.json`（新）          | ✅ 准备 mock 数据             | 只读        |

---

## 6. 联调用 Mock 数据

A 在写完真实实现前，先在 `audio_analysis.py` 里返回 mock；同时把样例存到 `tests/mock_voice_metrics.json`，B 可直接 load 调试 `score_expression`，**完全不依赖 A 的进度**。

样例见 `tests/mock_voice_metrics.json`。

---

## 7. 推进时间线

| 时段 | A                                                        | B                                                      |
| ---- | -------------------------------------------------------- | ------------------------------------------------------ |
| 1    | 一起 review 本契约 + rubric 阈值定稿                     | 同左                                                   |
| 2    | `audio_analysis` 真实实现（Whisper detailed → 特征提取） | `expression_evaluator` + rubric 实现，用 mock 数据自测 |
| 3    | `upload_voice` 接入 + `voice_metrics` 落库               | `end_interview` 接入 + `EvaluationDetail` 字段扩充     |
| 4    | 真实音频联调                                             | `ReportView.vue` 雷达图 + 词云 + 曲线                  |
| 5    | rubric 阈值打磨 + 答辩材料                               | 同左                                                   |

---

## 8. 变更记录

| 日期       | 版本 | 变更     | 提议人 |
| ---------- | ---- | -------- | ------ |
| 2026-04-18 | v1.0 | 初版契约 | A      |
