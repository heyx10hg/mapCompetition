# -*- coding: utf-8 -*-
"""
s01_fetch_poi_amap.py — 高德 POI 抓取 spike（多边形搜索 + 四叉树递归切分）

要解决的技术难点（这是本 spike 的核心验证目标）：
  1. 高德"关键字搜索"对单次查询的可返回总量有硬上限（实践中约 900 条，
     翻页到后面会返回空页）。广州全市"鸡"相关餐饮远超此数，直接按城市搜会严重漏采。
     解法：改用"多边形搜索"，先查一个矩形内的 count，若逼近上限就把矩形一分为四，
     递归下去，直到每个格子的结果数安全为止——四叉树切分。
  2. 配额是本项目头号约束！搜索类接口（多边形/关键字/周边/ID查询）个人认证
     开发者【日配额仅100次】，企业认证1000次/天，与其它基础服务(5000/天)不在一个量级。
     解法：① types=050000 面查询一次采集多次复用；② 限速；③ 断点续采，
     配额耗尽明天接着跑；④ 多人多key分片 / 申请企业认证额度。
  3. 返回坐标是 GCJ-02，入库时原样保存，坐标转换留到清洗阶段统一做（s03）。

用法：
  export AMAP_KEY=你的key
  python s01_fetch_poi_amap.py --mode all_food          # 抓广州全量餐饮POI（量大，建议企业key或分天跑）
  python s01_fetch_poi_amap.py --mode chicken_keyword   # 按"鸡"关键词抓（量小，个人key可行）
  python s01_fetch_poi_amap.py --bbox 113.20,23.05,113.40,23.20   # 只抓指定矩形（试跑用）
  python s01_fetch_poi_amap.py --mode all_food --clip-gz --keys k1,k2,k3  # 多key轮换，配额耗尽自动切换续采

输出：
  data/poi_raw_<mode>.jsonl   每行一个高德原始 POI JSON（保留原始字段，清洗在 s03）
  data/poi_done_<mode>.txt    已完成格子记录（断点续采）
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

API = "https://restapi.amap.com/v3/place/polygon"
DISTRICT_API = "https://restapi.amap.com/v3/config/district"   # 行政区域查询（取市界）
PAGE_SIZE = 25          # v3 单页上限
SAFE_COUNT = 180        # 单格子结果数超过它就切分（硬上限~200，留余量）
MAX_DEPTH = 10          # 递归保险丝（阈值降到180后需更深切分）
QPS_SLEEP = 0.35        # 个人key并发很低，宁慢勿封

# 广州市外接矩形（GCJ-02，略放大；正式采集可换成市界多边形逐区跑）
GUANGZHOU_BBOX = (112.95, 22.55, 114.05, 23.95)  # lng_min, lat_min, lng_max, lat_max

DATA_DIR = Path(__file__).parent / "data"
BOUNDARY_PATH = DATA_DIR / "gz_boundary.json"     # 市界缓存（GCJ-02），只拉一次


class Quota(Exception):
    pass


def _request(params: dict) -> dict:
    net_fail = 0
    while True:                       # 网络错误无限重试：断网/关机/睡眠后能自动恢复
        try:
            r = requests.get(API, params=params, timeout=15)
            j = r.json()
        except Exception as e:
            net_fail += 1
            wait = min(2 ** min(net_fail, 6), 60)   # 退避，最长等60秒一轮
            print(f"  ! 网络异常(第{net_fail}次)，{wait}s后重试；若已断网会一直等待恢复: "
                  f"{type(e).__name__}", file=sys.stderr)
            time.sleep(wait)
            continue
        net_fail = 0
        status, info = j.get("status"), j.get("info", "")
        if status == "1":
            return j
        # 常见错误码：CUQPS_HAS_EXCEEDED_THE_LIMIT(QPS超限) / DAILY_QUERY_OVER_LIMIT(配额尽)
        if "QPS" in info.upper():
            time.sleep(1.5)
            continue
        if "LIMIT" in info.upper() or "QUOTA" in info.upper():
            raise Quota(f"配额耗尽: {info}")
        raise RuntimeError(f"API错误: {info} ({j.get('infocode')})")


def query_cell(key: str, bbox, keywords: str, types: str, page: int = 1) -> dict:
    lng1, lat1, lng2, lat2 = bbox
    params = {
        "key": key,
        # polygon 参数：左上|右下（高德要求经度在前）
        "polygon": f"{lng1},{lat2}|{lng2},{lat1}",
        "offset": PAGE_SIZE,
        "page": page,
        "extensions": "all",   # 带 biz_ext（评分/人均），对后续分析有用
    }
    if keywords:
        params["keywords"] = keywords
    if types:
        params["types"] = types
    time.sleep(QPS_SLEEP)
    return _request(params)


# ---------------- 广州市界预剪枝（GCJ-02，与采集坐标系一致，无需纠偏） ----------------
def load_gz_boundary(key: str):
    """取广州市界多边形，缓存到本地只拉一次。返回 rings: [[(lng,lat),...], ...]"""
    if BOUNDARY_PATH.exists():
        return json.loads(BOUNDARY_PATH.read_text(encoding="utf-8"))
    j = requests.get(DISTRICT_API, params={
        "key": key, "keywords": "广州市", "subdistrict": 0, "extensions": "all",
    }, timeout=15).json()
    if j.get("status") != "1" or not j.get("districts"):
        raise RuntimeError(f"获取广州市界失败: {j.get('info')} ({j.get('infocode')})")
    polyline = j["districts"][0].get("polyline", "")
    if not polyline:
        raise RuntimeError("市界 polyline 为空（该接口偶发，重试即可）")
    rings = []
    for ring_str in polyline.split("|"):          # 南沙等岛屿是独立环，用 | 分隔
        ring = [tuple(map(float, pt.split(",")))
                for pt in ring_str.split(";") if "," in pt]
        if len(ring) >= 3:
            rings.append(ring)
    DATA_DIR.mkdir(exist_ok=True)
    BOUNDARY_PATH.write_text(json.dumps(rings, ensure_ascii=False), encoding="utf-8")
    print(f"已缓存广州市界: {len(rings)} 环 / {sum(len(r) for r in rings)} 点 -> {BOUNDARY_PATH}")
    return rings


def _point_in_ring(x, y, ring) -> bool:
    """射线法：点(x=lng,y=lat)是否在单环内"""
    inside, n, j = False, len(ring), len(ring) - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def point_in_gz(x, y, rings) -> bool:
    return any(_point_in_ring(x, y, r) for r in rings)


def cell_in_gz(bbox, rings, samples: int = 5) -> bool:
    """保守判断格子是否与市界相交（宁多采不漏采）：
    ① 5x5 采样点任一落在界内 -> 相交；② 任一界点落在格内（防大格子切到市界一角时漏判）。"""
    lng1, lat1, lng2, lat2 = bbox
    for i in range(samples):
        x = lng1 + (lng2 - lng1) * i / (samples - 1)
        for k in range(samples):
            y = lat1 + (lat2 - lat1) * k / (samples - 1)
            if point_in_gz(x, y, rings):
                return True
    for r in rings:
        for px, py in r:
            if lng1 <= px <= lng2 and lat1 <= py <= lat2:
                return True
    return False


def harvest(key: str, bbox, keywords: str, types: str,
            out_f, done: set, done_f, depth: int = 0, rings=None):
    """四叉树递归采集一个矩形格子；rings 非空时跳过完全落在广州市界外的格子"""
    tag = ",".join(f"{v:.5f}" for v in bbox)
    if tag in done:
        return 0
    if rings is not None and not cell_in_gz(bbox, rings):   # 市界外，连count都不查
        indent = "  " * depth
        print(f"{indent}[{tag}] 市界外，跳过")
        done_f.write(tag + "\n"); done_f.flush()
        return 0
    head = query_cell(key, bbox, keywords, types, page=1)
    count = int(head.get("count", 0))
    indent = "  " * depth
    if count == 0:
        print(f"{indent}[{tag}] 0 条，跳过")
        done_f.write(tag + "\n"); done_f.flush()
        return 0
    if count > SAFE_COUNT and depth < MAX_DEPTH:
        print(f"{indent}[{tag}] {count} 条 > {SAFE_COUNT}，切分为4")
        lng1, lat1, lng2, lat2 = bbox
        mx, my = (lng1 + lng2) / 2, (lat1 + lat2) / 2
        n = 0
        for sub in [(lng1, lat1, mx, my), (mx, lat1, lng2, my),
                    (lng1, my, mx, lat2), (mx, my, lng2, lat2)]:
            n += harvest(key, sub, keywords, types, out_f, done, done_f, depth + 1, rings)
        done_f.write(tag + "\n"); done_f.flush()
        return n
    # 安全格子：翻页取完
    pois = head.get("pois", [])
    page = 1
    while len(pois) < count:
        page += 1
        j = query_cell(key, bbox, keywords, types, page=page)
        batch = j.get("pois", [])
        if not batch:
            break
        pois.extend(batch)
    for p in pois:
        p["_cell"] = tag
        out_f.write(json.dumps(p, ensure_ascii=False) + "\n")
    out_f.flush()
    print(f"{indent}[{tag}] 取得 {len(pois)}/{count} 条")
    done_f.write(tag + "\n"); done_f.flush()
    return len(pois)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["all_food", "chicken_keyword"],
                    default="chicken_keyword",
                    help="all_food=全量餐饮(types=050000,做分母); chicken_keyword=关键词'鸡'(做分子初筛)")
    ap.add_argument("--bbox", default=None, help="lng1,lat1,lng2,lat2 仅抓该矩形(试跑)")
    ap.add_argument("--clip-gz", action="store_true",
                    help="开启广州市界预剪枝：跳过完全落在市界外的格子，省掉邻市(东莞/深圳/佛山)的浪费")
    ap.add_argument("--keys", default=None,
                    help="逗号分隔的多个key，按序轮换：当前key配额耗尽自动切下一个续采(默认用环境变量 AMAP_KEY)")
    args = ap.parse_args()

    keys = [k.strip() for k in (args.keys.split(",") if args.keys
                                else [os.environ.get("AMAP_KEY", "")]) if k.strip()]
    if not keys:
        sys.exit("请用 --keys k1,k2,k3 传入key，或 export AMAP_KEY=你的高德Web服务key")

    bbox = tuple(map(float, args.bbox.split(","))) if args.bbox else GUANGZHOU_BBOX
    keywords, types = ("", "050000") if args.mode == "all_food" else ("鸡", "050000")

    rings = None
    if args.clip_gz:
        rings = load_gz_boundary(keys[0])
        print(f"市界剪枝已开启: {len(rings)} 环 / {sum(len(r) for r in rings)} 点")

    DATA_DIR.mkdir(exist_ok=True)
    raw_path = DATA_DIR / f"poi_raw_{args.mode}.jsonl"
    done_path = DATA_DIR / f"poi_done_{args.mode}.txt"

    with open(raw_path, "a", encoding="utf-8") as out_f, \
         open(done_path, "a", encoding="utf-8") as done_f:
        for i, key in enumerate(keys, 1):
            done = set(done_path.read_text().split()) if done_path.exists() else set()  # 换key时重载断点
            try:
                got = harvest(key, bbox, keywords, types, out_f, done, done_f, rings=rings)
                print(f"\nkey #{i} 本轮新增 {got} 条；所有格子已采完。")
                break
            except Quota as e:
                print(f"\nkey #{i} {e}")
                if i < len(keys):
                    print(f"→ 切到 key #{i + 1} 继续（断点续采，已采格子自动跳过）")
        else:
            print("\n所有key配额都已耗尽，进度已保存。补充新key或次日重跑同一命令即可续采。")

    n = sum(1 for _ in open(raw_path, encoding="utf-8"))
    print(f"输出文件现共 {n} 条 -> {raw_path}")


if __name__ == "__main__":
    main()
