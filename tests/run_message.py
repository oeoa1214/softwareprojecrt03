"""Message를 눈으로 확인하는 실행 파일 (TE 번호 없음, 분담서2 5장 Message 단위 테스트).
실행: py tests/run_message.py   (프로젝트 맨 위 폴더에서)
- 이름이 튜플인 문구(경고창)는 버튼을 누르면 경고창으로 뜬다. 「닫기」를 누르면 터미널에 '닫기 눌림'이 찍힌다.
- 글 문구는 버튼을 누르면 버튼 위에 2초 안내(흰색)로 뜬다.
- 맨 아래 「회색 안내」는 gray=True, 「안내 두 번」은 2초 안에 두 번 띄워 앞 것이 먼저 사라지는지 본다."""
import os
import sys
import tkinter as tk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from page_tinker.message import Message
from page_tinker.style import COLOR, FONT

root = tk.Tk()
root.geometry("960x650")
root.resizable(False, False)
Message.root = root

names = [n for n in vars(Message) if n.isupper()]
print("문구 상수", len(names), "개")
frame = tk.Frame(root)
frame.pack(fill="both", expand=True, padx=10, pady=10)
btn_holder = {}   # {상수 이름: 버튼}. for문 밖에서 한 번만 만든다 (안에서 만들면 마지막 사전만 남는다)
for i, name in enumerate(names):
    value = getattr(Message, name)
    if isinstance(value, tuple):
        # 경고창 문구 (첫 문장, 둘째 문장 또는 None)
        command = lambda v=value, n=name: Message.show_alert(*v, on_close=lambda: print(n, "닫기 눌림"))
    else:
        command = lambda v=value, n=name: Message.show_toast(v if len(v) < 40 else v[:38] + "…", btn_holder[n])
    btn = tk.Button(frame, text=name, width=20, command=command)
    if not isinstance(value, tuple):
        btn_holder[name] = btn
    btn.grid(row=i // 4, column=i % 4, padx=4, pady=4)

extra = tk.Frame(root)
extra.pack(side="bottom", pady=10)
gray = tk.Button(extra, text="회색 안내", width=20)
gray.configure(command=lambda: Message.show_toast(Message.ALREADY_SAVED, gray, gray=True))
gray.pack(side="left", padx=10)
twice = tk.Button(extra, text="안내 두 번", width=20)
twice.configure(command=lambda: (Message.show_toast(Message.SAVED, twice),
                                 root.after(500, lambda: Message.show_toast(Message.NO_DELETE_SELECT, twice))))
twice.pack(side="left", padx=10)
root.mainloop()
