from collections import Counter, OrderedDict, defaultdict, deque
import bisect
import heapq
import math


def _ensure_newline(value):
    return value if value.endswith("\n") else value + "\n"


def _ints(value):
    return list(map(int, value.split()))


def _join(values):
    return " ".join(str(value) for value in values)


def _join_lines(rows):
    return "\n".join(_join(row) for row in rows)


def _bool(value):
    return "true" if value else "false"


def _format_number(value):
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, float):
        return f"{value:.1f}"
    return str(value)


def _read_tree(text):
    parts = text.split()
    if not parts:
        return [], None
    n = int(parts[0])
    tokens = parts[1 : 1 + n]
    if n == 0 or not tokens or tokens[0] == "#":
        return [], None

    nodes = []

    def add(value):
        nodes.append({"val": int(value), "left": None, "right": None})
        return len(nodes) - 1

    root = add(tokens[0])
    queue = deque([root])
    i = 1
    while queue and i < len(tokens):
        current = queue.popleft()
        if i < len(tokens) and tokens[i] != "#":
            nodes[current]["left"] = add(tokens[i])
            queue.append(nodes[current]["left"])
        i += 1
        if i < len(tokens) and tokens[i] != "#":
            nodes[current]["right"] = add(tokens[i])
            queue.append(nodes[current]["right"])
        i += 1
    return nodes, root


def _tree_level_order(nodes, root):
    if root is None:
        return ""
    result = []
    queue = deque([root])
    while queue:
        current = queue.popleft()
        if current is None:
            result.append("#")
            continue
        result.append(str(nodes[current]["val"]))
        queue.append(nodes[current]["left"])
        queue.append(nodes[current]["right"])
    while result and result[-1] == "#":
        result.pop()
    return " ".join(result)


def _tree_tokens(text):
    parts = text.split()
    n = int(parts[0])
    return parts[1 : 1 + n]


def _solve_trap(text):
    values = _ints(text)
    nums = values[1:]
    left, right = 0, len(nums) - 1
    left_max = right_max = water = 0
    while left < right:
        if nums[left] <= nums[right]:
            left_max = max(left_max, nums[left])
            water += left_max - nums[left]
            left += 1
        else:
            right_max = max(right_max, nums[right])
            water += right_max - nums[right]
            right -= 1
    return str(water)


def _solve_min_window(text):
    lines = text.rstrip("\n").splitlines()
    s = lines[0] if lines else ""
    t = lines[1] if len(lines) > 1 else ""
    if not t:
        return ""
    need = Counter(t)
    missing = len(t)
    best = None
    left = 0
    for right, char in enumerate(s):
        if need[char] > 0:
            missing -= 1
        need[char] -= 1
        while missing == 0:
            if best is None or right - left + 1 < best[1] - best[0]:
                best = (left, right + 1)
            need[s[left]] += 1
            if need[s[left]] > 0:
                missing += 1
            left += 1
    return "" if best is None else s[best[0] : best[1]]


def _solve_anagram(text):
    a, b = text.split()[:2]
    return _bool(Counter(a) == Counter(b))


def _solve_longest_consecutive(text):
    values = _ints(text)
    nums = set(values[1:])
    best = 0
    for num in nums:
        if num - 1 not in nums:
            current = num
            length = 1
            while current + 1 in nums:
                current += 1
                length += 1
            best = max(best, length)
    return str(best)


def _solve_move_zeroes(text):
    values = _ints(text)
    nums = values[1:]
    non_zero = [value for value in nums if value != 0]
    return _join(non_zero + [0] * (len(nums) - len(non_zero)))


def _solve_non_overlap(text):
    values = _ints(text)
    n = values[0]
    intervals = [tuple(values[i : i + 2]) for i in range(1, 1 + 2 * n, 2)]
    if not intervals:
        return "0"
    intervals.sort(key=lambda item: (item[1], item[0]))
    kept = 0
    end = -10**30
    for start, finish in intervals:
        if start >= end:
            kept += 1
            end = finish
    return str(n - kept)


def _solve_max_product(text):
    values = _ints(text)
    nums = values[1:]
    high = low = best = nums[0]
    for value in nums[1:]:
        if value < 0:
            high, low = low, high
        high = max(value, high * value)
        low = min(value, low * value)
        best = max(best, high)
    return str(best)


def _solve_house_robber(text):
    nums = _ints(text)[1:]
    prev2 = prev1 = 0
    for value in nums:
        prev2, prev1 = prev1, max(prev1, prev2 + value)
    return str(prev1)


def _solve_climb(text):
    n = int(text.strip())
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return str(a)


def _solve_unique_paths(text):
    m, n = _ints(text)[:2]
    return str(math.comb(m + n - 2, m - 1))


def _solve_min_path_sum(text):
    values = _ints(text)
    m, n = values[0], values[1]
    grid = [values[2 + i * n : 2 + (i + 1) * n] for i in range(m)]
    dp = [10**30] * n
    dp[0] = 0
    for i in range(m):
        for j in range(n):
            if j == 0:
                dp[j] += grid[i][j]
            else:
                dp[j] = min(dp[j], dp[j - 1]) + grid[i][j]
    return str(dp[-1])


def _solve_edit_distance(text):
    lines = text.rstrip("\n").splitlines()
    a = lines[0] if lines else ""
    b = lines[1] if len(lines) > 1 else ""
    dp = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        prev = dp[0]
        dp[0] = i
        for j, cb in enumerate(b, 1):
            old = dp[j]
            dp[j] = prev if ca == cb else min(prev, dp[j], dp[j - 1]) + 1
            prev = old
    return str(dp[-1])


def _solve_lis(text):
    values = _ints(text)
    tails = []
    for value in values[1:]:
        pos = bisect.bisect_left(tails, value)
        if pos == len(tails):
            tails.append(value)
        else:
            tails[pos] = value
    return str(len(tails))


def _solve_partition(text):
    nums = _ints(text)[1:]
    total = sum(nums)
    if total % 2:
        return "false"
    target = total // 2
    reachable = {0}
    for value in nums:
        reachable |= {item + value for item in list(reachable) if item + value <= target}
    return _bool(target in reachable)


def _solve_target_sum(text):
    values = _ints(text)
    n, target = values[0], values[1]
    nums = values[2 : 2 + n]
    ways = Counter({0: 1})
    for value in nums:
        nxt = Counter()
        for total, count in ways.items():
            nxt[total + value] += count
            nxt[total - value] += count
        ways = nxt
    return str(ways[target])


def _solve_word_break(text):
    lines = text.rstrip("\n").splitlines()
    s = lines[0].strip()
    n = int(lines[1])
    words = set(" ".join(lines[2:]).split()[:n])
    dp = [False] * (len(s) + 1)
    dp[0] = True
    max_len = max((len(word) for word in words), default=0)
    for i in range(1, len(s) + 1):
        start = max(0, i - max_len)
        dp[i] = any(dp[j] and s[j:i] in words for j in range(start, i))
    return _bool(dp[-1])


def _solve_islands(text):
    lines = text.strip().splitlines()
    m, n = map(int, lines[0].split())
    grid = [list(lines[i + 1].replace(" ", "").strip()) for i in range(m)]
    count = 0
    for r in range(m):
        for c in range(n):
            if grid[r][c] == "1":
                count += 1
                stack = [(r, c)]
                grid[r][c] = "0"
                while stack:
                    x, y = stack.pop()
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < m and 0 <= ny < n and grid[nx][ny] == "1":
                            grid[nx][ny] = "0"
                            stack.append((nx, ny))
    return str(count)


def _solve_oranges(text):
    values = _ints(text)
    m, n = values[0], values[1]
    grid = [values[2 + i * n : 2 + (i + 1) * n] for i in range(m)]
    queue = deque()
    fresh = 0
    for i in range(m):
        for j in range(n):
            if grid[i][j] == 2:
                queue.append((i, j, 0))
            elif grid[i][j] == 1:
                fresh += 1
    minutes = 0
    while queue:
        x, y, minutes = queue.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < m and 0 <= ny < n and grid[nx][ny] == 1:
                grid[nx][ny] = 2
                fresh -= 1
                queue.append((nx, ny, minutes + 1))
    return str(minutes if fresh == 0 else -1)


def _solve_course(text):
    values = _ints(text)
    n, m = values[0], values[1]
    graph = [[] for _ in range(n)]
    indeg = [0] * n
    cursor = 2
    for _ in range(m):
        course, pre = values[cursor], values[cursor + 1]
        cursor += 2
        graph[pre].append(course)
        indeg[course] += 1
    queue = deque(i for i, degree in enumerate(indeg) if degree == 0)
    seen = 0
    while queue:
        node = queue.popleft()
        seen += 1
        for nxt in graph[node]:
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                queue.append(nxt)
    return _bool(seen == n)


def _solve_trie(text):
    lines = text.strip().splitlines()
    trie = {}
    outputs = []
    for line in lines[1:]:
        op, word = line.split()
        if op == "INSERT":
            node = trie
            for char in word:
                node = node.setdefault(char, {})
            node["$"] = True
            continue
        node = trie
        ok = True
        for char in word:
            if char not in node:
                ok = False
                break
            node = node[char]
        if op == "SEARCH":
            ok = ok and "$" in node
        outputs.append(_bool(ok))
    return "\n".join(outputs)


def _solve_top_k(text):
    values = _ints(text)
    n, k = values[0], values[1]
    nums = values[2 : 2 + n]
    items = sorted(Counter(nums).items(), key=lambda item: (-item[1], item[0]))
    return _join(value for value, _ in items[:k])


def _solve_median_stream(text):
    lines = text.strip().splitlines()
    low, high = [], []
    outputs = []
    for line in lines[1:]:
        parts = line.split()
        if parts[0] == "ADD":
            value = int(parts[1])
            if not low or value <= -low[0]:
                heapq.heappush(low, -value)
            else:
                heapq.heappush(high, value)
            if len(low) > len(high) + 1:
                heapq.heappush(high, -heapq.heappop(low))
            if len(high) > len(low):
                heapq.heappush(low, -heapq.heappop(high))
        else:
            if len(low) == len(high):
                outputs.append(_format_number((-low[0] + high[0]) / 2))
            else:
                outputs.append(str(-low[0]))
    return "\n".join(outputs)


def _solve_sliding_max(text):
    values = _ints(text)
    n, k = values[0], values[1]
    nums = values[2 : 2 + n]
    queue = deque()
    result = []
    for i, value in enumerate(nums):
        while queue and queue[0] <= i - k:
            queue.popleft()
        while queue and nums[queue[-1]] <= value:
            queue.pop()
        queue.append(i)
        if i >= k - 1:
            result.append(nums[queue[0]])
    return _join(result)


def _solve_kth_largest(text):
    values = _ints(text)
    n, k = values[0], values[1]
    return str(sorted(values[2 : 2 + n], reverse=True)[k - 1])


def _solve_merge_k_lists(text):
    lines = text.strip().splitlines()
    heap = []
    for row, line in enumerate(lines[1:]):
        values = _ints(line)
        for col, value in enumerate(values[1:]):
            heapq.heappush(heap, (value, row, col))
    result = []
    while heap:
        result.append(heapq.heappop(heap)[0])
    return _join(result)


def _solve_reverse_list(text):
    values = _ints(text)
    return _join(reversed(values[1:]))


def _solve_cycle_entry(text):
    values = _ints(text)
    n = values[0]
    nxt = values[1 : 1 + n]
    visited = set()
    current = 0 if n else -1
    while current != -1:
        if current in visited:
            return str(current)
        visited.add(current)
        current = nxt[current]
    return "-1"


def _solve_intersection_list(text):
    values = _ints(text)
    n, m = values[0], values[1]
    a = values[2 : 2 + n]
    b = set(values[2 + n : 2 + n + m])
    for value in a:
        if value in b:
            return str(value)
    return "-1"


def _solve_palindrome_list(text):
    nums = _ints(text)[1:]
    return _bool(nums == nums[::-1])


def _solve_swap_pairs(text):
    nums = _ints(text)[1:]
    for i in range(0, len(nums) - 1, 2):
        nums[i], nums[i + 1] = nums[i + 1], nums[i]
    return _join(nums)


def _solve_reverse_k_group(text):
    values = _ints(text)
    n, k = values[0], values[1]
    nums = values[2 : 2 + n]
    result = []
    for i in range(0, n, k):
        group = nums[i : i + k]
        result.extend(group[::-1] if len(group) == k else group)
    return _join(result)


def _solve_tree_depth(text):
    nodes, root = _read_tree(text)
    if root is None:
        return "0"
    depth = 0
    queue = deque([root])
    while queue:
        depth += 1
        for _ in range(len(queue)):
            node = queue.popleft()
            if nodes[node]["left"] is not None:
                queue.append(nodes[node]["left"])
            if nodes[node]["right"] is not None:
                queue.append(nodes[node]["right"])
    return str(depth)


def _solve_invert_tree(text):
    nodes, root = _read_tree(text)

    def dfs(node):
        if node is None:
            return
        nodes[node]["left"], nodes[node]["right"] = nodes[node]["right"], nodes[node]["left"]
        dfs(nodes[node]["left"])
        dfs(nodes[node]["right"])

    dfs(root)
    return _tree_level_order(nodes, root)


def _solve_symmetric(text):
    nodes, root = _read_tree(text)

    def same(a, b):
        if a is None or b is None:
            return a is b
        return (
            nodes[a]["val"] == nodes[b]["val"]
            and same(nodes[a]["left"], nodes[b]["right"])
            and same(nodes[a]["right"], nodes[b]["left"])
        )

    return _bool(root is None or same(nodes[root]["left"], nodes[root]["right"]))


def _solve_diameter(text):
    nodes, root = _read_tree(text)
    best = 0

    def depth(node):
        nonlocal best
        if node is None:
            return 0
        left = depth(nodes[node]["left"])
        right = depth(nodes[node]["right"])
        best = max(best, left + right)
        return max(left, right) + 1

    depth(root)
    return str(best)


def _solve_path_sum_iii(text):
    values = text.split()
    n = int(values[0])
    target = int(values[1 + n])
    tree_text = f"{n}\n{' '.join(values[1 : 1 + n])}\n"
    nodes, root = _read_tree(tree_text)
    prefixes = Counter({0: 1})
    result = 0

    def dfs(node, total):
        nonlocal result
        if node is None:
            return
        total += nodes[node]["val"]
        result += prefixes[total - target]
        prefixes[total] += 1
        dfs(nodes[node]["left"], total)
        dfs(nodes[node]["right"], total)
        prefixes[total] -= 1

    dfs(root, 0)
    return str(result)


def _solve_lca(text):
    values = text.split()
    n = int(values[0])
    p, q = map(int, values[1 + n : 3 + n])
    nodes, root = _read_tree(f"{n}\n{' '.join(values[1 : 1 + n])}\n")

    def dfs(node):
        if node is None:
            return None
        if nodes[node]["val"] in (p, q):
            return node
        left = dfs(nodes[node]["left"])
        right = dfs(nodes[node]["right"])
        if left is not None and right is not None:
            return node
        return left if left is not None else right

    answer = dfs(root)
    return str(nodes[answer]["val"])


def _solve_right_view(text):
    nodes, root = _read_tree(text)
    if root is None:
        return ""
    result = []
    queue = deque([root])
    while queue:
        result.append(nodes[queue[-1]]["val"])
        for _ in range(len(queue)):
            node = queue.popleft()
            if nodes[node]["left"] is not None:
                queue.append(nodes[node]["left"])
            if nodes[node]["right"] is not None:
                queue.append(nodes[node]["right"])
    return _join(result)


def _solve_validate_bst(text):
    nodes, root = _read_tree(text)
    prev = None
    ok = True

    def inorder(node):
        nonlocal prev, ok
        if node is None or not ok:
            return
        inorder(nodes[node]["left"])
        if prev is not None and nodes[node]["val"] <= prev:
            ok = False
            return
        prev = nodes[node]["val"]
        inorder(nodes[node]["right"])

    inorder(root)
    return _bool(ok)


def _solve_kth_bst(text):
    values = text.split()
    n = int(values[0])
    k = int(values[1 + n])
    nodes, root = _read_tree(f"{n}\n{' '.join(values[1 : 1 + n])}\n")
    order = []

    def inorder(node):
        if node is None:
            return
        inorder(nodes[node]["left"])
        order.append(nodes[node]["val"])
        inorder(nodes[node]["right"])

    inorder(root)
    return str(order[k - 1])


def _solve_flatten_tree(text):
    nodes, root = _read_tree(text)
    result = []

    def preorder(node):
        if node is None:
            return
        result.append(nodes[node]["val"])
        preorder(nodes[node]["left"])
        preorder(nodes[node]["right"])

    preorder(root)
    return _join(result)


def _solve_build_tree(text):
    values = _ints(text)
    n = values[0]
    preorder = values[1 : 1 + n]
    inorder = values[1 + n : 1 + 2 * n]
    pos = {value: i for i, value in enumerate(inorder)}
    nodes = []

    def add(value):
        nodes.append({"val": value, "left": None, "right": None})
        return len(nodes) - 1

    def build(pl, pr, il, ir):
        if pl > pr:
            return None
        root = add(preorder[pl])
        mid = pos[preorder[pl]]
        left_size = mid - il
        nodes[root]["left"] = build(pl + 1, pl + left_size, il, mid - 1)
        nodes[root]["right"] = build(pl + left_size + 1, pr, mid + 1, ir)
        return root

    root = build(0, n - 1, 0, n - 1)
    return _tree_level_order(nodes, root)


def _solve_max_path_sum(text):
    nodes, root = _read_tree(text)
    best = -10**30

    def dfs(node):
        nonlocal best
        if node is None:
            return 0
        left = max(0, dfs(nodes[node]["left"]))
        right = max(0, dfs(nodes[node]["right"]))
        best = max(best, nodes[node]["val"] + left + right)
        return nodes[node]["val"] + max(left, right)

    dfs(root)
    return str(best)


def _solve_permutations(text):
    nums = sorted(_ints(text)[1:])
    result = []

    def dfs(path, used):
        if len(path) == len(nums):
            result.append(path[:])
            return
        for i, value in enumerate(nums):
            if not used[i]:
                used[i] = True
                path.append(value)
                dfs(path, used)
                path.pop()
                used[i] = False

    dfs([], [False] * len(nums))
    return "\n".join([str(len(result))] + [_join(row) for row in result])


def _solve_subsets(text):
    nums = sorted(_ints(text)[1:])
    result = [[]]
    for value in nums:
        result += [row + [value] for row in result]
    result.sort(key=lambda row: (len(row), row))
    lines = [str(len(result))]
    lines.extend("EMPTY" if not row else _join(row) for row in result)
    return "\n".join(lines)


def _solve_phone(text):
    digits = text.strip()
    mapping = {
        "2": "abc",
        "3": "def",
        "4": "ghi",
        "5": "jkl",
        "6": "mno",
        "7": "pqrs",
        "8": "tuv",
        "9": "wxyz",
    }
    result = [""]
    for digit in digits:
        result = [prefix + char for prefix in result for char in mapping[digit]]
    return "\n".join([str(len(result))] + result)


def _solve_word_search(text):
    lines = text.strip().splitlines()
    m, n = map(int, lines[0].split())
    board = [list(lines[i + 1].replace(" ", "").strip()) for i in range(m)]
    word = lines[1 + m].strip()

    def dfs(x, y, index):
        if index == len(word):
            return True
        if not (0 <= x < m and 0 <= y < n) or board[x][y] != word[index]:
            return False
        original = board[x][y]
        board[x][y] = "#"
        ok = any(dfs(x + dx, y + dy, index + 1) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        board[x][y] = original
        return ok

    return _bool(any(dfs(i, j, 0) for i in range(m) for j in range(n)))


def _solve_n_queens(text):
    n = int(text.strip())
    count = 0
    cols, diag1, diag2 = set(), set(), set()

    def dfs(row):
        nonlocal count
        if row == n:
            count += 1
            return
        for col in range(n):
            if col in cols or row + col in diag1 or row - col in diag2:
                continue
            cols.add(col)
            diag1.add(row + col)
            diag2.add(row - col)
            dfs(row + 1)
            cols.remove(col)
            diag1.remove(row + col)
            diag2.remove(row - col)

    dfs(0)
    return str(count)


def _solve_search_matrix(text):
    values = _ints(text)
    m, n = values[0], values[1]
    target = values[2 + m * n]
    nums = values[2 : 2 + m * n]
    return _bool(target in nums)


def _solve_peak(text):
    nums = _ints(text)[1:]
    n = len(nums)
    for i, value in enumerate(nums):
        left = nums[i - 1] if i else -10**30
        right = nums[i + 1] if i + 1 < n else -10**30
        if value > left and value > right:
            return str(i)
    return "-1"


def _solve_rotated_min(text):
    return str(min(_ints(text)[1:]))


def _solve_word_ladder(text):
    lines = text.strip().splitlines()
    begin, end = lines[0].split()
    n = int(lines[1])
    words = set(" ".join(lines[2:]).split()[:n])
    if end not in words:
        return "0"
    queue = deque([(begin, 1)])
    seen = {begin}
    while queue:
        word, depth = queue.popleft()
        if word == end:
            return str(depth)
        for i in range(len(word)):
            for code in range(ord("a"), ord("z") + 1):
                nxt = word[:i] + chr(code) + word[i + 1 :]
                if nxt in words and nxt not in seen:
                    seen.add(nxt)
                    queue.append((nxt, depth + 1))
    return "0"


def _solve_division(text):
    lines = text.strip().splitlines()
    e = int(lines[0])
    graph = defaultdict(list)
    for line in lines[1 : 1 + e]:
        a, b, value = line.split()
        value = float(value)
        graph[a].append((b, value))
        graph[b].append((a, 1 / value))
    q_line = 1 + e
    q = int(lines[q_line])
    outputs = []
    for line in lines[q_line + 1 : q_line + 1 + q]:
        start, end = line.split()
        if start not in graph or end not in graph:
            outputs.append("-1.00000")
            continue
        queue = deque([(start, 1.0)])
        seen = {start}
        found = None
        while queue:
            node, value = queue.popleft()
            if node == end:
                found = value
                break
            for nxt, weight in graph[node]:
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append((nxt, value * weight))
        outputs.append(f"{found:.5f}" if found is not None else "-1.00000")
    return "\n".join(outputs)


def _solve_components(text):
    values = _ints(text)
    n, m = values[0], values[1]
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    count = n
    cursor = 2
    for _ in range(m):
        a, b = values[cursor], values[cursor + 1]
        cursor += 2
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
            count -= 1
    return str(count)


def _solve_lcs(text):
    lines = text.rstrip("\n").splitlines()
    a = lines[0] if lines else ""
    b = lines[1] if len(lines) > 1 else ""
    dp = [0] * (len(b) + 1)
    for ca in a:
        prev = 0
        for j, cb in enumerate(b, 1):
            old = dp[j]
            dp[j] = prev + 1 if ca == cb else max(dp[j], dp[j - 1])
            prev = old
    return str(dp[-1])


def _solve_best_stock(text):
    prices = _ints(text)[1:]
    best = 0
    low = prices[0]
    for price in prices:
        low = min(low, price)
        best = max(best, price - low)
    return str(best)


def _solve_stock_cooldown(text):
    prices = _ints(text)[1:]
    hold, sold, rest = -10**30, 0, 0
    for price in prices:
        hold, sold, rest = max(hold, rest - price), hold + price, max(rest, sold)
    return str(max(sold, rest))


def _solve_squares(text):
    n = int(text.strip())
    dp = [0] + [10**9] * n
    squares = [i * i for i in range(1, int(n**0.5) + 1)]
    for i in range(1, n + 1):
        dp[i] = min(dp[i - square] + 1 for square in squares if square <= i)
    return str(dp[n])


def _solve_daily_temps(text):
    temps = _ints(text)[1:]
    result = [0] * len(temps)
    stack = []
    for i, temp in enumerate(temps):
        while stack and temps[stack[-1]] < temp:
            prev = stack.pop()
            result[prev] = i - prev
        stack.append(i)
    return _join(result)


def _solve_largest_rectangle(text):
    heights = _ints(text)[1:] + [0]
    stack = []
    best = 0
    for i, height in enumerate(heights):
        while stack and heights[stack[-1]] > height:
            h = heights[stack.pop()]
            left = stack[-1] if stack else -1
            best = max(best, h * (i - left - 1))
        stack.append(i)
    return str(best)


def _solve_min_stack(text):
    lines = text.strip().splitlines()
    stack, mins, outputs = [], [], []
    for line in lines[1:]:
        parts = line.split()
        if parts[0] == "PUSH":
            value = int(parts[1])
            stack.append(value)
            mins.append(value if not mins else min(value, mins[-1]))
        elif parts[0] == "POP":
            if stack:
                stack.pop()
                mins.pop()
        elif parts[0] == "TOP":
            outputs.append(str(stack[-1]) if stack else "EMPTY")
        else:
            outputs.append(str(mins[-1]) if mins else "EMPTY")
    return "\n".join(outputs)


def _solve_decode(text):
    stack = []
    current = ""
    number = 0
    for char in text.strip():
        if char.isdigit():
            number = number * 10 + int(char)
        elif char == "[":
            stack.append((current, number))
            current = ""
            number = 0
        elif char == "]":
            prefix, count = stack.pop()
            current = prefix + current * count
        else:
            current += char
    return current


def _solve_lru(text):
    lines = text.strip().splitlines()
    capacity, q = map(int, lines[0].split())
    cache = OrderedDict()
    outputs = []
    for line in lines[1 : 1 + q]:
        parts = line.split()
        if parts[0] == "GET":
            key = parts[1]
            if key not in cache:
                outputs.append("-1")
            else:
                value = cache.pop(key)
                cache[key] = value
                outputs.append(str(value))
        else:
            key, value = parts[1], int(parts[2])
            if key in cache:
                cache.pop(key)
            elif len(cache) == capacity:
                cache.popitem(last=False)
            cache[key] = value
    return "\n".join(outputs)


def _solve_unique_permutations(text):
    nums = sorted(_ints(text)[1:])
    counter = Counter(nums)
    result = []

    def dfs(path):
        if len(path) == len(nums):
            result.append(path[:])
            return
        for value in sorted(counter):
            if counter[value] == 0:
                continue
            counter[value] -= 1
            path.append(value)
            dfs(path)
            path.pop()
            counter[value] += 1

    dfs([])
    return "\n".join([str(len(result))] + [_join(row) for row in result])


def _solve_first_missing(text):
    nums = set(_ints(text)[1:])
    answer = 1
    while answer in nums:
        answer += 1
    return str(answer)


def _solve_sort_colors(text):
    return _join(sorted(_ints(text)[1:]))


def _solve_next_permutation(text):
    nums = _ints(text)[1:]
    i = len(nums) - 2
    while i >= 0 and nums[i] >= nums[i + 1]:
        i -= 1
    if i >= 0:
        j = len(nums) - 1
        while nums[j] <= nums[i]:
            j -= 1
        nums[i], nums[j] = nums[j], nums[i]
    nums[i + 1 :] = reversed(nums[i + 1 :])
    return _join(nums)


def _solve_single_number(text):
    ans = 0
    for value in _ints(text)[1:]:
        ans ^= value
    return str(ans)


def _solve_majority(text):
    candidate = None
    count = 0
    for value in _ints(text)[1:]:
        if count == 0:
            candidate = value
        count += 1 if value == candidate else -1
    return str(candidate)


def _solve_rotate_array(text):
    values = _ints(text)
    n, k = values[0], values[1]
    nums = values[2 : 2 + n]
    k %= n
    return _join(nums[-k:] + nums[:-k] if k else nums)


def _solve_duplicate(text):
    seen = set()
    for value in _ints(text)[1:]:
        if value in seen:
            return str(value)
        seen.add(value)
    return "-1"


def _solve_life(text):
    values = _ints(text)
    m, n = values[0], values[1]
    grid = [values[2 + i * n : 2 + (i + 1) * n] for i in range(m)]
    result = [[0] * n for _ in range(m)]
    for i in range(m):
        for j in range(n):
            live = 0
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    x, y = i + dx, j + dy
                    if 0 <= x < m and 0 <= y < n:
                        live += grid[x][y]
            result[i][j] = 1 if live == 3 or (grid[i][j] == 1 and live == 2) else 0
    return _join_lines(result)


def _solve_zeroes(text):
    values = _ints(text)
    m, n = values[0], values[1]
    grid = [values[2 + i * n : 2 + (i + 1) * n] for i in range(m)]
    rows = {i for i in range(m) for j in range(n) if grid[i][j] == 0}
    cols = {j for i in range(m) for j in range(n) if grid[i][j] == 0}
    for i in range(m):
        for j in range(n):
            if i in rows or j in cols:
                grid[i][j] = 0
    return _join_lines(grid)


def _solve_spiral(text):
    values = _ints(text)
    m, n = values[0], values[1]
    grid = [values[2 + i * n : 2 + (i + 1) * n] for i in range(m)]
    top, bottom, left, right = 0, m - 1, 0, n - 1
    result = []
    while top <= bottom and left <= right:
        result.extend(grid[top][left : right + 1])
        top += 1
        for i in range(top, bottom + 1):
            result.append(grid[i][right])
        right -= 1
        if top <= bottom:
            result.extend(reversed(grid[bottom][left : right + 1]))
            bottom -= 1
        if left <= right:
            for i in range(bottom, top - 1, -1):
                result.append(grid[i][left])
            left += 1
    return _join(result)


def _solve_search_insert(text):
    values = _ints(text)
    n, target = values[0], values[1]
    return str(bisect.bisect_left(values[2 : 2 + n], target))


def _solve_merge_sorted_arrays(text):
    values = _ints(text)
    n, m = values[0], values[1]
    a = values[2 : 2 + n]
    b = values[2 + n : 2 + n + m]
    return _join(sorted(a + b))


def _solve_three_closest(text):
    values = _ints(text)
    n, target = values[0], values[1]
    nums = sorted(values[2 : 2 + n])
    best = nums[0] + nums[1] + nums[2]
    for i in range(n - 2):
        left, right = i + 1, n - 1
        while left < right:
            total = nums[i] + nums[left] + nums[right]
            if abs(total - target) < abs(best - target) or (
                abs(total - target) == abs(best - target) and total < best
            ):
                best = total
            if total < target:
                left += 1
            elif total > target:
                right -= 1
            else:
                return str(total)
    return str(best)


def _solve_four_sum(text):
    values = _ints(text)
    n, target = values[0], values[1]
    nums = sorted(values[2 : 2 + n])
    result = []
    for i in range(n - 3):
        if i and nums[i] == nums[i - 1]:
            continue
        for j in range(i + 1, n - 2):
            if j > i + 1 and nums[j] == nums[j - 1]:
                continue
            left, right = j + 1, n - 1
            while left < right:
                total = nums[i] + nums[j] + nums[left] + nums[right]
                if total == target:
                    result.append([nums[i], nums[j], nums[left], nums[right]])
                    left += 1
                    right -= 1
                    while left < right and nums[left] == nums[left - 1]:
                        left += 1
                    while left < right and nums[right] == nums[right + 1]:
                        right -= 1
                elif total < target:
                    left += 1
                else:
                    right -= 1
    lines = [str(len(result))]
    lines.extend(_join(row) for row in result)
    return "\n".join(lines)


def _solve_happy(text):
    n = int(text.strip())
    seen = set()
    while n != 1 and n not in seen:
        seen.add(n)
        n = sum(int(char) ** 2 for char in str(n))
    return _bool(n == 1)


def _solve_roman(text):
    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    s = text.strip()
    total = 0
    for i, char in enumerate(s):
        value = values[char]
        if i + 1 < len(s) and value < values[s[i + 1]]:
            total -= value
        else:
            total += value
    return str(total)


PRACTICE_PROBLEM_BANK = {
    "trapping-rain-water-acm": {
        "description": "给定每个位置的柱子高度，雨后水只会被左右更高的柱子围住。请计算总接水量。",
        "input_format": "第一行输入整数 n。第二行输入 n 个非负整数表示高度。",
        "output_format": "输出一个整数，表示可以接住的雨水总量。",
        "constraints": ["1 <= n <= 200000", "0 <= height[i] <= 10^9"],
        "solver": _solve_trap,
        "samples": ["12\n0 1 0 2 1 0 1 3 2 1 2 1\n"],
        "hidden": ["6\n4 2 0 3 2 5\n", "5\n1 2 3 4 5\n", "5\n5 4 1 2 3\n", "3\n2 0 2\n", "7\n0 3 0 1 0 2 0\n"],
    },
    "minimum-window-substring-acm": {
        "description": "给定字符串 s 和 t，请找出 s 中最短的连续子串，使它包含 t 中每个字符及其出现次数。若长度相同，输出最靠左的一段。",
        "input_format": "第一行输入字符串 s，第二行输入字符串 t。字符串只包含可见 ASCII 字符且不含空格。",
        "output_format": "输出满足条件的最短子串；如果不存在，输出空行。",
        "constraints": ["1 <= |s|, |t| <= 200000"],
        "solver": _solve_min_window,
        "samples": ["ADOBECODEBANC\nABC\n"],
        "hidden": ["a\naa\n", "aa\naa\n", "abdecfab\nabc\n", "bbaa\naba\n", "cabefgecdaecf\ncae\n"],
    },
    "valid-anagram-acm": {
        "description": "给定两个小写字符串，判断它们是否由完全相同的字符重排得到。",
        "input_format": "输入两行，每行一个字符串。",
        "output_format": "若互为字母异位词输出 true，否则输出 false。",
        "constraints": ["1 <= 字符串长度 <= 200000", "字符串仅包含小写字母"],
        "solver": _solve_anagram,
        "samples": ["anagram\nnagaram\n"],
        "hidden": ["rat\ncar\n", "a\nb\n", "listen\nsilent\n", "aaab\nabaa\n", "abc\nabcc\n"],
    },
    "longest-consecutive-sequence-acm": {
        "description": "给定一个未排序整数数组，请计算最长连续整数序列的长度，序列中的数字不要求在原数组中相邻。",
        "input_format": "第一行输入整数 n。第二行输入 n 个整数。",
        "output_format": "输出最长连续序列的长度。",
        "constraints": ["0 <= n <= 200000", "-10^9 <= nums[i] <= 10^9"],
        "solver": _solve_longest_consecutive,
        "samples": ["6\n100 4 200 1 3 2\n"],
        "hidden": ["0\n\n", "10\n0 3 7 2 5 8 4 6 0 1\n", "5\n1 2 0 1 3\n", "6\n-2 -3 -1 5 6 7\n", "4\n10 10 10 10\n"],
    },
    "move-zeroes-acm": {
        "description": "给定数组，在保持非零元素相对顺序的前提下，将所有 0 移动到末尾。",
        "input_format": "第一行输入整数 n。第二行输入 n 个整数。",
        "output_format": "输出调整后的数组，数字之间用一个空格分隔。",
        "constraints": ["1 <= n <= 200000", "-10^9 <= nums[i] <= 10^9"],
        "solver": _solve_move_zeroes,
        "samples": ["5\n0 1 0 3 12\n"],
        "hidden": ["3\n0 0 0\n", "4\n1 2 3 4\n", "6\n0 -1 0 -2 0 3\n", "1\n0\n", "5\n4 0 5 0 0\n"],
    },
    "non-overlapping-intervals-acm": {
        "description": "给定若干闭区间，请删除尽量少的区间，使剩余区间两两不重叠。若一个区间终点等于另一个区间起点，视为不重叠。",
        "input_format": "第一行输入整数 n。随后 n 行每行输入 l r 表示一个区间。",
        "output_format": "输出最少需要删除的区间数量。",
        "constraints": ["0 <= n <= 200000", "-10^9 <= l <= r <= 10^9"],
        "solver": _solve_non_overlap,
        "samples": ["4\n1 2\n2 3\n3 4\n1 3\n"],
        "hidden": ["3\n1 2\n1 2\n1 2\n", "2\n1 2\n2 3\n", "5\n-5 -1\n-2 0\n0 1\n1 3\n2 4\n", "0\n", "4\n1 100\n11 22\n1 11\n2 12\n"],
    },
    "maximum-product-subarray-acm": {
        "description": "给定整数数组，请找出乘积最大的非空连续子数组，并输出这个最大乘积。",
        "input_format": "第一行输入整数 n。第二行输入 n 个整数。",
        "output_format": "输出最大连续子数组乘积。",
        "constraints": ["1 <= n <= 200000", "-100 <= nums[i] <= 100"],
        "solver": _solve_max_product,
        "samples": ["4\n2 3 -2 4\n"],
        "hidden": ["3\n-2 0 -1\n", "4\n-2 3 -4 2\n", "5\n0 2 -5 -2 0\n", "1\n-3\n", "6\n-1 -2 -9 -6 0 4\n"],
    },
    "house-robber-acm": {
        "description": "一排房屋中每间都有一定金额，不能选择相邻房屋。请输出能够取得的最大金额。",
        "input_format": "第一行输入整数 n。第二行输入 n 个非负整数。",
        "output_format": "输出最大金额。",
        "constraints": ["1 <= n <= 200000", "0 <= nums[i] <= 10^9"],
        "solver": _solve_house_robber,
        "samples": ["4\n1 2 3 1\n"],
        "hidden": ["5\n2 7 9 3 1\n", "1\n10\n", "4\n2 1 1 2\n", "5\n0 0 0 0 0\n", "6\n6 6 4 8 4 3\n"],
    },
    "climbing-stairs-acm": {
        "description": "每次可以爬 1 级或 2 级台阶。给定台阶数 n，计算到达顶部的不同走法数量。",
        "input_format": "输入一个整数 n。",
        "output_format": "输出不同走法数量。",
        "constraints": ["1 <= n <= 90"],
        "solver": _solve_climb,
        "samples": ["3\n"],
        "hidden": ["1\n", "2\n", "10\n", "20\n", "45\n"],
    },
    "unique-paths-acm": {
        "description": "机器人从 m x n 网格左上角出发，每次只能向右或向下移动一步。请计算到达右下角的路径数。",
        "input_format": "输入两个整数 m n。",
        "output_format": "输出不同路径数量。",
        "constraints": ["1 <= m, n <= 30"],
        "solver": _solve_unique_paths,
        "samples": ["3 7\n"],
        "hidden": ["3 2\n", "1 10\n", "10 1\n", "10 10\n", "15 12\n"],
    },
    "minimum-path-sum-acm": {
        "description": "给定非负整数网格，从左上角走到右下角，每次只能向右或向下。请输出路径数字和的最小值。",
        "input_format": "第一行输入 m n。随后 m 行每行 n 个整数。",
        "output_format": "输出最小路径和。",
        "constraints": ["1 <= m, n <= 300", "0 <= grid[i][j] <= 10^9"],
        "solver": _solve_min_path_sum,
        "samples": ["3 3\n1 3 1\n1 5 1\n4 2 1\n"],
        "hidden": ["2 3\n1 2 3\n4 5 6\n", "1 4\n5 1 2 3\n", "3 1\n2\n3\n4\n", "2 2\n0 0\n0 0\n", "3 4\n1 9 1 1\n1 9 1 9\n1 1 1 1\n"],
    },
    "edit-distance-acm": {
        "description": "给定两个字符串，每次可以插入、删除或替换一个字符。请计算把第一个字符串变成第二个字符串的最少操作次数。",
        "input_format": "输入两行，分别为字符串 a 和 b。",
        "output_format": "输出最少编辑次数。",
        "constraints": ["0 <= |a|, |b| <= 2000"],
        "solver": _solve_edit_distance,
        "samples": ["horse\nros\n"],
        "hidden": ["intention\nexecution\n", "abc\nabc\n", "a\nb\n", "kitten\nsitting\n", "abcdef\nazced\n"],
    },
    "longest-increasing-subsequence-acm": {
        "description": "给定整数数组，请输出严格递增子序列的最大长度。",
        "input_format": "第一行输入整数 n。第二行输入 n 个整数。",
        "output_format": "输出最长严格递增子序列长度。",
        "constraints": ["1 <= n <= 200000", "-10^9 <= nums[i] <= 10^9"],
        "solver": _solve_lis,
        "samples": ["8\n10 9 2 5 3 7 101 18\n"],
        "hidden": ["6\n0 1 0 3 2 3\n", "7\n7 7 7 7 7 7 7\n", "5\n1 2 3 4 5\n", "5\n5 4 3 2 1\n", "8\n-1 3 4 -2 0 6 2 3\n"],
    },
    "partition-equal-subset-sum-acm": {
        "description": "给定正整数数组，判断能否把它分成两个元素和相等的子集。",
        "input_format": "第一行输入整数 n。第二行输入 n 个正整数。",
        "output_format": "可以分割输出 true，否则输出 false。",
        "constraints": ["1 <= n <= 200", "1 <= nums[i] <= 2000"],
        "solver": _solve_partition,
        "samples": ["4\n1 5 11 5\n"],
        "hidden": ["4\n1 2 3 5\n", "1\n2\n", "5\n2 2 3 5 5\n", "6\n3 3 3 4 5 6\n", "4\n100 100 100 100\n"],
    },
    "target-sum-acm": {
        "description": "给定数组和目标值，请给每个数字前添加 + 或 -，统计表达式结果等于目标值的方案数。",
        "input_format": "第一行输入 n target。第二行输入 n 个非负整数。",
        "output_format": "输出方案数。",
        "constraints": ["1 <= n <= 30", "0 <= nums[i] <= 1000"],
        "solver": _solve_target_sum,
        "samples": ["5 3\n1 1 1 1 1\n"],
        "hidden": ["1 1\n1\n", "1 2\n1\n", "3 0\n0 0 0\n", "4 2\n1 2 1 2\n", "5 5\n2 3 5 7 1\n"],
    },
    "word-break-acm": {
        "description": "给定字符串和词典，判断字符串能否由词典中的一个或多个单词拼接而成，单词可以重复使用。",
        "input_format": "第一行输入字符串 s。第二行输入整数 n。第三行输入 n 个单词。",
        "output_format": "可以拼接输出 true，否则输出 false。",
        "constraints": ["1 <= |s| <= 200000", "1 <= n <= 20000"],
        "solver": _solve_word_break,
        "samples": ["leetcode\n2\nleet code\n"],
        "hidden": ["applepenapple\n2\napple pen\n", "catsandog\n5\ncats dog sand and cat\n", "aaaaaaa\n2\naaaa aaa\n", "cars\n3\ncar ca rs\n", "goalspecial\n5\ngo goal goals special al\n"],
    },
    "number-of-islands-acm": {
        "description": "给定由 0 和 1 组成的网格，水平或竖直相邻的 1 属于同一个岛屿。请统计岛屿数量。",
        "input_format": "第一行输入 m n。随后 m 行输入长度为 n 的 01 字符串。",
        "output_format": "输出岛屿数量。",
        "constraints": ["1 <= m, n <= 1000"],
        "solver": _solve_islands,
        "samples": ["4 5\n11110\n11010\n11000\n00000\n"],
        "hidden": ["4 5\n11000\n11000\n00100\n00011\n", "1 1\n0\n", "1 1\n1\n", "3 3\n101\n010\n101\n", "3 4\n1111\n0000\n1111\n"],
    },
    "rotting-oranges-acm": {
        "description": "网格中 0 表示空格，1 表示新鲜橘子，2 表示腐烂橘子。每分钟腐烂橘子会感染四邻的新鲜橘子。请计算全部腐烂所需时间，若无法全部腐烂输出 -1。",
        "input_format": "第一行输入 m n。随后 m 行每行 n 个整数。",
        "output_format": "输出分钟数或 -1。",
        "constraints": ["1 <= m, n <= 1000"],
        "solver": _solve_oranges,
        "samples": ["3 3\n2 1 1\n1 1 0\n0 1 1\n"],
        "hidden": ["3 3\n2 1 1\n0 1 1\n1 0 1\n", "1 2\n0 2\n", "1 1\n1\n", "2 2\n2 2\n1 1\n", "3 3\n0 0 0\n0 0 0\n0 0 0\n"],
    },
    "course-schedule-acm": {
        "description": "共有 n 门课程，若输入 a b 表示学习 a 之前必须先学习 b。请判断是否能完成所有课程。",
        "input_format": "第一行输入 n m。随后 m 行每行输入 a b。",
        "output_format": "可以完成输出 true，否则输出 false。",
        "constraints": ["1 <= n <= 200000", "0 <= m <= 200000"],
        "solver": _solve_course,
        "samples": ["2 1\n1 0\n"],
        "hidden": ["2 2\n1 0\n0 1\n", "4 4\n1 0\n2 0\n3 1\n3 2\n", "3 0\n", "3 3\n0 1\n1 2\n2 0\n", "5 4\n1 0\n2 1\n3 2\n4 3\n"],
    },
    "implement-trie-acm": {
        "description": "请模拟一个只包含小写字母的 Trie，支持插入单词、查询完整单词、查询前缀。",
        "input_format": "第一行输入操作数 q。随后 q 行形如 INSERT word、SEARCH word 或 PREFIX word。",
        "output_format": "对每个 SEARCH/PREFIX 操作输出 true 或 false，各占一行。",
        "constraints": ["1 <= q <= 200000", "所有单词总长度 <= 500000"],
        "solver": _solve_trie,
        "samples": ["5\nINSERT apple\nSEARCH apple\nSEARCH app\nPREFIX app\nINSERT app\n"],
        "hidden": ["6\nINSERT app\nINSERT apple\nSEARCH app\nSEARCH apple\nPREFIX appl\nSEARCH apply\n", "4\nSEARCH a\nPREFIX a\nINSERT a\nSEARCH a\n", "5\nINSERT abc\nINSERT ab\nPREFIX abc\nSEARCH abc\nSEARCH a\n", "3\nINSERT zoo\nPREFIX zo\nPREFIX za\n", "7\nINSERT a\nINSERT aa\nINSERT aaa\nSEARCH aa\nPREFIX aaaa\nSEARCH aaa\nSEARCH b\n"],
    },
    "top-k-frequent-elements-acm": {
        "description": "给定数组和 k，请输出出现频率最高的 k 个数字。频率相同按数字升序。",
        "input_format": "第一行输入 n k。第二行输入 n 个整数。",
        "output_format": "输出 k 个整数，按频率降序、数字升序排列。",
        "constraints": ["1 <= k <= 不同元素个数 <= n <= 200000"],
        "solver": _solve_top_k,
        "samples": ["6 2\n1 1 1 2 2 3\n"],
        "hidden": ["1 1\n1\n", "7 2\n4 4 1 1 2 2 3\n", "8 3\n-1 -1 -2 -2 -2 3 3 4\n", "5 2\n5 4 3 2 1\n", "10 1\n9 9 8 8 8 7 7 7 7 6\n"],
    },
    "find-median-from-data-stream-acm": {
        "description": "维护一个整数数据流，支持添加数字和查询当前中位数。偶数个数字时，中位数为中间两个数的平均值。",
        "input_format": "第一行输入操作数 q。随后 q 行为 ADD x 或 MEDIAN。",
        "output_format": "对每个 MEDIAN 输出一行；若结果为 .5，保留一位小数，否则输出整数。",
        "constraints": ["1 <= q <= 200000", "查询 MEDIAN 时数据流非空"],
        "solver": _solve_median_stream,
        "samples": ["5\nADD 1\nADD 2\nMEDIAN\nADD 3\nMEDIAN\n"],
        "hidden": ["6\nADD 5\nMEDIAN\nADD 1\nMEDIAN\nADD 9\nMEDIAN\n", "7\nADD -1\nADD -2\nADD -3\nMEDIAN\nADD -4\nMEDIAN\nADD 0\n", "4\nADD 10\nADD 20\nADD 30\nMEDIAN\n", "8\nADD 2\nADD 2\nADD 2\nMEDIAN\nADD 3\nMEDIAN\nADD 1\nMEDIAN\n", "3\nADD 100\nADD -100\nMEDIAN\n"],
    },
    "sliding-window-maximum-acm": {
        "description": "给定数组和窗口长度 k，请输出每个连续窗口中的最大值。",
        "input_format": "第一行输入 n k。第二行输入 n 个整数。",
        "output_format": "输出 n-k+1 个整数，表示每个窗口最大值。",
        "constraints": ["1 <= k <= n <= 200000"],
        "solver": _solve_sliding_max,
        "samples": ["8 3\n1 3 -1 -3 5 3 6 7\n"],
        "hidden": ["1 1\n1\n", "5 2\n9 8 7 6 5\n", "5 5\n1 2 3 4 5\n", "6 3\n4 4 4 4 4 4\n", "7 4\n2 1 3 4 6 3 8\n"],
    },
    "kth-largest-element-acm": {
        "description": "给定数组和 k，请输出排序后第 k 大的元素，重复元素按出现次数计算。",
        "input_format": "第一行输入 n k。第二行输入 n 个整数。",
        "output_format": "输出第 k 大元素。",
        "constraints": ["1 <= k <= n <= 200000"],
        "solver": _solve_kth_largest,
        "samples": ["6 2\n3 2 1 5 6 4\n"],
        "hidden": ["9 4\n3 2 3 1 2 4 5 5 6\n", "1 1\n10\n", "5 5\n5 4 3 2 1\n", "5 1\n-1 -2 -3 -4 -5\n", "6 3\n2 2 2 1 1 3\n"],
    },
    "merge-k-sorted-lists-acm": {
        "description": "给定 k 个升序整数序列，请合并成一个升序序列。",
        "input_format": "第一行输入 k。随后 k 行，每行先输入长度 len，再输入 len 个升序整数。",
        "output_format": "输出合并后的升序序列；若为空输出空行。",
        "constraints": ["0 <= k <= 10000", "所有序列总长度 <= 200000"],
        "solver": _solve_merge_k_lists,
        "samples": ["3\n3 1 4 5\n3 1 3 4\n2 2 6\n"],
        "hidden": ["0\n", "1\n0\n", "2\n3 -3 -1 0\n2 -2 2\n", "3\n1 5\n1 4\n1 3\n", "4\n2 1 1\n0\n3 2 2 2\n1 3\n"],
    },
    "reverse-linked-list-acm": {
        "description": "用数组表示一条链表从头到尾的节点值。请输出反转后的链表值。",
        "input_format": "第一行输入 n。第二行输入 n 个整数。",
        "output_format": "输出反转后的 n 个整数。",
        "constraints": ["0 <= n <= 200000"],
        "solver": _solve_reverse_list,
        "samples": ["5\n1 2 3 4 5\n"],
        "hidden": ["1\n9\n", "0\n\n", "4\n-1 0 2 3\n", "3\n7 7 7\n", "6\n1 2 3 4 5 6\n"],
    },
    "linked-list-cycle-entry-acm": {
        "description": "给定链表每个节点的 next 下标，头节点固定为 0。请输出环入口下标；若无环输出 -1。",
        "input_format": "第一行输入 n。第二行输入 n 个整数，第 i 个数表示节点 i 的 next 下标，-1 表示空。",
        "output_format": "输出环入口下标或 -1。",
        "constraints": ["0 <= n <= 200000", "-1 <= next[i] < n"],
        "solver": _solve_cycle_entry,
        "samples": ["4\n1 2 0 -1\n"],
        "hidden": ["5\n1 2 3 4 -1\n", "1\n0\n", "0\n\n", "6\n1 2 3 4 2 -1\n", "3\n1 -1 1\n"],
    },
    "intersection-of-two-linked-lists-acm": {
        "description": "两条链表用节点编号序列表示。若它们从某个节点编号开始相交，请输出第一条链表中最早出现的公共节点编号；否则输出 -1。",
        "input_format": "第一行输入 n m。第二行输入第一条链表的 n 个节点编号。第三行输入第二条链表的 m 个节点编号。",
        "output_format": "输出公共节点编号或 -1。",
        "constraints": ["0 <= n, m <= 200000"],
        "solver": _solve_intersection_list,
        "samples": ["5 4\n4 1 8 4 5\n5 6 1 8\n"],
        "hidden": ["3 3\n1 2 3\n4 5 6\n", "1 1\n7\n7\n", "4 2\n1 2 3 4\n3 4\n", "0 2\n\n1 2\n", "5 5\n9 8 7 6 5\n1 2 6 5 4\n"],
    },
    "palindrome-linked-list-acm": {
        "description": "给定链表从头到尾的节点值，判断它是否为回文序列。",
        "input_format": "第一行输入 n。第二行输入 n 个整数。",
        "output_format": "是回文输出 true，否则输出 false。",
        "constraints": ["0 <= n <= 200000"],
        "solver": _solve_palindrome_list,
        "samples": ["4\n1 2 2 1\n"],
        "hidden": ["2\n1 2\n", "1\n1\n", "5\n1 2 3 2 1\n", "0\n\n", "6\n1 2 3 3 2 1\n"],
    },
    "swap-nodes-in-pairs-acm": {
        "description": "给定链表节点值，请每两个相邻节点交换一次，最后一个单独节点保持不变。",
        "input_format": "第一行输入 n。第二行输入 n 个整数。",
        "output_format": "输出交换后的节点值。",
        "constraints": ["0 <= n <= 200000"],
        "solver": _solve_swap_pairs,
        "samples": ["4\n1 2 3 4\n"],
        "hidden": ["3\n1 2 3\n", "1\n1\n", "0\n\n", "5\n5 4 3 2 1\n", "6\n1 1 2 2 3 3\n"],
    },
    "reverse-nodes-in-k-group-acm": {
        "description": "给定链表节点值和 k，每 k 个节点为一组翻转；不足 k 个的最后一组保持原顺序。",
        "input_format": "第一行输入 n k。第二行输入 n 个整数。",
        "output_format": "输出处理后的节点值。",
        "constraints": ["1 <= k <= n <= 200000"],
        "solver": _solve_reverse_k_group,
        "samples": ["5 2\n1 2 3 4 5\n"],
        "hidden": ["5 3\n1 2 3 4 5\n", "1 1\n1\n", "6 6\n1 2 3 4 5 6\n", "6 4\n1 2 3 4 5 6\n", "7 2\n7 6 5 4 3 2 1\n"],
    },
    "maximum-depth-of-binary-tree-acm": {
        "description": "给定二叉树层序表示，空节点用 # 表示。请输出二叉树最大深度。",
        "input_format": "第一行输入 token 数 n。第二行输入 n 个 token。",
        "output_format": "输出最大深度。",
        "constraints": ["0 <= n <= 200000"],
        "solver": _solve_tree_depth,
        "samples": ["7\n3 9 20 # # 15 7\n"],
        "hidden": ["0\n\n", "1\n1\n", "3\n1 # 2\n", "7\n1 2 3 4 # # 5\n", "6\n1 2 # 3 # #\n"],
    },
    "invert-binary-tree-acm": {
        "description": "给定二叉树层序表示，请左右翻转整棵树，并输出翻转后的层序表示，末尾多余的 # 需要省略。",
        "input_format": "第一行输入 token 数 n。第二行输入 n 个 token。",
        "output_format": "输出翻转后的层序序列。",
        "constraints": ["0 <= n <= 200000"],
        "solver": _solve_invert_tree,
        "samples": ["7\n4 2 7 1 3 6 9\n"],
        "hidden": ["0\n\n", "1\n1\n", "3\n1 # 2\n", "7\n1 2 3 4 # # 5\n", "6\n1 2 # 3 # #\n"],
    },
    "symmetric-tree-acm": {
        "description": "给定二叉树层序表示，判断它是否关于根节点左右对称。",
        "input_format": "第一行输入 token 数 n。第二行输入 n 个 token。",
        "output_format": "对称输出 true，否则输出 false。",
        "constraints": ["0 <= n <= 200000"],
        "solver": _solve_symmetric,
        "samples": ["7\n1 2 2 3 4 4 3\n"],
        "hidden": ["7\n1 2 2 # 3 # 3\n", "1\n1\n", "0\n\n", "7\n1 2 2 2 # 2 #\n", "7\n1 2 2 # 3 3 #\n"],
    },
    "diameter-of-binary-tree-acm": {
        "description": "给定二叉树层序表示，请输出任意两个节点之间最长路径的边数。",
        "input_format": "第一行输入 token 数 n。第二行输入 n 个 token。",
        "output_format": "输出二叉树直径。",
        "constraints": ["0 <= n <= 200000"],
        "solver": _solve_diameter,
        "samples": ["5\n1 2 3 4 5\n"],
        "hidden": ["1\n1\n", "0\n\n", "3\n1 # 2\n", "7\n1 2 3 4 # # 5\n", "9\n1 2 # 3 # 4 # 5 #\n"],
    },
    "path-sum-iii-acm": {
        "description": "给定二叉树和目标和，请统计从某个节点向下到其后代的路径中，节点值之和等于目标值的路径数量。",
        "input_format": "第一行输入 token 数 n。第二行输入 n 个 token。第三行输入目标值 target。",
        "output_format": "输出满足条件的路径数量。",
        "constraints": ["0 <= n <= 200000", "-10^9 <= 节点值, target <= 10^9"],
        "solver": _solve_path_sum_iii,
        "samples": ["11\n10 5 -3 3 2 # 11 3 -2 # 1\n8\n"],
        "hidden": ["3\n1 2 3\n3\n", "1\n1\n1\n", "0\n\n0\n", "7\n1 -2 -3 1 3 -2 #\n-1\n", "5\n0 0 0 0 0\n0\n"],
    },
    "lowest-common-ancestor-acm": {
        "description": "给定二叉树层序表示和两个节点值。所有节点值互不相同，请输出这两个节点的最近公共祖先值。",
        "input_format": "第一行输入 token 数 n。第二行输入 n 个 token。第三行输入 p q。",
        "output_format": "输出最近公共祖先的节点值。",
        "constraints": ["1 <= n <= 200000"],
        "solver": _solve_lca,
        "samples": ["11\n3 5 1 6 2 0 8 # # 7 4\n5 1\n"],
        "hidden": ["11\n3 5 1 6 2 0 8 # # 7 4\n5 4\n", "1\n1\n1 1\n", "3\n1 2 3\n2 3\n", "7\n1 2 3 4 5 6 7\n4 5\n", "7\n1 2 3 4 5 6 7\n4 6\n"],
    },
    "binary-tree-right-side-view-acm": {
        "description": "从二叉树右侧观察，输出每一层最右侧能看到的节点值。",
        "input_format": "第一行输入 token 数 n。第二行输入 n 个 token。",
        "output_format": "按从上到下输出右视图节点值。",
        "constraints": ["0 <= n <= 200000"],
        "solver": _solve_right_view,
        "samples": ["7\n1 2 3 # 5 # 4\n"],
        "hidden": ["0\n\n", "1\n1\n", "3\n1 # 2\n", "7\n1 2 3 4 # # 5\n", "7\n1 2 3 4 5 6 7\n"],
    },
    "validate-binary-search-tree-acm": {
        "description": "给定二叉树层序表示，判断它是否是一棵严格二叉搜索树：左子树所有值小于根，右子树所有值大于根。",
        "input_format": "第一行输入 token 数 n。第二行输入 n 个 token。",
        "output_format": "合法输出 true，否则输出 false。",
        "constraints": ["0 <= n <= 200000"],
        "solver": _solve_validate_bst,
        "samples": ["3\n2 1 3\n"],
        "hidden": ["5\n5 1 4 # # 3 6\n", "1\n1\n", "0\n\n", "3\n2 2 2\n", "7\n5 3 7 2 4 6 8\n"],
    },
    "kth-smallest-in-bst-acm": {
        "description": "给定一棵二叉搜索树和 k，请输出第 k 小的节点值。",
        "input_format": "第一行输入 token 数 n。第二行输入 n 个 token。第三行输入 k。",
        "output_format": "输出第 k 小的值。",
        "constraints": ["1 <= k <= 节点数 <= 200000"],
        "solver": _solve_kth_bst,
        "samples": ["5\n3 1 4 # 2\n1\n"],
        "hidden": ["8\n5 3 6 2 4 # # 1\n3\n", "1\n1\n1\n", "7\n4 2 6 1 3 5 7\n7\n", "3\n2 1 3\n2\n", "7\n2 1 4 # # 3 5\n4\n"],
    },
    "flatten-binary-tree-acm": {
        "description": "给定二叉树，请按照先序遍历顺序把它展开为单链表。输出展开后的节点值序列。",
        "input_format": "第一行输入 token 数 n。第二行输入 n 个 token。",
        "output_format": "输出先序序列。",
        "constraints": ["0 <= n <= 200000"],
        "solver": _solve_flatten_tree,
        "samples": ["7\n1 2 5 3 4 # 6\n"],
        "hidden": ["0\n\n", "1\n1\n", "3\n1 # 2\n", "7\n1 2 3 4 5 6 7\n", "7\n1 2 # 3 # 4 #\n"],
    },
    "construct-tree-preorder-inorder-acm": {
        "description": "给定二叉树先序遍历和中序遍历，节点值互不相同。请重建二叉树并输出层序表示，末尾多余 # 省略。",
        "input_format": "第一行输入 n。第二行输入 n 个先序值。第三行输入 n 个中序值。",
        "output_format": "输出重建后树的层序序列。",
        "constraints": ["1 <= n <= 200000"],
        "solver": _solve_build_tree,
        "samples": ["5\n3 9 20 15 7\n9 3 15 20 7\n"],
        "hidden": ["1\n1\n1\n", "3\n1 2 3\n2 1 3\n", "3\n1 2 3\n3 2 1\n", "7\n1 2 4 5 3 6 7\n4 2 5 1 6 3 7\n", "4\n1 2 3 4\n1 2 3 4\n"],
    },
    "binary-tree-maximum-path-sum-acm": {
        "description": "给定二叉树，路径可以从任意节点开始并到任意节点结束，但必须沿父子边连接。请输出最大路径和。",
        "input_format": "第一行输入 token 数 n。第二行输入 n 个 token。",
        "output_format": "输出最大路径和。",
        "constraints": ["1 <= 节点数 <= 200000"],
        "solver": _solve_max_path_sum,
        "samples": ["3\n1 2 3\n"],
        "hidden": ["7\n-10 9 20 # # 15 7\n", "1\n-3\n", "3\n2 -1 -2\n", "7\n1 -2 3 4 5 -6 2\n", "3\n-1 -2 -3\n"],
    },
    "permutations-acm": {
        "description": "给定 n 个互不相同的整数，请按字典序输出它们的所有全排列。",
        "input_format": "第一行输入 n。第二行输入 n 个互不相同的整数。",
        "output_format": "第一行输出排列数量。随后每行输出一个排列，按字典序排列。",
        "constraints": ["1 <= n <= 8"],
        "solver": _solve_permutations,
        "samples": ["3\n1 2 3\n"],
        "hidden": ["1\n5\n", "2\n2 1\n", "3\n-1 0 1\n", "4\n1 2 3 4\n", "3\n3 1 2\n"],
    },
    "subsets-acm": {
        "description": "给定互不相同的整数数组，请输出所有子集。子集先按长度升序，长度相同按字典序升序。",
        "input_format": "第一行输入 n。第二行输入 n 个互不相同的整数。",
        "output_format": "第一行输出子集数量。空集输出 EMPTY，其余子集每行升序输出。",
        "constraints": ["0 <= n <= 15"],
        "solver": _solve_subsets,
        "samples": ["3\n1 2 3\n"],
        "hidden": ["0\n\n", "1\n5\n", "2\n2 1\n", "3\n-1 0 1\n", "4\n1 2 3 4\n"],
    },
    "letter-combinations-phone-acm": {
        "description": "给定由 2-9 组成的数字串，输出它在电话九宫格上可能对应的所有字母组合。",
        "input_format": "输入一行数字串。",
        "output_format": "第一行输出组合数量。随后按字典序每行输出一个组合。",
        "constraints": ["1 <= digits.length <= 8"],
        "solver": _solve_phone,
        "samples": ["23\n"],
        "hidden": ["2\n", "79\n", "234\n", "999\n", "56\n"],
    },
    "word-search-acm": {
        "description": "给定字符网格和单词，判断能否从网格中按上下左右相邻路径拼出该单词，同一个格子不能重复使用。",
        "input_format": "第一行输入 m n。随后 m 行输入字符网格。最后一行输入目标单词。",
        "output_format": "存在路径输出 true，否则输出 false。",
        "constraints": ["1 <= m, n <= 20", "1 <= word.length <= 200"],
        "solver": _solve_word_search,
        "samples": ["3 4\nABCE\nSFCS\nADEE\nABCCED\n"],
        "hidden": ["3 4\nABCE\nSFCS\nADEE\nSEE\n", "3 4\nABCE\nSFCS\nADEE\nABCB\n", "1 1\nA\nA\n", "2 2\nAA\nAA\nAAAAA\n", "2 3\nABC\nDEF\nBE\n"],
    },
    "n-queens-acm": {
        "description": "在 n x n 棋盘上放置 n 个皇后，使任意两个皇后都不在同一行、同一列或同一对角线。请输出方案数量。",
        "input_format": "输入整数 n。",
        "output_format": "输出 N 皇后方案数。",
        "constraints": ["1 <= n <= 12"],
        "solver": _solve_n_queens,
        "samples": ["4\n"],
        "hidden": ["1\n", "2\n", "3\n", "5\n", "8\n"],
    },
    "search-2d-matrix-acm": {
        "description": "给定矩阵，每行升序，且下一行第一个数大于上一行最后一个数。判断目标值是否存在。",
        "input_format": "第一行输入 m n。随后 m 行每行 n 个整数。最后一行输入 target。",
        "output_format": "存在输出 true，否则输出 false。",
        "constraints": ["1 <= m, n <= 1000"],
        "solver": _solve_search_matrix,
        "samples": ["3 4\n1 3 5 7\n10 11 16 20\n23 30 34 60\n3\n"],
        "hidden": ["3 4\n1 3 5 7\n10 11 16 20\n23 30 34 60\n13\n", "1 1\n1\n1\n", "1 3\n1 2 3\n0\n", "2 2\n1 2\n3 4\n4\n", "2 3\n-5 -3 -1\n0 2 4\n-3\n"],
    },
    "find-peak-element-acm": {
        "description": "若一个位置的值严格大于相邻位置，则它是峰值。数组两端外侧视为负无穷。若有多个峰值，输出最小下标。",
        "input_format": "第一行输入 n。第二行输入 n 个整数。",
        "output_format": "输出峰值下标。",
        "constraints": ["1 <= n <= 200000", "相邻元素不相等"],
        "solver": _solve_peak,
        "samples": ["4\n1 2 3 1\n"],
        "hidden": ["7\n1 2 1 3 5 6 4\n", "1\n1\n", "2\n2 1\n", "2\n1 2\n", "5\n5 4 3 2 1\n"],
    },
    "find-minimum-rotated-array-acm": {
        "description": "一个严格升序数组被旋转若干次后得到当前数组。请输出其中的最小值。",
        "input_format": "第一行输入 n。第二行输入 n 个互不相同的整数。",
        "output_format": "输出最小值。",
        "constraints": ["1 <= n <= 200000"],
        "solver": _solve_rotated_min,
        "samples": ["5\n3 4 5 1 2\n"],
        "hidden": ["7\n4 5 6 7 0 1 2\n", "1\n11\n", "3\n1 2 3\n", "2\n2 1\n", "5\n5 1 2 3 4\n"],
    },
    "word-ladder-acm": {
        "description": "每次只能改变一个字母，并且中间单词必须在词典中。请计算从 begin 到 end 的最短转换序列长度，包含起点和终点。",
        "input_format": "第一行输入 begin end。第二行输入词典大小 n。第三行输入 n 个单词。",
        "output_format": "输出最短长度；若不可达输出 0。",
        "constraints": ["1 <= 单词长度 <= 10", "1 <= n <= 50000"],
        "solver": _solve_word_ladder,
        "samples": ["hit cog\n6\nhot dot dog lot log cog\n"],
        "hidden": ["hit cog\n5\nhot dot dog lot log\n", "a c\n3\na b c\n", "lost cost\n5\nlost cost cast case cose\n", "red tax\n8\nted tex red tax tad den rex pee\n", "same same\n1\nsame\n"],
    },
    "evaluate-division-acm": {
        "description": "给定若干形如 a / b = value 的关系，请回答多个除法查询。无法确定时输出 -1.00000。",
        "input_format": "第一行输入关系数 e。随后 e 行输入 a b value。下一行输入查询数 q。随后 q 行输入 a b。",
        "output_format": "每个查询输出一行，保留 5 位小数。",
        "constraints": ["1 <= e, q <= 20000"],
        "solver": _solve_division,
        "samples": ["2\na b 2.0\nb c 3.0\n5\na c\nb a\na e\na a\nx x\n"],
        "hidden": ["1\na b 4.0\n3\na b\nb a\na a\n", "3\na b 2.0\nb c 5.0\nc d 0.5\n2\na d\nd a\n", "2\nx y 3.0\na b 2.0\n2\nx b\na y\n", "2\na b 2.5\nb c 4.0\n1\nc a\n", "1\nfoo bar 8.0\n1\nbar foo\n"],
    },
    "connected-components-union-find-acm": {
        "description": "给定无向图的 n 个点和 m 条边，请输出连通分量数量。",
        "input_format": "第一行输入 n m。随后 m 行每行输入一条无向边 u v。",
        "output_format": "输出连通分量数量。",
        "constraints": ["1 <= n <= 200000", "0 <= m <= 200000"],
        "solver": _solve_components,
        "samples": ["5 3\n0 1\n1 2\n3 4\n"],
        "hidden": ["5 0\n", "4 3\n0 1\n1 2\n2 3\n", "6 3\n0 1\n2 3\n4 5\n", "3 3\n0 1\n1 2\n0 2\n", "7 4\n0 1\n2 3\n3 4\n5 6\n"],
    },
    "longest-common-subsequence-acm": {
        "description": "给定两个字符串，请输出它们最长公共子序列的长度。子序列可以不连续，但相对顺序不能改变。",
        "input_format": "输入两行字符串。",
        "output_format": "输出最长公共子序列长度。",
        "constraints": ["0 <= 字符串长度 <= 2000"],
        "solver": _solve_lcs,
        "samples": ["abcde\nace\n"],
        "hidden": ["abc\nabc\n", "abc\ndef\n", "bsbininm\njmjkbkjkv\n", "AGGTAB\nGXTXAYB\n", "aaaa\naa\n"],
    },
    "best-time-buy-sell-stock-acm": {
        "description": "给定每日股价，最多进行一次买入和一次卖出，且买入必须在卖出之前。请输出最大利润。",
        "input_format": "第一行输入 n。第二行输入 n 个价格。",
        "output_format": "输出最大利润；若无法盈利输出 0。",
        "constraints": ["1 <= n <= 200000", "0 <= price[i] <= 10^9"],
        "solver": _solve_best_stock,
        "samples": ["6\n7 1 5 3 6 4\n"],
        "hidden": ["5\n7 6 4 3 1\n", "1\n5\n", "4\n1 2 3 4\n", "6\n2 4 1 7 5 3\n", "5\n3 3 3 3 3\n"],
    },
    "stock-with-cooldown-acm": {
        "description": "给定每日股价，可以多次交易，但卖出后第二天不能买入。任意时刻最多持有一股。请输出最大利润。",
        "input_format": "第一行输入 n。第二行输入 n 个价格。",
        "output_format": "输出最大利润。",
        "constraints": ["1 <= n <= 200000"],
        "solver": _solve_stock_cooldown,
        "samples": ["5\n1 2 3 0 2\n"],
        "hidden": ["1\n1\n", "2\n1 2\n", "5\n2 1 4 5 2\n", "6\n6 1 6 4 3 0\n", "7\n1 2 4 0 2 3 1\n"],
    },
    "perfect-squares-acm": {
        "description": "给定正整数 n，请用尽量少的完全平方数相加得到 n，并输出最少数量。",
        "input_format": "输入整数 n。",
        "output_format": "输出最少完全平方数个数。",
        "constraints": ["1 <= n <= 10000"],
        "solver": _solve_squares,
        "samples": ["12\n"],
        "hidden": ["13\n", "1\n", "43\n", "99\n", "100\n"],
    },
    "daily-temperatures-acm": {
        "description": "给定每日温度，请对每一天计算需要等待多少天才会出现更高温度；若之后都没有更高温度，记为 0。",
        "input_format": "第一行输入 n。第二行输入 n 个温度。",
        "output_format": "输出 n 个等待天数。",
        "constraints": ["1 <= n <= 200000"],
        "solver": _solve_daily_temps,
        "samples": ["8\n73 74 75 71 69 72 76 73\n"],
        "hidden": ["4\n30 40 50 60\n", "3\n30 60 90\n", "5\n90 80 70 60 50\n", "6\n70 70 71 70 72 69\n", "1\n100\n"],
    },
    "largest-rectangle-histogram-acm": {
        "description": "给定柱状图每根柱子的高度，每根柱子宽度为 1。请计算能形成的最大矩形面积。",
        "input_format": "第一行输入 n。第二行输入 n 个非负整数。",
        "output_format": "输出最大矩形面积。",
        "constraints": ["1 <= n <= 200000"],
        "solver": _solve_largest_rectangle,
        "samples": ["6\n2 1 5 6 2 3\n"],
        "hidden": ["2\n2 4\n", "5\n1 1 1 1 1\n", "5\n5 4 3 2 1\n", "5\n1 2 3 4 5\n", "7\n2 0 2 1 3 2 1\n"],
    },
    "min-stack-acm": {
        "description": "实现一个栈，支持压入、弹出、读取栈顶和读取最小值，所有操作都应按顺序模拟。",
        "input_format": "第一行输入操作数 q。随后 q 行为 PUSH x、POP、TOP 或 MIN。",
        "output_format": "对每个 TOP/MIN 输出结果；若栈为空输出 EMPTY。",
        "constraints": ["1 <= q <= 200000"],
        "solver": _solve_min_stack,
        "samples": ["7\nPUSH -2\nPUSH 0\nPUSH -3\nMIN\nPOP\nTOP\nMIN\n"],
        "hidden": ["4\nTOP\nMIN\nPUSH 1\nMIN\n", "6\nPUSH 2\nPUSH 2\nMIN\nPOP\nMIN\nTOP\n", "5\nPUSH 5\nPUSH 3\nPUSH 4\nMIN\nTOP\n", "7\nPUSH -1\nPUSH -5\nPOP\nMIN\nPOP\nTOP\nMIN\n", "3\nPUSH 10\nPOP\nTOP\n"],
    },
    "decode-string-acm": {
        "description": "给定编码字符串，形式为 k[encoded]，表示方括号内字符串重复 k 次。编码可以嵌套，请输出解码结果。",
        "input_format": "输入一行编码字符串。",
        "output_format": "输出解码后的字符串。",
        "constraints": ["1 <= 输入长度 <= 200000", "重复次数为正整数"],
        "solver": _solve_decode,
        "samples": ["3[a]2[bc]\n"],
        "hidden": ["3[a2[c]]\n", "2[abc]3[cd]ef\n", "10[a]\n", "abc3[cd]xyz\n", "2[3[a]b]\n"],
    },
    "lru-cache-acm": {
        "description": "模拟容量固定的 LRU 缓存。GET 会读取并刷新使用时间，PUT 会插入或更新；容量满时淘汰最久未使用的键。",
        "input_format": "第一行输入 capacity q。随后 q 行为 GET key 或 PUT key value。",
        "output_format": "对每个 GET 输出 value，若不存在输出 -1。",
        "constraints": ["1 <= capacity <= 100000", "1 <= q <= 200000"],
        "solver": _solve_lru,
        "samples": ["10 1\nGET missing\n"],
        "hidden": ["2 7\nPUT 1 1\nPUT 2 2\nGET 1\nPUT 3 3\nGET 2\nPUT 4 4\nGET 1\n", "1 5\nPUT a 1\nGET a\nPUT b 2\nGET a\nGET b\n", "2 6\nPUT x 1\nPUT x 2\nGET x\nPUT y 3\nPUT z 4\nGET y\n", "3 7\nPUT 1 1\nPUT 2 2\nPUT 3 3\nGET 2\nPUT 4 4\nGET 1\nGET 3\n", "2 4\nGET 1\nPUT 1 10\nPUT 2 20\nGET 1\n"],
    },
    "permutations-ii-acm": {
        "description": "给定可能包含重复数字的数组，请按字典序输出所有不重复的全排列。",
        "input_format": "第一行输入 n。第二行输入 n 个整数。",
        "output_format": "第一行输出排列数量。随后每行输出一个排列。",
        "constraints": ["1 <= n <= 8"],
        "solver": _solve_unique_permutations,
        "samples": ["3\n1 1 2\n"],
        "hidden": ["1\n1\n", "3\n1 2 3\n", "4\n1 1 2 2\n", "4\n2 2 2 2\n", "3\n-1 0 -1\n"],
    },
    "first-missing-positive-acm": {
        "description": "给定未排序整数数组，请找出其中缺失的最小正整数。",
        "input_format": "第一行输入 n。第二行输入 n 个整数。",
        "output_format": "输出缺失的最小正整数。",
        "constraints": ["1 <= n <= 200000"],
        "solver": _solve_first_missing,
        "samples": ["3\n1 2 0\n"],
        "hidden": ["4\n3 4 -1 1\n", "5\n7 8 9 11 12\n", "1\n1\n", "2\n1 1\n", "6\n2 3 4 5 6 7\n"],
    },
    "sort-colors-acm": {
        "description": "给定只包含 0、1、2 的数组，请按升序重新排列。",
        "input_format": "第一行输入 n。第二行输入 n 个整数。",
        "output_format": "输出排序后的数组。",
        "constraints": ["1 <= n <= 200000", "nums[i] in {0,1,2}"],
        "solver": _solve_sort_colors,
        "samples": ["6\n2 0 2 1 1 0\n"],
        "hidden": ["3\n2 0 1\n", "1\n0\n", "5\n1 1 1 1 1\n", "6\n2 2 1 1 0 0\n", "7\n0 2 1 2 0 1 2\n"],
    },
    "next-permutation-acm": {
        "description": "给定一个整数排列，请输出按字典序排列的下一个排列；若不存在更大的排列，输出最小排列。",
        "input_format": "第一行输入 n。第二行输入 n 个整数。",
        "output_format": "输出处理后的排列。",
        "constraints": ["1 <= n <= 200000"],
        "solver": _solve_next_permutation,
        "samples": ["3\n1 2 3\n"],
        "hidden": ["3\n3 2 1\n", "3\n1 1 5\n", "5\n1 3 2 4 5\n", "1\n1\n", "4\n2 3 1 3\n"],
    },
    "single-number-acm": {
        "description": "数组中只有一个数字出现一次，其余数字均出现两次。请输出只出现一次的数字。",
        "input_format": "第一行输入 n。第二行输入 n 个整数。",
        "output_format": "输出只出现一次的数字。",
        "constraints": ["1 <= n <= 200000", "n 为奇数"],
        "solver": _solve_single_number,
        "samples": ["3\n2 2 1\n"],
        "hidden": ["5\n4 1 2 1 2\n", "1\n7\n", "5\n-1 -1 -2 -3 -3\n", "7\n0 1 0 2 2 3 3\n", "9\n5 6 6 7 7 8 8 9 9\n"],
    },
    "majority-element-acm": {
        "description": "给定数组，存在一个元素出现次数严格超过 n/2。请输出这个多数元素。",
        "input_format": "第一行输入 n。第二行输入 n 个整数。",
        "output_format": "输出多数元素。",
        "constraints": ["1 <= n <= 200000"],
        "solver": _solve_majority,
        "samples": ["3\n3 2 3\n"],
        "hidden": ["7\n2 2 1 1 1 2 2\n", "1\n5\n", "5\n-1 -1 -1 2 3\n", "4\n4 4 4 4\n", "9\n1 2 1 3 1 4 1 5 1\n"],
    },
    "rotate-array-acm": {
        "description": "给定数组和整数 k，请将数组向右轮转 k 步。",
        "input_format": "第一行输入 n k。第二行输入 n 个整数。",
        "output_format": "输出轮转后的数组。",
        "constraints": ["1 <= n <= 200000", "0 <= k <= 10^18"],
        "solver": _solve_rotate_array,
        "samples": ["7 3\n1 2 3 4 5 6 7\n"],
        "hidden": ["4 2\n-1 -100 3 99\n", "1 10\n5\n", "5 0\n1 2 3 4 5\n", "5 5\n1 2 3 4 5\n", "6 8\n1 2 3 4 5 6\n"],
    },
    "find-duplicate-number-acm": {
        "description": "给定 n+1 个整数，每个整数都在 1 到 n 之间，且至少有一个重复。请输出任意一个重复数字。",
        "input_format": "第一行输入 n。第二行输入 n+1 个整数。",
        "output_format": "输出一个重复数字。",
        "constraints": ["1 <= n <= 200000", "1 <= nums[i] <= n"],
        "solver": _solve_duplicate,
        "samples": ["4\n1 3 4 2 2\n"],
        "hidden": ["4\n3 1 3 4 2\n", "1\n1 1\n", "5\n1 4 5 2 3 4\n", "5\n5 4 3 2 1 5\n", "6\n2 5 1 4 3 6 2\n"],
    },
    "game-of-life-acm": {
        "description": "给定生命游戏当前状态，1 表示活细胞，0 表示死细胞。请按经典规则输出下一轮状态。",
        "input_format": "第一行输入 m n。随后 m 行每行 n 个 0/1 整数。",
        "output_format": "输出下一轮 m 行状态。",
        "constraints": ["1 <= m, n <= 200"],
        "solver": _solve_life,
        "samples": ["4 3\n0 1 0\n0 0 1\n1 1 1\n0 0 0\n"],
        "hidden": ["1 1\n1\n", "2 2\n1 1\n1 1\n", "3 3\n0 0 0\n1 1 1\n0 0 0\n", "2 3\n1 0 1\n0 1 0\n", "3 3\n1 1 0\n1 0 0\n0 0 1\n"],
    },
    "set-matrix-zeroes-acm": {
        "description": "给定矩阵，如果某个元素为 0，则将它所在的整行和整列都置为 0。",
        "input_format": "第一行输入 m n。随后 m 行每行 n 个整数。",
        "output_format": "输出处理后的矩阵。",
        "constraints": ["1 <= m, n <= 500"],
        "solver": _solve_zeroes,
        "samples": ["3 3\n1 1 1\n1 0 1\n1 1 1\n"],
        "hidden": ["3 4\n0 1 2 0\n3 4 5 2\n1 3 1 5\n", "1 1\n1\n", "1 3\n1 0 3\n", "3 1\n1\n0\n3\n", "2 2\n0 0\n1 1\n"],
    },
    "spiral-matrix-acm": {
        "description": "给定 m x n 矩阵，请按顺时针螺旋顺序输出所有元素。",
        "input_format": "第一行输入 m n。随后 m 行每行 n 个整数。",
        "output_format": "输出螺旋遍历序列。",
        "constraints": ["1 <= m, n <= 500"],
        "solver": _solve_spiral,
        "samples": ["3 3\n1 2 3\n4 5 6\n7 8 9\n"],
        "hidden": ["3 4\n1 2 3 4\n5 6 7 8\n9 10 11 12\n", "1 4\n1 2 3 4\n", "4 1\n1\n2\n3\n4\n", "2 2\n1 2\n3 4\n", "2 3\n1 2 3\n4 5 6\n"],
    },
    "search-insert-position-acm": {
        "description": "给定升序数组和目标值，若目标存在输出其下标；否则输出它应插入的位置，使数组仍保持升序。",
        "input_format": "第一行输入 n target。第二行输入 n 个升序整数。",
        "output_format": "输出插入位置下标。",
        "constraints": ["1 <= n <= 200000"],
        "solver": _solve_search_insert,
        "samples": ["4 5\n1 3 5 6\n"],
        "hidden": ["4 2\n1 3 5 6\n", "4 7\n1 3 5 6\n", "4 0\n1 3 5 6\n", "1 1\n1\n", "5 3\n1 3 3 3 5\n"],
    },
    "merge-sorted-array-acm": {
        "description": "给定两个升序数组，请合并为一个升序数组。",
        "input_format": "第一行输入 n m。第二行输入 n 个升序整数。第三行输入 m 个升序整数。",
        "output_format": "输出合并后的升序数组。",
        "constraints": ["0 <= n, m <= 200000", "n + m >= 1"],
        "solver": _solve_merge_sorted_arrays,
        "samples": ["3 3\n1 2 3\n2 5 6\n"],
        "hidden": ["1 0\n1\n\n", "0 1\n\n1\n", "3 3\n1 1 1\n1 1 1\n", "3 2\n-3 -1 4\n-2 5\n", "4 3\n1 3 5 7\n2 4 6\n"],
    },
    "three-sum-closest-acm": {
        "description": "给定数组和目标值，请从数组中选三个不同位置的数，使三数之和最接近目标值。若距离相同，输出较小的和。",
        "input_format": "第一行输入 n target。第二行输入 n 个整数。",
        "output_format": "输出最接近的三数之和。",
        "constraints": ["3 <= n <= 200000"],
        "solver": _solve_three_closest,
        "samples": ["4 1\n-1 2 1 -4\n"],
        "hidden": ["3 1\n0 0 0\n", "4 100\n1 1 1 0\n", "5 3\n1 1 1 1 1\n", "6 2\n-3 -2 -5 3 -4 10\n", "5 0\n-1 0 1 1 55\n"],
    },
    "four-sum-acm": {
        "description": "给定数组和目标值，请输出所有不重复的四元组，使四数之和等于目标值。四元组内升序，整体按字典序输出。",
        "input_format": "第一行输入 n target。第二行输入 n 个整数。",
        "output_format": "第一行输出四元组数量。随后每行输出一个四元组。",
        "constraints": ["4 <= n <= 200"],
        "solver": _solve_four_sum,
        "samples": ["6 0\n1 0 -1 0 -2 2\n"],
        "hidden": ["5 8\n2 2 2 2 2\n", "4 10\n1 2 3 4\n", "7 0\n0 0 0 0 0 0 0\n", "6 2\n-3 -1 0 2 4 5\n", "8 4\n1 1 1 2 2 2 3 3\n"],
    },
    "happy-number-acm": {
        "description": "不断把一个正整数替换为各位数字平方和。若最终变成 1，则它是快乐数。请判断给定数字是否为快乐数。",
        "input_format": "输入一个正整数 n。",
        "output_format": "是快乐数输出 true，否则输出 false。",
        "constraints": ["1 <= n <= 2^31 - 1"],
        "solver": _solve_happy,
        "samples": ["19\n"],
        "hidden": ["2\n", "1\n", "7\n", "1111111\n", "2147483647\n"],
    },
    "roman-to-integer-acm": {
        "description": "给定一个合法罗马数字，请把它转换为整数。",
        "input_format": "输入一行罗马数字字符串。",
        "output_format": "输出对应整数。",
        "constraints": ["1 <= s.length <= 15", "1 <= value <= 3999"],
        "solver": _solve_roman,
        "samples": ["MCMXCIV\n"],
        "hidden": ["III\n", "LVIII\n", "IX\n", "XL\n", "MMMDCCCLXXXVIII\n"],
    },
}


def build_practice_problem(index, spec, problem_builder, tc_builder):
    title, slug, difficulty, tags = spec
    definition = PRACTICE_PROBLEM_BANK[slug]
    solver = definition["solver"]
    samples = [
        {
            "input": _ensure_newline(sample_input),
            "output": solver(_ensure_newline(sample_input)),
        }
        for sample_input in definition["samples"]
    ]
    hidden = [
        tc_builder(_ensure_newline(case_input), solver(_ensure_newline(case_input)))
        for case_input in definition["hidden"]
    ]
    return problem_builder(
        index,
        title,
        slug,
        difficulty,
        tags,
        definition["description"],
        definition["input_format"],
        definition["output_format"],
        samples,
        definition["constraints"],
        hidden,
    )
