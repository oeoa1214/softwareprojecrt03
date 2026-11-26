import heapq, os, sys
import pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shortest_road import ShortestRoad
from road_api import RoadApi

S, A, B, C, H1, H2, H3 = 1, 2, 3, 4, 5, 6, 7
# 36km/h = 10m/s 이므로 길이(m) = 시간(초) x 10
KMH36 = 36


def L(link_id, f, t, seconds):
    return (link_id, f, t, seconds * 10.0, KMH36)


def test_3_4_3_1_passway_time_600m_36kmh_is_60s():
    assert ShortestRoad([], []).passway_time(600, 36) == 60.0


def test_3_4_3_2_heap_order():
    h = []
    for item in [(60, "A"), (90, "C"), (30, "B")]:
        heapq.heappush(h, item)
    assert "".join(heapq.heappop(h)[1] for _ in range(3)) == "BAC"


def test_3_4_3_3_dijkstra_takes_cheaper_path():
    links = [L(1, S, A, 60), L(2, A, C, 60), L(3, S, B, 60), L(4, B, C, 30)]
    sr = ShortestRoad(links, [])
    dist = sr.dijkstra(S)
    assert dist[C] == 90          # A 경유 120이 아니라 B 경유 90
    assert sr.make_route(C) == [S, B, C]


def test_3_4_3_4_faster_hospital_first_even_if_farther():
    # 병원1: 사고->A->병원1 (1km, 100초) / 병원2: 사고->B->병원2 (500m, 200초)
    links = [(1, S, A, 500, 36), (2, A, H1, 500, 36),
             (3, S, B, 250, 9), (4, B, H2, 250, 9)]
    sr = ShortestRoad(links, [])
    sr.dijkstra(S)
    rows = sr.sort_hospitals([("h2", "병원2", H2, 3), ("h1", "병원1", H1, 3)])
    assert [r[0] for r in rows] == ["h1", "h2"]
    assert rows[0][3] == 100 / 60 and rows[0][4] == 1000 and rows[0][5] == 3
    assert rows[1][3] == 200 / 60 and rows[1][4] == 500


def test_3_5_2_2_speed_boundaries():
    # 속도 0, 1, 150, 151인 도로: 0과 151은 graph에 없고 1, 150은 있다.
    links = [(1, S, A, 1000, 60), (2, S, B, 1000, 60), (3, S, C, 1000, 60), (4, S, H1, 1000, 60)]
    speeds = [(1, 0), (2, 1), (3, 150), (4, 151)]
    sr = ShortestRoad(links, speeds)
    dist = sr.dijkstra(S)
    assert A not in dist and H1 not in dist
    assert B in dist and C in dist


def test_speed_missing_uses_max_spd():
    sr = ShortestRoad([(1, S, A, 1000, 60)], [])          # speeds에 없는 도로
    assert sr.dijkstra(S)[A] == pytest.approx(60.0)        # 1000 / (60/3.6) = 60초


def test_api_speed_overrides_max_spd():
    sr = ShortestRoad([(1, S, A, 1000, 60)], [(1, 30)])
    assert sr.dijkstra(S)[A] == pytest.approx(120.0)


def test_TE14_no_bed_hospitals_go_last():
    links = [L(1, S, H1, 60), L(2, S, H2, 120), L(3, S, H3, 300), L(4, S, A, 30), L(5, S, B, 40)]
    sr = ShortestRoad(links, [])
    sr.dijkstra(S)
    rows = sr.sort_hospitals([
        ("a", "빠른0", A, 0), ("b", "빠른0b", B, 0),
        ("h1", "병상있음1", H1, 2), ("h2", "병상있음2", H2, 1), ("h3", "병상있음3", H3, 5)])
    assert [r[0] for r in rows] == ["h1", "h2", "h3", "a", "b"]


def test_3_5_2_3_start_hospital_and_unreachable():
    links = [L(1, S, A, 60)]
    sr = ShortestRoad(links, [])
    sr.dijkstra(S)
    rows = sr.sort_hospitals([("here", "사고지점병원", S, 3), ("a", "A병원", A, 3), ("x", "못감", 99, 3)])
    assert rows[0][0] == "here" and rows[0][3] == 0
    assert [r[0] for r in rows] == ["here", "a"]            # 갈 수 없는 병원은 목록에 없다
    assert sr.make_route(99) == []


def test_3_4_3_table_beds_none_goes_last():
    links = [L(1, S, H1, 30), L(2, S, H2, 90)]
    sr = ShortestRoad(links, [])
    sr.dijkstra(S)
    rows = sr.sort_hospitals([("n", "정보없음", H1, None), ("ok", "병상있음", H2, 1)])
    assert [r[0] for r in rows] == ["ok", "n"]
    assert rows[1][2] is None


def test_sort_before_dijkstra_raises():
    with pytest.raises(ValueError):
        ShortestRoad([], []).sort_hospitals([])


def test_dummy_data_end_to_end_no_error():
    nodes, links, is_dummy = RoadApi("없음", "없음").load_node_link()
    assert is_dummy
    sr = ShortestRoad(links, [(101, 30), (103, 20)])
    sr.dijkstra(1)
    rows = sr.sort_hospitals([("h4", "대구역병원", 4, 2), ("h5", "경북대병원", 5, 0), ("h2", "반월당병원", 2, 1)])
    assert [r[0] for r in rows] == ["h2", "h4", "h5"]   # 병상 있는 병원 중 빠른 h2(약 32초)가 먼저, 병상 0인 h5는 맨 뒤
    assert all(r[3] >= 0 and r[4] > 0 and r[5] >= 2 for r in rows)


def test_3_5_same_time_shorter_distance_first():
    """도착 시간이 같으면 거리가 짧은 병원이 먼저 (2주차 정렬 한 줄)
    병원1: 600m 36km/h = 60초 / 병원2: 300m 18km/h = 60초 (시간은 같고 거리는 병원2가 짧다)"""
    links = [(1, S, H1, 600, 36), (2, S, H2, 300, 18)]
    sr = ShortestRoad(links, [])
    sr.dijkstra(S)
    rows = sr.sort_hospitals([("h1", "병원1", H1, 3), ("h2", "병원2", H2, 3)])
    assert [r[0] for r in rows] == ["h2", "h1"]
    assert rows[0][3] == pytest.approx(1.0) and rows[1][3] == pytest.approx(1.0)
    assert [r[4] for r in rows] == [300.0, 600.0]
    # 입력 순서를 바꿔도 같은 결과
    rows = sr.sort_hospitals([("h2", "병원2", H2, 3), ("h1", "병원1", H1, 3)])
    assert [r[0] for r in rows] == ["h2", "h1"]
