"""PastRouteManager - 과거 경로의 입력을 확인하고 조회와 삭제를 처리한다 (오은찬 담당, FR-04)."""
# datetime: 날짜 글자가 진짜 있는 날짜인지(2026-13-40 같은 것) 확인한다
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
        # None이 와도 빈 글자로 바꾸고 앞뒤 빈칸을 지운다
        id_text = (id_text or "").strip()
        name_text = (name_text or "").strip()
        date_text = (date_text or "").strip()

        # 1. 입력 형식 확인 (시퀀스 5~7)
        # 식별 번호 칸이 비어 있으면 None = '이 조건은 쓰지 않는다'
        route_id = None
        if id_text != "":
            route_id = self.__to_route_id(id_text)
            if route_id is None:
                return [], MSG_ID
        # 날짜는 입력했을 때만 형식을 검사한다
        if date_text != "" and not self.__is_date(date_text):
            return [], MSG_DATE

        # 2. 조회 (시퀀스 8~11)
        # 비어 있지 않은 조건만 Repository에 넘긴다 (None인 조건은 SQL에서 빠진다)
        rows = self.__repo.search_routes(route_id=route_id,
                                         hospital_name=name_text if name_text != "" else None,
                                         date=date_text if date_text != "" else None)

        # 3. 찾는 기록이 없을 때 (시퀀스 12~13, 3.2.4)
        # 입력 형식은 맞는데 기록이 없을 때, 어느 칸 때문인지에 따라 메시지를 고른다
        if not rows:
            if route_id is not None:
                return [], MSG_ID
            if name_text != "":
                return [], MSG_NAME
        return rows, None

    def delete(self, route_id):
        """고른 행의 식별 번호로 기록을 지운다 (FR-04 시퀀스 수정본 17~22).
        반환: 지웠으면 True (화면이 목록에서 그 행을 지운다), 없는 번호면 False"""
        # 지우는 일은 Repository가 한다. 성공 여부(True/False)를 화면에 그대로 돌려준다
        return self.__repo.delete_route(route_id)

    def __to_route_id(self, text):
        """1 이상의 정수 글자면 int, 아니면 None ("001"은 1, "0" · "-3" · "1.5" · "abc"는 None)"""
        # '1.5', '-3', 'abc', 빈칸은 숫자 글자만으로 이루어져 있지 않으므로 여기서 걸러진다
        if not text.isdecimal():
            return None
        number = int(text)
        # 0은 '1 이상'이 아니므로 None이다
        return number if number >= 1 else None

    def __is_date(self, text):
        """2026-11-09처럼 숫자 4-2-2 자리이고 실제로 있는 날짜면 True (2026-13-40, 2026-1-9는 False)"""
        # '2026-1-9'처럼 자릿수가 모자란 것을 걸러낸다. strptime은 이런 것도 받아 주기 때문이다
        if len(text) != 10:
            return False
        try:
            # 글자를 날짜로 바꿔 본다. 2026-13-40처럼 없는 날짜면 ValueError가 난다
            datetime.strptime(text, "%Y-%m-%d")
        except ValueError:
            return False
        return True