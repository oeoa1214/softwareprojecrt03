"""PastRouteManager - 과거 경로의 입력을 확인하고 조회와 삭제를 처리한다 (오은찬 담당, FR-04)."""
from datetime import datetime

# 계획서 2.6 EX-08 · EX-09 · EX-10, 3.2.4 메시지 정책
MSG_ID = "1 이상의 정수를 입력해주세요."
MSG_NAME = "병원명을 다시 입력해주세요."
MSG_DATE = "날짜는 XXXX-XX-XX 형태로 입력해주세요."


class PastRouteManager:
    def __init__(self, repo):
        """repo = main에서 만든 Repository (DB 연결을 같이 쓴다)"""
        self.__repo = repo

    def search(self, id_text="", name_text="", date_text=""):
        """과거 경로 화면의 세 칸(식별 번호, 병원명, 저장 날짜)에 입력한 글자로 찾는다 (FR-04 시퀀스 수정본 4~15).
        빈 칸은 조건에서 뺀다. 세 칸이 다 비어 있으면 전체 기록.
        반환: (rows, message)
          rows = [(route_id, calculated_at, hospital_name, beds, eta_minutes, distance_m, node_count), ...]
          message = 화면에 띄울 경고 문구, 문제가 없으면 None
        - 식별 번호가 1 이상의 정수가 아니거나 그 번호의 기록이 없음 → MSG_ID (EX-09)
        - 날짜가 2026-11-09 형식이 아님 → MSG_DATE (EX-10)
        - 그 병원명의 기록이 없음 → MSG_NAME (EX-08)"""
        id_text = (id_text or "").strip()
        name_text = (name_text or "").strip()
        date_text = (date_text or "").strip()

        # 1. 입력 형식 확인 (시퀀스 5~7)
        route_id = None
        if id_text != "":
            route_id = self.__to_route_id(id_text)
            if route_id is None:
                return [], MSG_ID
        if date_text != "" and not self.__is_date(date_text):
            return [], MSG_DATE

        # 2. 조회 (시퀀스 8~11)
        rows = self.__repo.search_routes(route_id=route_id,
                                         hospital_name=name_text if name_text != "" else None,
                                         date=date_text if date_text != "" else None)

        # 3. 찾는 기록이 없을 때 (시퀀스 12~13, 3.2.4)
        if not rows:
            if route_id is not None:
                return [], MSG_ID
            if name_text != "":
                return [], MSG_NAME
        return rows, None

    def delete(self, route_id):
        """고른 행의 식별 번호로 기록을 지운다 (FR-04 시퀀스 수정본 17~22).
        반환: 지웠으면 True (화면이 목록에서 그 행을 지운다), 없는 번호면 False"""
        return self.__repo.delete_route(route_id)

    def __to_route_id(self, text):
        """1 이상의 정수 글자면 int, 아니면 None ("001"은 1, "0" · "-3" · "1.5" · "abc"는 None)"""
        if not text.isdecimal():
            return None
        number = int(text)
        return number if number >= 1 else None

    def __is_date(self, text):
        """2026-11-09처럼 숫자 4-2-2 자리이고 실제로 있는 날짜면 True (2026-13-40, 2026-1-9는 False)"""
        if len(text) != 10:
            return False
        try:
            datetime.strptime(text, "%Y-%m-%d")
        except ValueError:
            return False
        return True