"""더미 병원 파일 만들기 — 한 번만 실행한다.
save_hospital_response.py로 저장한 실제 응답 두 개를 data/dummy_hospital.csv로 바꾼다.
병원 API가 실패하면 HospitalApi가 이 파일을 쓴다 (EX-01, TE-02).

실행: py make_dummy_hospital.py
"""
import csv

from hospital_api import HospitalApi

with open("data/hospital_list_response.xml", "rb") as f:
    list_xml = f.read()
with open("data/hospital_beds_response.xml", "rb") as f:
    beds_xml = f.read()

rows = HospitalApi().make_hospitals(list_xml, beds_xml)
with open("data/dummy_hospital.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["hpid", "name", "lat", "lon", "addr", "tel", "beds"])
    for hpid, name, lat, lon, node_id, addr, tel, beds in rows:
        w.writerow([hpid, name, lat, lon, addr, tel, "" if beds is None else beds])
print("data/dummy_hospital.csv 저장:", len(rows), "곳 (병상 정보 있는 곳", sum(r[7] is not None for r in rows), "곳)")