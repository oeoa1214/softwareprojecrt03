import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from road_api import RoadApi

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(HERE, "data")


def _api(node, link):
    return RoadApi(node_csv=node, link_csv=link,
                   dummy_node_csv=os.path.join(D, "dummy_node.csv"),
                   dummy_link_csv=os.path.join(D, "dummy_link.csv"))


def test_TE25_normal_read(tmp_path):
    n = tmp_path / "node.csv"; l = tmp_path / "link.csv"
    n.write_text("node_id,node_name,lat,lon\n10,A,35.1,128.1\n11,B,35.2,128.2\n", encoding="utf-8")
    l.write_text("link_id,f_node_id,t_node_id,length_m,max_spd\n1,10,11,500.5,60\n", encoding="utf-8")
    nodes, links, is_dummy = _api(str(n), str(l)).load_node_link()
    assert len(nodes) > 0 and len(links) > 0
    assert nodes[0] == (10, "A", 35.1, 128.1)
    assert links[0] == (1, 10, 11, 500.5, 60)
    assert isinstance(nodes[0][0], int) and isinstance(nodes[0][2], float)
    assert isinstance(links[0][3], float) and isinstance(links[0][4], int)
    assert is_dummy is False


def test_TE24_missing_file_falls_back_to_dummy(tmp_path):
    nodes, links, is_dummy = _api(str(tmp_path / "없는파일.csv"), str(tmp_path / "없는파일2.csv")).load_node_link()
    assert is_dummy is True
    assert len(nodes) == 5 and len(links) == 6


def test_TE24_broken_file_falls_back_to_dummy(tmp_path):
    n = tmp_path / "node.csv"; l = tmp_path / "link.csv"
    n.write_text("node_id,node_name,lat,lon\nabc,A,x,y\n", encoding="utf-8")   # 숫자가 아님
    l.write_text("link_id,f_node_id,t_node_id,length_m,max_spd\n1,10,11,500,60\n", encoding="utf-8")
    _, _, is_dummy = _api(str(n), str(l)).load_node_link()
    assert is_dummy is True


def test_TE24_empty_file_falls_back_to_dummy(tmp_path):
    n = tmp_path / "node.csv"; l = tmp_path / "link.csv"
    n.write_text("", encoding="utf-8"); l.write_text("", encoding="utf-8")
    _, _, is_dummy = _api(str(n), str(l)).load_node_link()
    assert is_dummy is True


def test_dummy_links_connect_only_dummy_nodes():
    nodes, links, _ = _api("없음", "없음").load_node_link()
    ids = {n[0] for n in nodes}
    assert all(f in ids and t in ids for _, f, t, _, _ in links)
