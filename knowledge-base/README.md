# InterviewEcho 知识库与题库规范文档

本目录（`knowledge-base/`）包含了系统用于 RAG（检索增强生成）的数据基础，分为三大岗位：Java后端、Web前端、Python算法。

## 目录结构
- `<role>/questions/*.json`: 结构化题库（技术题、场景题、行为题等）。
- `<role>/knowledge/*.md`: 核心技术栈指南、优秀回答范例（用于评分基准）。

## JSON 题库字段说明
每个 JSON 文件包含一个题目数组，每道题目遵循以下 Schema：
- `id` (String): 唯一标识符。
- `question` (String): 面试问题正文。
- `category` (String): 问题分类（如：底层原理、框架应用、项目经验等）。
- `tags` (Array<String>): 知识点标签，用于精确过滤或权重检索。
- `difficulty` (String): 难度级别（简单/中等/困难）。
- `expected_points` (Array<String>): 候选人回答中必须踩中的核心得分点。
- `evaluation_criteria` (Object): 
  - `excellent` (String): 满分回答的特征。
  - `good` (String): 及格回答的特征。
  - `bad` (String): 糟糕或错误的回答特征。

## 数据使用建议
1. **题库抽取**：在面试初始化阶段，根据候选人简历（标签匹配）和目标难度，从 JSON 库中随机或定向抽取题目。
2. **RAG 问答与评估**：在面试过程中，将 `expected_points` 与 `<role>/knowledge/interview_excellent_answers.md` 结合输入给 LLM 控制追问深度和打分。
