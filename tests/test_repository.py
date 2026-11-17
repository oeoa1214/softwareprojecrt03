import os
import sys
from datetime import datetime

# 한 칸 위 폴더(프로젝트 폴더)에서 repository.py를 찾게 한다
PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT)

import duckdb
import pytest
from repository import Repository
from road_api import RoadApi
from crossroad import Crossroad

DATA = os.path.join(PROJECT, "data")
EXPECTED = {"node", "link", "link_speed", "hospital",
            "accident_point", "route_result", "route_node"}

# 가짜 병원 (dummy_node.csv의 교차로 5번 · 2번 근처)
H1 = ("A0001", "경북대병원", 35.8700, 128.6050, 5, "대구 중구 동덕로 130", "053-200-5114", 3)
H2 = ("A0002", "계명대동산병원", 35.8650, 128.5930, 2, "대구 중구 달성로 56", "053-250-7114", 0)


def road_api(node_file="node.csv", link_file="link.csv"):
    return RoadApi(node_csv=os.path.join(DATA, node_file),
                   link_csv=os.path.join(DATA, link_file),
                   dummy_node_csv=os.path.join(DATA, "dummy_node.csv"),
                   dummy_link_csv=os.path.join(DATA, "dummy_link.csv"))


@pytest.fixture
def repo(tmp_path):
    """더미 교차로 5개 · 도로 6개를 넣어 둔 테스트용 DB"""
    r = Repository(str(tmp_path / "t.db"))
    nodes, links, _ = road_api("dummy_node.csv", "dummy_link.csv").load_node_link()
    r.save_road(nodes, links)
    yield r
    r.close()


def count(db_path, table):
    """테스트에서 테이블 행 수를 직접 센다"""
    con = duckdb.connect(db_path)
    n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    con.close()
    return n


# ================================================================ 테이블
def test_tables_created(tmp_path):
    """AD-01 사전 확인: 테이블 7개가 만들어지는가"""
    r = Repository(str(tmp_path / "t.db"))
    assert set(r.table_names()) == EXPECTED
    r.close()


def test_create_tables_twice_no_error(tmp_path):
    """프로그램을 다시 켤 때처럼 한 번 더 만들어도 오류가 없는가"""
    r = Repository(str(tmp_path / "t.db"))
    r.create_tables()
    assert set(r.table_names()) == EXPECTED
    r.close()


def test_reopen_same_file(tmp_path):
    """DB 파일을 닫았다가 다시 열어도 테이블이 그대로 있는가"""
    path = str(tmp_path / "t.db")
    Repository(path).close()
    r = Repository(path)
    assert set(r.table_names()) == EXPECTED
    r.close()


# ================================================================ node · link
def test_dummy_road_save_and_get_same(tmp_path):
    """더미 CSV로 저장한 값과 꺼낸 값이 같은가"""
    nodes, links, _ = road_api("dummy_node.csv", "dummy_link.csv").load_node_link()
    r = Repository(str(tmp_path / "t.db"))
    assert r.save_road(nodes, links) is True
    assert sorted(r.get_nodes()) == sorted(nodes)
    assert sorted(r.get_links()) == sorted(links)
    r.close()


def test_TE25_real_node_link_saved(tmp_path):
    """TE-25: 표준노드링크(실제 node.csv · link.csv)의 교차로와 도로구간이 DB에 저장되는가"""
    nodes, links, is_dummy = road_api().load_node_link()
    assert is_dummy is False
    r = Repository(str(tmp_path / "t.db"))
    assert r.save_road(nodes, links) is True
    saved_nodes = r.get_nodes()
    saved_links = r.get_links()
    print("교차로", len(saved_nodes), "개 / 도로", len(saved_links), "개 저장")
    assert len(saved_nodes) == len(nodes) == 28441
    assert len(saved_links) == len(links) == 40914
    assert set(saved_nodes) == set(nodes)
    assert set(saved_links) == set(links)
    r.close()


def test_save_road_twice_skips(tmp_path):
    """도로망이 이미 있으면 다시 넣지 않는다 (중복 없음)"""
    nodes, links, _ = road_api("dummy_node.csv", "dummy_link.csv").load_node_link()
    r = Repository(str(tmp_path / "t.db"))
    assert r.has_road() is False
    assert r.save_road(nodes, links) is True
    assert r.has_road() is True
    assert r.save_road(nodes, links) is False
    assert len(r.get_nodes()) == len(nodes)
    assert len(r.get_links()) == len(links)
    r.close()


def test_id_is_varchar_in_db_and_int_outside(tmp_path):
    """규칙 5: 번호는 DB 안에서 VARCHAR, 꺼내면 int"""
    path = str(tmp_path / "t.db")
    nodes, links, _ = road_api("dummy_node.csv", "dummy_link.csv").load_node_link()
    r = Repository(path)
    r.save_road(nodes, links)
    assert isinstance(r.get_nodes()[0][0], int)
    assert isinstance(r.get_links()[0][1], int)
    r.close()
    con = duckdb.connect(path)
    assert con.execute("SELECT typeof(node_id) FROM node LIMIT 1").fetchone()[0] == "VARCHAR"
    assert con.execute("SELECT typeof(f_node_id) FROM link LIMIT 1").fetchone()[0] == "VARCHAR"
    con.close()


def test_crossroad_points_work_with_crossroad(tmp_path):
    """get_crossroad_points()를 Crossroad에 그대로 넣어 쓸 수 있는가"""
    nodes, links, _ = road_api().load_node_link()
    r = Repository(str(tmp_path / "t.db"))
    r.save_road(nodes, links)
    cross = Crossroad(r.get_crossroad_points())
    node_id, name, lat, lon = nodes[0]
    assert cross.find_crossroad(lat, lon) == node_id      # 교차로 위를 누르면 그 교차로
    assert cross.find_crossroad(37.56, 126.97) == -1      # 서울
    r.close()


def test_save_road_rollback_on_error(tmp_path):
    """없는 교차로를 가리키는 도로가 있으면(외래키 오류) 교차로도 저장되지 않는다 (ROLLBACK)"""
    nodes = [(1, "A", 35.87, 128.60), (2, "B", 35.88, 128.61)]
    bad_links = [(10, 1, 999, 100.0, 60)]          # 999번 교차로는 없음
    r = Repository(str(tmp_path / "t.db"))
    with pytest.raises(Exception):
        r.save_road(nodes, bad_links)
    assert r.has_road() is False
    r.close()


# ================================================================ link_speed
def test_TE03_save_speeds_only_known_links(repo):
    """TE-03 저장 부분: link에 있는 번호만 저장된다 (없는 번호는 뺀다)"""
    t = datetime(2026, 11, 16, 11, 45)
    saved = repo.save_speeds([(101, 30.0), (102, 40.0), (9999, 50.0)], t)
    assert saved == 2
    assert sorted(repo.get_latest_speeds()) == [(101, 30.0), (102, 40.0)]


def test_latest_speeds_only(repo):
    """두 번 저장하면 가장 최근에 잰 속도만 나온다"""
    repo.save_speeds([(101, 30.0), (102, 40.0)], datetime(2026, 11, 16, 11, 45))
    repo.save_speeds([(101, 45.0)], datetime(2026, 11, 17, 9, 0))
    assert repo.get_latest_speeds() == [(101, 45.0)]


def test_latest_speeds_empty(repo):
    """속도를 한 번도 저장하지 않았으면 빈 목록"""
    assert repo.get_latest_speeds() == []


def test_speeds_work_with_get_links_shape(repo):
    """꺼낸 속도의 번호가 get_links의 번호와 같은 모양(int)이다"""
    repo.save_speeds([(101, 30.0)], datetime(2026, 11, 16, 11, 45))
    link_ids = {l[0] for l in repo.get_links()}
    assert repo.get_latest_speeds()[0][0] in link_ids


# ================================================================ hospital
def test_TE12_hospital_save_and_get(repo):
    """TE-12: 저장한 병원이 그대로 조회되는가"""
    repo.save_hospitals([H1, H2])
    assert sorted(repo.get_hospitals()) == sorted([H1, H2])


def test_hospital_second_save_updates_beds_only(repo):
    """이미 있는 병원은 병상 수만 바뀌고 행 수는 그대로다"""
    repo.save_hospitals([H1, H2])
    changed = ("A0001", "다른이름", 35.0, 128.0, 5, "다른주소", "000-0000-0000", 7)
    repo.save_hospitals([changed])
    rows = {h[0]: h for h in repo.get_hospitals()}
    assert len(rows) == 2
    assert rows["A0001"][7] == 7               # 병상만 바뀜
    assert rows["A0001"][1] == "경북대병원"      # 이름은 그대로


def test_hospitals_for_sort_shape_and_no_node(repo):
    """sort_hospitals에 넣을 모양 (hpid, name, node_id:int, beds), 교차로 없는 병원은 빠진다"""
    no_node = ("A0003", "교차로없는병원", 35.9, 128.7, None, "주소", "053-000-0000", 5)
    repo.save_hospitals([H1, H2, no_node])
    rows = sorted(repo.get_hospitals_for_sort())
    assert rows == [("A0001", "경북대병원", 5, 3), ("A0002", "계명대동산병원", 2, 0)]


def test_get_hospital_and_find_by_name(repo):
    """선택한 병원(hpid)과 이름으로 찾기, 없으면 None"""
    repo.save_hospitals([H1, H2])
    assert repo.get_hospital("A0002") == H2
    assert repo.get_hospital("없는번호") is None
    assert repo.find_hospital_by_name("경북대병원") == H1
    assert repo.find_hospital_by_name("없는병원") is None


# ================================================================ 경로 저장 · 조회 · 삭제
def save_sample_route(repo, hpid="A0001", saved_at=None):
    """사고 교차로 1번 → 5번(경북대병원) 경로를 저장한다"""
    return repo.save_route(35.8691, 128.5941, 1, hpid, 3.0, 1090.0, 2, 3, True, [1, 5],
                           saved_at=saved_at)


def test_TE13_save_route(repo):
    """TE-13 저장 부분: 경로를 저장하면 번호가 나오고, 그 번호로 찾을 수 있다"""
    repo.save_hospitals([H1, H2])
    route_id = save_sample_route(repo)
    assert isinstance(route_id, int)
    rows = repo.search_routes(route_id=route_id)
    assert len(rows) == 1
    rid, saved_at, name, beds, eta, dist, cnt = rows[0]
    assert (rid, name, beds, eta, dist, cnt) == (route_id, "경북대병원", 3, 3.0, 1090.0, 2)


def test_TE23_save_route_failure_leaves_nothing(tmp_path):
    """TE-23 앞부분: 저장이 실패하면(없는 병원) None이 나오고 아무것도 남지 않는다"""
    path = str(tmp_path / "t.db")
    r = Repository(path)
    nodes, links, _ = road_api("dummy_node.csv", "dummy_link.csv").load_node_link()
    r.save_road(nodes, links)
    assert save_sample_route(r, hpid="없는병원") is None
    r.close()
    assert count(path, "accident_point") == 0
    assert count(path, "route_result") == 0
    assert count(path, "route_node") == 0


def test_TE26_search_by_id_name_date(repo):
    """TE-26: 식별 번호, 병원 명, 날짜로 검색하면 맞는 기록만 나온다"""
    repo.save_hospitals([H1, H2])
    id1 = save_sample_route(repo, "A0001", datetime(2026, 11, 9, 10, 0))
    id2 = save_sample_route(repo, "A0002", datetime(2026, 11, 10, 15, 30))
    assert [r[0] for r in repo.search_routes()] == [id1, id2]                        # 전체
    assert [r[0] for r in repo.search_routes(route_id=id2)] == [id2]                 # 식별 번호
    assert [r[0] for r in repo.search_routes(hospital_name="경북대병원")] == [id1]    # 병원 명
    assert [r[0] for r in repo.search_routes(date="2026-11-10")] == [id2]            # 날짜
    assert repo.search_routes(date="2026-11-11") == []                               # 없는 날짜


def test_TE27_delete_route(tmp_path):
    """TE-27: 지우면 세 테이블에서 모두 사라지고, 없는 번호는 False"""
    path = str(tmp_path / "t.db")
    r = Repository(path)
    nodes, links, _ = road_api("dummy_node.csv", "dummy_link.csv").load_node_link()
    r.save_road(nodes, links)
    r.save_hospitals([H1, H2])
    route_id = save_sample_route(r)
    assert r.delete_route(route_id) is True
    assert r.search_routes() == []
    assert r.delete_route(route_id) is False          # 이미 지운 번호
    r.close()
    assert count(path, "route_node") == 0
    assert count(path, "route_result") == 0
    assert count(path, "accident_point") == 0


def test_hospital_beds_update_after_route_saved(repo):
    """경로가 병원을 참조하고 있어도 다음 실행 때 병상 수를 바꿀 수 있다"""
    repo.save_hospitals([H1, H2])
    save_sample_route(repo)
    repo.save_hospitals([("A0001",) + H1[1:7] + (9,)])
    assert repo.get_hospital("A0001")[7] == 9


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])