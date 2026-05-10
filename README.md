# InterviewEcho - AI 模拟面试与能力提升平台

这是一个深度整合了 **RAG (检索增强生成)** 与 **大型语言模型** 的 AI 模拟面试与能力提升平台，专为计算机相关专业学生打造。

## 🌟 核心特性
- **专业化 RAG 架构**: 基于 `knowledge-base` 资料构建的便携式向量检索系统，确保面试问题具有极高的岗位针对性。
- **真实 LLM 交互**: 接入 OpenAI/DeepSeek 等真实模型接口，支持动态追问与多轮深度对话。
- **多维度评估报告**: 面试结束后通过 AI 专家模型对技术深度、沟通表达、问题解决等维度进行结构化评分。
- **现代化 UI/UX**: 使用 Vue 3 + Tailwind CSS 打造的极简、灵动、高端的交互体验。

## 📂 项目结构
项目已进行高度模块化合理化：
- `backend/`
  - `core/`: 核心逻辑（LLM 驱动、Prompt 管理、配置）。
  - `db/`: 数据库模型、Schema 及连接管理。
  - `routers/`: 业务路由。
  - `services/`: 核心服务（便携式 RAG 检索器）。
  - `rag/`: 知识检索索引库。
- `frontend/`: 基于 Vite 的 Vue 3 响应式前端。
- `knowledge-base/`: 供 RAG 使用的原始题库与知识点。


## 首次拉代码后，按顺序做以下 4 步

### 1. 装 ffmpeg（语音功能依赖）

- 下载：https://www.gyan.dev/ffmpeg/builds/ → 选 **release essentials build**
- 解压到 `C:\ffmpeg\`（解压后最终路径应该是 `C:\ffmpeg\bin\ffmpeg.exe`）
- 把 `C:\ffmpeg\bin` 加到**系统 PATH**：

### 2. 装 Python 依赖

```powershell
cd D:\xxx\InterviewEcho-ServiceOutsourcing\backend
pip install -r requirements.txt
```

---

### 3. 建数据库 + 跑 migration

```powershell
$env:MYSQL_PWD="你自己的MySQL密码"

# 建数据库
mysql -u root -e "CREATE DATABASE interview_echo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 按顺序跑所有建表/迁移脚本
cd D:\xxx\InterviewEcho-ServiceOutsourcing
Get-Content backend\sql\init_db.sql | mysql -u root interview_echo
Get-Content backend\sql\migration_v2_voice.sql | mysql -u root interview_echo
Get-Content backend\sql\migration_v3_github.sql | mysql -u root interview_echo
```

**验证表都建好**：

```powershell
mysql -u root interview_echo -e "SHOW TABLES;"
```

应该看到 **6 张表**：

- `users`
- `interviews`
- `messages`
- `questions`
- `evaluations`
- `voice_metrics`

---

### 4. 构建 RAG 向量索引

```powershell
cd D:\xxx\InterviewEcho-ServiceOutsourcing\backend
python -m rag.build_index
```

## 🚀 快速开始
### 1. 数据库初始化
1. 确保 MySQL 8.0 运行中。
2. 执行: `backend/sql/init_db.sql;`(请先创建数据库 interview_echo)

### 2. 后端配置 (Python 3.12)
1. 进入 `backend` 目录，安装依赖: `pip install -r requirements.txt`
2. 配置 `.env`: 配置好自己的mysql信息、大模型信息
3. **构建 RAG 索引**: 运行 `python -m rag.build_index` (这会通过 Embedding API 向量knowledge-base中的RAG知识库)。
4. 启动后端: `uvicorn main:app --reload`

### 3. 前端启动
1. 进入 `frontend` 目录。
2. `npm install` && `npm run dev`
