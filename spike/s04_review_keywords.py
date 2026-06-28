# -*- coding: utf-8 -*-
"""
s04_review_keywords.py — 评论文本 -> 关键词词频 spike

定位：评论数据建议走"小样本人工/半人工采集"（理由见 README 的法律与反爬部分），
本脚本验证的是采到样本之后的处理链路是否通畅：

  评论CSV(shop,district,review) --> jieba分词 --> 菜名词典保护 --> 停用词过滤
      --> 词频表 out/review_word_freq.csv --> (GeoScene Online / 在线词云工具出图)

技术要点：
  1. jieba 默认会把"白切鸡"切成"白切/鸡"、"盐焗鸡"切成"盐/焗/鸡"。
     必须先 jieba.add_word() 把全部菜名词典注入，否则词云上不会出现完整菜名。
  2. 停用词除通用词外，要加评论域专属噪声词：好吃/不错/味道/服务/老板/分量…
     这些词频极高但无信息量，不滤掉的话词云会被它们淹没。
  3. 输出按 district 分组的词频，方便做"分区词云"或与地图联动。
"""
import csv
from collections import Counter, defaultdict
from pathlib import Path

import jieba

HERE = Path(__file__).parent

DISH_WORDS = [
    "白切鸡", "白斩鸡", "盐焗鸡", "豉油鸡", "手撕鸡", "沙姜鸡", "葱油鸡", "太爷鸡",
    "啫啫鸡", "豆酱鸡", "卤水鸡", "猪肚鸡", "清远鸡", "走地鸡", "湛江鸡", "椰子鸡",
    "炸鸡", "鸡排", "黄焖鸡", "鸡公煲", "口水鸡", "辣子鸡", "皮爽肉滑", "鸡有鸡味",
    "沙姜", "豉油", "姜葱蓉", "斩料",  # 佐料/行话，防止被错切（如"蘸沙姜豉油"->"姜豉"）
]

STOP = set("""
的 了 是 我 也 都 很 还 就 在 和 有 不 这 那 吃 去 来 说 没 又 给 但 要 跟 被 让
好吃 不错 味道 感觉 觉得 喜欢 推荐 服务 老板 分量 价格 环境 排队 一般 可以 真的
非常 比较 一个 这家 他们 我们 没有 就是 不过 而且 因为 所以 如果 还是 有点 点了
""".split())


def tokenize(text: str):
    for w in jieba.cut(text):
        w = w.strip()
        if len(w) >= 2 and w not in STOP and not w.isdigit():
            yield w


def main():
    for w in DISH_WORDS:                # 要点1：词典保护
        jieba.add_word(w, freq=10000)

    src = HERE / "data" / "sample_reviews.csv"
    by_district = defaultdict(Counter)
    overall = Counter()
    n = 0
    with open(src, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            n += 1
            for w in tokenize(row["review"]):
                overall[w] += 1
                by_district[row["district"]][w] += 1

    out = HERE / "out"
    out.mkdir(exist_ok=True)
    path = out / "review_word_freq.csv"
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["district", "word", "freq"])
        for word, c in overall.most_common():
            w.writerow(["__全部__", word, c])
        for d, cnt in by_district.items():
            for word, c in cnt.most_common(50):
                w.writerow([d, word, c])

    print(f"处理评论 {n} 条")
    print("整体 Top15 关键词:")
    for word, c in overall.most_common(15):
        print(f"  {word:8s} {c}")
    print(f"词频表 -> {path}")


if __name__ == "__main__":
    main()
