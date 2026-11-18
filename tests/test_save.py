import os
import sys

# 한 칸 위 폴더(프로젝트 폴더)에서 save.py, repository.py를 찾게 한다
PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT)

import duckdb
import pytest
from save import Save
from repository import Repository
from road_api import RoadApi
from shortest_road import ShortestRoad

DATA = os.path.join(PROJECT, "data")

# 가짜 병원 (dummy_node.csv의 교차로 5번 · 2번 근처)
H1 = ("A0001", "경북대병원", 35.8700, 128.6050, 5, "대구 중구 동덕로 130", "053-200-5114", 3)
H2 = ("A0002", "계명대동산병원", 35.8650, 128.5930, 2, "대구 중구 달성로 56", "053-250-7114", 0)
ACC = (35.8691, 128.5941, 1)      # 사고 위치 (위도, 경도, 교차로 1번 동성로)


@pytest.fixture
def setup(tmp_path):
    """더미 도로 + 가짜 병원 2곳을 넣은 임시 DB에서, 교차로 1번 사고로 병원 순서를 계산해 둔다"""
    path = str(tmp_path / "t.db")
    repo = Repository(path)
    dummy_node = os.path.join(DATA, "dummy_node.csv")
    dummy_link = os.path.join(DATA, "dummy_link.csv")
    nodes, links, _ = RoadApi(dummy_node, dummy_link, dummy_node, dummy_link).load_node_link()
    repo.save_road(nodes, links)
    repo.save_hospitals([H1, H2])
    road = ShortestRoad(repo.get_links(), repo.get_latest_speeds())
    road.dijkstra(ACC[2])
    results = road.sort_hospitals(repo.get_hospitals_for_sort())   # 경북대병원(병상 3) → 계명대동산병원(병상 0)
    yield repo, path, results, road
    repo.close()


def count(path, table):
    con = duckdb.connect(path)
    n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    con.close()
    return n


def test_TE13_save_success(setup):
    """TE-13: 병원을 고르고 저장하면 결과 번호가 나오고, 과거 경로에서 그 기록이 있다"""
    repo, path, results, road = setup
    route_id = Save(repo).save_route(*ACC, results, "A0001", road.make_route(5))
    assert route_id >= 1
    rows = repo.search_routes(route_id=route_id)
    assert len(rows) == 1
    rid, saved_at, name, beds, eta, dist, cnt = rows[0]
    assert (name, beds, dist, cnt) == ("경북대병원", 3, 1090.0, 2)


def test_recommended_flag(setup):
    """맨 앞(추천) 병원을 고르면 추천 True, 다른 병원을 고르면 False로 저장된다"""
    repo, path, results, road = setup
    first = Save(repo).save_route(*ACC, results, "A0001", road.make_route(5))
    second = Save(repo).save_route(*ACC, results, "A0002", road.make_route(2))
    repo.close()
    con = duckdb.connect(path)
    flags = dict(con.execute("SELECT route_id, is_recommended FROM route_result").fetchall())
    con.close()
    assert flags == {first: True, second: False}


def test_TE18_no_hospital_selected(setup):
    """TE-18 · EX-11: 병원을 고르지 않고 저장하면 -1, 아무것도 저장하지 않는다"""
    repo, path, results, road = setup
    assert Save(repo).save_route(*ACC, results, None, []) == -1
    assert repo.search_routes() == []


def test_TE23_db_fail(setup):
    """TE-23 · EX-12: DB 저장이 실패하면 -2, 세 테이블 모두 아무것도 남지 않는다"""
    repo, path, results, road = setup
    bad = [("없는병원", "가짜", 1, 1.0, 100.0, 2)]          # hospital 테이블에 없는 병원 → 외래키 오류
    assert Save(repo).save_route(*ACC, bad, "없는병원", [1, 5]) == -2
    repo.close()
    assert count(path, "accident_point") == 0
    assert count(path, "route_result") == 0
    assert count(path, "route_node") == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])