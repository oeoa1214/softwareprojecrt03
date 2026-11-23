"""HospitalSearch - 입력한 병원 명으로 병원 정보를 찾는다 (오은찬 담당, FR-05)."""


class HospitalSearch:
    def __init__(self, repo):
        """repo = main에서 만든 Repository (DB 연결을 같이 쓴다)"""
        self.__repo = repo

    def search(self, name_text):
        """병원 검색 슬롯에 입력한 글자로 병원을 찾는다 (FR-05 시퀀스 2~7, 11).
        반환: 병원 한 줄 (hpid, name, lat, lon, node_id, addr, tel, beds)
              없는 병원이거나 빈 입력이면 None → 화면이 EX-07 메시지를 띄운다
        이름이 정확히 같은 병원만 찾는다. 앞뒤 빈칸은 지우고 찾는다."""
        if name_text is None:
            return None
        # 앞뒤 빈칸을 지운다 (' 경북대학교병원 ' -> '경북대학교병원')
        name = name_text.strip()
        # 빈 입력은 찾을 수 없으므로 None을 돌려준다 (화면이 EX-07 메시지를 띄운다)
        if name == "":
            return None
        # 실제 검색(SQL)은 Repository가 한다. 이 클래스는 입력을 다듬어 전달만 한다
        return self.__repo.find_hospital_by_name(name)