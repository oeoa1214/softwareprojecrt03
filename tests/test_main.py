import os
import sys
from datetime import datetime

# 한 칸 위 폴더(프로젝트 폴더)에서 main.py, repository.py를 찾게 한다
PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT)

import pytest
from main import (prepare, MSG_HOSPITAL_FAIL, MSG_SPEED_FAIL, MSG_ROAD_FAIL,
                  MSG_NO_ROAD, MSG_NO_HOSPITAL)
from repository import Repository
from road_api import RoadApi

DATA = os.path.join(PROJECT, "data")
DN = os.path.join(DATA, "dummy_node.csv")
DL = os.path.join(DATA, "dummy_link.csv")

# 가짜 병원 응답: 교차로 5번(경북대병원앞) 위, 교차로 2번(반월당) 위, 서울(대구 밖)
API_ROWS = [("A0001", "경북대병원", 35.8700, 128.6050, None, "대구 중구 동덕로 130", "053-200-5114", 3),
            ("A0002", "계명대동산병원", 35.8650, 128.5930, None, "대구 중구 달성로 56", "053-250-7114", 0),
            ("A0009", "서울병원", 37.5600, 126.9700, None, "서울", "02-000-0000", 5)]


class FakeRoadApi:
    """RoadApi 대신 쓰는 가짜: 도로망은 더미 CSV, 속도는 정해 둔 값"""
    def __init__(self, road_dummy=False, broken=False, speed_ok=True):
        self.road_dummy, self.broken, self.speed_ok = road_dummy, broken, speed_ok

    def load_node_link(self):
        if self.broken:
            raise OSError("도로망 CSV도 더미 CSV도 없음")
        nodes, links, _ = RoadApi(DN, DL, DN, DL).load_node_link()
        return nodes, links, self.road_dummy

    def load_speeds(self):
        if self.speed_ok:
            return [(101, 30.0), (105, 40.0)], datetime(2026, 11, 18, 9, 0), False
        return [], None, True


class FakeHospitalApi:
    """HospitalApi 대신 쓰는 가짜: 정해 둔 (rows, is_dummy)를 돌려준다"""
    def __init__(self, rows, is_dummy):
        self.rows, self.is_dummy = rows, is_dummy

    def load_hospitals(self):
        return self.rows, self.is_dummy


@pytest.fixture
def repo(tmp_path):
    r = Repository(str(tmp_path / "t.db"))
    yield r
    r.close()


# ================================================================ 정상 시작
def test_start_normal(repo):
    """API가 다 되면 안내 문구 없이 준비되고, 병원 · 속도가 저장된다"""
    parts, messages = prepare(repo, FakeRoadApi(), FakeHospitalApi(API_ROWS, False))
    assert parts is not None and messages == []
    assert set(parts) == {"repo", "crossroad", "road", "hospital_search", "save", "past_route"}
    assert len(repo.get_hospitals()) == 3
    assert len(repo.get_latest_speeds()) == 2


def test_hospital_gets_nearest_crossroad(repo):
    """병원에 가장 가까운 교차로가 붙고, 대구 밖 병원은 None이라 경로 계산에서 빠진다"""
    prepare(repo, FakeRoadApi(), FakeHospitalApi(API_ROWS, False))
    nodes = {h[0]: h[4] for h in repo.get_hospitals()}
    assert nodes == {"A0001": 5, "A0002": 2, "A0009": None}
    assert sorted(h[0] for h in repo.get_hospitals_for_sort()) == ["A0001", "A0002"]


def test_restart_does_not_duplicate(repo):
    """프로그램을 다시 켜도 도로망 · 병원이 두 번 들어가지 않는다"""
    prepare(repo, FakeRoadApi(), FakeHospitalApi(API_ROWS, False))
    prepare(repo, FakeRoadApi(), FakeHospitalApi(API_ROWS, False))
    assert len(repo.get_nodes()) == 5
    assert len(repo.get_hospitals()) == 3


# ================================================================ 도로망 (흐름도 2, EX-03)
def test_EX03_road_dummy(repo):
    """도로망 CSV를 못 읽어 더미를 쓰면 EX-03 문구를 띄우고 계속 실행한다"""
    parts, messages = prepare(repo, FakeRoadApi(road_dummy=True), FakeHospitalApi(API_ROWS, False))
    assert parts is not None and messages == [MSG_ROAD_FAIL]


def test_no_road_exits(repo):
    """도로망 CSV도 더미 CSV도 없으면 안내 후 종료"""
    assert prepare(repo, FakeRoadApi(broken=True), FakeHospitalApi(API_ROWS, False)) == (None, [MSG_NO_ROAD])


# ================================================================ 병원 (흐름도 4, EX-01, D-8)
def test_EX01_api_fail_uses_saved_hospitals(repo):
    """병원 API가 실패해도 지난번에 저장한 병원이 있으면 그걸 쓴다"""
    prepare(repo, FakeRoadApi(), FakeHospitalApi(API_ROWS, False))
    parts, messages = prepare(repo, FakeRoadApi(), FakeHospitalApi([], True))
    assert parts is not None and messages == [MSG_HOSPITAL_FAIL]
    assert len(repo.get_hospitals()) == 3


def test_EX01_api_fail_uses_dummy(repo):
    """병원 API가 실패하고 저장된 병원이 없으면 더미 병원을 저장해서 쓴다"""
    parts, messages = prepare(repo, FakeRoadApi(), FakeHospitalApi(API_ROWS[:1], True))
    assert parts is not None and messages == [MSG_HOSPITAL_FAIL]
    assert [h[0] for h in repo.get_hospitals()] == ["A0001"]


def test_no_hospital_exits(repo):
    """병원 API 실패 + 저장된 병원 없음 + 더미도 없음이면 안내 후 종료 (D-8)"""
    parts, messages = prepare(repo, FakeRoadApi(), FakeHospitalApi([], True))
    assert parts is None
    assert messages == [MSG_HOSPITAL_FAIL, MSG_NO_HOSPITAL]


# ================================================================ 속도 (흐름도 5, EX-02)
def test_EX02_speed_fail(repo):
    """속도 API가 실패하면 EX-02 문구를 띄우고 계속 실행한다 (저장된 속도가 없으면 제한 속도로 계산)"""
    parts, messages = prepare(repo, FakeRoadApi(speed_ok=False), FakeHospitalApi(API_ROWS, False))
    assert parts is not None and messages == [MSG_SPEED_FAIL]
    assert repo.get_latest_speeds() == []


# ================================================================ TE-29 계산 부분 (D-12)
def test_TE29_same_crossroad_0m(repo):
    """TE-29: 사고 교차로가 병원 교차로(5번)면 그 병원이 거리 0m, 도착 0분, 교차로 1개로 목록 맨 앞"""
    parts, _ = prepare(repo, FakeRoadApi(), FakeHospitalApi(API_ROWS, False))
    road = parts["road"]
    road.dijkstra(5)
    first = road.sort_hospitals(repo.get_hospitals_for_sort())[0]
    hpid, name, beds, eta_min, distance_m, node_count = first
    assert (hpid, eta_min, distance_m, node_count) == ("A0001", 0, 0, 1)
    assert road.make_route(5) == [5]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])