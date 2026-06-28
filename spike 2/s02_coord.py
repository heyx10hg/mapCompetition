# -*- coding: utf-8 -*-
"""
s02_coord.py — GCJ-02 <-> WGS-84 坐标转换

为什么需要这个文件：
  高德 API 返回的所有经纬度都是 GCJ-02（国测局加密坐标，俗称"火星坐标"）。
  GeoScene Online 默认底图（天地图）使用 CGCS2000，与 WGS-84 在米级上可视为一致。
  如果不转换直接上图，所有点位会整体偏移约 300~700 米——在城市尺度的 POI 热力图上
  足以把店铺画到马路对面甚至错误街区。

  例外：如果你在 GeoScene Online 中选用的是"高德底图"（同为 GCJ-02），则不要转换。
  原则：点数据坐标系必须与底图坐标系一致。

精度说明：
  gcj02_to_wgs84() 使用公开逆推算法 + 迭代收敛，误差 < 1 米，对 POI 制图完全够用。
"""
import math

A = 6378245.0          # 克拉索夫斯基椭球长半轴
EE = 0.00669342162296594323  # 偏心率平方


def _out_of_china(lng: float, lat: float) -> bool:
    return not (72.004 <= lng <= 137.8347 and 0.8293 <= lat <= 55.8271)


def _transform_lat(x: float, y: float) -> float:
    ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(y * math.pi) + 40.0 * math.sin(y / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(y / 12.0 * math.pi) + 320 * math.sin(y * math.pi / 30.0)) * 2.0 / 3.0
    return ret


def _transform_lng(x: float, y: float) -> float:
    ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(x * math.pi) + 40.0 * math.sin(x / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(x / 12.0 * math.pi) + 300.0 * math.sin(x / 30.0 * math.pi)) * 2.0 / 3.0
    return ret


def wgs84_to_gcj02(lng: float, lat: float):
    """WGS-84 -> GCJ-02（加偏）"""
    if _out_of_china(lng, lat):
        return lng, lat
    dlat = _transform_lat(lng - 105.0, lat - 35.0)
    dlng = _transform_lng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * math.pi
    magic = math.sin(radlat)
    magic = 1 - EE * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((A * (1 - EE)) / (magic * sqrtmagic) * math.pi)
    dlng = (dlng * 180.0) / (A / sqrtmagic * math.cos(radlat) * math.pi)
    return lng + dlng, lat + dlat


def gcj02_to_wgs84(lng: float, lat: float, eps: float = 1e-7):
    """GCJ-02 -> WGS-84（纠偏，迭代逆推，误差<1m）"""
    if _out_of_china(lng, lat):
        return lng, lat
    wlng, wlat = lng, lat
    for _ in range(30):
        glng, glat = wgs84_to_gcj02(wlng, wlat)
        dlng, dlat = glng - lng, glat - lat
        wlng -= dlng
        wlat -= dlat
        if abs(dlng) < eps and abs(dlat) < eps:
            break
    return wlng, wlat


if __name__ == "__main__":
    # 自检：广州塔的 GCJ-02 坐标，纠偏后应西移/南移若干百米
    gcj = (113.330803, 23.113155)
    wgs = gcj02_to_wgs84(*gcj)
    back = wgs84_to_gcj02(*wgs)
    print(f"GCJ-02 : {gcj}")
    print(f"WGS-84 : ({wgs[0]:.6f}, {wgs[1]:.6f})")
    print(f"往返误差: {abs(back[0]-gcj[0]):.2e}, {abs(back[1]-gcj[1]):.2e}  (应接近0)")
    # 偏移距离粗算
    dx = (gcj[0] - wgs[0]) * 102000  # 该纬度1度经度约102km
    dy = (gcj[1] - wgs[1]) * 111000
    print(f"该点加密偏移量约: 东西 {dx:.0f} m, 南北 {dy:.0f} m")
