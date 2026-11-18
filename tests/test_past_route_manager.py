import os
import sys
from datetime import datetime

# 한 칸 위 폴더(프로젝트 폴더)에서 past_route_manager.py, repository.py를 찾게 한다
PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT)

import pytest
from past_route_manager import PastRouteManager, MSG_ID, MSG_NAME, MSG_DATE
from repository import Repository
from road_api import RoadApi

DATA = os.path.join(PROJECT, "data")

# 가짜 병원 (dummy_node.csv의 교차로 5번 · 2번 근처)
H1 = ("A0001", "경북대병원", 35.8700, 128.6050, 5, "대구 중구 동덕로 130", "053-200-5114", 3)
H2 = ("A0002", "계명대동산병원", 35.8650, 128.5930, 2, "대구 중구 달성로 56", "053-250-7114", 0)


@pytest.fixture
def setup(tmp_path):
    """더미 도로 + 가짜 병원 2곳 + 저장된 경로 2개(11/9 경북대병원, 11/10 계명대동산병원)"""
    repo = Repository(str(tmp_path / "t.db"))
    dummy_node = os.path.join(DATA, "dummy_node.csv")
    dummy_link = os.path.join(DATA, "dummy_link.csv")
    nodes, links, _ = RoadApi(dummy_node, dummy_link, dummy_node, dummy_link).load_node_link()
    repo.save_road(nodes, links)
    repo.save_hospitals([H1, H2])
    id1 = repo.save_route(35.8691, 128.5941, 1, "A0001", 1.09, 1090.0, 2, 3, True, [1, 5],
                          saved_at=datetime(2026, 11, 9, 10, 0))
    id2 = repo.save_route(35.8691, 128.5941, 1, "A0002", 0.54, 450.0, 2, 0, False, [1, 2],
                          saved_at=datetime(2026, 11, 10, 15, 30))
    yield PastRouteManager(repo), id1, id2
    repo.close()


def ids(rows):
    return [r[0] for r in rows]


# ================================================================ 검색 성공 (TE-26)
def test_TE26_all_when_empty(setup):
    """세 칸이 다 비어 있으면 전체 기록"""
    m, id1, id2 = setup
    rows, msg = m.search("", "", "")
    assert (ids(rows), msg) == ([id1, id2], None)


def test_TE26_by_id_name_date(setup):
    """TE-26: 식별 번호, 병원 명, 날짜로 검색하면 맞는 기록만 나온다"""
    m, id1, id2 = setup
    assert ids(m.search(str(id2), "", "")[0]) == [id2]
    assert ids(m.search("", "경북대병원", "")[0]) == [id1]
    assert ids(m.search("", "", "2026-11-10")[0]) == [id2]


def test_spaces_and_leading_zero(setup):
    """앞뒤 빈칸은 지우고, 001처럼 0이 붙어도 1로 읽는다"""
    m, id1, id2 = setup
    assert ids(m.search(" 00" + str(id1) + " ", "", "")[0]) == [id1]


def test_date_ok_but_no_record(setup):
    """날짜 형식은 맞는데 그날 기록이 없으면 빈 목록, 문구 없음 (계획서에 문구 없음)"""
    m, id1, id2 = setup
    assert m.search("", "", "2026-11-11") == ([], None)


# ================================================================ 형식이 틀림 (TE-19 · TE-21)
def test_TE21_id_not_positive_integer(setup):
    """TE-21 · EX-09: 식별 번호에 1 이상의 정수가 아닌 값을 넣으면 안내 문구"""
    m, id1, id2 = setup
    for text in ["abc", "0", "-1", "1.5", "일"]:
        assert m.search(text, "", "") == ([], MSG_ID)


def test_TE19_wrong_date_format(setup):
    """TE-19 · EX-10: 날짜가 2026-11-09 형식이 아니면 안내 문구"""
    m, id1, id2 = setup
    for text in ["2026/11/10", "20261110", "2026-1-9", "2026-13-40", "내일"]:
        assert m.search("", "", text) == ([], MSG_DATE)


# ================================================================ 찾는 기록이 없음 (TE-20 · 3.2.4)
def test_TE20_hospital_not_found(setup):
    """TE-20 · EX-08: 없는 병원 명을 넣으면 「병원명을 다시 입력해주세요.」"""
    m, id1, id2 = setup
    assert m.search("", "없는병원", "") == ([], MSG_NAME)


def test_id_not_found(setup):
    """3.2.4: 형식은 맞지만 없는 식별 번호면 「1 이상의 정수를 입력해주세요.」"""
    m, id1, id2 = setup
    assert m.search("999", "", "") == ([], MSG_ID)


# ================================================================ 삭제 (TE-27)
def test_TE27_delete(setup):
    """TE-27: 행을 고르고 삭제하면 기록이 지워지고, 없는 번호는 False"""
    m, id1, id2 = setup
    assert m.delete(id1) is True
    assert ids(m.search("", "", "")[0]) == [id2]
    assert m.delete(id1) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])