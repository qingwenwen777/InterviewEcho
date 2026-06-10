from collections import Counter, defaultdict, deque
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


def _parse_nums(text):
    values = _ints(text)
    n = values[0]
    return values[1 : 1 + n]


def _parse_matrix(text):
    values = _ints(text)
    m, n = values[0], values[1]
    nums = values[2 : 2 + m * n]
    return m, n, [nums[i * n : (i + 1) * n] for i in range(m)]


def _parse_intervals(text):
    values = _ints(text)
    n = values[0]
    return [tuple(values[1 + i * 2 : 3 + i * 2]) for i in range(n)]


def _family_info():
    return {
        "array_aggregate": (
            "数组聚合",
            "第一行输入整数 n，第二行输入 n 个整数。",
            "输出一个整数。",
            ["1 <= n <= 200000", "-10^9 <= nums[i] <= 10^9"],
        ),
        "array_count": (
            "数组计数",
            "第一行输入整数 n，第二行输入 n 个整数；目标计数题第一行输入 n target。",
            "输出一个整数。",
            ["1 <= n <= 200000", "-10^9 <= nums[i], target <= 10^9"],
        ),
        "array_extreme": (
            "数组极值",
            "第一行输入整数 n，第二行输入 n 个整数。",
            "输出对应结果；若第二大不同元素不存在，输出 NONE。",
            ["1 <= n <= 200000", "-10^9 <= nums[i] <= 10^9"],
        ),
        "array_order": (
            "数组重排",
            "按题意输入数组，轮转题第一行输入 n k。",
            "输出处理后的数组，数字之间用一个空格分隔。",
            ["1 <= n <= 200000", "0 <= k <= 10^18"],
        ),
        "prefix_queries": (
            "前缀查询",
            "查询题第一行输入 n q，第二行输入数组，随后 q 行输入 l r；平衡下标题输入 n 与数组。",
            "每个查询输出一行；平衡下标题输出一个下标或 -1。",
            ["1 <= n, q <= 200000", "下标从 0 开始且区间闭合"],
        ),
        "intervals": (
            "区间处理",
            "第一行输入区间数量 n，随后 n 行输入 l r；点覆盖题第一行输入 n q 后再输入 q 个查询点。",
            "输出题目要求的整数结果。",
            ["0 <= n <= 200000", "-10^9 <= l <= r <= 10^9"],
        ),
        "strings_count": (
            "字符串统计",
            "输入一行字符串。",
            "输出一个整数。",
            ["0 <= |s| <= 200000", "字符串由可见 ASCII 字符组成"],
        ),
        "strings_transform": (
            "字符串变换",
            "按题意输入字符串或字符串列表。",
            "输出变换后的字符串或字符串列表结果。",
            ["0 <= 字符串总长度 <= 200000"],
        ),
        "strings_match": (
            "字符串匹配",
            "按题意输入两个字符串或字符串列表。",
            "输出 true/false、计数或匹配结果。",
            ["0 <= 字符串总长度 <= 200000"],
        ),
        "stack_queue": (
            "栈与队列",
            "按题意输入序列、表达式或窗口参数。",
            "输出模拟或单调结构处理后的结果。",
            ["1 <= n <= 200000"],
        ),
        "matrix_basic": (
            "矩阵基础",
            "第一行输入矩阵规模，随后输入矩阵；搜索题最后一行输入 target。",
            "输出矩阵、布尔值或一个整数。",
            ["1 <= m, n <= 500"],
        ),
        "grid": (
            "网格搜索",
            "第一行输入 m n，随后输入 m 行网格。",
            "输出计数、面积或最短步数。",
            ["1 <= m, n <= 1000"],
        ),
        "graph_basic": (
            "图基础",
            "第一行输入点数、边数及必要参数，随后输入边。",
            "输出距离序列、布尔值或计数。",
            ["1 <= n <= 200000", "点编号从 0 开始"],
        ),
        "graph_weighted": (
            "带权图",
            "第一行输入点数、边数及必要参数，随后输入带权边。",
            "输出最短路、生成树或路径容量结果。",
            ["1 <= n <= 5000", "边权为正整数"],
        ),
        "tree": (
            "树",
            "按题意输入父节点数组或树边。",
            "输出树的深度、子树大小、直径、LCA 或叶子数量。",
            ["1 <= n <= 200000", "点编号从 0 开始"],
        ),
        "number_theory": (
            "数论",
            "按题意输入整数、数组或模数。",
            "输出对应数论计算结果。",
            ["1 <= n <= 10^6", "中间结果使用 64 位整数范围内的数据"],
        ),
        "dp_classic": (
            "动态规划",
            "按题意输入数组、背包容量或硬币集合。",
            "输出最优值或方案数量。",
            ["1 <= n <= 200000"],
        ),
        "dp_string": (
            "字符串动态规划",
            "按题意输入字符串和词典。",
            "输出长度、距离或 true/false。",
            ["0 <= 字符串长度 <= 2000"],
        ),
        "greedy": (
            "贪心",
            "按题意输入区间、数组或评分。",
            "输出贪心得到的最优结果。",
            ["1 <= n <= 200000"],
        ),
        "simulation": (
            "模拟",
            "按题意输入参数、指令或日期。",
            "输出模拟后的结果。",
            ["输入保证在题目约束范围内"],
        ),
    }


EXTRA_VARIANTS = {
    "array_aggregate": [
        ("sum", "数组元素总和", "array-total-sum-acm", "简单", ["数组"], "计算数组所有元素之和。"),
        ("even_sum", "数组偶数和", "array-even-sum-acm", "简单", ["数组"], "计算数组中所有偶数元素之和。"),
        ("odd_sum", "数组奇数和", "array-odd-sum-acm", "简单", ["数组"], "计算数组中所有奇数元素之和。"),
        ("positive_sum", "数组正数和", "array-positive-sum-acm", "简单", ["数组"], "计算数组中所有正数元素之和。"),
        ("absolute_sum", "数组绝对值和", "array-absolute-sum-acm", "简单", ["数组"], "计算数组所有元素绝对值之和。"),
    ],
    "array_count": [
        ("positive_count", "正数个数", "count-positive-numbers-acm", "简单", ["数组"], "统计数组中正数的个数。"),
        ("negative_count", "负数个数", "count-negative-numbers-acm", "简单", ["数组"], "统计数组中负数的个数。"),
        ("zero_count", "零的个数", "count-zeroes-acm", "简单", ["数组"], "统计数组中 0 的个数。"),
        ("distinct_count", "不同数字个数", "count-distinct-numbers-acm", "简单", ["数组", "哈希表"], "统计数组中不同整数的个数。"),
        ("target_count", "目标值出现次数", "count-target-occurrences-acm", "简单", ["数组", "哈希表"], "统计目标值在数组中出现的次数。"),
    ],
    "array_extreme": [
        ("maximum", "数组最大值", "array-maximum-acm", "简单", ["数组"], "输出数组最大值。"),
        ("minimum", "数组最小值", "array-minimum-acm", "简单", ["数组"], "输出数组最小值。"),
        ("range", "数组极差", "array-value-range-acm", "简单", ["数组"], "输出最大值与最小值的差。"),
        ("second_largest", "第二大不同元素", "second-distinct-largest-acm", "简单", ["数组", "排序"], "输出第二大的不同元素。"),
        ("max_abs", "最大绝对值", "maximum-absolute-value-acm", "简单", ["数组"], "输出数组元素绝对值的最大值。"),
    ],
    "array_order": [
        ("stable_unique", "稳定去重", "stable-unique-array-acm", "简单", ["数组", "哈希表"], "保留每个数字首次出现的位置并输出去重后的序列。"),
        ("parity_partition", "奇偶稳定分区", "stable-parity-partition-acm", "简单", ["数组"], "先输出所有偶数，再输出所有奇数，分别保持原相对顺序。"),
        ("rotate_right", "数组右轮转", "rotate-array-right-acm", "简单", ["数组"], "将数组向右轮转 k 步。"),
        ("plus_one", "数字数组加一", "digits-plus-one-acm", "简单", ["数组", "模拟"], "将十进制数字数组表示的非负整数加一。"),
        ("next_permutation", "下一个字典序排列", "next-lexicographic-permutation-acm", "中等", ["数组", "双指针"], "输出当前排列的下一个字典序排列。"),
    ],
    "prefix_queries": [
        ("range_sum", "区间和查询", "range-sum-query-acm", "简单", ["前缀和"], "回答多个闭区间求和查询。"),
        ("range_xor", "区间异或查询", "range-xor-query-acm", "简单", ["前缀和", "位运算"], "回答多个闭区间异或查询。"),
        ("range_min", "区间最小值查询", "range-min-query-acm", "中等", ["数组"], "回答多个闭区间最小值查询。"),
        ("range_max", "区间最大值查询", "range-max-query-acm", "中等", ["数组"], "回答多个闭区间最大值查询。"),
        ("balanced_pivot", "左右和相等下标", "balanced-pivot-index-acm", "简单", ["前缀和"], "找出最小下标，使其左侧元素和等于右侧元素和。"),
    ],
    "intervals": [
        ("union_length", "区间并集长度", "interval-union-length-acm", "中等", ["排序", "区间"], "给定若干半开区间 [l,r)，输出并集总长度。"),
        ("max_overlap", "最多重叠区间数", "maximum-overlapping-intervals-acm", "中等", ["扫描线"], "给定半开区间，输出同一时刻最多有多少区间重叠。"),
        ("erase_overlap", "删除重叠区间", "erase-overlapping-intervals-acm", "中等", ["贪心", "区间"], "删除尽量少的区间，使剩余区间互不重叠。"),
        ("point_coverage", "点被区间覆盖次数", "point-interval-coverage-acm", "中等", ["排序", "二分"], "对每个查询点，输出覆盖它的闭区间数量。"),
        ("meeting_rooms", "会议室数量", "minimum-meeting-rooms-acm", "中等", ["扫描线", "堆"], "给定半开会议时间，输出同时安排所有会议所需的最少会议室数量。"),
    ],
    "strings_count": [
        ("vowels", "元音字母数量", "count-vowels-acm", "简单", ["字符串"], "统计字符串中的英文元音字母数量。"),
        ("digits", "数字字符数量", "count-digit-characters-acm", "简单", ["字符串"], "统计字符串中的数字字符数量。"),
        ("uppercase", "大写字母数量", "count-uppercase-letters-acm", "简单", ["字符串"], "统计字符串中的大写英文字母数量。"),
        ("first_unique_index", "首个唯一字符下标", "first-unique-character-index-acm", "简单", ["字符串", "哈希表"], "输出第一个只出现一次的字符下标，不存在输出 -1。"),
        ("longest_run", "最长连续相同字符", "longest-equal-character-run-acm", "简单", ["字符串"], "输出最长连续相同字符片段的长度。"),
    ],
    "strings_transform": [
        ("reverse_words", "翻转单词顺序", "reverse-words-order-acm", "简单", ["字符串"], "按单词翻转输入句子的顺序。"),
        ("rle_encode", "游程编码", "run-length-encode-acm", "简单", ["字符串"], "对连续相同字符做游程编码。"),
        ("rle_decode", "游程解码", "run-length-decode-acm", "简单", ["字符串"], "根据字符与重复次数还原原字符串。"),
        ("remove_adjacent_duplicates", "删除相邻重复字符", "remove-adjacent-duplicates-acm", "简单", ["栈", "字符串"], "反复删除相邻相同字符，输出最终字符串。"),
        ("common_prefix", "最长公共前缀", "longest-common-prefix-acm", "简单", ["字符串"], "输出多个单词的最长公共前缀。"),
    ],
    "strings_match": [
        ("is_subsequence", "判断子序列", "is-subsequence-acm", "简单", ["双指针", "字符串"], "判断第一个字符串是否是第二个字符串的子序列。"),
        ("rotation", "判断旋转字符串", "string-rotation-check-acm", "简单", ["字符串"], "判断两个字符串是否能通过旋转得到彼此。"),
        ("anagram", "字母重排判断", "anagram-check-extra-acm", "简单", ["哈希表", "字符串"], "判断两个字符串是否由完全相同的字符重排得到。"),
        ("pattern_count", "模式串出现次数", "overlapping-pattern-count-acm", "中等", ["字符串"], "统计模式串在文本中出现的次数，允许重叠。"),
        ("longest_common_suffix", "最长公共后缀", "longest-common-suffix-acm", "简单", ["字符串"], "输出多个单词的最长公共后缀。"),
    ],
    "stack_queue": [
        ("valid_brackets", "括号序列合法性", "valid-bracket-sequence-acm", "简单", ["栈"], "判断括号序列是否完全匹配。"),
        ("postfix_eval", "后缀表达式求值", "postfix-expression-evaluation-acm", "中等", ["栈"], "计算只包含整数和四则运算符的后缀表达式。"),
        ("next_greater", "右侧下一个更大元素", "next-greater-values-acm", "中等", ["单调栈"], "对每个位置输出右侧第一个更大的元素，不存在输出 -1。"),
        ("sliding_min", "滑动窗口最小值", "sliding-window-minimum-acm", "中等", ["单调队列"], "输出每个长度为 k 的窗口最小值。"),
        ("remove_k_digits", "删除 K 位最小数", "remove-k-digits-extra-acm", "中等", ["栈", "贪心"], "从非负整数字符串中删除 k 位，使剩余数字最小。"),
    ],
    "matrix_basic": [
        ("transpose", "矩阵转置", "matrix-transpose-acm", "简单", ["矩阵"], "输出矩阵的转置。"),
        ("rotate_clockwise", "矩阵顺时针旋转", "rotate-square-matrix-acm", "中等", ["矩阵"], "将 n x n 矩阵顺时针旋转 90 度。"),
        ("diagonal_sum", "矩阵对角线和", "matrix-diagonal-sum-acm", "简单", ["矩阵"], "输出主对角线和副对角线元素总和，中心元素只计算一次。"),
        ("border_sum", "矩阵边界和", "matrix-border-sum-acm", "简单", ["矩阵"], "输出矩阵边界元素总和。"),
        ("search_matrix", "行列有序矩阵搜索", "row-column-sorted-matrix-search-acm", "中等", ["矩阵", "二分"], "判断目标值是否存在于行列都升序的矩阵中。"),
    ],
    "grid": [
        ("island_count", "岛屿数量扩展", "island-count-extra-acm", "中等", ["DFS", "矩阵"], "统计 01 网格中四连通岛屿数量。"),
        ("max_island_area", "最大岛屿面积", "maximum-island-area-acm", "中等", ["DFS", "矩阵"], "输出最大四连通岛屿面积。"),
        ("shortest_path", "网格最短路", "grid-shortest-path-acm", "中等", ["BFS", "矩阵"], "在 0 可走、1 障碍的网格中，求左上到右下最短步数。"),
        ("flood_fill_size", "同色连通块大小", "flood-fill-component-size-acm", "简单", ["DFS", "矩阵"], "输出指定格子所在同字符连通块大小。"),
        ("unique_paths_obstacles", "障碍网格路径数", "unique-paths-with-obstacles-acm", "中等", ["动态规划", "矩阵"], "只允许向右或向下移动，统计避开障碍到达右下角的路径数。"),
    ],
    "graph_basic": [
        ("bfs_distances", "无权图最短距离", "unweighted-graph-distances-acm", "中等", ["图", "BFS"], "输出源点到所有点的无权最短距离。"),
        ("connected_components", "无向图连通分量", "graph-connected-components-extra-acm", "简单", ["图", "DFS"], "统计无向图连通分量数量。"),
        ("bipartite", "二分图判断", "bipartite-graph-check-acm", "中等", ["图", "BFS"], "判断无向图是否为二分图。"),
        ("cycle_directed", "有向图是否有环", "directed-cycle-check-acm", "中等", ["图", "拓扑排序"], "判断有向图是否存在环。"),
        ("topo_semesters", "课程最少学期数", "minimum-course-semesters-acm", "中等", ["图", "拓扑排序"], "每学期可学习所有先修已满足的课程，输出完成所有课程的最少学期数，若有环输出 -1。"),
    ],
    "graph_weighted": [
        ("dijkstra_shortest", "带权最短路", "weighted-shortest-path-acm", "中等", ["图", "最短路"], "输出有向带权图中 s 到 t 的最短距离。"),
        ("mst_weight", "最小生成树权重", "minimum-spanning-tree-weight-acm", "中等", ["图", "并查集"], "输出无向带权图最小生成树总权重，若不连通输出 IMPOSSIBLE。"),
        ("limited_reachable", "距离限制可达点数", "reachable-nodes-within-limit-acm", "中等", ["图", "最短路"], "统计无向带权图中从源点出发距离不超过 limit 的点数。"),
        ("all_pairs_center", "图中心节点", "graph-center-node-acm", "困难", ["图", "最短路"], "输出到其他所有节点最短距离和最小的节点，平局取编号最小。"),
        ("widest_path", "最大瓶颈路径", "widest-path-capacity-acm", "中等", ["图", "堆"], "路径容量定义为路径上最小边容量，输出 s 到 t 的最大路径容量。"),
    ],
    "tree": [
        ("max_depth_parent", "父数组树最大深度", "tree-max-depth-parent-array-acm", "简单", ["树"], "根据父节点数组输出树的最大深度。"),
        ("subtree_sizes", "父数组子树大小", "tree-subtree-sizes-acm", "中等", ["树"], "根据父节点数组输出每个节点的子树大小。"),
        ("tree_diameter", "树的直径扩展", "tree-diameter-extra-acm", "中等", ["树", "BFS"], "输出无权树任意两点间最长路径的边数。"),
        ("lca_parent", "父数组最近公共祖先", "lca-parent-array-acm", "中等", ["树"], "回答多组最近公共祖先查询。"),
        ("leaf_count", "树叶子节点数量", "tree-leaf-count-acm", "简单", ["树"], "根据父节点数组统计叶子节点数量。"),
    ],
    "number_theory": [
        ("gcd_array", "数组最大公约数", "array-gcd-acm", "简单", ["数学"], "输出数组所有元素的最大公约数。"),
        ("lcm_array", "数组最小公倍数", "array-lcm-acm", "简单", ["数学"], "输出数组所有元素的最小公倍数。"),
        ("count_primes", "素数计数", "count-primes-up-to-n-acm", "中等", ["数学", "筛法"], "统计不超过 n 的素数数量。"),
        ("mod_pow", "快速幂取模", "modular-exponentiation-acm", "中等", ["数学", "快速幂"], "输出 a^b mod m。"),
        ("fib_mod", "斐波那契取模", "fibonacci-modulo-acm", "简单", ["动态规划", "数学"], "输出第 n 个斐波那契数对 mod 取模的结果，F0=0，F1=1。"),
    ],
    "dp_classic": [
        ("coin_change_min", "零钱兑换最少硬币", "coin-change-minimum-acm", "中等", ["动态规划"], "输出凑成目标金额所需的最少硬币数，不可达输出 -1。"),
        ("coin_change_count", "零钱兑换方案数", "coin-change-combinations-acm", "中等", ["动态规划"], "输出凑成目标金额的组合方案数，硬币顺序不区分。"),
        ("knapsack01", "01 背包最大价值", "zero-one-knapsack-acm", "中等", ["动态规划"], "每件物品最多选择一次，输出容量内可获得的最大价值。"),
        ("lis_length", "最长递增子序列扩展", "lis-length-extra-acm", "中等", ["动态规划", "二分"], "输出严格递增子序列的最大长度。"),
        ("max_subarray", "最大子数组和扩展", "max-subarray-sum-extra-acm", "简单", ["动态规划"], "输出非空连续子数组的最大和。"),
    ],
    "dp_string": [
        ("lcs_length", "最长公共子序列扩展", "lcs-length-extra-acm", "中等", ["动态规划", "字符串"], "输出两个字符串的最长公共子序列长度。"),
        ("longest_common_substring", "最长公共子串", "longest-common-substring-acm", "中等", ["动态规划", "字符串"], "输出两个字符串的最长公共连续子串长度。"),
        ("edit_distance", "编辑距离扩展", "edit-distance-extra-acm", "中等", ["动态规划", "字符串"], "输出将第一个字符串变为第二个字符串的最少编辑次数。"),
        ("min_delete_palindrome", "变成回文的最少删除", "minimum-deletions-palindrome-acm", "中等", ["动态规划", "字符串"], "输出把字符串变成回文所需删除的最少字符数。"),
        ("word_break", "单词拆分扩展", "word-break-extra-acm", "中等", ["动态规划", "字符串"], "判断字符串能否由词典单词拼接而成。"),
    ],
    "greedy": [
        ("activity_selection", "最多不重叠活动", "activity-selection-maximum-acm", "中等", ["贪心", "区间"], "给定活动时间，输出最多能参加的互不重叠活动数量。"),
        ("gas_station", "加油站起点", "gas-station-start-acm", "中等", ["贪心"], "输出绕环一周的最小可行起点，不存在输出 -1。"),
        ("assign_cookies", "分发饼干", "assign-cookies-acm", "简单", ["贪心", "排序"], "每个孩子最多得到一块饼干，输出最多满足的孩子数量。"),
        ("jump_game_min_steps", "跳跃游戏最少步数", "jump-game-min-steps-acm", "中等", ["贪心"], "输出到达最后一个位置的最少跳跃次数，不可达输出 -1。"),
        ("candy_count", "分发糖果", "candy-distribution-acm", "困难", ["贪心"], "相邻评分更高的孩子必须得到更多糖果，输出最少糖果数。"),
    ],
    "simulation": [
        ("josephus", "约瑟夫环", "josephus-survivor-acm", "中等", ["模拟"], "n 个人从 1 开始编号，每次数到 k 的人出局，输出最后幸存者编号。"),
        ("robot_return", "机器人是否回原点", "robot-return-origin-acm", "简单", ["模拟", "字符串"], "根据 UDLR 指令判断机器人最终是否回到原点。"),
        ("base_convert", "十进制转进制", "decimal-base-conversion-acm", "简单", ["数学", "模拟"], "将非负十进制整数转换为 2 到 16 进制。"),
        ("binary_add", "二进制字符串相加", "add-binary-strings-acm", "简单", ["字符串", "模拟"], "输出两个二进制字符串的和。"),
        ("day_of_year", "一年中的第几天", "day-of-year-acm", "简单", ["模拟"], "给定日期，输出它是一年中的第几天。"),
    ],
}


def _cases_for(family, variant):
    generic_arrays = [
        "5\n1 2 3 4 5\n",
        "6\n-3 0 7 -2 8 0\n",
        "1\n-9\n",
        "4\n10 10 10 10\n",
        "7\n5 -5 6 -6 0 1 -1\n",
        "8\n2 4 6 8 1 3 5 7\n",
    ]
    if family == "array_aggregate":
        return generic_arrays
    if family == "array_count":
        if variant == "target_count":
            return [
                "6 2\n1 2 2 3 2 4\n",
                "5 7\n7 7 1 2 7\n",
                "3 0\n1 2 3\n",
                "4 -1\n-1 -1 -2 -3\n",
                "1 5\n5\n",
                "8 3\n3 1 3 2 3 4 3 5\n",
            ]
        return generic_arrays
    if family == "array_extreme":
        return generic_arrays
    if family == "array_order":
        data = {
            "stable_unique": ["7\n1 2 1 3 2 4 1\n", "4\n5 5 5 5\n", "5\n-1 0 -1 2 0\n", "1\n9\n", "6\n1 2 3 4 5 6\n", "8\n3 1 3 2 1 4 2 5\n"],
            "parity_partition": ["6\n3 2 4 1 6 5\n", "4\n1 3 5 7\n", "4\n2 4 6 8\n", "5\n0 -1 -2 3 4\n", "1\n9\n", "7\n8 7 6 5 4 3 2\n"],
            "rotate_right": ["7 3\n1 2 3 4 5 6 7\n", "4 2\n-1 -100 3 99\n", "1 99\n5\n", "5 0\n1 2 3 4 5\n", "5 5\n1 2 3 4 5\n", "6 8\n1 2 3 4 5 6\n"],
            "plus_one": ["3\n1 2 3\n", "1\n9\n", "4\n9 9 9 9\n", "2\n0 0\n", "5\n1 0 0 0 0\n", "6\n8 9 9 9 9 9\n"],
            "next_permutation": ["3\n1 2 3\n", "3\n3 2 1\n", "3\n1 1 5\n", "5\n1 3 2 4 5\n", "1\n1\n", "4\n2 3 1 3\n"],
        }
        return data[variant]
    if family == "prefix_queries":
        if variant == "balanced_pivot":
            return ["6\n1 7 3 6 5 6\n", "3\n1 2 3\n", "1\n0\n", "5\n2 1 -1 2 0\n", "4\n0 0 0 0\n", "7\n-1 -1 0 1 1 0 0\n"]
        return [
            "5 3\n1 2 3 4 5\n0 2\n1 3\n2 4\n",
            "4 2\n-1 0 7 3\n0 3\n2 2\n",
            "1 1\n9\n0 0\n",
            "6 4\n5 5 5 5 5 5\n0 5\n1 4\n3 3\n2 5\n",
            "5 2\n8 -2 4 -6 10\n0 1\n1 4\n",
            "7 3\n1 3 5 7 9 11 13\n0 6\n2 5\n4 4\n",
        ]
    if family == "intervals":
        if variant == "point_coverage":
            return [
                "3 4\n1 3\n2 5\n7 8\n1 2 6 8\n",
                "2 3\n0 0\n1 2\n0 1 3\n",
                "0 2\n\n5 -1\n",
                "4 4\n-3 1\n-1 4\n4 4\n10 20\n-2 4 5 15\n",
                "3 3\n1 10\n2 3\n4 5\n3 6 11\n",
                "5 5\n0 2\n2 4\n4 6\n6 8\n8 10\n0 2 4 8 10\n",
            ]
        return [
            "4\n1 3\n2 5\n7 10\n9 12\n",
            "3\n1 2\n2 3\n3 4\n",
            "3\n1 2\n1 2\n1 2\n",
            "0\n",
            "5\n-5 -1\n-2 0\n0 1\n1 3\n2 4\n",
            "4\n1 100\n11 22\n1 11\n2 12\n",
        ]
    if family == "strings_count":
        return ["InterviewEcho2026\n", "AaEeIiOoUu\n", "12345abcDEF\n", "swiss\n", "aaaaabbbbcc\n", "No digits here!\n"]
    if family == "strings_transform":
        data = {
            "reverse_words": ["hello world from echo\n", "  keep   spaces  tidy \n", "single\n", "a b c d\n", "\n", "面试 回声 系统\n"],
            "rle_encode": ["aaabbc\n", "abcd\n", "zzzzzz\n", "aabbaa\n", "AABB111\n", "x\n"],
            "rle_decode": ["3\na 3\nb 2\nc 1\n", "1\nz 5\n", "2\nA 2\nB 3\n", "3\n1 1\n2 2\n3 3\n", "0\n", "4\nx 1\ny 1\nz 1\nx 2\n"],
            "remove_adjacent_duplicates": ["abbaca\n", "azxxzy\n", "aaaa\n", "abc\n", "aabccbadd\n", "mississippi\n"],
            "common_prefix": ["3\nflower flow flight\n", "3\ndog racecar car\n", "1\nalone\n", "4\ninterview interval internal internet\n", "2\nsame same\n", "3\nprefix prelude prevent\n"],
        }
        return data[variant]
    if family == "strings_match":
        data = {
            "is_subsequence": ["abc\nahbgdc\n", "axc\nahbgdc\n", "\nabc\n", "ace\nabcde\n", "aaaa\naa\n", "echo\ninterviewecho\n"],
            "rotation": ["abcde\ncdeab\n", "abcde\nabced\n", "a\na\n", "aaab\nabaa\n", "waterbottle\nerbottlewat\n", "abc\nabcabc\n"],
            "anagram": ["listen\nsilent\n", "rat\ncar\n", "aabb\nbaba\n", "abc\nabcc\n", "\n\n", "Dormitory\ndirtyroom\n"],
            "pattern_count": ["aaaa\naa\n", "abababa\naba\n", "abc\nx\n", "mississippi\nissi\n", "aaaaa\na\n", "edgecase\ncase\n"],
            "longest_common_suffix": ["3\nrunning jumping singing\n", "3\nabc xyz pqr\n", "1\nalone\n", "4\ntransaction action fraction satisfaction\n", "2\nsame same\n", "3\ncoder reader builder\n"],
        }
        return data[variant]
    if family == "stack_queue":
        data = {
            "valid_brackets": ["()[]{}\n", "(]\n", "([{}])\n", "((())\n", "\n", "{[()()]}\n"],
            "postfix_eval": ["2 1 + 3 *\n", "4 13 5 / +\n", "10 6 9 3 + -11 * / * 17 + 5 +\n", "5\n", "7 3 - 2 *\n", "-4 2 /\n"],
            "next_greater": ["4\n2 1 2 4\n", "5\n5 4 3 2 1\n", "5\n1 2 3 4 5\n", "1\n9\n", "6\n2 7 3 5 4 6\n", "5\n1 1 1 1 1\n"],
            "sliding_min": ["8 3\n1 3 -1 -3 5 3 6 7\n", "1 1\n9\n", "5 2\n5 4 3 2 1\n", "5 5\n1 2 3 4 5\n", "6 3\n4 4 4 4 4 4\n", "7 4\n2 1 3 4 6 3 8\n"],
            "remove_k_digits": ["1432219\n3\n", "10200\n1\n", "10\n2\n", "123456\n3\n", "100200\n1\n", "765028321\n5\n"],
        }
        return data[variant]
    if family == "matrix_basic":
        data = {
            "transpose": ["2 3\n1 2 3\n4 5 6\n", "1 4\n1 2 3 4\n", "3 1\n1\n2\n3\n", "2 2\n1 2\n3 4\n", "3 3\n1 2 3\n4 5 6\n7 8 9\n", "1 1\n9\n"],
            "rotate_clockwise": ["3\n1 2 3\n4 5 6\n7 8 9\n", "1\n5\n", "2\n1 2\n3 4\n", "4\n1 2 3 4\n5 6 7 8\n9 10 11 12\n13 14 15 16\n", "3\n9 8 7\n6 5 4\n3 2 1\n", "2\n-1 0\n2 3\n"],
            "diagonal_sum": ["3\n1 2 3\n4 5 6\n7 8 9\n", "1\n5\n", "2\n1 2\n3 4\n", "4\n1 1 1 1\n1 1 1 1\n1 1 1 1\n1 1 1 1\n", "3\n-1 0 1\n2 3 4\n5 6 7\n", "5\n1 2 3 4 5\n6 7 8 9 10\n11 12 13 14 15\n16 17 18 19 20\n21 22 23 24 25\n"],
            "border_sum": ["3 3\n1 2 3\n4 5 6\n7 8 9\n", "1 4\n1 2 3 4\n", "4 1\n1\n2\n3\n4\n", "2 2\n1 2\n3 4\n", "3 4\n1 2 3 4\n5 6 7 8\n9 10 11 12\n", "1 1\n9\n"],
            "search_matrix": ["3 3\n1 4 7\n2 5 8\n3 6 9\n5\n", "3 3\n1 4 7\n2 5 8\n3 6 9\n10\n", "1 1\n1\n1\n", "2 3\n1 3 5\n2 4 6\n4\n", "2 2\n-5 -1\n0 3\n-5\n", "3 4\n1 2 8 9\n2 4 9 12\n4 7 10 13\n6\n"],
        }
        return data[variant]
    if family == "grid":
        data = {
            "island_count": ["4 5\n11110\n11010\n11000\n00000\n", "4 5\n11000\n11000\n00100\n00011\n", "1 1\n0\n", "1 1\n1\n", "3 3\n101\n010\n101\n", "3 4\n1111\n0000\n1111\n"],
            "max_island_area": ["4 5\n11000\n11000\n00100\n00011\n", "1 1\n0\n", "1 1\n1\n", "3 3\n101\n010\n101\n", "3 4\n1111\n0000\n1111\n", "4 4\n1001\n1100\n0011\n0011\n"],
            "shortest_path": ["3 3\n000\n010\n000\n", "2 2\n01\n10\n", "1 1\n0\n", "3 4\n0000\n1110\n0000\n", "3 3\n010\n010\n000\n", "2 3\n000\n001\n"],
            "flood_fill_size": ["3 4\nAABC\nAABC\nDDDC\n0 0\n", "1 1\nZ\n0 0\n", "2 3\nABC\nDEF\n1 1\n", "3 3\nXXX\nXOX\nXXX\n1 1\n", "3 3\nXXX\nXOX\nXXX\n0 0\n", "4 4\nAABB\nAABB\nBBAA\nBBAA\n2 2\n"],
            "unique_paths_obstacles": ["3 3\n000\n010\n000\n", "1 1\n0\n", "1 1\n1\n", "2 2\n00\n00\n", "3 4\n0000\n0010\n0000\n", "3 3\n010\n000\n010\n"],
        }
        return data[variant]
    if family == "graph_basic":
        data = {
            "bfs_distances": ["5 4 0\n0 1\n1 2\n0 3\n3 4\n", "3 0 1\n", "4 2 0\n0 1\n2 3\n", "6 6 2\n0 1\n1 2\n2 3\n3 4\n4 5\n0 5\n", "1 0 0\n", "5 5 4\n0 1\n1 2\n2 3\n3 4\n0 4\n"],
            "connected_components": ["5 3\n0 1\n1 2\n3 4\n", "5 0\n", "4 3\n0 1\n1 2\n2 3\n", "6 3\n0 1\n2 3\n4 5\n", "1 0\n", "7 4\n0 1\n2 3\n3 4\n5 6\n"],
            "bipartite": ["4 4\n0 1\n0 3\n2 1\n2 3\n", "3 3\n0 1\n1 2\n2 0\n", "1 0\n", "4 2\n0 1\n2 3\n", "5 4\n0 1\n1 2\n2 3\n3 4\n", "4 4\n0 1\n1 2\n2 3\n3 0\n"],
            "cycle_directed": ["3 3\n0 1\n1 2\n2 0\n", "3 2\n0 1\n1 2\n", "1 0\n", "4 4\n0 1\n1 2\n2 3\n3 1\n", "5 4\n0 1\n0 2\n2 3\n3 4\n", "2 1\n1 0\n"],
            "topo_semesters": ["3 2\n1 0\n2 1\n", "2 2\n1 0\n0 1\n", "3 0\n", "4 4\n1 0\n2 0\n3 1\n3 2\n", "5 4\n1 0\n2 1\n3 2\n4 3\n", "3 3\n0 1\n1 2\n2 0\n"],
        }
        return data[variant]
    if family == "graph_weighted":
        data = {
            "dijkstra_shortest": ["4 5 0 3\n0 1 2\n1 2 3\n0 2 10\n2 3 1\n1 3 8\n", "3 1 0 2\n0 1 5\n", "1 0 0 0\n", "5 6 0 4\n0 1 1\n1 2 1\n2 4 1\n0 3 10\n3 4 1\n1 4 7\n", "3 3 2 0\n0 1 2\n1 2 2\n2 0 5\n", "4 4 0 2\n0 1 100\n0 2 5\n2 1 1\n1 3 1\n"],
            "mst_weight": ["4 5\n0 1 1\n1 2 2\n2 3 3\n0 3 10\n0 2 4\n", "3 1\n0 1 5\n", "1 0\n", "5 7\n0 1 2\n0 2 3\n1 2 1\n1 3 4\n2 3 5\n3 4 7\n2 4 6\n", "4 3\n0 1 1\n1 2 1\n2 3 1\n", "4 2\n0 1 1\n2 3 1\n"],
            "limited_reachable": ["4 4 0 4\n0 1 2\n1 2 2\n2 3 2\n0 3 10\n", "3 1 0 1\n0 1 5\n", "1 0 0 0\n", "5 5 2 3\n0 1 1\n1 2 1\n2 3 1\n3 4 1\n0 4 10\n", "4 4 3 6\n0 1 2\n1 2 2\n2 3 2\n0 3 100\n", "6 5 0 2\n0 1 1\n1 2 1\n2 3 1\n3 4 1\n4 5 1\n"],
            "all_pairs_center": ["3 3\n0 1 1\n1 2 1\n0 2 5\n", "4 2\n0 1 1\n2 3 1\n", "1 0\n", "4 4\n0 1 2\n1 2 2\n2 3 2\n0 3 10\n", "3 3\n0 1 5\n1 2 5\n0 2 1\n", "5 6\n0 1 1\n1 2 1\n2 3 1\n3 4 1\n0 4 1\n1 3 2\n"],
            "widest_path": ["4 5 0 3\n0 1 5\n1 3 4\n0 2 3\n2 3 10\n1 2 2\n", "3 1 0 2\n0 1 5\n", "1 0 0 0\n", "5 5 0 4\n0 1 8\n1 4 3\n0 2 5\n2 3 5\n3 4 5\n", "3 3 0 2\n0 1 1\n1 2 1\n0 2 10\n", "4 4 1 3\n0 1 7\n0 2 6\n2 3 6\n1 3 2\n"],
        }
        return data[variant]
    if family == "tree":
        parent_cases = ["5\n-1 0 0 1 1\n", "1\n-1\n", "6\n-1 0 1 2 3 4\n", "7\n-1 0 0 1 1 2 2\n", "4\n-1 0 1 1\n", "8\n-1 0 0 1 1 3 3 6\n"]
        if variant in {"max_depth_parent", "subtree_sizes", "leaf_count"}:
            return parent_cases
        if variant == "lca_parent":
            return ["5 3\n-1 0 0 1 1\n3 4\n2 4\n1 4\n", "1 1\n-1\n0 0\n", "7 3\n-1 0 0 1 1 2 2\n3 4\n3 6\n5 6\n", "4 2\n-1 0 1 1\n2 3\n1 3\n", "6 2\n-1 0 1 2 3 4\n5 4\n5 0\n", "8 3\n-1 0 0 1 1 3 3 6\n5 7\n4 7\n1 2\n"]
        return ["5\n0 1\n1 2\n1 3\n3 4\n", "1\n", "6\n0 1\n1 2\n2 3\n3 4\n4 5\n", "7\n0 1\n0 2\n1 3\n1 4\n2 5\n2 6\n", "4\n0 1\n1 2\n1 3\n", "8\n0 1\n0 2\n1 3\n3 4\n4 5\n2 6\n6 7\n"]
    if family == "number_theory":
        data = {
            "gcd_array": ["4\n12 18 24 30\n", "1\n7\n", "3\n17 19 23\n", "5\n100 50 25 75 125\n", "4\n6 10 15 35\n", "3\n0 12 18\n"],
            "lcm_array": ["3\n4 6 8\n", "1\n7\n", "3\n2 3 5\n", "4\n6 10 15 30\n", "3\n9 6 3\n", "2\n21 6\n"],
            "count_primes": ["10\n", "1\n", "2\n", "100\n", "30\n", "999\n"],
            "mod_pow": ["2 10 1000\n", "3 0 7\n", "5 5 13\n", "10 9 6\n", "123456 789 1000000007\n", "7 2 1\n"],
            "fib_mod": ["10 1000\n", "0 7\n", "1 7\n", "50 1000000007\n", "100 12345\n", "2 2\n"],
        }
        return data[variant]
    if family == "dp_classic":
        data = {
            "coin_change_min": ["11 3\n1 2 5\n", "3 1\n2\n", "0 2\n1 2\n", "27 4\n2 5 10 1\n", "7 2\n3 4\n", "100 3\n1 25 10\n"],
            "coin_change_count": ["5 3\n1 2 5\n", "3 1\n2\n", "0 2\n1 2\n", "10 4\n2 5 3 6\n", "7 2\n3 4\n", "8 3\n1 3 4\n"],
            "knapsack01": ["3 4\n1 15\n3 20\n4 30\n", "1 10\n5 100\n", "3 0\n1 1\n2 2\n3 3\n", "4 7\n6 13\n4 8\n3 6\n5 12\n", "5 10\n2 3\n2 4\n6 10\n5 8\n4 7\n", "2 3\n4 10\n5 20\n"],
            "lis_length": ["8\n10 9 2 5 3 7 101 18\n", "6\n0 1 0 3 2 3\n", "7\n7 7 7 7 7 7 7\n", "5\n1 2 3 4 5\n", "5\n5 4 3 2 1\n", "8\n-1 3 4 -2 0 6 2 3\n"],
            "max_subarray": ["9\n-2 1 -3 4 -1 2 1 -5 4\n", "1\n-1\n", "5\n1 2 3 4 5\n", "4\n-5 -2 -3 -4\n", "6\n5 -10 6 7 -2 3\n", "3\n0 0 0\n"],
        }
        return data[variant]
    if family == "dp_string":
        data = {
            "lcs_length": ["abcde\nace\n", "abc\nabc\n", "abc\ndef\n", "AGGTAB\nGXTXAYB\n", "aaaa\naa\n", "\nabc\n"],
            "longest_common_substring": ["abcdxyz\nxyzabcd\n", "abc\ndef\n", "same\nsame\n", "banana\nananas\n", "prefix\nsuffix\n", "\nabc\n"],
            "edit_distance": ["horse\nros\n", "intention\nexecution\n", "abc\nabc\n", "a\nb\n", "kitten\nsitting\n", "\nabc\n"],
            "min_delete_palindrome": ["aebcbda\n", "racecar\n", "abc\n", "aaaa\n", "character\n", "\n"],
            "word_break": ["leetcode\n2\nleet code\n", "applepenapple\n2\napple pen\n", "catsandog\n5\ncats dog sand and cat\n", "aaaaaaa\n2\naaaa aaa\n", "cars\n3\ncar ca rs\n", "goalspecial\n5\ngo goal goals special al\n"],
        }
        return data[variant]
    if family == "greedy":
        data = {
            "activity_selection": ["4\n1 3\n2 4\n3 5\n0 7\n", "3\n1 2\n2 3\n3 4\n", "3\n1 2\n1 2\n1 2\n", "0\n", "5\n-5 -1\n-2 0\n0 1\n1 3\n2 4\n", "4\n1 100\n11 22\n1 11\n2 12\n"],
            "gas_station": ["5\n1 2 3 4 5\n3 4 5 1 2\n", "3\n2 3 4\n3 4 3\n", "1\n5\n4\n", "4\n4 6 7 4\n6 5 3 5\n", "3\n1 1 1\n1 1 1\n", "5\n5 1 2 3 4\n4 4 1 5 1\n"],
            "assign_cookies": ["3 2\n1 2 3\n1 1\n", "2 3\n1 2\n1 2 3\n", "1 1\n10\n9\n", "4 4\n1 2 2 3\n1 1 2 3\n", "0 2\n\n1 2\n", "5 3\n10 9 8 7 6\n5 6 7\n"],
            "jump_game_min_steps": ["5\n2 3 1 1 4\n", "5\n3 2 1 0 4\n", "1\n0\n", "6\n2 3 0 1 4 2\n", "4\n1 1 1 1\n", "5\n4 0 0 0 0\n"],
            "candy_count": ["3\n1 0 2\n", "3\n1 2 2\n", "1\n5\n", "5\n1 3 4 5 2\n", "5\n5 4 3 2 1\n", "6\n1 2 2 3 2 1\n"],
        }
        return data[variant]
    data = {
        "josephus": ["5 2\n", "1 3\n", "7 3\n", "10 1\n", "10 10\n", "41 3\n"],
        "robot_return": ["UD\n", "LL\n", "UDLR\n", "\n", "UUDDLRLR\n", "URDLDD\n"],
        "base_convert": ["31 16\n", "0 2\n", "10 2\n", "255 16\n", "100 8\n", "12345 36\n"],
        "binary_add": ["1010\n1011\n", "0\n0\n", "1\n111\n", "1111\n1\n", "100000\n100000\n", "101010\n010101\n"],
        "day_of_year": ["2024 3 1\n", "2023 3 1\n", "2000 12 31\n", "1900 3 1\n", "2026 6 10\n", "2024 2 29\n"],
    }
    return data[variant]


def _solve_array_aggregate(variant, text):
    nums = _parse_nums(text)
    if variant == "sum":
        return str(sum(nums))
    if variant == "even_sum":
        return str(sum(value for value in nums if value % 2 == 0))
    if variant == "odd_sum":
        return str(sum(value for value in nums if value % 2 != 0))
    if variant == "positive_sum":
        return str(sum(value for value in nums if value > 0))
    return str(sum(abs(value) for value in nums))


def _solve_array_count(variant, text):
    values = _ints(text)
    if variant == "target_count":
        n, target = values[0], values[1]
        nums = values[2 : 2 + n]
        return str(nums.count(target))
    nums = values[1 : 1 + values[0]]
    if variant == "positive_count":
        return str(sum(1 for value in nums if value > 0))
    if variant == "negative_count":
        return str(sum(1 for value in nums if value < 0))
    if variant == "zero_count":
        return str(sum(1 for value in nums if value == 0))
    return str(len(set(nums)))


def _solve_array_extreme(variant, text):
    nums = _parse_nums(text)
    if variant == "maximum":
        return str(max(nums))
    if variant == "minimum":
        return str(min(nums))
    if variant == "range":
        return str(max(nums) - min(nums))
    if variant == "second_largest":
        ordered = sorted(set(nums))
        return "NONE" if len(ordered) < 2 else str(ordered[-2])
    return str(max(abs(value) for value in nums))


def _solve_array_order(variant, text):
    values = _ints(text)
    if variant == "rotate_right":
        n, k = values[0], values[1]
        nums = values[2 : 2 + n]
        k %= n
        return _join(nums[-k:] + nums[:-k] if k else nums)
    nums = values[1 : 1 + values[0]]
    if variant == "stable_unique":
        seen, result = set(), []
        for value in nums:
            if value not in seen:
                seen.add(value)
                result.append(value)
        return _join(result)
    if variant == "parity_partition":
        return _join([value for value in nums if value % 2 == 0] + [value for value in nums if value % 2 != 0])
    if variant == "plus_one":
        carry = 1
        for i in range(len(nums) - 1, -1, -1):
            total = nums[i] + carry
            nums[i] = total % 10
            carry = total // 10
            if not carry:
                break
        if carry:
            nums.insert(0, carry)
        return _join(nums)
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


def _solve_prefix_queries(variant, text):
    values = _ints(text)
    if variant == "balanced_pivot":
        nums = values[1 : 1 + values[0]]
        total, left = sum(nums), 0
        for index, value in enumerate(nums):
            if left == total - left - value:
                return str(index)
            left += value
        return "-1"
    n, q = values[0], values[1]
    nums = values[2 : 2 + n]
    cursor = 2 + n
    outputs = []
    if variant in {"range_sum", "range_xor"}:
        prefix = [0]
        for value in nums:
            prefix.append(prefix[-1] + value if variant == "range_sum" else prefix[-1] ^ value)
        for _ in range(q):
            left, right = values[cursor], values[cursor + 1]
            cursor += 2
            if variant == "range_sum":
                outputs.append(str(prefix[right + 1] - prefix[left]))
            else:
                outputs.append(str(prefix[right + 1] ^ prefix[left]))
        return "\n".join(outputs)
    for _ in range(q):
        left, right = values[cursor], values[cursor + 1]
        cursor += 2
        segment = nums[left : right + 1]
        outputs.append(str(min(segment) if variant == "range_min" else max(segment)))
    return "\n".join(outputs)


def _solve_intervals(variant, text):
    values = _ints(text)
    if variant == "point_coverage":
        n, q = values[0], values[1]
        starts, ends = [], []
        cursor = 2
        for _ in range(n):
            starts.append(values[cursor])
            ends.append(values[cursor + 1])
            cursor += 2
        starts.sort()
        ends.sort()
        points = values[cursor : cursor + q]
        return _join(bisect.bisect_right(starts, p) - bisect.bisect_left(ends, p) for p in points)
    intervals = _parse_intervals(text)
    if not intervals:
        return "0"
    if variant == "union_length":
        intervals.sort()
        total = 0
        left, right = intervals[0]
        for start, end in intervals[1:]:
            if start > right:
                total += right - left
                left, right = start, end
            else:
                right = max(right, end)
        return str(total + right - left)
    if variant in {"max_overlap", "meeting_rooms"}:
        events = []
        for start, end in intervals:
            events.append((start, 1))
            events.append((end, -1))
        active = best = 0
        for _, delta in sorted(events, key=lambda item: (item[0], item[1])):
            active += delta
            best = max(best, active)
        return str(best)
    intervals.sort(key=lambda item: (item[1], item[0]))
    kept, end = 0, -10**30
    for start, finish in intervals:
        if start >= end:
            kept += 1
            end = finish
    if variant == "erase_overlap":
        return str(len(intervals) - kept)
    return str(kept)


def _solve_strings_count(variant, text):
    value = text.rstrip("\n")
    if variant == "vowels":
        return str(sum(char.lower() in "aeiou" for char in value))
    if variant == "digits":
        return str(sum(char.isdigit() for char in value))
    if variant == "uppercase":
        return str(sum("A" <= char <= "Z" for char in value))
    if variant == "first_unique_index":
        counts = Counter(value)
        for index, char in enumerate(value):
            if counts[char] == 1:
                return str(index)
        return "-1"
    if not value:
        return "0"
    best = current = 1
    for i in range(1, len(value)):
        current = current + 1 if value[i] == value[i - 1] else 1
        best = max(best, current)
    return str(best)


def _solve_strings_transform(variant, text):
    lines = text.rstrip("\n").splitlines()
    if variant == "reverse_words":
        return " ".join(reversed(text.split()))
    if variant == "rle_encode":
        s = text.rstrip("\n")
        if not s:
            return ""
        result = []
        current, count = s[0], 1
        for char in s[1:]:
            if char == current:
                count += 1
            else:
                result.append(f"{current}{count}")
                current, count = char, 1
        result.append(f"{current}{count}")
        return " ".join(result)
    if variant == "rle_decode":
        n = int(lines[0]) if lines else 0
        output = []
        for line in lines[1 : 1 + n]:
            char, count = line.split()
            output.append(char * int(count))
        return "".join(output)
    if variant == "remove_adjacent_duplicates":
        stack = []
        for char in text.rstrip("\n"):
            if stack and stack[-1] == char:
                stack.pop()
            else:
                stack.append(char)
        return "".join(stack)
    if not lines:
        return ""
    n = int(lines[0])
    words = " ".join(lines[1:]).split()[:n]
    if not words:
        return ""
    prefix = words[0]
    for word in words[1:]:
        while not word.startswith(prefix):
            prefix = prefix[:-1]
            if not prefix:
                return ""
    return prefix


def _solve_strings_match(variant, text):
    lines = text.rstrip("\n").splitlines()
    if variant == "is_subsequence":
        source = lines[0] if lines else ""
        target = lines[1] if len(lines) > 1 else ""
        pos = 0
        for char in target:
            if pos < len(source) and source[pos] == char:
                pos += 1
        return _bool(pos == len(source))
    if variant == "rotation":
        a = lines[0] if lines else ""
        b = lines[1] if len(lines) > 1 else ""
        return _bool(len(a) == len(b) and b in (a + a))
    if variant == "anagram":
        a = lines[0] if lines else ""
        b = lines[1] if len(lines) > 1 else ""
        return _bool(Counter(a.lower()) == Counter(b.lower()))
    if variant == "pattern_count":
        haystack = lines[0] if lines else ""
        needle = lines[1] if len(lines) > 1 else ""
        if needle == "":
            return "0"
        count = 0
        for index in range(0, len(haystack) - len(needle) + 1):
            if haystack[index : index + len(needle)] == needle:
                count += 1
        return str(count)
    n = int(lines[0]) if lines else 0
    words = " ".join(lines[1:]).split()[:n]
    if not words:
        return ""
    suffix = words[0]
    for word in words[1:]:
        while not word.endswith(suffix):
            suffix = suffix[1:]
            if not suffix:
                return ""
    return suffix


def _solve_stack_queue(variant, text):
    if variant == "valid_brackets":
        pairs = {")": "(", "]": "[", "}": "{"}
        stack = []
        for char in text.strip():
            if char in "([{":
                stack.append(char)
            elif char in pairs:
                if not stack or stack.pop() != pairs[char]:
                    return "false"
        return _bool(not stack)
    if variant == "postfix_eval":
        stack = []
        for token in text.split():
            if token in {"+", "-", "*", "/"}:
                b = stack.pop()
                a = stack.pop()
                if token == "+":
                    stack.append(a + b)
                elif token == "-":
                    stack.append(a - b)
                elif token == "*":
                    stack.append(a * b)
                else:
                    stack.append(int(a / b))
            else:
                stack.append(int(token))
        return str(stack[-1])
    if variant == "next_greater":
        nums = _parse_nums(text)
        result = [-1] * len(nums)
        stack = []
        for i, value in enumerate(nums):
            while stack and nums[stack[-1]] < value:
                result[stack.pop()] = value
            stack.append(i)
        return _join(result)
    if variant == "sliding_min":
        values = _ints(text)
        n, k = values[0], values[1]
        nums = values[2 : 2 + n]
        queue, result = deque(), []
        for i, value in enumerate(nums):
            while queue and queue[0] <= i - k:
                queue.popleft()
            while queue and nums[queue[-1]] >= value:
                queue.pop()
            queue.append(i)
            if i >= k - 1:
                result.append(nums[queue[0]])
        return _join(result)
    lines = text.strip().splitlines()
    num = lines[0].strip()
    k = int(lines[1])
    stack = []
    for digit in num:
        while k and stack and stack[-1] > digit:
            stack.pop()
            k -= 1
        stack.append(digit)
    if k:
        stack = stack[:-k]
    answer = "".join(stack).lstrip("0")
    return answer or "0"


def _solve_matrix_basic(variant, text):
    if variant == "rotate_clockwise":
        values = _ints(text)
        n = values[0]
        grid = [values[1 + i * n : 1 + (i + 1) * n] for i in range(n)]
        return _join_lines([[grid[n - 1 - r][c] for r in range(n)] for c in range(n)])
    if variant == "diagonal_sum":
        values = _ints(text)
        n = values[0]
        grid = [values[1 + i * n : 1 + (i + 1) * n] for i in range(n)]
        total = sum(grid[i][i] + grid[i][n - 1 - i] for i in range(n))
        if n % 2:
            total -= grid[n // 2][n // 2]
        return str(total)
    m, n, grid = _parse_matrix(text)
    if variant == "transpose":
        return _join_lines([[grid[r][c] for r in range(m)] for c in range(n)])
    if variant == "border_sum":
        total = 0
        for r in range(m):
            for c in range(n):
                if r in (0, m - 1) or c in (0, n - 1):
                    total += grid[r][c]
        return str(total)
    target = _ints(text)[2 + m * n]
    row, col = 0, n - 1
    while row < m and col >= 0:
        if grid[row][col] == target:
            return "true"
        if grid[row][col] > target:
            col -= 1
        else:
            row += 1
    return "false"


def _grid_lines(text):
    lines = text.strip().splitlines()
    m, n = map(int, lines[0].split())
    return m, n, [list(lines[i + 1].replace(" ", "")) for i in range(m)], lines


def _solve_grid(variant, text):
    m, n, grid, lines = _grid_lines(text)
    if variant == "unique_paths_obstacles":
        dp = [0] * n
        dp[0] = 0 if grid[0][0] == "1" else 1
        for r in range(m):
            for c in range(n):
                if grid[r][c] == "1":
                    dp[c] = 0
                elif c:
                    dp[c] += dp[c - 1]
        return str(dp[-1])
    if variant == "shortest_path":
        if grid[0][0] == "1" or grid[m - 1][n - 1] == "1":
            return "-1"
        queue = deque([(0, 0, 0)])
        seen = {(0, 0)}
        while queue:
            r, c, dist = queue.popleft()
            if (r, c) == (m - 1, n - 1):
                return str(dist)
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < m and 0 <= nc < n and grid[nr][nc] == "0" and (nr, nc) not in seen:
                    seen.add((nr, nc))
                    queue.append((nr, nc, dist + 1))
        return "-1"
    if variant == "flood_fill_size":
        sr, sc = map(int, lines[1 + m].split())
        target = grid[sr][sc]
        stack, seen = [(sr, sc)], {(sr, sc)}
        while stack:
            r, c = stack.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < m and 0 <= nc < n and (nr, nc) not in seen and grid[nr][nc] == target:
                    seen.add((nr, nc))
                    stack.append((nr, nc))
        return str(len(seen))
    count = 0
    best = 0
    for r in range(m):
        for c in range(n):
            if grid[r][c] == "1":
                count += 1
                area = 0
                stack = [(r, c)]
                grid[r][c] = "0"
                while stack:
                    x, y = stack.pop()
                    area += 1
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < m and 0 <= ny < n and grid[nx][ny] == "1":
                            grid[nx][ny] = "0"
                            stack.append((nx, ny))
                best = max(best, area)
    return str(count if variant == "island_count" else best)


def _solve_graph_basic(variant, text):
    values = _ints(text)
    if variant == "bfs_distances":
        n, m, start = values[0], values[1], values[2]
        cursor = 3
        graph = [[] for _ in range(n)]
        for _ in range(m):
            a, b = values[cursor], values[cursor + 1]
            cursor += 2
            graph[a].append(b)
            graph[b].append(a)
        dist = [-1] * n
        dist[start] = 0
        queue = deque([start])
        while queue:
            node = queue.popleft()
            for nxt in graph[node]:
                if dist[nxt] == -1:
                    dist[nxt] = dist[node] + 1
                    queue.append(nxt)
        return _join(dist)
    n, m = values[0], values[1]
    cursor = 2
    graph = [[] for _ in range(n)]
    indeg = [0] * n
    for _ in range(m):
        a, b = values[cursor], values[cursor + 1]
        cursor += 2
        if variant in {"cycle_directed", "topo_semesters"}:
            if variant == "topo_semesters":
                a, b = b, a
            graph[a].append(b)
            indeg[b] += 1
        else:
            graph[a].append(b)
            graph[b].append(a)
    if variant == "connected_components":
        seen = [False] * n
        count = 0
        for i in range(n):
            if not seen[i]:
                count += 1
                stack = [i]
                seen[i] = True
                while stack:
                    node = stack.pop()
                    for nxt in graph[node]:
                        if not seen[nxt]:
                            seen[nxt] = True
                            stack.append(nxt)
        return str(count)
    if variant == "bipartite":
        color = [None] * n
        for i in range(n):
            if color[i] is None:
                color[i] = 0
                queue = deque([i])
                while queue:
                    node = queue.popleft()
                    for nxt in graph[node]:
                        if color[nxt] is None:
                            color[nxt] = color[node] ^ 1
                            queue.append(nxt)
                        elif color[nxt] == color[node]:
                            return "false"
        return "true"
    queue = deque(i for i, degree in enumerate(indeg) if degree == 0)
    seen = 0
    semester = 0
    while queue:
        semester += 1
        for _ in range(len(queue)):
            node = queue.popleft()
            seen += 1
            for nxt in graph[node]:
                indeg[nxt] -= 1
                if indeg[nxt] == 0:
                    queue.append(nxt)
    if variant == "cycle_directed":
        return _bool(seen < n)
    return str(semester if seen == n else -1)


def _dijkstra(n, graph, start):
    dist = [10**30] * n
    dist[start] = 0
    heap = [(0, start)]
    while heap:
        cost, node = heapq.heappop(heap)
        if cost != dist[node]:
            continue
        for nxt, weight in graph[node]:
            new_cost = cost + weight
            if new_cost < dist[nxt]:
                dist[nxt] = new_cost
                heapq.heappush(heap, (new_cost, nxt))
    return dist


def _solve_graph_weighted(variant, text):
    values = _ints(text)
    if variant in {"dijkstra_shortest", "limited_reachable", "widest_path"}:
        n, m, s, last = values[0], values[1], values[2], values[3]
        cursor = 4
        graph = [[] for _ in range(n)]
        for _ in range(m):
            a, b, w = values[cursor], values[cursor + 1], values[cursor + 2]
            cursor += 3
            if variant == "dijkstra_shortest":
                graph[a].append((b, w))
            else:
                graph[a].append((b, w))
                graph[b].append((a, w))
        if variant == "widest_path":
            cap = [0] * n
            cap[s] = 10**30
            heap = [(-cap[s], s)]
            while heap:
                current, node = heapq.heappop(heap)
                current = -current
                if current != cap[node]:
                    continue
                for nxt, weight in graph[node]:
                    new_cap = min(current, weight)
                    if new_cap > cap[nxt]:
                        cap[nxt] = new_cap
                        heapq.heappush(heap, (-new_cap, nxt))
            return str(cap[last])
        dist = _dijkstra(n, graph, s)
        if variant == "limited_reachable":
            return str(sum(value <= last for value in dist))
        return str(-1 if dist[last] >= 10**30 else dist[last])
    n, m = values[0], values[1]
    edges = []
    cursor = 2
    for _ in range(m):
        a, b, w = values[cursor], values[cursor + 1], values[cursor + 2]
        cursor += 3
        edges.append((w, a, b))
    if variant == "mst_weight":
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        total = used = 0
        for weight, a, b in sorted(edges):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb
                total += weight
                used += 1
        return str(total) if used == n - 1 else "IMPOSSIBLE"
    graph = [[10**12] * n for _ in range(n)]
    for i in range(n):
        graph[i][i] = 0
    for weight, a, b in edges:
        graph[a][b] = min(graph[a][b], weight)
        graph[b][a] = min(graph[b][a], weight)
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if graph[i][k] + graph[k][j] < graph[i][j]:
                    graph[i][j] = graph[i][k] + graph[k][j]
    best_node, best_sum = -1, 10**30
    for i in range(n):
        if any(value >= 10**12 for value in graph[i]):
            continue
        total = sum(graph[i])
        if total < best_sum:
            best_sum = total
            best_node = i
    return str(best_node)


def _solve_tree(variant, text):
    values = _ints(text)
    if variant in {"max_depth_parent", "subtree_sizes", "leaf_count", "lca_parent"}:
        n = values[0]
        q = values[1] if variant == "lca_parent" else 0
        offset = 2 if variant == "lca_parent" else 1
        parents = values[offset : offset + n]
        children = [[] for _ in range(n)]
        root = 0
        for node, parent in enumerate(parents):
            if parent == -1:
                root = node
            else:
                children[parent].append(node)
        if variant == "leaf_count":
            return str(sum(1 for node in range(n) if not children[node]))
        if variant == "max_depth_parent":
            best = 0
            stack = [(root, 1)]
            while stack:
                node, depth = stack.pop()
                best = max(best, depth)
                for child in children[node]:
                    stack.append((child, depth + 1))
            return str(best)
        if variant == "subtree_sizes":
            sizes = [1] * n
            order = [root]
            for node in order:
                order.extend(children[node])
            for node in reversed(order):
                for child in children[node]:
                    sizes[node] += sizes[child]
            return _join(sizes)
        cursor = offset + n
        outputs = []
        for _ in range(q):
            a, b = values[cursor], values[cursor + 1]
            cursor += 2
            ancestors = set()
            while a != -1:
                ancestors.add(a)
                a = parents[a]
            while b not in ancestors:
                b = parents[b]
            outputs.append(str(b))
        return "\n".join(outputs)
    n = values[0]
    if n <= 1:
        return "0"
    graph = [[] for _ in range(n)]
    cursor = 1
    for _ in range(n - 1):
        a, b = values[cursor], values[cursor + 1]
        cursor += 2
        graph[a].append(b)
        graph[b].append(a)

    def farthest(start):
        dist = [-1] * n
        dist[start] = 0
        queue = deque([start])
        while queue:
            node = queue.popleft()
            for nxt in graph[node]:
                if dist[nxt] == -1:
                    dist[nxt] = dist[node] + 1
                    queue.append(nxt)
        node = max(range(n), key=lambda i: dist[i])
        return node, dist[node]

    node, _ = farthest(0)
    _, diameter = farthest(node)
    return str(diameter)


def _solve_number_theory(variant, text):
    values = _ints(text)
    if variant == "mod_pow":
        return str(pow(values[0], values[1], values[2]))
    if variant == "fib_mod":
        n, mod = values[0], values[1]
        a, b = 0, 1
        for _ in range(n):
            a, b = b, (a + b) % mod
        return str(a % mod)
    if variant == "count_primes":
        n = values[0]
        if n < 2:
            return "0"
        sieve = [True] * (n + 1)
        sieve[0] = sieve[1] = False
        for i in range(2, int(n**0.5) + 1):
            if sieve[i]:
                step = i
                start = i * i
                sieve[start : n + 1 : step] = [False] * (((n - start) // step) + 1)
        return str(sum(sieve))
    nums = values[1 : 1 + values[0]]
    if variant == "gcd_array":
        result = 0
        for value in nums:
            result = math.gcd(result, abs(value))
        return str(result)
    result = 1
    for value in nums:
        result = result * value // math.gcd(result, value)
    return str(result)


def _solve_dp_classic(variant, text):
    values = _ints(text)
    if variant in {"coin_change_min", "coin_change_count"}:
        amount, k = values[0], values[1]
        coins = values[2 : 2 + k]
        if variant == "coin_change_min":
            dp = [10**9] * (amount + 1)
            dp[0] = 0
            for coin in coins:
                for total in range(coin, amount + 1):
                    dp[total] = min(dp[total], dp[total - coin] + 1)
            return str(-1 if dp[amount] >= 10**9 else dp[amount])
        dp = [0] * (amount + 1)
        dp[0] = 1
        for coin in coins:
            for total in range(coin, amount + 1):
                dp[total] += dp[total - coin]
        return str(dp[amount])
    if variant == "knapsack01":
        n, capacity = values[0], values[1]
        dp = [0] * (capacity + 1)
        cursor = 2
        for _ in range(n):
            weight, value = values[cursor], values[cursor + 1]
            cursor += 2
            for cap in range(capacity, weight - 1, -1):
                dp[cap] = max(dp[cap], dp[cap - weight] + value)
        return str(max(dp))
    nums = values[1 : 1 + values[0]]
    if variant == "lis_length":
        tails = []
        for value in nums:
            pos = bisect.bisect_left(tails, value)
            if pos == len(tails):
                tails.append(value)
            else:
                tails[pos] = value
        return str(len(tails))
    best = current = nums[0]
    for value in nums[1:]:
        current = max(value, current + value)
        best = max(best, current)
    return str(best)


def _solve_dp_string(variant, text):
    lines = text.rstrip("\n").splitlines()
    if variant == "word_break":
        s = lines[0] if lines else ""
        n = int(lines[1]) if len(lines) > 1 else 0
        words = set(" ".join(lines[2:]).split()[:n])
        dp = [False] * (len(s) + 1)
        dp[0] = True
        max_len = max((len(word) for word in words), default=0)
        for i in range(1, len(s) + 1):
            dp[i] = any(dp[j] and s[j:i] in words for j in range(max(0, i - max_len), i))
        return _bool(dp[-1])
    a = lines[0] if lines else ""
    b = lines[1] if len(lines) > 1 else ""
    if variant == "longest_common_substring":
        dp = [0] * (len(b) + 1)
        best = 0
        for ca in a:
            prev = 0
            for j, cb in enumerate(b, 1):
                old = dp[j]
                dp[j] = prev + 1 if ca == cb else 0
                best = max(best, dp[j])
                prev = old
        return str(best)
    if variant == "edit_distance":
        dp = list(range(len(b) + 1))
        for i, ca in enumerate(a, 1):
            prev = dp[0]
            dp[0] = i
            for j, cb in enumerate(b, 1):
                old = dp[j]
                dp[j] = prev if ca == cb else min(prev, dp[j], dp[j - 1]) + 1
                prev = old
        return str(dp[-1])
    if variant == "min_delete_palindrome":
        s = a
        rev = s[::-1]
        dp = [0] * (len(rev) + 1)
        for ca in s:
            prev = 0
            for j, cb in enumerate(rev, 1):
                old = dp[j]
                dp[j] = prev + 1 if ca == cb else max(dp[j], dp[j - 1])
                prev = old
        return str(len(s) - dp[-1])
    dp = [0] * (len(b) + 1)
    for ca in a:
        prev = 0
        for j, cb in enumerate(b, 1):
            old = dp[j]
            dp[j] = prev + 1 if ca == cb else max(dp[j], dp[j - 1])
            prev = old
    return str(dp[-1])


def _solve_greedy(variant, text):
    values = _ints(text)
    if variant == "gas_station":
        n = values[0]
        gas = values[1 : 1 + n]
        cost = values[1 + n : 1 + 2 * n]
        if sum(gas) < sum(cost):
            return "-1"
        start = tank = 0
        for i in range(n):
            tank += gas[i] - cost[i]
            if tank < 0:
                start = i + 1
                tank = 0
        return str(start)
    if variant == "assign_cookies":
        g, s = values[0], values[1]
        greed = sorted(values[2 : 2 + g])
        cookies = sorted(values[2 + g : 2 + g + s])
        i = answer = 0
        for cookie in cookies:
            if i < g and cookie >= greed[i]:
                answer += 1
                i += 1
        return str(answer)
    if variant == "jump_game_min_steps":
        nums = values[1 : 1 + values[0]]
        if len(nums) == 1:
            return "0"
        jumps = 0
        current_end = farthest = 0
        for i in range(len(nums) - 1):
            farthest = max(farthest, i + nums[i])
            if i == current_end:
                if farthest == current_end:
                    return "-1"
                jumps += 1
                current_end = farthest
                if current_end >= len(nums) - 1:
                    return str(jumps)
        return str(jumps)
    if variant == "candy_count":
        ratings = values[1 : 1 + values[0]]
        candies = [1] * len(ratings)
        for i in range(1, len(ratings)):
            if ratings[i] > ratings[i - 1]:
                candies[i] = candies[i - 1] + 1
        for i in range(len(ratings) - 2, -1, -1):
            if ratings[i] > ratings[i + 1]:
                candies[i] = max(candies[i], candies[i + 1] + 1)
        return str(sum(candies))
    intervals = _parse_intervals(text)
    intervals.sort(key=lambda item: (item[1], item[0]))
    count = 0
    end = -10**30
    for start, finish in intervals:
        if start >= end:
            count += 1
            end = finish
    return str(count)


def _solve_simulation(variant, text):
    if variant == "robot_return":
        x = y = 0
        for char in text.strip():
            if char == "U":
                y += 1
            elif char == "D":
                y -= 1
            elif char == "L":
                x -= 1
            elif char == "R":
                x += 1
        return _bool(x == 0 and y == 0)
    if variant == "binary_add":
        lines = text.strip().splitlines()
        return bin(int(lines[0] or "0", 2) + int(lines[1] or "0", 2))[2:]
    values = _ints(text)
    if variant == "josephus":
        n, k = values[0], values[1]
        survivor = 0
        for size in range(1, n + 1):
            survivor = (survivor + k) % size
        return str(survivor + 1)
    if variant == "base_convert":
        number, base = values[0], values[1]
        digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        if number == 0:
            return "0"
        result = []
        while number:
            result.append(digits[number % base])
            number //= base
        return "".join(reversed(result))
    year, month, day = values[0], values[1], values[2]
    leap = year % 400 == 0 or (year % 4 == 0 and year % 100 != 0)
    days = [31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return str(sum(days[: month - 1]) + day)


SOLVERS = {
    "array_aggregate": _solve_array_aggregate,
    "array_count": _solve_array_count,
    "array_extreme": _solve_array_extreme,
    "array_order": _solve_array_order,
    "prefix_queries": _solve_prefix_queries,
    "intervals": _solve_intervals,
    "strings_count": _solve_strings_count,
    "strings_transform": _solve_strings_transform,
    "strings_match": _solve_strings_match,
    "stack_queue": _solve_stack_queue,
    "matrix_basic": _solve_matrix_basic,
    "grid": _solve_grid,
    "graph_basic": _solve_graph_basic,
    "graph_weighted": _solve_graph_weighted,
    "tree": _solve_tree,
    "number_theory": _solve_number_theory,
    "dp_classic": _solve_dp_classic,
    "dp_string": _solve_dp_string,
    "greedy": _solve_greedy,
    "simulation": _solve_simulation,
}


def _build_definitions():
    info = _family_info()
    definitions = {}
    for family, variants in EXTRA_VARIANTS.items():
        family_title, input_format, output_format, constraints = info[family]
        for variant, title, slug, difficulty, tags, summary in variants:
            definitions[slug] = {
                "family": family,
                "family_title": family_title,
                "variant": variant,
                "title": title,
                "slug": slug,
                "difficulty": difficulty,
                "tags": tags,
                "description": f"{family_title}练习：{summary}",
                "input_format": input_format,
                "output_format": output_format,
                "constraints": constraints,
                "cases": _cases_for(family, variant),
            }
    return definitions


EXTRA_PROBLEM_BANK = _build_definitions()


def get_extra_problem_specs():
    return [
        (definition["title"], definition["slug"], definition["difficulty"], definition["tags"])
        for definition in EXTRA_PROBLEM_BANK.values()
    ]


def build_extra_problem(index, spec, problem_builder, tc_builder):
    title, slug, difficulty, tags = spec
    definition = EXTRA_PROBLEM_BANK[slug]
    solver = SOLVERS[definition["family"]]
    cases = [_ensure_newline(case) for case in definition["cases"]]
    samples = [
        {
            "input": cases[0],
            "output": solver(definition["variant"], cases[0]),
        }
    ]
    hidden = [
        tc_builder(case_input, solver(definition["variant"], case_input))
        for case_input in cases[1:]
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
