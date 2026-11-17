import json
import os
import sys
from datetime import datetime

# 한 칸 위 폴더(프로젝트 폴더)에서 road_api.py, repository.py를 찾게 한다
PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT)

import pytest
from road_api import RoadApi

DATA = os.path.join(PROJECT, "data")
KEY = os.path.join(PROJECT, "api_key.txt")


def road_api(**kw):
    return RoadApi(node_csv=os.path.join(DATA, "node.csv"),
                   link_csv=os.path.join(DATA, "link.csv"),
                   dummy_node_csv=os.path.join(DATA, "dummy_node.csv"),
                   dummy_link_csv=os.path.join(DATA, "dummy_link.csv"), **kw)


def saved_items():
    """11/16에 받아 둔 실제 API 응답(data/linkspeed.json)의 item 목록"""
    with open(os.path.join(DATA, "linkspeed.json"), encoding="utf-8") as f:
        return json.load(f)["body"]["items"]["item"]


# ================================================================ 평균 (D-2)
def test_duplicate_ids_are_averaged():
    """같은 번호가 18, 21km/h로 두 번 나오면 19.5km/h 한 번만 남는다"""
    items = [{"STD_LINK_ID": "1", "LINK_SPEED": 18, "ATMS_TM": "20261116114500"},
             {"STD_LINK_ID": "1", "LINK_SPEED": 21, "ATMS_TM": "20261116114500"},
             {"STD_LINK_ID": "2", "LINK_SPEED": 30, "ATMS_TM": "20261116114500"}]
    speeds, collected_at = road_api().make_speeds(items)
    assert sorted(speeds) == [(1, 19.5), (2, 30.0)]
    assert collected_at == datetime(2026, 11, 16, 11, 45)


def test_bad_rows_are_skipped():
    """번호나 속도가 숫자가 아닌 줄은 빼고 나머지는 쓴다"""
    items = [{"STD_LINK_ID": "abc", "LINK_SPEED": 30},
             {"STD_LINK_ID": "3", "LINK_SPEED": None},
             {"STD_LINK_ID": "4", "LINK_SPEED": "40", "ATMS_TM": "20261116114500"}]
    speeds, _ = road_api().make_speeds(items)
    assert speeds == [(4, 40.0)]


def test_real_response_file_no_duplicates():
    """실제 응답 5510줄 → 서로 다른 번호 4805개, 중복 없음, 1500003503은 (18+21)/2"""
    speeds, collected_at = road_api().make_speeds(saved_items())
    ids = [i for i, _ in speeds]
    assert len(ids) == len(set(ids)) == 4805
    assert dict(speeds)[1500003503] == 19.5
    assert collected_at == datetime(2026, 11, 16, 11, 45)


# ================================================================ TE-03 · TE-04
def test_TE03_speeds_saved_to_db(tmp_path):
    """TE-03 저장 부분: 실제 응답의 속도가 link_speed 테이블에 저장된다 (link.csv에 있는 4723개)"""
    from repository import Repository
    nodes, links, _ = road_api().load_node_link()
    repo = Repository(str(tmp_path / "t.db"))
    repo.save_road(nodes, links)
    speeds, collected_at = road_api().make_speeds(saved_items())
    assert repo.save_speeds(speeds, collected_at) == 4723
    assert len(repo.get_latest_speeds()) == 4723
    repo.close()


@pytest.mark.skipif(not os.path.exists(KEY), reason="api_key.txt가 없어서 실제 API는 건너뜀")
def test_TE03_real_api():
    """TE-03 API 부분: 실제 API로 속도를 받는다 (api_key.txt가 있을 때만)"""
    speeds, collected_at, is_dummy = road_api(key_path=KEY).load_speeds()
    print("받은 도로 속도", len(speeds), "개 /", collected_at)
    assert is_dummy is False
    assert len(speeds) > 1000
    assert isinstance(speeds[0][0], int)


def test_TE04_no_key_file_is_dummy(tmp_path):
    """TE-04: 인증키 파일이 없으면 API 실패 → 빈 속도, is_dummy True (오류로 멈추지 않는다)"""
    result = road_api(key_path=str(tmp_path / "없는파일.txt")).load_speeds()
    assert result == ([], None, True)


def test_TE04_bad_address_is_dummy(tmp_path):
    """TE-04: 주소가 잘못돼 연결이 안 되면 API 실패 → 빈 속도, is_dummy True"""
    key = tmp_path / "key.txt"
    key.write_text("가짜키", encoding="utf-8")
    result = road_api(speed_url="https://nowhere.invalid/linkspeed", key_path=str(key)).load_speeds()
    assert result == ([], None, True)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])