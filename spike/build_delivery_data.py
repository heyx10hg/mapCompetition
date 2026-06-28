# -*- coding: utf-8 -*-
"""
Build clean handoff datasets for the GeoScene story.

This script leaves the exploratory `out/` folder untouched and writes a clean,
team-facing package to `out_delivery/`.
"""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

import s03_clean_classify as s03

HERE = Path(__file__).parent


def is_synthetic_sample(record: dict) -> bool:
    """Return True for generated sample rows mixed into early raw exports."""
    address = str(record.get("address") or "")
    return "某某路" in address


def filter_synthetic_samples(records):
    kept, removed = [], []
    for record in records:
        if is_synthetic_sample(record):
            removed.append(record)
        else:
            kept.append(record)
    return kept, removed


def write_rows_csv(rows, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("no rows to write")
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_geojson(rows, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
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
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


def write_rejected_samples(rows, path: Path):
    if not rows:
        return None
    fields = sorted({key for row in rows for key in row.keys()})
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_penetration(rows, all_food_path: Path, out_dir: Path):
    return s03.penetration(rows, all_food_path, out_dir, districts=s03.GUANGZHOU_DISTRICTS)


def write_cleaning_report(stats, rows, removed_samples, out_dir: Path):
    labels = Counter(r["label"] for r in rows)
    sources = Counter(r["match_source"] for r in rows)
    report = {
        "scope": "广州11区",
        "coordinate_system": "WGS-84 unless --keep-gcj02 is passed",
        "removed_synthetic_samples": len(removed_samples),
        "clean_rows": len(rows),
        "contains_chicken_rows": sum(1 for r in rows if r["label"] != "non_chicken"),
        "signboard_rows": sum(1 for r in rows if r["match_source"] == "招牌"),
        "recommended_dish_rows": sum(1 for r in rows if r["match_source"] == "推荐菜"),
        "label_counts": dict(labels),
        "match_source_counts": dict(sources),
        "cleaning_stats": dict(stats),
        "metric_warning": (
            "These metrics describe visible restaurant-space penetration, not "
            "actual household or order-level chicken consumption."
        ),
    }
    path = out_dir / "cleaning_report.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_data_dictionary(out_dir: Path):
    rows = [
        ("id", "高德POI id", "用于去重和回溯原始记录"),
        ("name", "店铺原名", "GeoScene 弹窗标题"),
        ("name_norm", "规范化店名", "去括号和空白后用于去重"),
        ("label", "鸡肴分类", "traditional / modern / other_chicken / non_chicken"),
        ("match_source", "命中来源", "招牌=店名命中；推荐菜=tag字段命中；空=未命中鸡菜"),
        ("district", "广州行政区", "用于分区统计和专题图关联"),
        ("address", "地址", "用于人工核验和弹窗展示"),
        ("typecode", "高德类目码", "05开头为餐饮服务"),
        ("type", "高德类目名称", "辅助识别餐饮业态"),
        ("tag", "高德特色/推荐菜字段", "宽口径识别鸡菜的主要补充来源"),
        ("lng", "经度", "默认输出 WGS-84"),
        ("lat", "纬度", "默认输出 WGS-84"),
        ("signboard_pct", "招牌口径渗透率", "店名含鸡POI / 全量餐饮POI，主指标"),
        ("serves_pct", "宽口径渗透率", "店名或推荐菜含鸡POI / 全量餐饮POI，辅助指标"),
    ]
    path = out_dir / "data_dictionary.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["field", "meaning", "usage"])
        writer.writerows(rows)
    return path


def write_handoff_readme(out_dir: Path):
    text = """# 广州鸡类餐饮POI交付包

## 文件
- `poi_clean.csv`: 清洗后的点表。
- `poi_clean.geojson`: 上传 GeoScene Online 的主点图层。
- `penetration_by_district.csv`: 11区渗透率专题图数据。
- `data_dictionary.csv`: 字段说明。
- `cleaning_report.json`: 清洗统计和口径提醒。
- `rejected_synthetic_samples.csv`: 被剔除的合成样例记录。
- `background_context_sources.csv`: 官方统计背景源表。硬统计只引用 confidence=高 的行；地方鸡文化新闻/行业报告行目前是待补佐证。

## 口径
- 招牌口径：店名命中鸡类词，代表“专门鸡店”，适合作为主指标。
- 宽口径：店名或推荐菜命中鸡类词，代表“能吃到鸡”，用于支撑“无处不在”的叙事。
- 这些指标描述餐饮空间可见度，不等于居民实际消费量或订单量。
"""
    path = out_dir / "README.md"
    path.write_text(text, encoding="utf-8")
    return path


def build_delivery(input_path: Path, all_food_path: Path, out_dir: Path, keep_gcj02=False):
    records = list(s03.load_jsonl(input_path))
    records, removed = filter_synthetic_samples(records)
    rows, stats = s03.clean(
        records,
        keep_gcj02=keep_gcj02,
        districts=s03.GUANGZHOU_DISTRICTS,
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "poi_csv": write_rows_csv(rows, out_dir / "poi_clean.csv"),
        "poi_geojson": write_geojson(rows, out_dir / "poi_clean.geojson"),
        "penetration": write_penetration(rows, all_food_path, out_dir),
        "rejected_samples": write_rejected_samples(removed, out_dir / "rejected_synthetic_samples.csv"),
        "dictionary": write_data_dictionary(out_dir),
        "report": write_cleaning_report(stats, rows, removed, out_dir),
        "readme": write_handoff_readme(out_dir),
    }
    return paths


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(HERE / "data" / "poi_raw_chicken_keyword.jsonl"))
    parser.add_argument("--all-food", default=str(HERE / "data" / "poi_raw_all_food.jsonl"))
    parser.add_argument("--out-dir", default=str(HERE / "out_delivery"))
    parser.add_argument("--keep-gcj02", action="store_true", help="使用高德底图时保留 GCJ-02")
    args = parser.parse_args()

    paths = build_delivery(
        input_path=Path(args.input),
        all_food_path=Path(args.all_food),
        out_dir=Path(args.out_dir),
        keep_gcj02=args.keep_gcj02,
    )
    for name, path in paths.items():
        if path:
            print(f"{name}: {path}")


if __name__ == "__main__":
    main()
