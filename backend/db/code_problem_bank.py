from copy import deepcopy


BASE_STARTER_CODE = {
    "python": """import sys

def main():
    data = sys.stdin.read()
    # TODO: parse stdin and print the answer to stdout.

if __name__ == "__main__":
    main()
""",
    "java": """import java.io.*;
import java.util.*;

public class Main {
    public static void main(String[] args) throws Exception {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        // TODO: parse stdin and print the answer to stdout.
    }
}
""",
    "cpp": """#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    // TODO: parse stdin and print the answer to stdout.
    return 0;
}
""",
    "javascript": """const fs = require("fs");
const input = fs.readFileSync(0, "utf8");
// TODO: parse stdin and print the answer to stdout.
""",
}


def tc(input_text, expected_output, is_sample=False, explanation=None):
    return {
        "input": input_text,
        "expected_output": expected_output,
        "is_sample": is_sample,
        "explanation": explanation,
    }


def problem(
    id,
    title,
    slug,
    difficulty,
    tags,
    description,
    input_format,
    output_format,
    samples,
    constraints,
    hidden,
):
    sample_cases = [
        tc(item["input"], item["output"], True, item.get("explanation"))
        for item in samples
    ]
    return {
        "id": id,
        "title": title,
        "slug": slug,
        "difficulty": difficulty,
        "tags": tags,
        "description": description,
        "input_format": input_format,
        "output_format": output_format,
        "samples": samples,
        "constraints": constraints,
        "starter_code": deepcopy(BASE_STARTER_CODE),
        "test_cases": sample_cases + hidden,
    }


JUDGABLE_PROBLEMS = [
    problem(
        1,
        "两数配对",
        "two-number-pair",
        "简单",
        ["数组", "哈希表"],
        "给定一个整数数组和一个目标值，请找出数组中两个不同位置的数，使它们的和等于目标值。若存在多组答案，输出下标字典序最小的一组；若不存在，输出 -1。",
        "第一行输入整数 n。第二行输入 n 个整数。第三行输入目标值 target。",
        "输出两个 0 基下标，按从小到大排列；若不存在答案，输出 -1。",
        [
            {
                "input": "4\n2 7 11 15\n9\n",
                "output": "0 1",
                "explanation": "nums[0] + nums[1] = 9。",
            }
        ],
        ["2 <= n <= 100000", "-10^9 <= nums[i], target <= 10^9"],
        [
            tc("3\n3 2 4\n6\n", "1 2"),
            tc("2\n-1 -2\n-3\n", "0 1"),
            tc("4\n1 2 3 4\n8\n", "-1"),
            tc("5\n1 4 6 99 9\n10\n", "0 4"),
            tc("6\n8 1 4 6 2 9\n10\n", "0 4"),
            tc("7\n-5 2 3 0 5 -2 7\n0\n", "0 4"),
            tc("6\n5 5 5 5 5 5\n10\n", "0 1"),
        ],
    ),
    problem(
        2,
        "逆序数字相加",
        "reverse-digit-sum",
        "中等",
        ["链表", "数学", "模拟"],
        "两个非负整数以逆序数字序列表示，每个节点只存一位数字。请计算两数之和，并以同样的逆序数字序列输出。",
        "第一行输入整数 n，第二行输入 n 个数字表示第一个数。第三行输入整数 m，第四行输入 m 个数字表示第二个数。",
        "输出相加后的逆序数字序列，数字之间用一个空格分隔。",
        [
            {
                "input": "3\n2 4 3\n3\n5 6 4\n",
                "output": "7 0 8",
                "explanation": "342 + 465 = 807，逆序输出为 7 0 8。",
            }
        ],
        ["1 <= n, m <= 100000", "每个数字均在 0 到 9 之间", "输入不会出现无意义的前导高位零"],
        [
            tc("1\n0\n1\n0\n", "0"),
            tc("4\n9 9 9 9\n1\n1\n", "0 0 0 0 1"),
            tc("3\n1 8 9\n2\n1 2\n", "2 0 0 1"),
            tc("5\n9 0 9 9 9\n3\n1 9 0\n", "0 0 0 0 0 1"),
            tc("6\n0 0 0 0 0 1\n1\n9\n", "9 0 0 0 0 1"),
            tc("3\n5 6 7\n5\n5 4 3 2 1\n", "0 1 1 3 1"),
        ],
    ),
    problem(
        3,
        "最长无重复片段",
        "longest-unique-substring",
        "中等",
        ["字符串", "哈希表", "滑动窗口"],
        "给定一个字符串，请求出不含重复字符的最长连续片段长度。",
        "输入一行字符串 s，可包含可见 ASCII 字符；若输入为空，视为空串。",
        "输出一个整数，表示最长无重复连续片段的长度。",
        [{"input": "abcabcbb\n", "output": "3", "explanation": "最长片段可以是 abc。"}],
        ["0 <= |s| <= 200000"],
        [
            tc("bbbbb\n", "1"),
            tc("pwwkew\n", "3"),
            tc("\n", "0"),
            tc("abba\n", "2"),
            tc("dvdf\n", "3"),
            tc("a bca\n", "4"),
            tc("tmmzuxt\n", "5"),
        ],
    ),
    problem(
        4,
        "两个有序数组的中位数",
        "median-of-two-sorted-arrays-acm",
        "困难",
        ["数组", "二分"],
        "给定两个非降序整数数组，请求出它们合并后的中位数。要求不实际合并也能通过大数据用例。",
        "第一行输入两个整数 m 和 n。第二行输入 m 个整数。第三行输入 n 个整数。若某个数组长度为 0，对应行为空行。",
        "输出中位数。若结果为整数，输出整数；否则输出一位小数。",
        [{"input": "2 1\n1 3\n2\n", "output": "2", "explanation": "合并后为 1 2 3。"}],
        ["0 <= m, n <= 200000", "m + n >= 1", "数组均为非降序"],
        [
            tc("2 2\n1 2\n3 4\n", "2.5"),
            tc("0 1\n\n5\n", "5"),
            tc("3 4\n1 4 7\n2 3 6 9\n", "4"),
            tc("1 2\n100\n1 2\n", "2"),
            tc("3 3\n-5 -3 -1\n-4 -2 0\n", "-2.5"),
            tc("5 0\n1 2 3 4 5\n\n", "3"),
        ],
    ),
    problem(
        5,
        "最长回文子串",
        "longest-palindrome-substring-acm",
        "中等",
        ["字符串", "动态规划", "中心扩展"],
        "给定一个字符串，请输出它的最长回文连续子串。若存在多个长度相同的答案，输出最靠左的一个。",
        "输入一行字符串 s。",
        "输出最长回文子串。",
        [{"input": "babad\n", "output": "bab", "explanation": "bab 和 aba 长度相同，选择更靠左的 bab。"}],
        ["1 <= |s| <= 5000"],
        [
            tc("cbbd\n", "bb"),
            tc("a\n", "a"),
            tc("ac\n", "a"),
            tc("forgeeksskeegfor\n", "geeksskeeg"),
            tc("abacdfgdcaba\n", "aba"),
            tc("aaaa\n", "aaaa"),
            tc("bananas\n", "anana"),
            tc("abcda\n", "a"),
        ],
    ),
    problem(
        6,
        "盛水边界",
        "container-most-water-acm",
        "中等",
        ["数组", "双指针", "贪心"],
        "给定若干条竖线的高度，任选两条作为边界，与 x 轴共同形成容器。请输出容器可盛水的最大面积。",
        "第一行输入整数 n。第二行输入 n 个非负整数 height。",
        "输出一个整数，表示最大面积。",
        [{"input": "9\n1 8 6 2 5 4 8 3 7\n", "output": "49"}],
        ["2 <= n <= 200000", "0 <= height[i] <= 10^9"],
        [
            tc("2\n1 1\n", "1"),
            tc("5\n4 3 2 1 4\n", "16"),
            tc("5\n1 2 1 3 1\n", "4"),
            tc("3\n0 0 0\n", "0"),
            tc("6\n1 2 3 4 5 6\n", "9"),
            tc("6\n6 5 4 3 2 1\n", "9"),
            tc("7\n2 3 10 5 7 8 9\n", "36"),
        ],
    ),
    problem(
        7,
        "三数归零",
        "three-sum-zero-acm",
        "中等",
        ["数组", "双指针", "排序"],
        "给定一个整数数组，请找出所有不重复的三元组，使三元组内三个数之和为 0。",
        "第一行输入整数 n。第二行输入 n 个整数。",
        "第一行输出三元组数量 k。随后 k 行，每行输出一个升序三元组。三元组整体按字典序升序输出。",
        [
            {
                "input": "6\n-1 0 1 2 -1 -4\n",
                "output": "2\n-1 -1 2\n-1 0 1",
            }
        ],
        ["0 <= n <= 5000", "-10^5 <= nums[i] <= 10^5"],
        [
            tc("3\n0 1 1\n", "0"),
            tc("3\n0 0 0\n", "1\n0 0 0"),
            tc("7\n-2 0 1 1 2 -1 -4\n", "3\n-2 0 2\n-2 1 1\n-1 0 1"),
            tc("0\n\n", "0"),
            tc("6\n0 0 0 0 0 0\n", "1\n0 0 0"),
            tc("6\n-1 -1 -1 2 2 0\n", "1\n-1 -1 2"),
            tc("8\n-4 -2 -2 0 2 2 4 4\n", "4\n-4 0 4\n-4 2 2\n-2 -2 4\n-2 0 2"),
        ],
    ),
    problem(
        8,
        "删除倒数节点",
        "remove-nth-from-end-acm",
        "中等",
        ["链表", "双指针"],
        "给定一个单链表的节点值序列，请删除倒数第 k 个节点，并输出删除后的链表。",
        "第一行输入整数 n。第二行输入 n 个整数表示链表。第三行输入整数 k。",
        "输出删除后的链表节点值，值之间用一个空格分隔；若链表为空，输出空行。",
        [{"input": "5\n1 2 3 4 5\n2\n", "output": "1 2 3 5"}],
        ["1 <= k <= n <= 200000"],
        [
            tc("1\n1\n1\n", ""),
            tc("2\n1 2\n1\n", "1"),
            tc("5\n1 2 3 4 5\n5\n", "2 3 4 5"),
            tc("3\n1 2 3\n2\n", "1 3"),
            tc("4\n1 2 3 4\n1\n", "1 2 3"),
            tc("5\n-1 -2 -3 -4 -5\n3\n", "-1 -2 -4 -5"),
        ],
    ),
    problem(
        9,
        "括号序列校验",
        "valid-parentheses-acm",
        "简单",
        ["字符串", "栈"],
        "给定只包含 ()[]{} 六种字符的字符串，判断括号是否按正确顺序闭合。",
        "输入一行字符串 s。",
        "若合法输出 true，否则输出 false。",
        [{"input": "()[]{}\n", "output": "true"}],
        ["0 <= |s| <= 200000"],
        [
            tc("(]\n", "false"),
            tc("([{}])\n", "true"),
            tc("((\n", "false"),
            tc("\n", "true"),
            tc("([)]\n", "false"),
            tc("{[()()]}\n", "true"),
            tc("]\n", "false"),
        ],
    ),
    problem(
        10,
        "合并有序序列",
        "merge-two-sorted-sequences-acm",
        "简单",
        ["链表", "数组", "双指针"],
        "给定两个非降序整数序列，请将它们合并成一个新的非降序序列。",
        "第一行输入整数 n，第二行输入 n 个整数。第三行输入整数 m，第四行输入 m 个整数。长度为 0 时对应行可为空。",
        "输出合并后的序列，整数之间用一个空格分隔；若结果为空，输出空行。",
        [{"input": "3\n1 2 4\n3\n1 3 4\n", "output": "1 1 2 3 4 4"}],
        ["0 <= n, m <= 200000", "输入序列均为非降序"],
        [
            tc("0\n\n3\n0 1 2\n", "0 1 2"),
            tc("3\n-3 -1 2\n2\n-2 4\n", "-3 -2 -1 2 4"),
            tc("0\n\n0\n\n", ""),
            tc("4\n1 1 1 2\n4\n1 2 2 3\n", "1 1 1 1 2 2 2 3"),
            tc("3\n-5 0 0\n4\n-6 -5 1 2\n", "-6 -5 -5 0 0 1 2"),
            tc("1\n10\n0\n\n", "10"),
        ],
    ),
    problem(
        11,
        "生成括号集合",
        "generate-parentheses-acm",
        "中等",
        ["回溯", "字符串"],
        "给定括号对数 n，请生成所有合法括号序列。",
        "输入一个整数 n。",
        "第一行输出合法序列数量 k，随后 k 行按字典序输出每个序列。",
        [
            {
                "input": "3\n",
                "output": "5\n((()))\n(()())\n(())()\n()(())\n()()()",
            }
        ],
        ["1 <= n <= 8"],
        [
            tc("1\n", "1\n()"),
            tc("2\n", "2\n(())\n()()"),
            tc("4\n", "14\n(((())))\n((()()))\n((())())\n((()))()\n(()(()))\n(()()())\n(()())()\n(())(())\n(())()()\n()((()))\n()(()())\n()(())()\n()()(())\n()()()()"),
        ],
    ),
    problem(
        12,
        "旋转数组搜索",
        "search-rotated-array-acm",
        "中等",
        ["数组", "二分"],
        "一个严格升序数组在某个未知位置被旋转。给定旋转后的数组和目标值，请返回目标值下标；若不存在，输出 -1。",
        "第一行输入整数 n。第二行输入 n 个互不相同的整数。第三行输入 target。",
        "输出 target 的 0 基下标；不存在则输出 -1。",
        [{"input": "7\n4 5 6 7 0 1 2\n0\n", "output": "4"}],
        ["1 <= n <= 200000", "数组元素互不相同"],
        [
            tc("7\n4 5 6 7 0 1 2\n3\n", "-1"),
            tc("1\n1\n1\n", "0"),
            tc("5\n3 4 5 1 2\n2\n", "4"),
            tc("5\n1 2 3 4 5\n4\n", "3"),
            tc("5\n5 1 2 3 4\n5\n", "0"),
            tc("5\n2 3 4 5 1\n1\n", "4"),
            tc("1\n1\n0\n", "-1"),
        ],
    ),
    problem(
        13,
        "组合凑数",
        "combination-sum-acm",
        "中等",
        ["回溯", "数组"],
        "给定一组互不相同的正整数和目标值，每个数可以使用多次。请输出所有和为目标值的非降序组合。",
        "第一行输入 n 和 target。第二行输入 n 个候选数。",
        "第一行输出组合数量 k。随后 k 行每行输出一个组合。组合内部非降序，组合整体按字典序升序输出。",
        [{"input": "4 7\n2 3 6 7\n", "output": "2\n2 2 3\n7"}],
        ["1 <= n <= 30", "1 <= candidate[i], target <= 500"],
        [
            tc("3 8\n2 3 5\n", "3\n2 2 2 2\n2 3 3\n3 5"),
            tc("1 3\n2\n", "0"),
            tc("3 4\n1 2 3\n", "4\n1 1 1 1\n1 1 2\n1 3\n2 2"),
            tc("4 7\n7 3 2 6\n", "2\n2 2 3\n7"),
            tc("3 1\n2 3 4\n", "0"),
            tc("4 10\n8 1 4 5\n", "7\n1 1 1 1 1 1 1 1 1 1\n1 1 1 1 1 1 4\n1 1 1 1 1 5\n1 1 4 4\n1 1 8\n1 4 5\n5 5"),
        ],
    ),
    problem(
        14,
        "方阵顺时针旋转",
        "rotate-matrix-acm",
        "中等",
        ["数组", "矩阵"],
        "给定一个 n x n 方阵，请将它顺时针旋转 90 度后输出。",
        "第一行输入整数 n。随后 n 行，每行输入 n 个整数。",
        "输出旋转后的 n 行矩阵，每行 n 个整数，空格分隔。",
        [{"input": "3\n1 2 3\n4 5 6\n7 8 9\n", "output": "7 4 1\n8 5 2\n9 6 3"}],
        ["1 <= n <= 500"],
        [
            tc("1\n5\n", "5"),
            tc("2\n1 2\n3 4\n", "3 1\n4 2"),
            tc("4\n1 2 3 4\n5 6 7 8\n9 10 11 12\n13 14 15 16\n", "13 9 5 1\n14 10 6 2\n15 11 7 3\n16 12 8 4"),
            tc("3\n-1 -2 -3\n-4 -5 -6\n-7 -8 -9\n", "-7 -4 -1\n-8 -5 -2\n-9 -6 -3"),
            tc("2\n0 -1\n2 3\n", "2 0\n3 -1"),
        ],
    ),
    problem(
        15,
        "异位词分组",
        "group-anagrams-acm",
        "中等",
        ["哈希表", "字符串", "排序"],
        "给定若干小写单词，请把字母异位词放入同一组。",
        "第一行输入整数 n。第二行输入 n 个仅包含小写字母的单词。",
        "第一行输出组数。每组内单词按字典序输出；各组按组内第一个单词的字典序输出。",
        [{"input": "6\neat tea tan ate nat bat\n", "output": "3\nate eat tea\nbat\nnat tan"}],
        ["0 <= n <= 20000", "单词总长度 <= 200000"],
        [
            tc("1\na\n", "1\na"),
            tc("4\nabc bca cab dog\n", "2\nabc bca cab\ndog"),
            tc("0\n\n", "0"),
            tc("5\nab ba ab abc cab\n", "2\nab ab ba\nabc cab"),
            tc("3\nlisten silent enlist\n", "1\nenlist listen silent"),
            tc("4\nz z zz zzz\n", "3\nz z\nzz\nzzz"),
        ],
    ),
    problem(
        16,
        "最大连续和",
        "maximum-subarray-acm",
        "简单",
        ["数组", "动态规划"],
        "给定一个整数数组，请找出和最大的非空连续子数组，并输出这个最大和。",
        "第一行输入整数 n。第二行输入 n 个整数。",
        "输出一个整数，表示最大连续和。",
        [{"input": "9\n-2 1 -3 4 -1 2 1 -5 4\n", "output": "6"}],
        ["1 <= n <= 200000", "-10^9 <= nums[i] <= 10^9"],
        [
            tc("1\n1\n", "1"),
            tc("5\n5 4 -1 7 8\n", "23"),
            tc("3\n-3 -2 -5\n", "-2"),
            tc("5\n0 -1 0 -2 0\n", "0"),
            tc("8\n-2 -1 4 -1 -2 1 5 -3\n", "7"),
            tc("4\n1000000000 -1 1000000000 -1\n", "1999999999"),
        ],
    ),
    problem(
        17,
        "跳跃可达",
        "jump-game-acm",
        "中等",
        ["数组", "贪心"],
        "给定数组 nums，nums[i] 表示从位置 i 最远可以向右跳的步数。判断能否从下标 0 到达最后一个下标。",
        "第一行输入整数 n。第二行输入 n 个非负整数。",
        "可以到达输出 true，否则输出 false。",
        [{"input": "5\n2 3 1 1 4\n", "output": "true"}],
        ["1 <= n <= 200000", "0 <= nums[i] <= 10^9"],
        [
            tc("5\n3 2 1 0 4\n", "false"),
            tc("1\n0\n", "true"),
            tc("4\n1 1 0 1\n", "false"),
            tc("3\n2 0 0\n", "true"),
            tc("2\n0 1\n", "false"),
            tc("4\n2 5 0 0\n", "true"),
            tc("4\n1 0 1 0\n", "false"),
        ],
    ),
    problem(
        18,
        "区间合并",
        "merge-intervals-acm",
        "中等",
        ["数组", "排序"],
        "给定若干闭区间，请合并所有有交集的区间。",
        "第一行输入整数 n。随后 n 行，每行输入两个整数 l 和 r。",
        "第一行输出合并后的区间数量 k。随后 k 行按左端点升序输出区间。",
        [{"input": "4\n1 3\n2 6\n8 10\n15 18\n", "output": "3\n1 6\n8 10\n15 18"}],
        ["0 <= n <= 200000", "-10^9 <= l <= r <= 10^9"],
        [
            tc("2\n1 4\n4 5\n", "1\n1 5"),
            tc("0\n", "0"),
            tc("5\n5 7\n1 2\n2 4\n8 9\n6 8\n", "2\n1 4\n5 9"),
            tc("4\n-10 -1\n-5 0\n2 3\n3 3\n", "2\n-10 0\n2 3"),
            tc("1\n5 5\n", "1\n5 5"),
            tc("4\n10 12\n1 2\n3 4\n2 3\n", "2\n1 4\n10 12"),
        ],
    ),
    problem(
        19,
        "二叉树层序遍历",
        "binary-tree-level-order-acm",
        "中等",
        ["二叉树", "队列", "BFS"],
        "给定一棵二叉树的层序表示，请按层输出节点值。空节点使用 # 表示。",
        "第一行输入整数 n，表示层序数组长度。第二行输入 n 个 token，每个 token 为整数或 #。",
        "第一行输出层数 k。随后 k 行从上到下输出每层节点值，同行用空格分隔。",
        [{"input": "7\n3 9 20 # # 15 7\n", "output": "3\n3\n9 20\n15 7"}],
        ["0 <= n <= 200000", "节点值为 32 位有符号整数"],
        [
            tc("0\n\n", "0"),
            tc("3\n1 # 2\n", "2\n1\n2"),
            tc("7\n1 2 3 4 # # 5\n", "3\n1\n2 3\n4 5"),
            tc("1\n42\n", "1\n42"),
            tc("6\n1 2 # 3 # #\n", "3\n1\n2\n3"),
            tc("7\n1 # 2 # # 3 4\n", "3\n1\n2\n3 4"),
        ],
    ),
    problem(
        20,
        "零钱最少枚数",
        "coin-change-acm",
        "中等",
        ["动态规划", "数组"],
        "给定若干硬币面额和一个金额，请计算凑出该金额所需的最少硬币数。每种硬币可以使用无限次；若无法凑出，输出 -1。",
        "第一行输入 n 和 amount。第二行输入 n 个正整数表示硬币面额。",
        "输出一个整数，表示最少硬币数或 -1。",
        [{"input": "3 11\n1 2 5\n", "output": "3"}],
        ["1 <= n <= 100", "0 <= amount <= 100000", "1 <= coin[i] <= 100000"],
        [
            tc("1 3\n2\n", "-1"),
            tc("3 0\n1 2 5\n", "0"),
            tc("4 27\n2 5 10 1\n", "4"),
            tc("3 6\n1 3 4\n", "2"),
            tc("2 7\n4 6\n", "-1"),
            tc("3 6\n1 3 3\n", "2"),
        ],
    ),
]


PLACEHOLDER_SPECS = [
    ("接雨水", "trapping-rain-water-acm", "困难", ["数组", "双指针", "栈"]),
    ("最小覆盖窗口", "minimum-window-substring-acm", "困难", ["字符串", "滑动窗口", "哈希表"]),
    ("有效字母异位词", "valid-anagram-acm", "简单", ["字符串", "哈希表"]),
    ("最长连续序列", "longest-consecutive-sequence-acm", "中等", ["数组", "哈希表"]),
    ("移动零", "move-zeroes-acm", "简单", ["数组", "双指针"]),
    ("无重叠区间", "non-overlapping-intervals-acm", "中等", ["贪心", "排序"]),
    ("乘积最大子数组", "maximum-product-subarray-acm", "中等", ["动态规划", "数组"]),
    ("打家劫舍", "house-robber-acm", "中等", ["动态规划"]),
    ("爬楼梯", "climbing-stairs-acm", "简单", ["动态规划"]),
    ("不同路径", "unique-paths-acm", "中等", ["动态规划", "数学"]),
    ("最小路径和", "minimum-path-sum-acm", "中等", ["动态规划", "矩阵"]),
    ("编辑距离", "edit-distance-acm", "困难", ["动态规划", "字符串"]),
    ("最长递增子序列", "longest-increasing-subsequence-acm", "中等", ["动态规划", "二分"]),
    ("分割等和子集", "partition-equal-subset-sum-acm", "中等", ["动态规划", "背包"]),
    ("目标和", "target-sum-acm", "中等", ["动态规划", "回溯"]),
    ("单词拆分", "word-break-acm", "中等", ["动态规划", "字符串"]),
    ("岛屿数量", "number-of-islands-acm", "中等", ["图", "DFS", "BFS"]),
    ("腐烂橘子", "rotting-oranges-acm", "中等", ["图", "BFS"]),
    ("课程表", "course-schedule-acm", "中等", ["图", "拓扑排序"]),
    ("实现 Trie", "implement-trie-acm", "中等", ["设计", "字典树"]),
    ("前 K 个高频元素", "top-k-frequent-elements-acm", "中等", ["堆", "哈希表"]),
    ("数据流中位数", "find-median-from-data-stream-acm", "困难", ["堆", "设计"]),
    ("滑动窗口最大值", "sliding-window-maximum-acm", "困难", ["队列", "堆", "滑动窗口"]),
    ("数组中的第 K 个最大元素", "kth-largest-element-acm", "中等", ["堆", "快速选择"]),
    ("合并 K 个有序链表", "merge-k-sorted-lists-acm", "困难", ["链表", "堆"]),
    ("反转链表", "reverse-linked-list-acm", "简单", ["链表"]),
    ("链表环入口", "linked-list-cycle-entry-acm", "中等", ["链表", "双指针"]),
    ("相交链表", "intersection-of-two-linked-lists-acm", "简单", ["链表", "双指针"]),
    ("回文链表", "palindrome-linked-list-acm", "简单", ["链表", "双指针"]),
    ("两两交换链表节点", "swap-nodes-in-pairs-acm", "中等", ["链表"]),
    ("K 个一组翻转链表", "reverse-nodes-in-k-group-acm", "困难", ["链表"]),
    ("二叉树最大深度", "maximum-depth-of-binary-tree-acm", "简单", ["二叉树", "DFS"]),
    ("翻转二叉树", "invert-binary-tree-acm", "简单", ["二叉树", "DFS"]),
    ("对称二叉树", "symmetric-tree-acm", "简单", ["二叉树", "递归"]),
    ("二叉树直径", "diameter-of-binary-tree-acm", "简单", ["二叉树", "DFS"]),
    ("路径总和 III", "path-sum-iii-acm", "中等", ["二叉树", "前缀和"]),
    ("二叉树最近公共祖先", "lowest-common-ancestor-acm", "中等", ["二叉树"]),
    ("二叉树右视图", "binary-tree-right-side-view-acm", "中等", ["二叉树", "BFS"]),
    ("验证二叉搜索树", "validate-binary-search-tree-acm", "中等", ["二叉搜索树", "DFS"]),
    ("二叉搜索树第 K 小", "kth-smallest-in-bst-acm", "中等", ["二叉搜索树", "中序遍历"]),
    ("二叉树展开为链表", "flatten-binary-tree-acm", "中等", ["二叉树", "链表"]),
    ("从前序与中序构造二叉树", "construct-tree-preorder-inorder-acm", "中等", ["二叉树", "递归"]),
    ("路径最大和", "binary-tree-maximum-path-sum-acm", "困难", ["二叉树", "动态规划"]),
    ("全排列", "permutations-acm", "中等", ["回溯"]),
    ("子集", "subsets-acm", "中等", ["回溯"]),
    ("电话号码字母组合", "letter-combinations-phone-acm", "中等", ["回溯", "字符串"]),
    ("单词搜索", "word-search-acm", "中等", ["回溯", "矩阵"]),
    ("N 皇后", "n-queens-acm", "困难", ["回溯"]),
    ("搜索二维矩阵", "search-2d-matrix-acm", "中等", ["数组", "二分"]),
    ("寻找峰值", "find-peak-element-acm", "中等", ["二分"]),
    ("寻找旋转数组最小值", "find-minimum-rotated-array-acm", "中等", ["二分"]),
    ("单词接龙", "word-ladder-acm", "困难", ["图", "BFS"]),
    ("除法求值", "evaluate-division-acm", "中等", ["图", "并查集"]),
    ("并查集连通分量", "connected-components-union-find-acm", "中等", ["图", "并查集"]),
    ("最长公共子序列", "longest-common-subsequence-acm", "中等", ["动态规划", "字符串"]),
    ("买卖股票最佳时机", "best-time-buy-sell-stock-acm", "简单", ["数组", "动态规划"]),
    ("买卖股票含冷冻期", "stock-with-cooldown-acm", "中等", ["动态规划"]),
    ("完全平方数", "perfect-squares-acm", "中等", ["动态规划", "BFS"]),
    ("每日温度", "daily-temperatures-acm", "中等", ["栈", "数组"]),
    ("柱状图最大矩形", "largest-rectangle-histogram-acm", "困难", ["栈"]),
    ("最小栈", "min-stack-acm", "中等", ["栈", "设计"]),
    ("字符串解码", "decode-string-acm", "中等", ["栈", "字符串"]),
    ("LRU 缓存", "lru-cache-acm", "中等", ["设计", "哈希表", "双向链表"]),
    ("数组全排列去重", "permutations-ii-acm", "中等", ["回溯", "排序"]),
    ("缺失的第一个正数", "first-missing-positive-acm", "困难", ["数组", "原地哈希"]),
    ("颜色分类", "sort-colors-acm", "中等", ["数组", "双指针"]),
    ("下一个排列", "next-permutation-acm", "中等", ["数组", "双指针"]),
    ("只出现一次的数字", "single-number-acm", "简单", ["位运算"]),
    ("多数元素", "majority-element-acm", "简单", ["数组", "投票算法"]),
    ("旋转数组", "rotate-array-acm", "中等", ["数组"]),
    ("寻找重复数", "find-duplicate-number-acm", "中等", ["数组", "双指针"]),
    ("生命游戏", "game-of-life-acm", "中等", ["矩阵", "模拟"]),
    ("矩阵置零", "set-matrix-zeroes-acm", "中等", ["矩阵"]),
    ("螺旋矩阵", "spiral-matrix-acm", "中等", ["矩阵", "模拟"]),
    ("搜索插入位置", "search-insert-position-acm", "简单", ["二分"]),
    ("合并两个有序数组", "merge-sorted-array-acm", "简单", ["数组", "双指针"]),
    ("最接近的三数之和", "three-sum-closest-acm", "中等", ["数组", "双指针"]),
    ("四数之和", "four-sum-acm", "中等", ["数组", "双指针"]),
    ("快乐数", "happy-number-acm", "简单", ["哈希表", "双指针"]),
    ("罗马数字转整数", "roman-to-integer-acm", "简单", ["字符串", "哈希表"]),
]


def build_placeholder_problem(index, spec):
    title, slug, difficulty, tags = spec
    topic = "、".join(tags)
    return {
        "id": index,
        "title": title,
        "slug": slug,
        "difficulty": difficulty,
        "tags": tags,
        "description": f"{title} 是 Hot100 的 {topic} 方向练习。当前版本已预留 ACM 模式题面结构，完整隐藏测试将在后续增量补齐。",
        "input_format": "输入格式占位：本题将采用完整程序从 stdin 读取数据，不提供函数签名。",
        "output_format": "输出格式占位：程序需向 stdout 输出最终答案，末尾换行不影响判定。",
        "samples": [
            {
                "input": "",
                "output": "",
                "explanation": "该题暂未开放判题，仅作为 Hot100 结构占位。",
            }
        ],
        "constraints": ["题目元数据已入库", "隐藏测试待补齐后即可开放判题"],
        "starter_code": deepcopy(BASE_STARTER_CODE),
        "test_cases": [],
    }


def get_hot100_problems():
    problems = list(JUDGABLE_PROBLEMS)
    next_id = len(problems) + 1
    for offset, spec in enumerate(PLACEHOLDER_SPECS[: max(0, 100 - len(problems))]):
        problems.append(build_placeholder_problem(next_id + offset, spec))
    return problems
