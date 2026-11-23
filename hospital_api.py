"""HospitalApi - 대구 응급의료기관 목록과 응급실 병상 수 받기 (오은찬 담당, AD-03 · IF-001)."""
import csv
import urllib.parse
import urllib.request
# ElementTree: 병원 API 응답(XML 글자)을 읽어 태그(<hpid> 등)별로 값을 꺼낸다
import xml.etree.ElementTree as ET

# 국립중앙의료원 전국 응급의료기관 정보 조회 서비스 (IF-001)
BASE_URL = "https://apis.data.go.kr/B552657/ErmctInfoInqireService/"
LIST_OPERATION = "getEgytListInfoInqire"                  # 병원 목록 (이름 · 위치 · 주소 · 전화)
BEDS_OPERATION = "getEmrrmRltmUsefulSckbdInfoInqire"      # 실시간 가용 병상 (hvec = 응급실 병상 수)


class HospitalApi:
    def __init__(self, base_url=BASE_URL, key_path="api_key.txt",
                 dummy_csv="data/dummy_hospital.csv"):
        self.__base_url = base_url
        self.__key_path = key_path        # API 인증키 파일 (GitHub에 올리지 않음)
        self.__dummy_csv = dummy_csv      # API가 실패하면 쓰는 더미 병원 (EX-01)

    def load_hospitals(self):
        """대구 응급의료기관을 받는다 (시작 흐름도 4).
        반환: (rows, is_dummy)
        rows = [(hpid, name, lat, lon, node_id, addr, tel, beds), ...]  hospital 테이블 칸 순서
               node_id는 None (main이 Crossroad로 가까운 교차로를 찾아 채운다)
               beds는 응급실 남은 병상 수, 병상 정보가 없는 병원은 None
        is_dummy = API를 못 받아 더미 파일을 썼으면 True (더미 파일도 못 읽으면 rows는 빈 목록)"""
        try:
            key = self.__read_key()
            # API 두 개를 부른다: ① 병원 목록(이름·위치) ② 실시간 병상. 둘을 병원 번호(hpid)로 짝지어 합친다
            list_xml = self.__request(LIST_OPERATION, {"Q0": "대구광역시", "pageNo": 1, "numOfRows": 100}, key)
            beds_xml = self.__request(BEDS_OPERATION, {"STAGE1": "대구광역시", "pageNo": 1, "numOfRows": 100}, key)
            rows = self.make_hospitals(list_xml, beds_xml)
            # 받았는데 병원이 0곳이면 실패로 보고 더미를 쓴다
            if not rows:
                raise ValueError("병원 응답이 비어 있음")
            return rows, False
        # 인터넷 오류 / 결과 코드 이상 / 태그 없음 / XML 모양 깨짐 -> 더미 병원으로 대신한다 (EX-01)
        except (OSError, ValueError, KeyError, ET.ParseError):
            return self.__read_dummy(), True

    def make_hospitals(self, list_xml, beds_xml):
        """병원 목록 응답과 병상 응답(XML 글자)을 병원 번호(hpid)로 짝지어 rows를 만든다.
        반환: [(hpid, name, lat, lon, None, addr, tel, beds), ...]
        위도 · 경도가 없는 병원은 지도에 못 놓으므로 뺀다.
        병상 수가 0보다 작으면 0으로 둔다 (계획서 2.5.2: 병상 수는 0개 이상)."""
        # {병원 번호: 응급실 병상 수}. 병원 목록과 나중에 짝지으려고 먼저 만든다
        beds_by_hpid = {}
        for it in self.__items(beds_xml):
            try:
                # hvec = 응급실 남은 병상 수. 음수는 0으로 바꾼다 (계획서 2.5.2: 병상 수는 0개 이상)
                beds_by_hpid[it.findtext("hpid")] = max(0, int(it.findtext("hvec")))
            except (TypeError, ValueError):
                pass
        rows = []
        for it in self.__items(list_xml):
            try:
                # wgs84Lat/Lon = 병원 위도·경도. 값이 없으면 float(None)이 TypeError가 나서 아래 except로 가고, 그 병원은 뺀다
                lat = float(it.findtext("wgs84Lat"))
                lon = float(it.findtext("wgs84Lon"))
            except (TypeError, ValueError):
                continue
            hpid = it.findtext("hpid")
            # beds_by_hpid.get(hpid): 병상 응답에 없는 병원은 None(병상 정보 없음)이 된다. 정렬에서는 맨 뒤로 간다
            rows.append((hpid, it.findtext("dutyName"), lat, lon, None,
                         it.findtext("dutyAddr"), it.findtext("dutyTel3"), beds_by_hpid.get(hpid)))
        return rows

    def __items(self, xml_text):
        """XML 글자에서 item 목록을 꺼낸다. 결과 코드가 00이 아니면 ValueError"""
        # XML 글자를 태그 트리로 바꾼다
        root = ET.fromstring(xml_text)
        code = root.findtext(".//resultCode")
        # 결과 코드가 00이 아니면 키 오류·사용 한도 초과 등이므로 실패로 본다
        if code is not None and code != "00":
            raise ValueError(root.findtext(".//resultMsg") or "API 오류")
        # <item> 태그(병원 한 곳)를 전부 모아 목록으로 돌려준다
        return list(root.iter("item"))

    def __read_key(self):
        """api_key.txt 첫 줄의 인증키"""
        with open(self.__key_path, encoding="utf-8") as f:
            key = f.readline().strip()
        if not key:
            raise ValueError("인증키가 비어 있음")
        return urllib.parse.unquote(key)

    def __request(self, operation, params, key):
        """API 한 기능을 불러 응답(XML 글자)을 돌려준다. 결과 코드가 00이 아니면 ValueError"""
        query = urllib.parse.urlencode({"serviceKey": key, **params})
        with urllib.request.urlopen(self.__base_url + operation + "?" + query, timeout=10) as res:
            xml_text = res.read()
        self.__items(xml_text)            # 결과 코드 확인
        return xml_text

    def __read_dummy(self):
        """더미 병원 CSV (hpid,name,lat,lon,addr,tel,beds). 못 읽으면 빈 목록"""
        rows = []
        try:
            with open(self.__dummy_csv, newline="", encoding="utf-8-sig") as f:
                for r in csv.DictReader(f):
                    # CSV의 빈칸은 None(병상 정보 없음)으로 바꾼다
                    beds = int(r["beds"]) if r["beds"] != "" else None
                    rows.append((r["hpid"], r["name"], float(r["lat"]), float(r["lon"]), None,
                                 r["addr"], r["tel"], beds))
        except (OSError, ValueError, KeyError, csv.Error):
            return []
        return rows