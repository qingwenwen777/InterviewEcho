"""
GitHub 仓库信息抓取服务。

给 LLM 提供足够的上下文，以生成针对某个特定项目的深挖面试问题。

约定：
- 只支持公开 github.com 仓库（Gitee/GitLab 不支持）
- 无 GITHUB_TOKEN 时 60 次/小时，配了 token 后 5000 次/小时
- 单个仓库抓取超时 10s，失败返回 None
- README 截取前 3000 字，避免 LLM prompt 超限
"""

from __future__ import annotations

import base64
import os
import re
from typing import Optional

import httpx

GITHUB_API = "https://api.github.com"
README_MAX_CHARS = 3000
HTTP_TIMEOUT = 10.0

# 代码文件深挖配置
MAX_CODE_FILES = 3          # 最多抓 3 个关键代码文件
CODE_FILE_MAX_CHARS = 2000  # 每个文件前 2000 字

# 候选入口文件名（按语言 / 约定）
_ENTRY_FILE_NAMES = {
    "Python": ["main.py", "app.py", "run.py", "server.py", "__main__.py", "cli.py"],
    "JavaScript": ["index.js", "main.js", "app.js", "server.js"],
    "TypeScript": ["index.ts", "main.ts", "app.ts", "server.ts"],
    "Java": ["Main.java", "Application.java"],
    "Go": ["main.go"],
    "Rust": ["main.rs", "lib.rs"],
    "C++": ["main.cpp", "main.cc"],
    "C": ["main.c"],
}

# 跳过这些类型的文件（大多是配置/依赖，对面试无价值）
_SKIP_FILE_EXTS = {
    ".json", ".lock", ".toml", ".yaml", ".yml", ".ini", ".cfg", ".txt",
    ".md", ".rst",                    # 文档（README 已单独抓）
    ".png", ".jpg", ".svg", ".gif",   # 图片
    ".csv", ".tsv", ".parquet",       # 数据文件
    ".min.js", ".min.css",             # 压缩产物
}
_SKIP_FILE_NAMES = {
    "setup.py", "conftest.py",
    ".gitignore", ".env.example", "LICENSE",
    "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "requirements.txt", "Pipfile", "poetry.lock",
    "Dockerfile", "docker-compose.yml",
    ".eslintrc", ".prettierrc",
}

# 代码文件扩展名白名单
_CODE_FILE_EXTS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".vue",
    ".java", ".kt", ".go", ".rs", ".cpp", ".cc", ".c", ".h",
    ".rb", ".php", ".swift", ".scala",
    ".sh", ".sql",
}

# 支持的 URL 形式：
#   https://github.com/vuejs/vue
#   https://github.com/vuejs/vue.git
#   https://github.com/vuejs/vue/
#   github.com/vuejs/vue
#   git@github.com:vuejs/vue.git
_REPO_URL_RE = re.compile(
    r"(?:github\.com[:/])([\w.\-]+)/([\w.\-]+?)(?:\.git)?/?$",
    re.IGNORECASE,
)


def parse_repo_url(url: str) -> Optional[tuple[str, str]]:
    """
    解析 GitHub URL → (owner, name) 或 None。

    >>> parse_repo_url("https://github.com/vuejs/vue")
    ('vuejs', 'vue')
    >>> parse_repo_url("not-a-url")
    None
    """
    if not url or not isinstance(url, str):
        return None
    m = _REPO_URL_RE.search(url.strip())
    if not m:
        return None
    return m.group(1), m.group(2)


def _auth_headers() -> dict:
    """若 .env 里配了 GITHUB_TOKEN 则带上，否则走匿名（60 次/小时）。"""
    token = os.getenv("GITHUB_TOKEN", "").strip()
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _extract_tech_keywords(text: str, languages: dict) -> list[str]:
    """从 README + 语言分布中粗略提取技术关键词（启发式，够用）。"""
    if not text:
        return list(languages.keys())[:5]

    # 常见技术栈关键词字典
    tech_dict = [
        "Vue", "React", "Angular", "Svelte", "Next.js", "Nuxt",
        "Spring", "Spring Boot", "MyBatis", "Hibernate", "JPA",
        "Django", "Flask", "FastAPI", "Tornado",
        "PyTorch", "TensorFlow", "Keras", "Transformers", "LangChain",
        "Redis", "MongoDB", "MySQL", "PostgreSQL", "SQLite", "Elasticsearch",
        "Docker", "Kubernetes", "K8s", "Nginx",
        "RabbitMQ", "Kafka", "RocketMQ",
        "TypeScript", "JavaScript", "Python", "Java", "Go", "Rust", "C++", "Kotlin",
        "Webpack", "Vite", "Rollup", "Babel",
        "GraphQL", "REST", "gRPC", "WebSocket",
        "RAG", "LLM", "Embedding", "Vector", "Whisper",
    ]
    lower = text.lower()
    hits = [kw for kw in tech_dict if kw.lower() in lower]

    # 合并 languages（出现在语言分布里的保证不漏）
    for lang in languages:
        if lang not in hits:
            hits.append(lang)

    return hits[:15]  # 上限 15 个


def _is_code_file(path: str) -> bool:
    """判断一个文件路径是不是值得抓取的代码文件。"""
    basename = path.rsplit("/", 1)[-1]
    if basename in _SKIP_FILE_NAMES:
        return False
    # 扩展名校验
    for ext in _SKIP_FILE_EXTS:
        if basename.lower().endswith(ext):
            return False
    for ext in _CODE_FILE_EXTS:
        if basename.lower().endswith(ext):
            return True
    return False


def _score_code_file(path: str, main_language: str, readme_text: str) -> int:
    """给代码文件打重要性分，分数越高越值得抓。"""
    basename = path.rsplit("/", 1)[-1].lower()
    depth = path.count("/")
    score = 0

    # 入口文件得高分
    entries = _ENTRY_FILE_NAMES.get(main_language, [])
    if basename in [e.lower() for e in entries]:
        score += 50

    # README 里被提及的文件名
    if readme_text and basename in readme_text.lower():
        score += 20

    # 浅层路径优先（根目录 / src 下面）
    score += max(0, 10 - depth * 3)

    # 核心目录偏好
    if path.startswith(("src/", "lib/", "core/", "app/", "server/", "backend/")):
        score += 5

    # 测试文件降权
    if "test" in path.lower() or "__test__" in path.lower():
        score -= 10

    return score


async def _fetch_tree_recursive(client, owner: str, name: str) -> list[str]:
    """一次性抓取整个仓库的文件树（递归，最多 1 级深度的路径）。"""
    try:
        r = await client.get(f"{GITHUB_API}/repos/{owner}/{name}/git/trees/HEAD", params={"recursive": "1"})
        if r.status_code != 200:
            return []
        tree = r.json().get("tree", [])
        paths = [
            item["path"]
            for item in tree
            if item.get("type") == "blob" and item.get("path")
        ]
        # 限制在 2 级目录以内，避免拿到一堆 node_modules 路径
        return [p for p in paths if p.count("/") <= 2]
    except Exception as e:
        print(f"[repo_analyzer] tree fetch failed: {e}")
        return []


async def _fetch_file_content(client, owner: str, name: str, path: str) -> Optional[str]:
    """抓取单个文件的内容（截断到 CODE_FILE_MAX_CHARS）。"""
    try:
        r = await client.get(f"{GITHUB_API}/repos/{owner}/{name}/contents/{path}")
        if r.status_code != 200:
            return None
        data = r.json()
        content_b64 = data.get("content", "")
        if not content_b64:
            return None
        text = base64.b64decode(content_b64).decode("utf-8", errors="ignore")
        return text[:CODE_FILE_MAX_CHARS]
    except Exception as e:
        print(f"[repo_analyzer] fetch file {path} failed: {e}")
        return None


async def _pick_and_fetch_key_files(
    client,
    owner: str,
    name: str,
    main_language: str,
    readme_text: str,
) -> list[dict]:
    """
    智能挑选并抓取 repo 里最有代表性的 2-3 个代码文件内容。

    Returns: [{"path": "src/main.py", "content": "..."}] 或 []
    """
    all_paths = await _fetch_tree_recursive(client, owner, name)
    if not all_paths:
        return []

    # 过滤出代码文件
    code_paths = [p for p in all_paths if _is_code_file(p)]
    if not code_paths:
        return []

    # 打分 + 按分数排序
    scored = [(p, _score_code_file(p, main_language, readme_text)) for p in code_paths]
    scored.sort(key=lambda x: -x[1])
    top_paths = [p for p, _ in scored[:MAX_CODE_FILES]]

    # 并发抓取内容
    import asyncio as _aio
    results = await _aio.gather(*[
        _fetch_file_content(client, owner, name, p) for p in top_paths
    ])

    files = []
    for path, content in zip(top_paths, results):
        if content:
            files.append({"path": path, "content": content})
    return files


async def analyze_repo(url: str) -> Optional[dict]:
    """
    抓取一个 GitHub 公开仓库的信息。

    Args:
        url: 任意形式的 GitHub 仓库 URL

    Returns:
        {
            "owner": "vuejs",
            "name": "vue",
            "full_name": "vuejs/vue",
            "url": "https://github.com/vuejs/vue",
            "description": "...",
            "main_language": "JavaScript",
            "languages": {"JavaScript": 87.2, "TypeScript": 12.8},  # 百分比
            "stars": 207000,
            "readme_excerpt": "前 3000 字",
            "tech_keywords": ["Vue", "JavaScript", ...],
            "top_level_files": ["src/", "docs/", "package.json", ...],
            "recent_commits": [{"msg": "...", "date": "2026-04-18"}, ...]
        }
        或 None（URL 无效 / repo 不存在 / 私有 / 网络错误）
    """
    parsed = parse_repo_url(url)
    if not parsed:
        return None
    owner, name = parsed
    base = f"{GITHUB_API}/repos/{owner}/{name}"

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, headers=_auth_headers()) as client:
        # 1. 基本信息（必须成功）
        try:
            resp = await client.get(base)
            if resp.status_code != 200:
                print(f"[repo_analyzer] repo not accessible: {owner}/{name}, status={resp.status_code}")
                return None
            repo = resp.json()
        except Exception as e:
            print(f"[repo_analyzer] fetch repo failed: {type(e).__name__}: {e}")
            return None

        # 2. README（失败降级为空字符串，不阻塞）
        readme_text = ""
        try:
            r = await client.get(f"{base}/readme")
            if r.status_code == 200:
                data = r.json()
                content = data.get("content", "")
                if content:
                    readme_text = base64.b64decode(content).decode("utf-8", errors="ignore")
        except Exception as e:
            print(f"[repo_analyzer] README fetch failed (non-fatal): {e}")

        # 3. 语言分布（转成百分比）
        languages_pct: dict = {}
        try:
            r = await client.get(f"{base}/languages")
            if r.status_code == 200:
                raw = r.json()
                total = sum(raw.values()) if raw else 0
                if total > 0:
                    languages_pct = {
                        k: round(v / total * 100, 1)
                        for k, v in sorted(raw.items(), key=lambda x: -x[1])[:5]
                    }
        except Exception as e:
            print(f"[repo_analyzer] languages fetch failed (non-fatal): {e}")

        # 4. 根目录结构
        top_level: list[str] = []
        try:
            r = await client.get(f"{base}/contents/")
            if r.status_code == 200:
                items = r.json() or []
                for it in items:
                    n = it.get("name", "")
                    t = it.get("type", "")
                    if n:
                        top_level.append(f"{n}/" if t == "dir" else n)
        except Exception as e:
            print(f"[repo_analyzer] top-level fetch failed (non-fatal): {e}")

        # 5. 最近 5 条 commit
        commits: list = []
        try:
            r = await client.get(f"{base}/commits", params={"per_page": 5})
            if r.status_code == 200:
                for c in (r.json() or [])[:5]:
                    msg = (c.get("commit", {}).get("message") or "").split("\n")[0][:100]
                    date = c.get("commit", {}).get("author", {}).get("date", "")[:10]
                    commits.append({"msg": msg, "date": date})
        except Exception as e:
            print(f"[repo_analyzer] commits fetch failed (non-fatal): {e}")

        # 6. 关键代码文件（深挖用）
        main_lang = repo.get("language") or ""
        try:
            key_files = await _pick_and_fetch_key_files(client, owner, name, main_lang, readme_text)
        except Exception as e:
            print(f"[repo_analyzer] key_files fetch failed (non-fatal): {e}")
            key_files = []

    readme_excerpt = readme_text[:README_MAX_CHARS].strip()

    return {
        "owner": owner,
        "name": name,
        "full_name": f"{owner}/{name}",
        "url": f"https://github.com/{owner}/{name}",
        "description": (repo.get("description") or "").strip(),
        "main_language": main_lang,
        "languages": languages_pct,
        "stars": repo.get("stargazers_count", 0),
        "readme_excerpt": readme_excerpt,
        "tech_keywords": _extract_tech_keywords(readme_excerpt, languages_pct),
        "top_level_files": top_level[:30],
        "recent_commits": commits,
        "key_files": key_files,        # v2: 抓取的关键代码文件（[{"path":..., "content":...}]）
    }
