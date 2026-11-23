"""RoadApi - 표준노드링크 읽기 (홍정현 담당 메소드).

도로 속도 메소드는 오은찬이 같은 클래스에 추가한다.
"""
# csv: 교차로·도로 CSV 파일을 읽는다
import csv
# json: 속도 API 응답(JSON 글자)을 파이썬 사전으로 바꾼다
import json
# urllib.parse: 주소 뒤에 붙일 질문(serviceKey, pageNo 등)을 만들고 인증키 글자를 풀어 준다
import urllib.parse
# urllib.request: 인터넷으로 API 주소를 불러 응답을 받는다
import urllib.request
# datetime: 속도를 잰 시간 글자(20261116114500)를 날짜·시간 값으로 바꾼다
from datetime import datetime

# 대구광역시 교통소통정보 구간 소통 정보 (IF-002)
SPEED_URL = "https://apis.data.go.kr/6270000/service/rest1/linkspeed"


class RoadApi:
    def __init__(self, node_csv="data/node.csv", link_csv="data/link.csv",
                 dummy_node_csv="data/dummy_node.csv", dummy_link_csv="data/dummy_link.csv",
                 speed_url=SPEED_URL, key_path="api_key.txt"):
        self.__node_csv = node_csv
        self.__link_csv = link_csv
        self.__dummy_node_csv = dummy_node_csv
        self.__dummy_link_csv = dummy_link_csv
        self.__speed_url = speed_url      # 도로 속도 API 주소 (오은찬 추가)
        self.__key_path = key_path        # API 인증키 파일 (오은찬 추가, GitHub에 올리지 않음)

    def load_node_link(self):
        """반환: (nodes, links, is_dummy)
        nodes = [(node_id:int, node_name:str, lat:float, lon:float), ...]
        links = [(link_id:int, f_node_id:int, t_node_id:int, length_m:float, max_spd:int), ...]
        is_dummy = 진짜 파일을 못 읽어 더미를 썼으면 True"""
        try:
            nodes = self.__read_nodes(self.__node_csv)
            links = self.__read_links(self.__link_csv)
            return nodes, links, False
        # 파일이 없음 / 숫자가 아님 / 칸 이름이 다름 / CSV 모양이 깨짐 -> 더미 CSV로 대신 읽는다 (EX-03)
        except (OSError, ValueError, KeyError, csv.Error):
            nodes = self.__read_nodes(self.__dummy_node_csv)
            links = self.__read_links(self.__dummy_link_csv)
            return nodes, links, True

    def __read_nodes(self, path):
        nodes = []
        # utf-8-sig: 엑셀 등이 파일 맨 앞에 붙이는 눈에 안 보이는 표시(BOM)가 있어도 없어도 읽는다
        with open(path, newline="", encoding="utf-8-sig") as f:
            # DictReader: 첫 줄(칸 이름)을 기준으로 한 줄씩 {칸 이름: 값} 사전으로 읽는다
            for row in csv.DictReader(f):
                nodes.append((int(row["node_id"]), row["node_name"],
                              float(row["lat"]), float(row["lon"])))
        # 파일은 열렸지만 내용이 없으면 읽기 실패로 보고 더미를 쓰게 한다
        if not nodes:
            raise ValueError("node 파일이 비어 있음")
        return nodes

    def __read_links(self, path):
        links = []
        # (교차로 읽기와 같은 방식)
        with open(path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                links.append((int(row["link_id"]), int(row["f_node_id"]),
                              int(row["t_node_id"]), float(row["length_m"]),
                              int(row["max_spd"])))
        # 파일은 열렸지만 내용이 없으면 읽기 실패로 보고 더미를 쓰게 한다
        if not links:
            raise ValueError("link 파일이 비어 있음")
        return links

    # ================================================================== 도로 속도 (오은찬 추가)
    
    #api 로드 스피드 호출하고 실패하면 더비 true반환한느 함수 
    def load_speeds(self):
        """대구 교통소통정보 API(IF-002)에서 도로 속도를 받는다 (시작 흐름도 5).
        반환: (speeds, collected_at, is_dummy)
        speeds = [(link_id:int, speed_kmh:float), ...]  같은 번호는 평균을 내서 한 번만 (D-2)
        collected_at = 속도를 잰 시간 (datetime) / 실패하면 None
        is_dummy = API를 못 받았으면 True. 이때 speeds는 빈 목록이다
                   (main이 저장된 속도를 쓰고, 그것도 없으면 ShortestRoad가 제한 속도를 쓴다)"""
        try:
            key = self.__read_key()
            items = []
            page = 1
            # API는 한 번에 최대 1000개씩 주므로, 전체 개수(totalCount)에 닿을 때까지 쪽(page)을 넘기며 받는다
            while True:
                body = self.__request_page(key, page, 1000)
                new_items = self.__items_of(body)
                items += new_items
                total = int(body.get("totalCount", 0))
                # 더 받을 것이 없거나 전부 받았으면 반복을 끝낸다
                if not new_items or len(items) >= total:
                    break
                page += 1
            speeds, collected_at = self.make_speeds(items)
            if not speeds:
                raise ValueError("속도 응답이 비어 있음")
            return speeds, collected_at, False
        except (OSError, ValueError, KeyError, TypeError):
            return [], None, True
    #같은 도로번호가 여러번 나오면 평균 속도 하는 함수!
    def make_speeds(self, items):
        """API 응답의 item 목록을 speeds로 바꾼다.
        items = [{"STD_LINK_ID": "1500000100", "LINK_SPEED": 27, "ATMS_TM": "20261116114500"}, ...]
        반환: (speeds, collected_at)
        speeds = [(link_id:int, speed_kmh:float), ...]  같은 번호가 여러 번 나오면 속도 평균 (D-2)
        collected_at = ATMS_TM 중 가장 늦은 시간 (없으면 지금 시간)
        번호나 속도가 숫자가 아닌 줄은 뺀다."""
        # 같은 도로 번호가 여러 번 나오면 평균을 내기 위해 속도의 합과 개수를 모은다 (D-2)
        sums = {}      # {link_id: [속도 합, 개수]}
        times = []
        for it in items:
            try:
                link_id = int(it["STD_LINK_ID"])
                speed = float(it["LINK_SPEED"])
            except (KeyError, TypeError, ValueError):
                continue
            s = sums.setdefault(link_id, [0.0, 0])
            s[0] += speed
            s[1] += 1
            try:
                times.append(datetime.strptime(str(it["ATMS_TM"]), "%Y%m%d%H%M%S"))
            except (KeyError, ValueError):
                pass
        # 평균 속도 = 속도 합 ÷ 개수
        speeds = [(link_id, total / count) for link_id, (total, count) in sums.items()]
        # 여러 줄 중 가장 늦은 시간을 '속도를 잰 시간'으로 쓴다. 시간 정보가 하나도 없으면 지금 시간
        collected_at = max(times) if times else datetime.now().replace(microsecond=0)
        return speeds, collected_at


    #readkey는  키를 코드에 직접 쓰지 않기 위해 쓴다!
    def __read_key(self):
        """api_key.txt 첫 줄의 인증키. Encoding 키(%가 들어 있음)를 넣어도 Decoding 키로 바꿔 쓴다."""
        with open(self.__key_path, encoding="utf-8") as f:
            key = f.readline().strip()
        if not key:
            raise ValueError("인증키가 비어 있음")
        # 공공데이터포털은 Encoding 키(%가 든 글자)와 Decoding 키를 준다. urlencode가 다시 인코딩하므로 먼저 풀어서 넘겨야 키가 두 번 인코딩되지 않는다
        return urllib.parse.unquote(key)

    def __request_page(self, key, page, rows):
        """속도 API 한 쪽을 받아 body를 돌려준다. 결과 코드가 00이 아니면 ValueError"""
        # 주소 뒤에 붙일 ?serviceKey=...&pageNo=...&numOfRows=... 글자를 만든다
        query = urllib.parse.urlencode({"serviceKey": key, "pageNo": page, "numOfRows": rows})
        # timeout=10: 10초 안에 응답이 없으면 오류(OSError)로 끝내서 프로그램이 멈추지 않게 한다
        with urllib.request.urlopen(self.__speed_url + "?" + query, timeout=10) as res:
            data = json.loads(res.read().decode("utf-8"))
        if "response" in data:            # {"response": {"header", "body"}} 모양으로 올 때
            data = data["response"]
        # 공공데이터 API는 resultCode가 00이면 정상이다. 다른 값이면 실패로 본다
        if data["header"]["resultCode"] != "00":
            raise ValueError(data["header"].get("resultMsg", "API 오류"))
        return data["body"]

    def __items_of(self, body):
        """body -> items -> item 목록. item이 하나뿐이면 딕셔너리로 와서 목록으로 감싼다."""
        items = body.get("items") or []
        # items가 {"item": [...]} 모양으로 오면 item 목록만 꺼낸다
        if isinstance(items, dict):
            items = items.get("item") or []
        # item이 하나뿐이면 목록이 아니라 딕셔너리 하나로 오는 API 특성 때문에 목록으로 감싼다
        if isinstance(items, dict):
            items = [items]
        return items