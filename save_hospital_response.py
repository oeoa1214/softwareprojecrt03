"""병원 API(IF-001) 응답 확인용 — 한 번만 실행한다.
계획서 4.1: 받은 응답을 파일로 저장해서 우리가 쓸 항목이 들어 있는지 먼저 확인한다.

실행: py save_hospital_response.py   (프로젝트 폴더, api_key.txt 필요)
"""
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

BASE = "https://apis.data.go.kr/B552657/ErmctInfoInqireService/"
CALLS = [
    ("병원 목록", "getEgytListInfoInqire",
     {"Q0": "대구광역시", "pageNo": 1, "numOfRows": 100}, "data/hospital_list_response.xml"),
    ("실시간 병상", "getEmrrmRltmUsefulSckbdInfoInqire",
     {"STAGE1": "대구광역시", "pageNo": 1, "numOfRows": 100}, "data/hospital_beds_response.xml"),
]

with open("api_key.txt", encoding="utf-8") as f:
    key = urllib.parse.unquote(f.readline().strip())

for title, operation, params, path in CALLS:
    query = urllib.parse.urlencode({"serviceKey": key, **params})
    try:
        with urllib.request.urlopen(BASE + operation + "?" + query, timeout=10) as res:
            raw = res.read()
    except OSError as e:
        print(f"[{title}] 연결 실패: {e}")
        continue
    with open(path, "wb") as f:
        f.write(raw)
    print(f"[{title}] {path} 저장 ({len(raw)} 바이트)")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        print("   XML이 아님. 앞부분:", raw[:300].decode("utf-8", "replace"))
        continue
    print("   결과 코드:", root.findtext(".//resultCode"), root.findtext(".//resultMsg"))
    print("   전체 개수:", root.findtext(".//totalCount"))
    items = root.findall(".//item")
    if items:
        print("   첫 병원의 칸:")
        for child in items[0]:
            print(f"      {child.tag} = {child.text}")