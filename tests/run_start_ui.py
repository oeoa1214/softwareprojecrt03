"""StartUi를 혼자 띄워 보는 실행 파일 (TE-05, 분담서2 5장 「혼자 테스트하는 법」).
실행: py tests/run_start_ui.py   (프로젝트 맨 위 폴더에서)
- 처음 2초 동안 클릭: 넘어가지 않는다 (데이터 준비 중)
- 2초 뒤(터미널에 '클릭 받기 시작')부터 아무 곳이나 클릭: 터미널에 '지도 화면 열기'가 한 번 찍히고 메인 화면이 사라진다
- 사라진 뒤 창을 다시 클릭해도 '지도 화면 열기'가 또 찍히지 않는다"""
import os
import sys
import tkinter as tk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from page_tinker.message import Message
from page_tinker.start_ui import StartUi

root = tk.Tk()
root.geometry("960x650")
root.resizable(False, False)
Message.root = root
start = StartUi(root, on_start=lambda: print("지도 화면 열기"))
start.show()


def ready():
    print("클릭 받기 시작")
    start.enable_click()


root.after(2000, ready)   # 데이터 준비가 2초 걸린다고 치고
root.mainloop()
