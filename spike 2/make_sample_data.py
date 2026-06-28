# -*- coding: utf-8 -*-
"""
make_sample_data.py — 生成合成样例数据，模拟高德真实返回中会遇到的脏数据形态。
没有 API key 也能借助它把 s03/s04 整条流水线跑通（这正是 spike 的目的）。
"""
import json
import random
from pathlib import Path

random.seed(42)
DATA = Path(__file__).parent / "data"
DATA.mkdir(exist_ok=True)

DISTRICTS = {"天河区": (113.36, 23.13), "越秀区": (113.27, 23.13), "荔湾区": (113.23, 23.10),
             "海珠区": (113.30, 23.08), "白云区": (113.27, 23.20), "番禺区": (113.38, 22.94)}

def loc(d):
    lng, lat = DISTRICTS[d]
    return f"{lng + random.uniform(-.03,.03):.6f},{lat + random.uniform(-.03,.03):.6f}"

def poi(pid, name, d, typecode="050118", location=None):
    return {"id": pid, "name": name, "typecode": typecode,
            "type": "餐饮服务;中餐厅;中餐厅", "adname": d,
            "address": f"{d}某某路{random.randint(1,200)}号",
            "location": loc(d) if location is None else location}

chicken_names = (
    [f"{x}白切鸡饭店" for x in "顺德阿婆湛记金牌"] +
    ["客家盐焗鸡(总店)", "客家盐焗鸡（天河店）", "客家盐焗鸡（番禺店）",
     "祺记豉油鸡", "阿强沙姜鸡", "啫啫鸡煲王", "潮汕卤水鸡脚", "太爷鸡老铺",
     "清远走地鸡庄", "文记猪肚鸡", "湛江鸡专门店"] +
    ["华莱士炸鸡汉堡", "肯氏炸鸡", "首尔韩式炸鸡", "正新鸡排", "杨铭宇黄焖鸡米饭",
     "重庆鸡公煲", "川渝口水鸡", "新疆大盘鸡", "椰子鸡火锅(珠江新城店)"] +
    ["鸡仔唛美食店", "鸡煲一条街旗舰店", "鸡味浓茶餐厅"]
)
rows = []
for i, n in enumerate(chicken_names):
    rows.append(poi(f"B00{i:03d}", n, random.choice(list(DISTRICTS))))

# 脏数据形态注入
rows.append(rows[5] | {})                                        # R1a: id 完全重复
dup = dict(rows[6]); dup["id"] = "B00999"                        # R1b: 不同id同名同址
rows.append(dup)
rows.append(poi("B00900", "田鸡王美蛙馆", "天河区"))               # R2: 假阳性(青蛙)
rows.append(poi("B00901", "鸡尾酒清吧LOUNGE", "天河区"))          # R2: 假阳性(酒吧)
rows.append(poi("B00902", "港式鸡蛋仔甜品", "越秀区"))            # R2: 假阳性(无鸡肉)
rows.append(poi("B00903", "粤盛鸡精调味商行", "白云区", typecode="060400"))  # R3: 零售非餐饮
bad = poi("B00904", "无名白切鸡档", "荔湾区"); bad["location"] = ""          # 坐标缺失
rows.append(bad)

with open(DATA / "poi_raw_chicken_keyword.jsonl", "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

# 全量餐饮(分母)：每区造一批，含上面的鸡店
all_food = list(rows)
fillers = ["茶餐厅", "牛肉火锅", "肠粉店", "烧腊店", "湘菜馆", "日料店", "奶茶店", "粥城", "猪脚饭"]
k = 0
for d in DISTRICTS:
    for _ in range(random.randint(25, 60)):
        all_food.append(poi(f"F{k:05d}", f"{random.choice('金大好旺华兴顺')}{random.choice(fillers)}", d))
        k += 1
with open(DATA / "poi_raw_all_food.jsonl", "w", encoding="utf-8") as f:
    for r in all_food:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

# 评论样本
reviews = [
    ("湛记白切鸡", "荔湾区", "白切鸡皮爽肉滑，鸡有鸡味，蘸沙姜豉油一流，阿婆说用的是清远鸡"),
    ("湛记白切鸡", "荔湾区", "老字号了，白切鸡斩件均匀，皮脆有鸡味，配姜葱蓉绝了"),
    ("客家盐焗鸡", "天河区", "盐焗鸡咸香入味，手撕的口感很好，客家风味正宗"),
    ("祺记豉油鸡", "越秀区", "豉油鸡甜咸平衡，上色漂亮，米饭淋豉油汁无敌"),
    ("首尔韩式炸鸡", "天河区", "炸鸡外脆里嫩，蜂蜜黄油味好评，配啤酒很爽"),
    ("正新鸡排", "白云区", "鸡排很大块，外皮酥脆，排队的人不少"),
    ("文记猪肚鸡", "海珠区", "猪肚鸡汤底胡椒味足，鸡肉嫩滑，冬天喝汤一流"),
    ("椰子鸡火锅", "天河区", "椰子鸡清甜，鸡肉是文昌鸡，蘸料青桔小米辣点睛"),
    ("杨铭宇黄焖鸡", "番禺区", "黄焖鸡米饭量足，汤汁拌饭好吃，工作日快餐首选"),
    ("太爷鸡老铺", "越秀区", "太爷鸡烟熏味独特，老广州的味道，斩料配粥一流"),
]
with open(DATA / "sample_reviews.csv", "w", encoding="utf-8") as f:
    f.write("shop,district,review\n")
    for s, d, r in reviews:
        f.write(f"{s},{d},{r}\n")

print("样例数据生成完毕:",
      *(p.name for p in DATA.iterdir()), sep="\n  ")
