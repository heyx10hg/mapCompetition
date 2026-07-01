# GeoScene Online 制图交付清单

更新日期：2026-07-01

本文件用于 Windows 端制图时快速判断：哪些数据已经拿到，哪些还缺；每张图用什么数据；上传到 GeoScene Online 时需要保留和选择哪些字段。

## 1. 数据清单

| 数据 | 当前状态 | 文件位置 | 用途 | 备注 |
|---|---|---|---|---|
| 广州鸡类候选 POI 原始数据 | 已获取 | `spike/data/poi_raw_chicken_keyword.jsonl` | 清洗、去重、鸡类标签判定 | 高德 POI 原始抓取结果，不直接上图 |
| 广州全量餐饮 POI 原始数据 | 已获取 | `spike/data/poi_raw_all_food.jsonl` | 各区全量餐饮分母 | 用于计算 `all_food_poi`，不直接上图 |
| 清洗后 POI 点图层 | 已获取 | `spike/out_delivery/poi_clean.geojson` | 主点图层、分类点图、热力图、弹窗 | 推荐优先上传 GeoJSON |
| 清洗后 POI 表格 | 已获取 | `spike/out_delivery/poi_clean.csv` | 人工检查、筛选、必要时 CSV 上传 | CSV 上传时要指定 `lng` / `lat` |
| 11 区渗透率表 | 已获取 | `spike/out_delivery/penetration_by_district.csv` | 分区专题图、图表 | 需要与广州 11 区边界按 `district` 关联 |
| 数据字典 | 已获取 | `spike/out_delivery/data_dictionary.csv` | 字段解释 | 制图前先看字段含义 |
| 分类口径 DOCX | 已获取 | `spike/out_delivery/classification_readme.docx` | 解释 traditional / modern / other_chicken 等口径 | 写图说和答辩时引用 |
| 背景资料源表 | 已获取，部分待核验 | `spike/out_delivery/background_context_sources.csv` | 背景图表、故事旁白、引用线索 | 21 条资料，20 条高可信，1 条地方鸡文化材料待人工补证 |
| 广州行政区边界 | 已获取 | `spike/data/gz_boundary.json` | 渗透率分区专题图底图 | 若 Windows 端没有该文件，可从 `spike/data/` 复制到制图目录 |
| 广东人均禽类消费量 | 待获取 | 暂无 | 只用于宏观背景，不参与 POI 渗透率 | 需要优先找统计年鉴或住户调查口径 |
| 清远鸡、白切鸡、粤菜消费公开材料 | 待补强 | `background_context_sources.csv` 中已有占位行 | 用于故事升华和文字佐证 | 不能替代 POI 数据，主要服务叙事 |
| 广东四大名鸡代表点位 | 待获取/待核验 | 暂无正式点表 | 可做故事开头或辅助定位图 | 建议用“代表性原产地/地理标志区域”，不要伪造具体店铺或养殖场点 |
| 评论词云或评价数据 | 暂不作为主线 | 暂无正式交付 | 可选补充 | 与当前渗透率无关，不阻塞第四章制图 |

## 2. 当前核心数据口径

- 研究对象：广州 11 区餐饮 POI 中可识别出的鸡类菜品信号。
- 坐标系：`out_delivery` 中 `poi_clean.csv` 和 `poi_clean.geojson` 默认是 WGS-84。
- 不要把 POI 渗透率写成真实消费量、订单量或营业额。
- `traditional`、`modern`、`other_chicken` 都算鸡类 POI；`non_chicken` 不进入鸡类渗透率分子。
- `signboard_pct` 是主指标，表示“店名含鸡 POI / 全量餐饮 POI”。
- `serves_pct` 是辅助指标，表示“店名或推荐菜含鸡 POI / 全量餐饮 POI”。

当前版本摘要：

| 指标 | 当前值 |
|---|---:|
| 清洗后 POI | 14,091 |
| 鸡类 POI | 11,128 |
| 招牌命中 POI | 7,405 |
| 推荐菜命中 POI | 3,723 |
| traditional | 3,570 |
| modern | 4,560 |
| other_chicken | 2,998 |
| non_chicken | 2,963 |

## 3. 需要出的图

### 图 1：广州鸡类餐饮 POI 总分布图

| 项目 | 设置 |
|---|---|
| 使用数据 | `poi_clean.geojson` |
| 图层筛选 | `label` 不等于 `non_chicken` |
| 符号字段 | `label` |
| 呈现效果 | 广州底图上显示鸡类餐饮点位，用三类颜色区分传统、本地不明归属和现代/外来鸡类信号 |
| 建议配色 | `traditional` 用暖红或深橙；`modern` 用蓝紫或蓝色；`other_chicken` 用灰黄或浅灰 |
| 弹窗字段 | `name`、`label`、`match_source`、`district`、`address`、`tag` |
| 图说重点 | “鸡类菜品在广州餐饮空间中高度可见，但这不是消费量地图。” |

### 图 2：广州鸡类餐饮热力图

| 项目 | 设置 |
|---|---|
| 使用数据 | `poi_clean.geojson` |
| 图层筛选 | `label` 不等于 `non_chicken` |
| 渲染方式 | Heat Map / 热力图 |
| 权重字段 | 无权重，按点密度即可 |
| 呈现效果 | 显示鸡类餐饮可见度的空间集聚区，重点观察中心城区和大型居住/商业区 |
| 建议配色 | 低密度透明，高密度黄-橙-红；底图保持浅色 |
| 图说重点 | “哪里更容易在餐饮空间中遇到鸡类菜品。” |

### 图 3：11 区鸡类渗透率分区专题图

| 项目 | 设置 |
|---|---|
| 使用数据 | `penetration_by_district.csv` + 广州行政区边界 |
| 关联字段 | 两边都用 `district` |
| 主展示字段 | `signboard_pct` |
| 辅助弹窗字段 | `serves_pct`、`signboard_poi`、`serves_chicken_poi`、`all_food_poi` |
| 呈现效果 | 每个区按招牌口径渗透率深浅着色，突出“专门鸡店”在区内餐饮空间中的可见度 |
| 建议配色 | 单色顺序色带，不要用分类随机色；可用浅黄到深红 |
| 图说重点 | “招牌口径更稳，适合作为主图；宽口径用于说明能吃到鸡的范围更广。” |

### 图 4：招牌口径与宽口径对比图

| 项目 | 设置 |
|---|---|
| 使用数据 | `penetration_by_district.csv` |
| 展示字段 | `signboard_pct` 与 `serves_pct` |
| 呈现方式 | 分区柱状图、双变量图，或在专题图弹窗中同时显示两项 |
| 呈现效果 | 表现“专门鸡店”和“菜单中有鸡”的差异 |
| 推荐做法 | 如果 GeoScene Online 操作受限，先做一张 `signboard_pct` 分区图，再在弹窗或旁边图表展示 `serves_pct` |
| 图说重点 | “越是综合餐饮密集地区，宽口径可能明显高于招牌口径。” |

### 图 5：传统与现代鸡类做法结构图

| 项目 | 设置 |
|---|---|
| 使用数据 | `poi_clean.geojson` |
| 图层筛选 | `label` 等于 `traditional` 或 `modern` |
| 符号字段 | `label` |
| 呈现效果 | 传统广东本地做法与现代/外来鸡类信号的空间对比 |
| 建议配色 | `traditional` 用红/橙，`modern` 用蓝；避免和热力图色带混淆 |
| 可选统计 | 按区统计 traditional 与 modern 数量或占比，做附属柱状图 |
| 图说重点 | “传统并非消失，而是与现代快餐化、外来做法共同占据广州餐饮空间。” |

### 图 6：隐性菜单渗透点图

| 项目 | 设置 |
|---|---|
| 使用数据 | `poi_clean.geojson` |
| 图层筛选 | `match_source` 等于 `推荐菜` |
| 符号字段 | `label` 或统一符号 |
| 呈现效果 | 显示店名不一定写鸡、但推荐菜或标签中出现鸡类菜品的餐饮点 |
| 建议配色 | 使用浅色或半透明点，作为“隐性渗透”辅助图层 |
| 图说重点 | “没有把鸡写在招牌上，不代表这家店没有鸡类菜品。” |

### 图 7：背景叙事图表

| 项目 | 设置 |
|---|---|
| 使用数据 | `background_context_sources.csv` |
| 推荐内容 | 广东餐饮收入、广州住宿餐饮业零售额、广东禽肉产量、食品烟酒消费支出等 |
| 呈现方式 | 页面旁白、图表卡片或章节开头信息图 |
| 呈现效果 | 作为“广东餐饮市场大、禽肉供给充足、鸡类文化有现实基础”的背景 |
| 注意事项 | 地方鸡文化材料仍需补强；不要把宏观消费数据直接解释成广州 POI 分布原因 |

### 图 8：广东地方鸡文化代表点图

| 项目 | 设置 |
|---|---|
| 使用数据 | 待获取 |
| 推荐口径 | 清远鸡、杏花鸡、胡须鸡等代表性地方鸡种的原产地或地理标志区域 |
| 呈现效果 | 作为故事开头或结尾的文化来源图，不作为广州 POI 统计图 |
| 注意事项 | 没有权威来源前不要做精确点；可以先在文案里写“待补代表性产地资料” |

## 4. GeoScene Online 上传与字段勾选

### 4.1 上传 `poi_clean.geojson`

推荐优先上传 GeoJSON，因为坐标已经写在 geometry 中。

| 步骤 | 选择 |
|---|---|
| 添加方式 | Add layer from file / 从文件添加图层 |
| 文件 | `spike/out_delivery/poi_clean.geojson` |
| 坐标处理 | 使用文件自带几何；当前为 WGS-84 |
| 图层名称 | `广州鸡类餐饮POI_清洗版` |
| 保留字段 | `id`、`name`、`name_norm`、`label`、`match_source`、`district`、`address`、`typecode`、`type`、`tag` |
| 可隐藏字段 | `lng`、`lat` 可隐藏，但不要删除 |
| 弹窗标题 | `{name}` |
| 弹窗正文 | `label`、`match_source`、`district`、`address`、`tag` |

分类渲染时使用：

| 字段 | 用途 |
|---|---|
| `label` | traditional / modern / other_chicken / non_chicken 分类符号 |
| `match_source` | 招牌 / 推荐菜，用于显性与隐性渗透图 |
| `district` | 分区筛选和图表统计 |
| `tag` | 弹窗解释为什么某店被识别为鸡类 |

### 4.2 如果上传 `poi_clean.csv`

只有 GeoJSON 上传失败时才建议用 CSV。

| 步骤 | 选择 |
|---|---|
| X 字段 | `lng` |
| Y 字段 | `lat` |
| 坐标系 | WGS-84 / GCS WGS 1984 |
| 图层名称 | `广州鸡类餐饮POI_CSV` |
| 保留字段 | 与 GeoJSON 相同 |
| 注意 | 不要把 `district` 当作位置字段；它只用于筛选和统计 |

### 4.3 上传 `penetration_by_district.csv`

这个表本身没有坐标，不能直接当点图层。

| 步骤 | 选择 |
|---|---|
| 文件 | `spike/out_delivery/penetration_by_district.csv` |
| 位置字段 | 不选择经纬度 |
| 使用方式 | 作为表格，与广州行政区边界按 `district` 关联 |
| 关联字段 | 边界图层字段 `district` 或区名字段，对应 CSV 的 `district` |
| 主渲染字段 | `signboard_pct` |
| 弹窗字段 | `signboard_poi`、`serves_chicken_poi`、`all_food_poi`、`signboard_pct`、`serves_pct` |

如果 GeoScene Online 关联表不方便，可以先在本地 GIS 或表格工具中把 `penetration_by_district.csv` 合并到行政区边界，再上传合并后的边界图层。

### 4.4 上传 `background_context_sources.csv`

这个表不建议作为地图图层。

| 步骤 | 选择 |
|---|---|
| 使用方式 | 表格或资料备查 |
| 地图字段 | 不选择经纬度 |
| 展示位置 | 故事地图文字、图表卡片、资料来源页 |
| 筛选建议 | 正式展示优先使用 `confidence=高` 的行 |

## 5. 图层命名建议

| 图层 | 建议名称 |
|---|---|
| 主 POI 点图层 | `广州鸡类餐饮POI_分类` |
| 热力图图层 | `鸡类餐饮可见度热力` |
| 分区渗透率图层 | `广州11区鸡类渗透率_招牌口径` |
| 宽口径辅助图层 | `广州11区鸡类渗透率_宽口径` |
| 传统现代对比图层 | `传统与现代鸡类做法对比` |
| 隐性菜单渗透图层 | `菜单中含鸡_POI` |

## 6. 制图顺序建议

1. 先上传 `poi_clean.geojson`，确认点位没有明显整体偏移。
2. 做图 1：按 `label` 分类的 POI 总分布图。
3. 复制图层做图 2：鸡类 POI 热力图。
4. 上传或准备广州 11 区边界，关联 `penetration_by_district.csv`。
5. 做图 3：`signboard_pct` 分区专题图。
6. 在图 3 的弹窗或旁边图表中加入 `serves_pct`，形成图 4。
7. 回到 POI 图层，筛选 `traditional` 与 `modern`，做图 5。
8. 筛选 `match_source=推荐菜`，做图 6。
9. 最后再补图 7 和图 8；这两张不阻塞主线地图。

## 7. 不要这样做

- 不要把 `background_context_sources.csv` 当作点图层上传。
- 不要把 `penetration_by_district.csv` 当作有经纬度的点表。
- 不要把 `serves_pct` 写成真实消费率。
- 不要把 `label=modern` 理解成整家店是现代菜系，它只表示命中的鸡类菜品信号更接近现代、外来或快餐化语境。
- 不要在没有来源的情况下制作“四大名鸡精确点位”。
- 不要混用 WGS-84 点数据和 GCJ-02 高德底图；如果底图换成高德，需要重新导出 GCJ-02 版本。
