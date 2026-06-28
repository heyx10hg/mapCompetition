# -*- coding: utf-8 -*-
"""
tag_penetration.py — 菜单渗透率统计（L2 指标，整条数据方案的核心产出）

定位：这是"鸡无处不在"这个论点的直接证据。它统计的不是店名含鸡，而是
      高德 tag 字段(特色菜/推荐菜)含传统鸡肴的店占全部餐饮的比例——
      也就是连茶餐厅、酒楼这种招牌不含鸡、但菜单卖鸡的店都算进来。
      因此必须跑在 all_food（全量餐饮）数据集上，不是 chicken_keyword 上。

用法（需要先用 s01 --mode all_food 采集到全量餐饮数据）：
    python tag_penetration.py --input data/poi_raw_all_food.jsonl

输出：
    控制台打印整体 + 分区渗透率
    out/tag_penetration.csv

口径说明（写进图说时照抄，避免误读）：
    分母 = 该区全部餐饮 POI（typecode 05 开头）
    分子 = 该区 tag 含传统鸡肴关键词的餐饮 POI
    渗透率 = 分子/分母，反映"卖传统鸡肴的店在餐饮业态中的渗透程度"
"""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent

# 只统计"传统粤式鸡肴"渗透——这是文化论点要的。现代炸鸡不计入，
# 因为论点是"传统鸡文化存续"，不是"鸡这个食材常见"。
TRADITIONAL_DISH = [
    "白切鸡", "白斩鸡", "盐焗鸡", "豉油鸡", "手撕鸡", "沙姜鸡", "葱油鸡",
    "太爷鸡", "啫啫鸡", "豆酱鸡", "卤水鸡", "猪肚鸡", "清远鸡", "走地鸡",
    "湛江鸡", "文昌鸡", "椰子鸡", "葱油手撕鸡", "脆皮鸡",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=str(HERE / "data" / "poi_raw_all_food.jsonl"))
    args = ap.parse_args()
    src = Path(args.input)
    if not src.exists():
        raise SystemExit(f"找不到 {src}\n请先运行: python s01_fetch_poi_amap.py --mode all_food")

    denom = Counter()   # 分区全部餐饮
    numer = Counter()   # 分区 tag 含传统鸡肴
    tag_present = tag_total = 0

    with open(src, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            p = json.loads(line)
            if not str(p.get("typecode", "")).startswith("05"):
                continue
            d = p.get("adname") or "未知"
            denom[d] += 1
            tag_total += 1
            tag = p.get("tag") if isinstance(p.get("tag"), str) else ""
            if tag.strip():
                tag_present += 1
            text = (p.get("name", "") or "") + "|" + tag
            if any(w in text for w in TRADITIONAL_DISH):
                numer[d] += 1

    out = HERE / "out"
    out.mkdir(exist_ok=True)
    path = out / "tag_penetration.csv"
    total_d = sum(denom.values())
    total_n = sum(numer.values())

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["district", "traditional_chicken_poi", "all_food_poi", "penetration_pct"])
        w.writerow(["__全市__", total_n, total_d,
                    round(100 * total_n / total_d, 2) if total_d else ""])
        for d, total in sorted(denom.items(), key=lambda x: -x[1]):
            n = numer.get(d, 0)
            w.writerow([d, n, total, round(100 * n / total, 2) if total else ""])

    print(f"tag 字段覆盖率: {tag_present}/{tag_total} = "
          f"{100*tag_present/tag_total:.1f}%  (低于40%则结论需谨慎)")
    print(f"\n全市传统鸡肴渗透率: {total_n}/{total_d} = "
          f"{100*total_n/total_d:.2f}%\n")
    print("分区渗透率（按餐饮总数排序）:")
    for d, total in sorted(denom.items(), key=lambda x: -x[1]):
        n = numer.get(d, 0)
        pct = 100 * n / total if total else 0
        bar = "█" * int(pct)
        print(f"  {d:8s} {pct:5.1f}%  {bar}  ({n}/{total})")
    print(f"\n输出 -> {path}")


if __name__ == "__main__":
    main()
