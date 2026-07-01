# 广州鸡类餐饮POI交付包

## 文件
- `poi_clean.csv`: 清洗后的点表。
- `poi_clean.geojson`: 上传 GeoScene Online 的主点图层。
- `penetration_by_district.csv`: 11区渗透率专题图数据。
- `data_dictionary.csv`: 字段说明。
- `cleaning_report.json`: 清洗统计和口径提醒。
- `rejected_synthetic_samples.csv`: 被剔除的合成样例记录。
- `background_context_sources.csv`: 官方统计背景源表。硬统计只引用 confidence=高 的行；地方鸡文化新闻/行业报告行目前是待补佐证。
- `mapping_geoscene_workflow.md`: Windows 端 GeoScene Online 制图清单，说明数据状态、出图要求和上传字段选择。

## 口径
- 招牌口径：店名命中鸡类词，代表“专门鸡店”，适合作为主指标。
- 宽口径：店名或推荐菜命中鸡类词，代表“能吃到鸡”，用于支撑“无处不在”的叙事。
- 这些指标描述餐饮空间可见度，不等于居民实际消费量或订单量。
