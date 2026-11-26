"""PastRouteUi를 혼자 띄워 보는 실행 파일 (TE-16 · 19~21 · 26~28, 분담서2 5장 「혼자 테스트하는 법」).
PastRouteManager 고침이 오기 전에는 같은 메소드 네 개를 가진 가짜(FakeManager)로 화면을 만든다.
진짜 PastRouteManager를 받은 뒤에는 FakeManager(ROWS) 자리에 진짜를 넣어 다시 돌린다.
실행: py tests/run_past_route_ui.py   (프로젝트 맨 위 폴더에서)
- 병원명 「경북대병원」 검색 -> 쓰려던 건가요? / 「서울대병원」 검색 -> 음, 이 병원은…
- 병원명 「대구가」 입력 -> 추천 목록"""
import os
import sys
import tkinter as tk
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from page_tinker.message import Message
from page_tinker.past_route_ui import PastRouteUi


class FakeManager:
    """PastRouteManager 고침이 오기 전에 화면만 확인하는 가짜 (테스트 코드 안에서만 쓴다)"""
    def __init__(self, rows, delete_ok=True):
        self.rows = rows
        self.delete_ok = delete_ok           # False로 만들면 DB 삭제 실패 확인

    def search(self, id_text, name_text, year, month, day):
        if name_text == "경북대병원":
            return [], ("guess", "경북대학교병원")
        if name_text == "서울대병원":
            return [], "invalid"
        rows = self.rows
        if id_text:
            rows = [r for r in rows if r[0] == int(id_text)]
        if name_text:
            rows = [r for r in rows if r[2] == name_text]
        if year:
            rows = [r for r in rows if r[1].year == int(year)]
        if month:
            rows = [r for r in rows if r[1].month == int(month)]
        if day:
            rows = [r for r in rows if r[1].day == int(day)]
        return rows, None

    def suggest(self, name_text):
        if len(name_text.replace(" ", "")) < 3:
            return []
        return ["대구가톨릭대학교병원", "대구가톨릭대학교칠곡가톨릭병원"]

    def count(self):
        return len(self.rows)

    def delete(self, route_id):
        if self.delete_ok:
            self.rows = [r for r in self.rows if r[0] != route_id]
        return self.delete_ok


ROWS = [
    (3, datetime(2026, 11, 20, 14, 5), "경북대학교병원", 4, 6.2, 3100.0, 5),
    (2, datetime(2026, 11, 19, 9, 30), "영남대학교병원", 2, 8.7, 4800.0, 7),
    (1, datetime(2026, 11, 18, 21, 10), "(재)미리내천주성삼성직수도회천주성삼병원", 0, 5.1, 2600.0, 4),
]

root = tk.Tk()
root.geometry("960x650")
root.resizable(False, False)
Message.root = root
PastRouteUi(root, FakeManager(ROWS), on_back=lambda: print("on_back")).show()
root.mainloop()
