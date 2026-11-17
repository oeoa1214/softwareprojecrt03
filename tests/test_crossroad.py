import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crossroad import Crossroad

M_PER_DEG_LAT = 6371000 * math.pi / 180      # 위도 1도 = 약 111,195m

# 약 5km 범위의 작은 대구 안 교차로 3개: 가운데 교차로(2) 기준으로 위쪽(북쪽)에 300m를 잰다.
NODES = [(1, 35.8500, 128.5500), (2, 35.8700, 128.5900), (3, 35.8900, 128.6300)]


def _north_of_node2(meters):
    return 35.8700 + meters / M_PER_DEG_LAT, 128.5900


def test_TE09_normal_100m():
    lat, lon = _north_of_node2(100)
    assert Crossroad(NODES).find_crossroad(lat, lon) == 2


def test_TE10_boundary_0_300_300_1():
    c = Crossroad(NODES)
    assert c.find_crossroad(*_north_of_node2(0)) == 2
    assert c.find_crossroad(*_north_of_node2(300)) == 2       # 300m 딱 맞으면 정상
    assert c.find_crossroad(*_north_of_node2(300.1)) == -2    # 300m 초과


def test_TE11_outside_daegu():
    assert Crossroad(NODES).find_crossroad(37.56, 126.97) == -1


def test_distance_0_001_deg_is_about_111m():
    d = Crossroad(NODES)._Crossroad__distance(35.870, 128.590, 35.871, 128.590)
    assert 110 < d < 112


def test_nearest_of_several_is_chosen():
    # 노드 1과 3 사이, 노드 3에 더 가까운 점
    assert Crossroad(NODES).find_crossroad(35.8895, 128.6295) == 3


# ---------------------------------------------------------------- 대구 경계선 판정 (오은찬 추가)
import csv

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def _real_points():
    """실제 node.csv의 교차로 (node_id, lat, lon)"""
    with open(os.path.join(DATA, "node.csv"), encoding="utf-8-sig") as f:
        return [(int(r["node_id"]), float(r["lat"]), float(r["lon"])) for r in csv.DictReader(f)]


def test_EX04_outside_daegu_inside_rectangle():
    """EX-04: 교차로 사각형 범위 안이지만 대구 경계선 밖인 곳(경산 · 청도 · 칠곡 왜관)은 대구 밖(-1)"""
    c = Crossroad(_real_points())
    assert c.find_crossroad(35.825, 128.741) == -1    # 경산
    assert c.find_crossroad(35.647, 128.734) == -1    # 청도
    assert c.find_crossroad(35.990, 128.400) == -1    # 칠곡 왜관


def test_inside_daegu_by_boundary():
    """대구 경계선 안(대구시청 · 팔공산)은 대구 밖(-1)이 아니다"""
    c = Crossroad(_real_points())
    assert c.find_crossroad(35.871, 128.601) > 0      # 대구시청: 300m 안 교차로 번호
    assert c.find_crossroad(35.990, 128.670) != -1    # 팔공산