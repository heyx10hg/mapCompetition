# -*- coding: utf-8 -*-
"""
s03_clean_classify.py — POI 清洗 + 鸡肴分类 spike

输入:  data/poi_raw_*.jsonl   (s01 的原始输出，或本仓库自带的合成样例)
输出:  out/poi_clean.csv      (清洗后表格，含分类标签)
       out/poi_clean.geojson  (WGS-84，可直接上传 GeoScene Online 作 Web Map 图层)
       out/penetration_by_district.csv  (若同时有全量餐饮数据，输出分区渗透率)

清洗规则（每条都对应一个真实的脏数据形态，见行内注释）:
  R1 去重        同一店铺会因"分店/别名/多类目"在结果中重复出现 -> 按高德 id 去重，
                 再按 (规范化名称, 坐标网格~50m) 二次去重兜底。
  R2 假阳性剔除  名称含"鸡"不等于卖鸡: 田鸡(青蛙)/鸡尾酒/鸡蛋仔(无鸡肉)/鸡精 等。
  R3 类目过滤    只保留餐饮大类(typecode 05 开头)，去掉"XX鸡精商行"这类零售。
  R4 名称规范化  去括号注记("(天河店)")、全半角统一、去空白 -> 用于去重与连锁识别。
  R5 坐标处理    GCJ-02 -> WGS-84（见 s02 的说明；若用高德底图则加 --keep-gcj02 跳过）。
  R6 分类打标    传统粤式 / 现代外来 / 其他含鸡，词典见下，这是后续所有图层的基础字段。
"""
import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from s02_coord import gcj02_to_wgs84

HERE = Path(__file__).parent

# ---------- 分类词典（spike 版，正式版应扩到 100+ 词并人工抽检校准） ----------
TRADITIONAL = [  # 传统粤式（广府/客家/潮汕）
    "白切鸡", "白斩鸡", "盐焗鸡", "豉油鸡", "手撕鸡", "沙姜鸡", "葱油鸡",
    "太爷鸡", "啫啫鸡", "豆酱鸡", "卤水鸡", "猪肚鸡", "隔水蒸鸡", "桶子鸡",
    "清远鸡", "清远麻鸡", "胡须鸡", "杏花鸡", "怀乡鸡", "湛江鸡", "走地鸡", "文昌鸡",
]
MODERN = [  # 现代/外来体系
    "炸鸡", "韩式炸鸡", "鸡排", "鸡米花", "黄焖鸡", "鸡公煲", "大盘鸡",
    "辣子鸡", "口水鸡", "三杯鸡", "椰子鸡", "烤鸡", "新奥尔良", "脆皮鸡",
]
FALSE_POSITIVE = ["田鸡", "鸡尾酒", "鸡蛋仔", "鸡蛋灌饼", "鸡精", "鸡毛店"]  # 含"鸡"但与鸡肉无关
GENERIC = ["鸡"]  # 兜底：含鸡但词典未命中 -> "其他含鸡"

_PAREN = re.compile(r"[（(].*?[）)]")


def norm_name(name: str) -> str:
    """R4: 去括号注记/空白/全角 -> 规范化名称"""
    s = _PAREN.sub("", name or "")
    s = s.replace("　", "").replace(" ", "")
    return s.strip()


def classify(name: str) -> str:
    """R2+R6: 返回 traditional / modern / other_chicken / excluded / non_chicken"""
    n = name or ""
    if any(w in n for w in FALSE_POSITIVE):
        return "excluded"
    if any(w in n for w in TRADITIONAL):
        return "traditional"
    if any(w in n for w in MODERN):
        return "modern"
    if any(w in n for w in GENERIC):
        return "other_chicken"
    return "non_chicken"


def load_jsonl(path: Path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def parse_loc(p):
    try:
        lng, lat = map(float, p["location"].split(","))
        return lng, lat
    except Exception:
        return None


def clean(records, keep_gcj02=False):
    seen_id, seen_namegrid = set(), set()
    rows, stats = [], Counter()
    for p in records:
        stats["raw"] += 1
        pid = p.get("id") or ""
        if pid and pid in seen_id:                      # R1a id 去重
            stats["dup_id"] += 1
            continue
        seen_id.add(pid)

        typecode = str(p.get("typecode", ""))
        if not typecode.startswith("05"):               # R3 非餐饮
            stats["non_food"] += 1
            continue

        loc = parse_loc(p)
        if loc is None:                                 # 坐标缺失/畸形
            stats["bad_loc"] += 1
            continue
        lng_g, lat_g = loc

        name = p.get("name", "")
        nname = norm_name(name)
        grid = (nname, round(lng_g, 4), round(lat_g, 4))  # R1b 同名同址(~50m)兜底去重
        if grid in seen_namegrid:
            stats["dup_namegrid"] += 1
            continue
        seen_namegrid.add(grid)

        # tag 字段：extensions=all 时高德对部分餐饮POI返回的"特色内容"(近似推荐菜)。
        # 店名不含鸡但推荐菜含白切鸡的店（如普通茶餐厅），靠它才能被识别——这是
        # "菜单渗透率"自动化近似的关键来源。覆盖率需在真实数据上实测。
        tag = p.get("tag") if isinstance(p.get("tag"), str) else ""
        label = classify(nname + "|" + tag)             # R2+R6（店名+推荐菜联合判定）
        if label == "excluded":
            stats["false_positive"] += 1
            continue

        lng, lat = (lng_g, lat_g) if keep_gcj02 else gcj02_to_wgs84(lng_g, lat_g)  # R5
        rows.append({
            "id": pid, "name": name, "name_norm": nname,
            "label": label,
            "district": p.get("adname", ""),
            "address": p.get("address", "") if isinstance(p.get("address"), str) else "",
            "typecode": typecode, "type": p.get("type", ""),
            "tag": tag,
            "lng": round(lng, 6), "lat": round(lat, 6),
        })
        stats[label] += 1
    return rows, stats


def write_outputs(rows, out_dir: Path):
    out_dir.mkdir(exist_ok=True)
    csv_path = out_dir / "poi_clean.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:  # BOM: Excel直接打开不乱码
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    gj = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [r["lng"], r["lat"]]},
                "properties": {k: v for k, v in r.items() if k not in ("lng", "lat")},
            }
            for r in rows
        ],
    }
    gj_path = out_dir / "poi_clean.geojson"
    gj_path.write_text(json.dumps(gj, ensure_ascii=False), encoding="utf-8")
    return csv_path, gj_path


def penetration(chicken_rows, all_food_path: Path, out_dir: Path):
    """分区"含鸡POI渗透率" = 区内含鸡餐饮POI数 / 区内全量餐饮POI数。
    注意：这是 POI 口径的渗透率（招牌含鸡），不是菜单口径，两者要在文案中区分。"""
    denom = Counter()
    for p in load_jsonl(all_food_path):
        if str(p.get("typecode", "")).startswith("05"):
            denom[p.get("adname", "未知")] += 1
    numer = Counter(r["district"] for r in chicken_rows if r["label"] != "non_chicken")
    path = out_dir / "penetration_by_district.csv"
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["district", "chicken_poi", "all_food_poi", "penetration_pct"])
        for d, total in sorted(denom.items(), key=lambda x: -x[1]):
            c = numer.get(d, 0)
            w.writerow([d, c, total, round(100 * c / total, 2) if total else ""])
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=str(HERE / "data" / "poi_raw_chicken_keyword.jsonl"))
    ap.add_argument("--all-food", default=None, help="全量餐饮jsonl路径，提供则计算分区渗透率")
    ap.add_argument("--keep-gcj02", action="store_true", help="底图为高德时使用，跳过纠偏")
    args = ap.parse_args()

    src = Path(args.input)
    if not src.exists():
        sys.exit(f"找不到输入 {src}，请先跑 s01 或使用 data/ 下的样例")

    rows, stats = clean(load_jsonl(src), keep_gcj02=args.keep_gcj02)
    if not rows:
        sys.exit("清洗后无数据")
    csv_path, gj_path = write_outputs(rows, HERE / "out")

    print("== 清洗统计 ==")
    for k in ["raw", "dup_id", "dup_namegrid", "non_food", "bad_loc",
              "false_positive", "traditional", "modern", "other_chicken", "non_chicken"]:
        print(f"  {k:15s}: {stats.get(k, 0)}")
    print(f"输出: {csv_path}\n      {gj_path}")

    if args.all_food and Path(args.all_food).exists():
        p = penetration(rows, Path(args.all_food), HERE / "out")
        print(f"      {p}")


if __name__ == "__main__":
    main()
