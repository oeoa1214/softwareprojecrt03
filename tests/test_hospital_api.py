import os
import sys

# 한 칸 위 폴더(프로젝트 폴더)에서 hospital_api.py, repository.py를 찾게 한다
PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT)

import pytest
from hospital_api import HospitalApi

DATA = os.path.join(PROJECT, "data")
KEY = os.path.join(PROJECT, "api_key.txt")
LIST_FILE = os.path.join(DATA, "hospital_list_response.xml")
BEDS_FILE = os.path.join(DATA, "hospital_beds_response.xml")
DUMMY = os.path.join(DATA, "dummy_hospital.csv")

# 실제 응답과 같은 모양의 작은 가짜 응답
LIST_XML = """<response><header><resultCode>00</resultCode></header><body><items>
<item><hpid>A1</hpid><dutyName>가병원</dutyName><wgs84Lat>35.87</wgs84Lat><wgs84Lon>128.60</wgs84Lon>
<dutyAddr>대구 중구</dutyAddr><dutyTel3>053-111-1111</dutyTel3></item>
<item><hpid>A2</hpid><dutyName>나병원</dutyName><wgs84Lat>35.86</wgs84Lat><wgs84Lon>128.59</wgs84Lon>
<dutyAddr>대구 남구</dutyAddr><dutyTel3>053-222-2222</dutyTel3></item>
<item><hpid>A3</hpid><dutyName>다병원</dutyName><wgs84Lat>35.85</wgs84Lat><wgs84Lon>128.58</wgs84Lon>
<dutyAddr>대구 서구</dutyAddr><dutyTel3>053-333-3333</dutyTel3></item>
<item><hpid>A4</hpid><dutyName>위치없는병원</dutyName><dutyAddr>대구</dutyAddr></item>
</items></body></response>""".encode("utf-8")

BEDS_XML = """<response><header><resultCode>00</resultCode></header><body><items>
<item><hpid>A1</hpid><hvec>5</hvec></item>
<item><hpid>A2</hpid><hvec>-2</hvec></item>
</items></body></response>""".encode("utf-8")


# ================================================================ 응답 합치기
def test_list_and_beds_joined_by_hpid():
    """병원 목록과 병상을 hpid로 짝짓는다. 병상 없는 병원은 None, 위치 없는 병원은 뺀다"""
    rows = HospitalApi().make_hospitals(LIST_XML, BEDS_XML)
    assert rows == [
        ("A1", "가병원", 35.87, 128.60, None, "대구 중구", "053-111-1111", 5),
        ("A2", "나병원", 35.86, 128.59, None, "대구 남구", "053-222-2222", 0),
        ("A3", "다병원", 35.85, 128.58, None, "대구 서구", "053-333-3333", None),
    ]


def test_negative_beds_become_zero():
    """병상 수 -2(응급실 과밀)는 0으로 둔다 (계획서 2.5.2: 병상 수는 0개 이상)"""
    rows = HospitalApi().make_hospitals(LIST_XML, BEDS_XML)
    assert dict((r[0], r[7]) for r in rows)["A2"] == 0


def test_error_result_code_raises():
    """결과 코드가 00이 아니면 오류로 본다"""
    bad = b"<response><header><resultCode>30</resultCode><resultMsg>SERVICE_KEY_IS_NOT_REGISTERED_ERROR</resultMsg></header></response>"
    with pytest.raises(ValueError):
        HospitalApi().make_hospitals(bad, BEDS_XML)


# ================================================================ TE-01 · TE-02
@pytest.mark.skipif(not os.path.exists(LIST_FILE), reason="저장한 실제 응답이 없음")
def test_TE01_saved_response_to_db(tmp_path):
    """TE-01 저장 부분: 11/17에 받은 실제 응답 → hospital 테이블에 25곳 저장, 병상 정보 20곳"""
    from repository import Repository
    with open(LIST_FILE, "rb") as f:
        list_xml = f.read()
    with open(BEDS_FILE, "rb") as f:
        beds_xml = f.read()
    rows = HospitalApi().make_hospitals(list_xml, beds_xml)
    repo = Repository(str(tmp_path / "t.db"))
    repo.save_hospitals(rows)
    saved = repo.get_hospitals()
    repo.close()
    assert len(saved) == 25
    assert sum(1 for h in saved if h[7] is not None) == 20
    assert all(h[7] is None or h[7] >= 0 for h in saved)


@pytest.mark.skipif(not os.path.exists(KEY), reason="api_key.txt가 없어서 실제 API는 건너뜀")
def test_TE01_real_api():
    """TE-01 API 부분: 실제 API로 대구 응급의료기관을 받는다 (api_key.txt가 있을 때만)"""
    rows, is_dummy = HospitalApi(key_path=KEY, dummy_csv=DUMMY).load_hospitals()
    print("받은 병원", len(rows), "곳 / 병상 정보", sum(1 for r in rows if r[7] is not None), "곳")
    assert is_dummy is False
    assert len(rows) > 0
    assert all(35.5 < r[2] < 36.1 and 128.3 < r[3] < 128.9 for r in rows)    # 대구 근처 좌표


def test_TE02_api_fail_uses_dummy(tmp_path):
    """TE-02: 인증키 파일이 없으면 API 실패 → 더미 병원 파일로 실행, is_dummy True"""
    dummy = tmp_path / "dummy_hospital.csv"
    dummy.write_text("hpid,name,lat,lon,addr,tel,beds\n"
                     "D1,더미병원,35.87,128.60,대구 중구,053-000-0000,3\n"
                     "D2,병상모름병원,35.86,128.59,대구 남구,053-000-0001,\n", encoding="utf-8")
    rows, is_dummy = HospitalApi(key_path=str(tmp_path / "없는파일.txt"), dummy_csv=str(dummy)).load_hospitals()
    assert is_dummy is True
    assert rows == [("D1", "더미병원", 35.87, 128.60, None, "대구 중구", "053-000-0000", 3),
                    ("D2", "병상모름병원", 35.86, 128.59, None, "대구 남구", "053-000-0001", None)]


def test_TE02_bad_address_and_no_dummy(tmp_path):
    """TE-02: 주소가 잘못돼 실패하고 더미 파일도 없으면 빈 목록, is_dummy True (멈추지 않는다)"""
    key = tmp_path / "key.txt"
    key.write_text("가짜키", encoding="utf-8")
    api = HospitalApi(base_url="https://nowhere.invalid/", key_path=str(key),
                      dummy_csv=str(tmp_path / "없는더미.csv"))
    assert api.load_hospitals() == ([], True)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])