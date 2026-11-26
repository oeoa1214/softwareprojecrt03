"""그리드 탐색 확인 - 실제 교차로(node.csv)로, 예전 방식(전부 재기)과 결과가 같은지 비교한다."""
import csv, os, random, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from crossroad import Crossroad

# 실제 대구 교차로 28,441개
NODES = []
with open(os.path.join(ROOT, "data", "node.csv"), encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        NODES.append((int(r["node_id"]), float(r["lat"]), float(r["lon"])))

C = Crossroad(NODES)


def _old_way(lat, lon):
    """예전 방식: 대구 판정 → 28,441개 전부 거리를 재서 가장 가까운 교차로 → 300m 비교"""
    if not C._Crossroad__in_daegu(lat, lon):
        return -1
    best_id, best_dist = None, None
    for node_id, n_lat, n_lon in NODES:
        d = C._Crossroad__distance(lat, lon, n_lat, n_lon)
        if best_dist is None or d < best_dist:
            best_id, best_dist = node_id, d
    if round(best_dist, 6) <= Crossroad.LIMIT_M:
        return best_id
    return -2


def test_grid_same_as_old_random_points():
    # 대구를 덮는 네모 안 무작위 지점 1,000개 (대구 밖 · 300m 초과 · 교차로 번호가 섞여 나온다)
    random.seed(1)
    for _ in range(1000):
        lat = random.uniform(35.60, 36.02)
        lon = random.uniform(128.35, 128.78)
        assert C.find_crossroad(lat, lon) == _old_way(lat, lon)


def test_grid_same_as_old_near_300m():
    # 교차로에서 북쪽으로 약 298~300m 떨어진 지점 300개 (칸 경계에 걸리기 쉬운 거리)
    random.seed(2)
    for node_id, n_lat, n_lon in random.sample(NODES, 300):
        lat = n_lat + 0.00269
        assert C.find_crossroad(lat, n_lon) == _old_way(lat, n_lon)
