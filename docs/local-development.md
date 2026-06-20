# InterviewEcho 本地运行教程

本文档面向 Windows、macOS、Linux，从 0 开始说明如何在本地运行 InterviewEcho。

InterviewEcho 当前由以下部分组成：

- 后端：FastAPI + SQLAlchemy + MySQL，入口在 `backend/main.py`
- 前端：React + Vite，入口在 `frontend/src/App.jsx`
- 数据库：MySQL 8.x
- AI 能力：OpenAI 兼容接口，例如阿里云 DashScope、DeepSeek、OpenAI 等
- 可选能力：RAG 索引、语音识别、TTS、Judge0 代码判题

## 1. 本地端口

默认建议使用以下端口：

| 服务 | 地址 |
| --- | --- |
| 后端 API | `http://127.0.0.1:8000` |
| 前端 Vite | `http://127.0.0.1:5173` |
| MySQL | `127.0.0.1:3306` |
| Judge0，可选 | `http://127.0.0.1:2358` |

前端本地开发时必须配置：

```env
VITE_API_URL=http://127.0.0.1:8000/api
```

否则前端默认请求 `/api`，在没有反向代理的本地 Vite 环境下会请求到前端服务器自身。

## 2. 准备基础环境

### 2.1 Windows

推荐使用 PowerShell。

安装 Git、Node.js、Python、MySQL、FFmpeg：

```powershell
winget install --id Git.Git -e
winget install --id OpenJS.NodeJS.LTS -e
winget install --id Python.Python.3.12 -e
winget install --id Oracle.MySQL -e
winget install --id Gyan.FFmpeg -e
```

如果 `winget` 不可用，可以手动安装：

- Git: https://git-scm.com/downloads
- Node.js LTS: https://nodejs.org/
- Python 3.12: https://www.python.org/downloads/
- MySQL 8: https://dev.mysql.com/downloads/mysql/
- FFmpeg: https://www.gyan.dev/ffmpeg/builds/

确认版本：

```powershell
git --version
node -v
npm -v
python --version
mysql --version
ffmpeg -version
```

如果 PowerShell 无法激活 Python 虚拟环境，执行一次：

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 2.2 macOS

推荐使用 Homebrew：

```bash
xcode-select --install
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install git node python@3.12 mysql ffmpeg
brew services start mysql
```

确认版本：

```bash
git --version
node -v
npm -v
python3 --version
mysql --version
ffmpeg -version
```

### 2.3 Linux Ubuntu / Debian

```bash
sudo apt update
sudo apt install -y git curl build-essential python3 python3-venv python3-pip mysql-server ffmpeg
sudo systemctl enable --now mysql
```

安装 Node.js LTS。推荐 Node 20 或更新：

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

确认版本：

```bash
git --version
node -v
npm -v
python3 --version
mysql --version
ffmpeg -version
```

## 3. 拉取项目代码

```bash
git clone <你的仓库地址> InterviewEcho
cd InterviewEcho
```

如果已经有代码：

```bash
cd InterviewEcho
git pull
```

## 4. 配置 MySQL

### 4.1 启动 MySQL

Windows：

```powershell
net start MySQL80
```

如果服务名不是 `MySQL80`，在服务管理器中确认实际名称，或使用：

```powershell
Get-Service *mysql*
```

macOS：

```bash
brew services start mysql
```

Linux：

```bash
sudo systemctl start mysql
sudo systemctl status mysql
```

### 4.2 初始化数据库

项目 SQL 文件位于：

- `backend/sql/init_db.sql`
- `backend/sql/migration_v2_voice.sql`
- `backend/sql/migration_v3_github.sql`
- `backend/sql/migration_v4_code_practice.sql`
- `backend/sql/migration_v5_message_state.sql`

推荐按顺序执行全部 SQL。即使后端启动时会自动创建部分表，手动跑 SQL 仍然更稳，尤其是索引、历史迁移字段、初始题目数据。

#### Windows PowerShell

如果 MySQL root 有密码：

```powershell
$env:MYSQL_PWD="你的MySQL密码"
```

如果 root 没有密码，可以跳过上面这行。

从项目根目录执行：

```powershell
Get-Content -Raw -Encoding UTF8 backend\sql\init_db.sql | mysql --default-character-set=utf8mb4 -u root
Get-Content -Raw -Encoding UTF8 backend\sql\migration_v2_voice.sql | mysql --default-character-set=utf8mb4 -u root
Get-Content -Raw -Encoding UTF8 backend\sql\migration_v3_github.sql | mysql --default-character-set=utf8mb4 -u root
Get-Content -Raw -Encoding UTF8 backend\sql\migration_v4_code_practice.sql | mysql --default-character-set=utf8mb4 -u root
Get-Content -Raw -Encoding UTF8 backend\sql\migration_v5_message_state.sql | mysql --default-character-set=utf8mb4 -u root
```

验证：

```powershell
mysql --default-character-set=utf8mb4 -u root -e "USE interview_echo; SHOW TABLES;"
```

执行完可以清掉临时密码环境变量：

```powershell
Remove-Item Env:\MYSQL_PWD -ErrorAction SilentlyContinue
```

#### macOS / Linux

如果 MySQL root 有密码：

```bash
export MYSQL_PWD='你的MySQL密码'
```

如果 root 没有密码，可以跳过上面这行。

从项目根目录执行：

```bash
mysql --default-character-set=utf8mb4 -u root < backend/sql/init_db.sql
mysql --default-character-set=utf8mb4 -u root < backend/sql/migration_v2_voice.sql
mysql --default-character-set=utf8mb4 -u root < backend/sql/migration_v3_github.sql
mysql --default-character-set=utf8mb4 -u root < backend/sql/migration_v4_code_practice.sql
mysql --default-character-set=utf8mb4 -u root < backend/sql/migration_v5_message_state.sql
```

验证：

```bash
mysql --default-character-set=utf8mb4 -u root -e "USE interview_echo; SHOW TABLES;"
```

执行完可以清掉临时密码环境变量：

```bash
unset MYSQL_PWD
```

## 5. 配置后端环境变量

后端从 `.env` 读取配置。建议将根目录的 `.env.example` 复制到 `backend/.env`。

Windows：

```powershell
cd backend
Copy-Item ..\.env.example .env
```

macOS / Linux：

```bash
cd backend
cp ../.env.example .env
```

编辑 `backend/.env`，至少检查这些项：

```env
APP_HOST=127.0.0.1
APP_PORT=8000

DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASS=你的MySQL密码
DB_PASSWORD=你的MySQL密码
DB_NAME=interview_echo

CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

LLM_API_KEY=你的OpenAI兼容接口Key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-turbo
EMBEDDING_MODEL=text-embedding-v4

# 本地开发建议先关闭 Whisper 预加载，避免首次启动下载模型太慢。
WHISPER_PRELOAD=false

# 如果使用 DashScope ASR，ASR_API_KEY 为空时会复用 LLM_API_KEY。
ASR_PROVIDER=dashscope
ASR_API_KEY=

# TTS 可选，不配置 MIMO_API_KEY 时语音播放接口不可用，但不影响文字面试。
MIMO_API_KEY=

# 代码判题可选。不启动 Judge0 时，代码题列表可看，但运行/提交会失败。
JUDGE0_BASE_URL=http://127.0.0.1:2358
```

说明：

- 不配置 `LLM_API_KEY`：后端可以启动，但 AI 面试、评估、RAG 构建等功能无法正常使用。
- 不构建 RAG：后端会提示 `RAG 索引文件 ... 未找到`，但项目仍可启动。RAG 相关增强效果不可用。
- 不配置 `MIMO_API_KEY`：TTS 播放不可用，但文字面试不受影响。
- 不启动 Judge0：代码练习的运行/提交不可用，但其他功能不受影响。

## 6. 安装并启动后端

### 6.1 Windows PowerShell

从项目根目录：

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

启动后端：

```powershell
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 6.2 macOS / Linux

从项目根目录：

```bash
cd backend
python3.12 -m venv .venv || python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

启动后端：

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 6.3 验证后端

打开新终端执行：

Windows PowerShell：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/
Invoke-RestMethod http://127.0.0.1:8000/api/interview/roles
```

macOS / Linux：

```bash
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/api/interview/roles
```

正常情况下，第一个接口会返回：

```json
{"message":"Welcome to InterviewEcho API"}
```

## 7. 构建 RAG 索引，可选但推荐

RAG 索引会读取 `knowledge-base/`，调用 Embedding 模型生成 `backend/rag/vector_index.json`。

前提：

- `backend/.env` 中必须有 `LLM_API_KEY`
- `LLM_BASE_URL` 和 `EMBEDDING_MODEL` 必须与你的服务商兼容

执行：

Windows：

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m rag.build_index
```

macOS / Linux：

```bash
cd backend
source .venv/bin/activate
python -m rag.build_index
```

成功后应生成：

```text
backend/rag/vector_index.json
```

如果跳过此步骤，后端启动时出现以下提示是可接受的：

```text
提醒: RAG 索引文件 ... vector_index.json 未找到，请先运行 build_index.py
```

## 8. 配置并启动前端

### 8.1 安装依赖

打开新终端，从项目根目录执行：

Windows：

```powershell
cd frontend
npm install
```

macOS / Linux：

```bash
cd frontend
npm install
```

### 8.2 配置前端 API 地址

Windows PowerShell：

```powershell
"VITE_API_URL=http://127.0.0.1:8000/api" | Set-Content -Encoding UTF8 .env.local
```

macOS / Linux：

```bash
printf "VITE_API_URL=http://127.0.0.1:8000/api\n" > .env.local
```

### 8.3 启动前端

Windows：

```powershell
npm run dev -- --host 127.0.0.1 --port 5173
```

macOS / Linux：

```bash
npm run dev -- --host 127.0.0.1 --port 5173
```

浏览器打开：

```text
http://127.0.0.1:5173/
```

## 9. 首次使用

1. 打开 `http://127.0.0.1:5173/`
2. 注册一个本地账号
3. 登录
4. 进入用户中心，上传或粘贴简历
5. 选择岗位，进入模拟面试

也可以用接口创建账号。

macOS / Linux：

```bash
curl -X POST http://127.0.0.1:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"123456"}'
```

Windows PowerShell：

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/auth/register `
  -ContentType "application/json" `
  -Body '{"username":"demo","password":"123456"}'
```

## 10. 可选：代码判题 Judge0

代码练习模块的题目列表由后端自动 seed 到 MySQL。运行代码和提交代码需要本地 Judge0 服务。

后端默认读取：

```env
JUDGE0_BASE_URL=http://127.0.0.1:2358
```

本项目仓库没有维护本地 Judge0 Docker Compose 文件。推荐使用 Judge0 CE 官方 Docker Compose 部署，并确保只绑定本机地址。

启动完成后验证：

Windows PowerShell：

```powershell
Invoke-RestMethod http://127.0.0.1:2358/system_info
```

macOS / Linux：

```bash
curl http://127.0.0.1:2358/system_info
```

如果该接口不可用，代码练习中的“运行”和“提交”会报 Judge0 不可用。模拟面试、简历、GitHub 项目深挖、报告等功能不依赖 Judge0。

## 11. 可选：语音识别和 TTS

### 11.1 语音识别

项目当前支持：

- DashScope ASR，默认 `ASR_PROVIDER=dashscope`
- Whisper，本地模型相关配置以 `WHISPER_*` 开头

本地开发建议先设置：

```env
WHISPER_PRELOAD=false
```

否则后端启动时可能会尝试预加载 Whisper 模型，首次启动较慢。

如果使用 DashScope ASR：

```env
ASR_PROVIDER=dashscope
ASR_API_KEY=
```

当 `ASR_API_KEY` 为空时，代码会复用 `LLM_API_KEY`。

语音上传和转码依赖 FFmpeg。确认：

```bash
ffmpeg -version
```

### 11.2 TTS

TTS 使用 MiMo 接口。未配置时不影响文字面试。

```env
MIMO_API_KEY=你的MiMo Key
MIMO_BASE_URL=https://api.xiaomimimo.com/v1
MIMO_TTS_MODEL=mimo-v2.5-tts
```

## 12. 常用开发命令

### 后端

Windows：

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

macOS / Linux：

```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 前端

```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

### 前端生产构建

```bash
cd frontend
npm run build
```

### 后端基础测试

从项目根目录：

Windows：

```powershell
python backend\tests\test_interview_planning.py
$env:PYTHONPATH=(Resolve-Path backend).Path
python backend\tests\test_skip_detection.py
Remove-Item Env:\PYTHONPATH -ErrorAction SilentlyContinue
```

macOS / Linux：

```bash
python backend/tests/test_interview_planning.py
PYTHONPATH=backend python backend/tests/test_skip_detection.py
```

说明：本地未启动 MySQL 或未构建 RAG 时，测试启动阶段可能打印 MySQL/RAG warning。只要最终测试通过即可。

## 13. 常见问题

### 13.1 后端报 MySQL 连接失败

典型错误：

```text
Can't connect to MySQL server on 'localhost'
```

处理：

1. 确认 MySQL 已启动
2. 确认 `backend/.env` 中 `DB_HOST`、`DB_PORT`、`DB_USER`、`DB_PASS` 正确
3. 用命令行验证：

```bash
mysql -u root -p -e "SELECT 1;"
```

### 13.2 前端页面能打开，但接口 404 或登录失败

检查 `frontend/.env.local`：

```env
VITE_API_URL=http://127.0.0.1:8000/api
```

修改 `.env.local` 后必须重启 Vite：

```bash
npm run dev -- --host 127.0.0.1 --port 5173
```

### 13.3 后端启动很慢

可能是 Whisper 预加载。开发环境建议：

```env
WHISPER_PRELOAD=false
```

然后重启后端。

### 13.4 RAG 提示 vector_index.json 不存在

这是可恢复问题。需要 RAG 时执行：

```bash
cd backend
python -m rag.build_index
```

如果只想跑基本面试流程，可以暂时忽略该提示。

### 13.5 AI 面试回复失败

检查：

1. `LLM_API_KEY` 是否为空
2. `LLM_BASE_URL` 是否是 OpenAI 兼容 `/v1` 地址
3. `LLM_MODEL` 是否是服务商支持的模型
4. 本机是否能访问该服务商 API

### 13.6 PDF 上传后识别失败

检查：

1. 文件必须是 PDF
2. PDF 不能超过 `MAX_RESUME_PDF_BYTES`，默认约 10MB
3. 扫描图片型 PDF 可能无法提取文本，需要手动粘贴简历正文

### 13.7 代码练习运行失败

检查 Judge0：

```bash
curl http://127.0.0.1:2358/system_info
```

如果不可用，先跳过代码运行/提交功能。模拟面试不依赖 Judge0。

### 13.8 Windows 激活虚拟环境失败

执行：

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

然后重新打开 PowerShell。

## 14. 推荐的本地启动顺序

每次开发时按这个顺序启动：

1. 启动 MySQL
2. 启动后端
3. 启动前端
4. 可选：启动 Judge0

最常用的两个终端：

终端 1，后端：

```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Windows 对应：

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

终端 2，前端：

```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

访问：

```text
http://127.0.0.1:5173/
```

