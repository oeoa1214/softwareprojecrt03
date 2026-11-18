import os
import sys

# 한 칸 위 폴더(프로젝트 폴더)에서 hospital_search.py, repository.py를 찾게 한다
PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT)

import pytest
from hospital_search import HospitalSearch
from repository import Repository
from road_api import RoadApi

DATA = os.path.join(PROJECT, "data")

# 가짜 병원 (dummy_node.csv의 교차로 5번 · 2번 근처)
H1 = ("A0001", "경북대병원", 35.8700, 128.6050, 5, "대구 중구 동덕로 130", "053-200-5114", 3)
H2 = ("A0002", "계명대동산병원", 35.8650, 128.5930, 2, "대구 중구 달성로 56", "053-250-7114", 0)


@pytest.fixture
def search(tmp_path):
    """더미 도로와 가짜 병원 2곳을 넣어 둔 임시 DB로 HospitalSearch를 만든다"""
    repo = Repository(str(tmp_path / "t.db"))
    dummy_node = os.path.join(DATA, "dummy_node.csv")
    dummy_link = os.path.join(DATA, "dummy_link.csv")
    nodes, links, _ = RoadApi(dummy_node, dummy_link, dummy_node, dummy_link).load_node_link()
    repo.save_road(nodes, links)
    repo.save_hospitals([H1, H2])
    yield HospitalSearch(repo)
    repo.close()


def test_TE06_found(search):
    """TE-06: 있는 병원 이름을 넣으면 그 병원 정보(위치 · 병상 · 연락처)가 나온다"""
    assert search.search("경북대병원") == H1


def test_TE06_not_found(search):
    """TE-06 · EX-07: 없는 병원이면 None (화면이 「잘못된 입력입니다 다시 입력해주세요.」)"""
    assert search.search("없는병원") is None


def test_TE06_empty_input(search):
    """EX-07: 아무것도 안 넣거나 빈칸만 넣으면 None"""
    assert search.search("") is None
    assert search.search("   ") is None
    assert search.search(None) is None


def test_spaces_around_name_are_removed(search):
    """앞뒤에 빈칸이 붙어도 찾는다"""
    assert search.search("  계명대동산병원 ") == H2


def test_part_of_name_is_not_found(search):
    """이름 일부만 넣으면 찾지 않는다 (계획서: 같은 이름의 병원)"""
    assert search.search("경북대") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])