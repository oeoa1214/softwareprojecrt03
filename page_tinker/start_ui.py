"""StartUi - 메인 화면 (UI/UX 설계서 3.1 메인 화면 · 3.2 메인 화면 클릭)
주황 바탕 · 작품명 · 시작 안내 · 데이터 출처를 그린다.
main.py가 데이터 준비를 끝내고 enable_click()을 부르면, 창 어디를 눌러도 지도 화면으로 넘어간다."""
import os
import tkinter as tk

from page_tinker.style import COLOR, FONT, IMAGE_DIR
from page_tinker.message import Message


class StartUi:
    def __init__(self, root, on_start):
        """root = Tk 창 (main.py가 만듦),
        on_start = 클릭되면 부를 함수 (main.open_map: 지도 화면 열기)"""
        self.root = root
        self.on_start = on_start
        self.canvas = None      # 메인 화면. go_map에서 destroy()
        self.bg_image = None    # 주황 바탕 그림. 변수로 잡아 두지 않으면 그림이 사라진다

    def show(self):
        """Canvas(960x650)에 주황 바탕 그림 · 작품명 · 시작 안내 · 데이터 출처를 그린다.
        클릭은 아직 받지 않는다 (데이터 준비가 끝나면 main.py가 enable_click을 부른다)"""
        self.canvas = tk.Canvas(self.root, width=960, height=650, highlightthickness=0)
        self.canvas.pack(fill="both")
        self.bg_image = tk.PhotoImage(file=os.path.join(IMAGE_DIR, "start_bg.png"))
        self.canvas.create_image(0, 0, anchor="nw", image=self.bg_image)
        # 글자는 모두 Message 상수를 쓴다. 기본 anchor="center"라 (x, y)가 글자 가운데다
        self.canvas.create_text(480, 290, text=Message.TITLE, fill=COLOR["white"], font=FONT["2xl"])
        self.canvas.create_text(480, 345, text=Message.START, fill=COLOR["white"], font=FONT["m"])
        self.canvas.create_text(480, 626, text=Message.SOURCE, fill=COLOR["white"], font=FONT["xs"])

    def enable_click(self):
        """창 전체 클릭을 받기 시작한다. root에 걸었으므로 작품명 · 안내 글자 위를 눌러도 불린다"""
        self.root.bind("<Button-1>", self.go_map)

    def go_map(self, event):
        """한 번만 넘어간다: 클릭을 먼저 떼서 지도 화면의 클릭이 다시 오지 않게 한 뒤,
        메인 화면을 지우고 지도 화면 열기 함수를 부른다"""
        self.root.unbind("<Button-1>")
        self.canvas.destroy()
        self.on_start()
