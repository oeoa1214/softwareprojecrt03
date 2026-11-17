import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from check_linkspeed import read_speeds, compare_ids
from shortest_road import ShortestRoad


def _write(tmp_path, items):
    p = tmp_path / "linkspeed.json"
    p.write_text(json.dumps({"body": {"items": {"item": items}}}), encoding="utf-8")
    return str(p)


def test_read_speeds_converts_id_to_int(tmp_path):
    p = _write(tmp_path, [{"STD_LINK_ID": "1500000100", "LINK_SPEED": 27, "ATMS_TM": "20261116114500"}])
    assert read_speeds(p) == [(1500000100, 27.0)]


def test_compare_ids_counts_matches(tmp_path):
    p = _write(tmp_path, [{"STD_LINK_ID": "1", "LINK_SPEED": 30}, {"STD_LINK_ID": "2", "LINK_SPEED": 30},
                          {"STD_LINK_ID": "99", "LINK_SPEED": 30}])
    links = [(1, 10, 11, 100.0, 50), (2, 11, 12, 100.0, 50)]
    assert compare_ids(read_speeds(p), links) == (3, 2, [99])


def test_duplicate_ids_do_not_break_shortest_road(tmp_path):
    # 같은 번호 1이 18, 21km/h로 두 번 나와도 오류 없이 계산된다 (마지막 값이 쓰인다)
    p = _write(tmp_path, [{"STD_LINK_ID": "1", "LINK_SPEED": 18}, {"STD_LINK_ID": "1", "LINK_SPEED": 21}])
    sr = ShortestRoad([(1, 10, 11, 100.0, 50)], read_speeds(p))
    assert sr.dijkstra(10)[11] > 0
