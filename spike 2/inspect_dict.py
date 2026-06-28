# -*- coding: utf-8 -*-
"""
inspect_dict.py — 词典校准辅助工具

作用：把 s03 输出的 csv 里"待归类"的店名拆开，统计高频词模式，
让你照着列表往 s03 的 TRADITIONAL / MODERN 词典里收词，而不用逐条肉眼扫。

用法（在 spike 目录下，确保已经跑过一次 s03 生成了 out/poi_clean.csv）：
    python inspect_dict.py                  # 默认看 other_chicken 桶
    python inspect_dict.py non_chicken      # 看被判定为"非鸡"的桶(查肯德基类漏网)
    python inspect_dict.py modern           # 看任意已分类桶，核对有没有分错

输出：该桶内"鸡"字前后2字的高频搭配 + 整店名抽样，按出现次数排序。
"""
import csv
import re
import sys
from collections import Counter
from pathlib import Path

CSV = Path(__file__).parent / "out" / "poi_clean.csv"


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "other_chicken"
    if not CSV.exists():
        sys.exit(f"找不到 {CSV}\n请先运行: python s03_clean_classify.py --input data/poi_real_chicken.jsonl")

    names = []
    with open(CSV, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r["label"] == target:
                names.append(r["name_norm"])

    if not names:
        print(f"桶 [{target}] 里没有记录。可选桶名："
              "traditional / modern / other_chicken / non_chicken")
        return

    # 1) 含"鸡"的搭配模式（鸡字前后各取2字）
    patterns = Counter()
    for n in names:
        for m in re.finditer(r".{0,2}鸡.{0,2}", n):
            patterns[m.group()] += 1

    print(f"== 桶 [{target}] 共 {len(names)} 条 ==\n")
    print("【含「鸡」高频搭配 Top30】照此往 s03 词典收词：")
    for w, c in patterns.most_common(30):
        print(f"  {c:3d}  {w}")

    # 2) 店名抽样，帮你判断整体形态
    print(f"\n【店名抽样 前40条】：")
    for n in names[:40]:
        print(f"  {n}")

    print(f"\n提示：判定好归属后，打开 s03_clean_classify.py，"
          f"把词加进 TRADITIONAL（传统粤式）或 MODERN（现代外来）列表，"
          f"存盘后重跑 s03，再用本工具看桶是否缩小。")


if __name__ == "__main__":
    main()
