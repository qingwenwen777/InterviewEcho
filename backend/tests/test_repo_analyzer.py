"""
repo_analyzer 单元测试。

用法：
    cd backend
    python tests/test_repo_analyzer.py

预期：
- URL 解析 case 全部通过
- 真实抓取 vuejs/vue 成功（需要联网）
- 不存在的 repo / 无效 URL 返回 None
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.repo_analyzer import analyze_repo, parse_repo_url


def test_parse_url():
    """纯函数测试，不联网。"""
    print("\n[TEST 1] parse_repo_url")
    cases = [
        ("https://github.com/vuejs/vue", ("vuejs", "vue")),
        ("https://github.com/vuejs/vue.git", ("vuejs", "vue")),
        ("https://github.com/vuejs/vue/", ("vuejs", "vue")),
        ("github.com/vuejs/vue", ("vuejs", "vue")),
        ("https://github.com/my-org/my-project.name", ("my-org", "my-project.name")),
        ("not-a-url", None),
        ("", None),
        (None, None),
        ("https://gitlab.com/x/y", None),  # 非 github 拒绝
        ("https://github.com/", None),     # 无 owner/name
    ]
    passed = 0
    for url, expected in cases:
        result = parse_repo_url(url)
        ok = result == expected
        mark = "[OK]" if ok else "[FAIL]"
        print(f"  {mark} parse_repo_url({url!r}) == {expected} (got {result})")
        if ok:
            passed += 1
    print(f"  {passed}/{len(cases)} passed")
    return passed == len(cases)


async def test_real_fetch():
    """真实 GitHub API 抓取（需要联网）。"""
    print("\n[TEST 2] 真实抓取 vuejs/vue")
    result = await analyze_repo("https://github.com/vuejs/vue")
    if result is None:
        print("  [FAIL] 返回 None（可能网络问题或 API 限流）")
        return False

    checks = [
        ("owner", result.get("owner") == "vuejs"),
        ("name", result.get("name") == "vue"),
        ("description 非空", bool(result.get("description"))),
        ("main_language 是 JavaScript/TypeScript", result.get("main_language") in ("JavaScript", "TypeScript")),
        ("stars > 0", result.get("stars", 0) > 0),
        ("readme_excerpt 非空", len(result.get("readme_excerpt", "")) > 100),
        ("readme_excerpt 不超限", len(result.get("readme_excerpt", "")) <= 3000),
        ("tech_keywords 非空", len(result.get("tech_keywords", [])) > 0),
        ("top_level_files 非空", len(result.get("top_level_files", [])) > 0),
    ]
    passed = sum(1 for _, ok in checks if ok)
    for name, ok in checks:
        print(f"  {'[OK]' if ok else '[FAIL]'} {name}")

    # 打印样例信息
    print(f"\n  样例摘要：")
    print(f"    full_name: {result.get('full_name')}")
    print(f"    description: {result.get('description', '')[:80]}")
    print(f"    main_language: {result.get('main_language')}")
    print(f"    stars: {result.get('stars')}")
    print(f"    tech_keywords (top 5): {result.get('tech_keywords', [])[:5]}")
    print(f"    top_level_files: {result.get('top_level_files', [])[:8]}")
    print(f"    readme_excerpt[:100]: {result.get('readme_excerpt', '')[:100]}")

    print(f"  {passed}/{len(checks)} passed")
    return passed == len(checks)


async def test_nonexistent():
    """不存在的 repo 应返回 None。"""
    print("\n[TEST 3] 不存在的 repo")
    result = await analyze_repo("https://github.com/foobarbaz99999/this-does-not-exist-xyz")
    ok = result is None
    print(f"  {'[OK]' if ok else '[FAIL]'} returns None: {result}")
    return ok


async def test_invalid_url():
    """URL 格式错误应返回 None。"""
    print("\n[TEST 4] 无效 URL")
    cases = ["not-a-url", "https://gitlab.com/x/y", "", "https://github.com/"]
    passed = 0
    for u in cases:
        r = await analyze_repo(u)
        ok = r is None
        print(f"  {'[OK]' if ok else '[FAIL]'} analyze_repo({u!r}) -> None (got {r})")
        if ok:
            passed += 1
    return passed == len(cases)


async def main():
    results = []
    results.append(("URL 解析", test_parse_url()))
    results.append(("无效 URL", await test_invalid_url()))
    results.append(("不存在 repo", await test_nonexistent()))
    results.append(("真实抓取", await test_real_fetch()))

    print("\n" + "=" * 60)
    print("[SUMMARY]")
    print("=" * 60)
    for name, ok in results:
        print(f"  {'[OK]   ' if ok else '[FAIL] '} {name}")
    passed = sum(1 for _, ok in results if ok)
    print(f"\n  {passed}/{len(results)} test groups passed")


if __name__ == "__main__":
    asyncio.run(main())
