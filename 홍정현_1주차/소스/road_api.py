"""RoadApi - 표준노드링크 읽기 (홍정현 담당 메소드).

도로 속도 메소드는 오은찬이 같은 클래스에 추가한다.
"""
import csv


class RoadApi:
    def __init__(self, node_csv="data/node.csv", link_csv="data/link.csv",
                 dummy_node_csv="data/dummy_node.csv", dummy_link_csv="data/dummy_link.csv"):
        self.__node_csv = node_csv
        self.__link_csv = link_csv
        self.__dummy_node_csv = dummy_node_csv
        self.__dummy_link_csv = dummy_link_csv

    def load_node_link(self):
        """반환: (nodes, links, is_dummy)
        nodes = [(node_id:int, node_name:str, lat:float, lon:float), ...]
        links = [(link_id:int, f_node_id:int, t_node_id:int, length_m:float, max_spd:int), ...]
        is_dummy = 진짜 파일을 못 읽어 더미를 썼으면 True"""
        try:
            nodes = self.__read_nodes(self.__node_csv)
            links = self.__read_links(self.__link_csv)
            return nodes, links, False
        except (OSError, ValueError, KeyError, csv.Error):
            nodes = self.__read_nodes(self.__dummy_node_csv)
            links = self.__read_links(self.__dummy_link_csv)
            return nodes, links, True

    def __read_nodes(self, path):
        nodes = []
        with open(path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                nodes.append((int(row["node_id"]), row["node_name"],
                              float(row["lat"]), float(row["lon"])))
        if not nodes:
            raise ValueError("node 파일이 비어 있음")
        return nodes

    def __read_links(self, path):
        links = []
        with open(path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                links.append((int(row["link_id"]), int(row["f_node_id"]),
                              int(row["t_node_id"]), float(row["length_m"]),
                              int(row["max_spd"])))
        if not links:
            raise ValueError("link 파일이 비어 있음")
        return links
