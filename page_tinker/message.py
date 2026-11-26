"""Message - 모든 안내 · 경고 문장을 상수로 모으고, 경고창(show_alert)과 2초 안내(show_toast)를 만든다.
(UI/UX 설계서 3.1 · 3.5 · 3.8 · 3.10 · 3.11 · 3.15 · 3.16, 분담서2 5장 · 부록)
다른 화면은 이 상수와 두 메소드만 쓴다. 글자 · 띄어쓰기 · 마침표는 설계서 그대로다.
경고창 문구는 (첫 문장, 둘째 문장) 튜플이고, 둘째 문장이 없으면 None이다."""
import tkinter as tk
import tkinter.font as tkfont

from page_tinker.style import COLOR, FONT


class Message:
    root = None    # 경고창을 띄울 Tk 창. main.py가 창을 만든 직후 Message.root = root
    toast = None   # 지금 떠 있는 2초 안내 (새로 띄우기 전에 destroy)

    # ---- 문구 상수: 부록 표 그대로 ----
    # 3.1 메인 화면
    TITLE = "구급차를 도와서 사람들을 구하자"
    START = "시작하시려면 화면을 아무 곳이나 클릭해주세요"
    SOURCE = "데이터 제공: 국립중앙의료원 · 대구광역시 · 국토교통부 · 지도 © OpenStreetMap"
    HOSPITAL_SAVED = ("병원 정보를 새로 받지 못해 마지막으로 저장한 정보로 실행합니다.",
                      "병상 수가 지금과 다를 수 있습니다.")
    HOSPITAL_DUMMY = ("병원 정보를 받지 못해 가상 병원으로 실행합니다.",
                      "화면의 병원은 실제 병원이 아닙니다.")
    SPEED_SAVED = ("도로 속도를 새로 받지 못해 마지막으로 저장한 속도로 계산합니다.",
                   "도착 시간이 실제와 다를 수 있습니다.")
    SPEED_DUMMY = ("도로 속도를 받지 못해 가상 속도로 계산합니다.",
                   "도착 시간이 실제와 다릅니다.")
    ROAD_DUMMY = ("도로망 정보를 읽지 못해 가상 도로로 실행합니다.",
                  "화면의 경로는 실제 도로와 다릅니다.")
    NO_HOSPITAL = ("프로그램 문제로 병원 정보를 불러오지 못해 프로그램을 종료합니다.",
                   "잠시 후 다시 실행해주세요.")
    NO_ROAD = ("프로그램 문제로 도로 정보를 불러오지 못해 프로그램을 종료합니다.", None)

    # 3.3 · 3.7 지도 화면
    SEARCH_HINT = "병원 이름을 입력하세요"
    STRIP_SHOW = "여기를 누르면 병원 정보가 나옵니다"
    STRIP_HIDE = "여기를 누르면 병원 정보가 접힙니다"
    STRIP_NO_HOSPITAL = "병원 심볼을 먼저 눌러주세요"

    # 3.5 사고 지점 클릭
    OUTSIDE_DAEGU = ("대구이외의 지역은 서비스 지역이 아닙니다.",
                     "대구 안을 다시 클릭해주세요.")
    TOO_FAR = ("여기는 도로에서 너무 떨어진 위치입니다.",
               "도로 가까이를 다시 클릭해주세요.")
    NO_BED = ("병상이 있는 병원이 없습니다.", "병원 목록에서 직접 골라주세요.")

    # 3.8 · 3.15 병원 검색
    GUESS_TAIL = "이라고 쓰려던 건가요?"
    INVALID_NAME = ("음, 이 병원은 유효하지 않은 것 같네요.",
                    "오타가 포함되어 있는지 확인해 보세요.")

    # 3.9 · 3.10 메뉴 화면
    EMPTY_HOSPITALS = ("아래 사고 지점 찾기를 누르고 지도에서 사고 지점을 클릭하면 병원 목록이 나옵니다.")
    CLICK_ACCIDENT = "지도에서 사고 지점을 클릭해주세요."

    # 3.11 경로 저장
    SAVED = "경로가 저장되었습니다."
    NO_SELECT = ("병원을 먼저 선택해주세요.",
                 "지도의 테두리 병원 심볼이나 병원 목록에서 고를 수 있습니다.")
    NO_ACCIDENT = ("사고 지점을 먼저 찾아주세요.",
                   "아래 사고 지점 찾기를 누르고 지도를 클릭하세요.")
    SAVE_FAIL = ("경로 저장이 실패했습니다.", None)
    ALREADY_SAVED = "이미 저장했습니다."

    # 3.14 ~ 3.16 과거 경로 화면
    EMPTY_PAST = ("저장된 경로가 없습니다.",
                  "메뉴에서 경로 저장하기를 누르면 여기에 나옵니다.")
    DELETE_ASK = "{}번 경로를 삭제할까요?"
    DELETE_WARN = "삭제하면 되돌릴 수 없습니다."
    NO_DELETE_SELECT = "삭제할 경로를 먼저 선택해주세요."
    DELETE_FAIL = ("데이터베이스 오류로 삭제할 수 없습니다.", "잠시 후 다시 삭제해 주세요.")

    @staticmethod
    def show_alert(first, second=None, on_close=None):
        """3.11 경고창. 창 가운데에 뜨고, 「닫기」를 누르기 전에는 뒤 화면을 누를 수 없다.
        first = 첫 문장, second = 둘째 문장 (None이면 한 줄),
        on_close = 「닫기」를 누른 뒤 부를 함수 (main.py의 다음 안내, root.destroy 등)"""
        root = Message.root
        # 1) 새 창(Toplevel)을 만들지 않고, root 창 안에 테두리 1px짜리 Frame을 올린다
        #    (제목 줄 없는 별도 창은 Windows에서 창 전체가 먹통이 되는 일이 있어서 쓰지 않는다)
        alert = tk.Frame(root, bg=COLOR["border"])
        body = tk.Frame(alert, bg=COLOR["white"])
        body.pack(fill="both", expand=True, padx=1, pady=1)
        # 2) 첫 문장 → (둘째 문장) → 구분선 → 닫기를 위에서부터 붙인다
        tk.Label(body, text=first, font=FONT["l_bold"], fg="black", bg=COLOR["white"],
                 wraplength=360, justify="center").pack(fill="x", pady=(24, 0), padx=20)
        if second:
            tk.Label(body, text=second, font=FONT["m"], fg=COLOR["text_sub"], bg=COLOR["white"],
                     wraplength=360, justify="center").pack(fill="x", pady=(6, 0), padx=20)
        tk.Frame(body, height=1, bg=COLOR["line"]).pack(fill="x", pady=(24, 0))
        close_box = tk.Frame(body, height=48, bg=COLOR["white"])
        close_box.pack(fill="x")
        close_box.pack_propagate(False)
        close = tk.Label(close_box, text="닫기", font=FONT["l_bold"], fg="black", bg=COLOR["white"])
        close.pack(fill="both", expand=True)

        def press(_event):
            close.configure(bg=COLOR["white_press"])
            close_box.configure(bg=COLOR["white_press"])

        def release(_event):
            alert.destroy()
            if on_close:
                on_close()

        close.bind("<ButtonPress-1>", press)
        close.bind("<ButtonRelease-1>", release)
        # 3) 폭 400, 높이는 내용만큼, root 창 한가운데에 놓고 맨 위로 올린다
        alert.place(relx=0.5, rely=0.5, anchor="center", width=400)
        alert.lift()
        # 4) 닫기 전에는 뒤 화면을 누를 수 없게: 경고창 Frame이 클릭을 모두 가져간다 (닫으면 저절로 풀림)
        #    새 창이 아니라 Frame에 거는 것이라 Windows 먹통 문제와 상관없다
        Message.hold_clicks(alert)

    @staticmethod
    def show_toast(text, widget, gray=False):
        """3.16 · 3.11 2초 안내. widget 바로 위 8px에 둥근 안내를 2초 동안 띄운다.
        gray=False: 흰 바탕 90% + 테두리, 안내 오른쪽 끝을 widget 오른쪽 끝에 맞춘다 (3.16)
        gray=True : track 회색 바탕, 테두리 없음, widget 가운데에 맞춘다 (3.11)"""
        root = Message.root
        # 6) 이미 떠 있는 안내가 있으면 먼저 지운다 (2초 안에 다시 띄우면 앞 것이 먼저 사라진다)
        if Message.toast is not None:
            try:
                Message.toast.destroy()
            except tk.TclError:
                pass
            Message.toast = None
        # 7) 폭 = 글자 폭 + 좌우 20, 높이 36. 둥근 모서리 밖은 투명하게 한다 (Windows만)
        width = tkfont.Font(font=FONT["m"]).measure(text) + 40
        height = 36
        toast = tk.Toplevel(root)
        toast.overrideredirect(True)
        try:
            toast.attributes("-alpha", 0.9)
            toast.attributes("-transparentcolor", "#FF00FF")
        except tk.TclError:
            pass   # Windows가 아니면 투명 처리를 건너뛴다
        # 8) 모서리 12px 둥근 네모를 Canvas에 그리고 그 위에 글자를 얹는다
        canvas = tk.Canvas(toast, width=width, height=height, bg="#FF00FF", highlightthickness=0)
        canvas.pack()
        fill = COLOR["track"] if gray else COLOR["white"]
        outline = "" if gray else COLOR["border"]
        Message.__round_rect(canvas, 1, 1, width - 1, height - 1, 12, fill, outline)
        canvas.create_text(width // 2, height // 2, text=text, fill=COLOR["text_sub"], font=FONT["m"])
        # 9) 위치: widget 위 8px
        y = widget.winfo_rooty() - 8 - height
        if gray:
            x = widget.winfo_rootx() + (widget.winfo_width() - width) // 2
        else:
            x = widget.winfo_rootx() + widget.winfo_width() - width
        toast.geometry(f"{width}x{height}+{x}+{y}")
        # 10) 2초 뒤 지운다. 그 사이 다른 안내로 바뀌었으면 건드리지 않는다
        Message.toast = toast

        def remove():
            try:
                toast.destroy()
            except tk.TclError:
                pass
            if Message.toast is toast:
                Message.toast = None

        root.after(2000, remove)

    @staticmethod
    def hold_clicks(frame):
        """frame이 화면에 보인 뒤 grab_set()으로 앱의 클릭을 frame 안으로만 받는다 (경고창 · 확인창 공통).
        frame을 destroy()하면 grab이 저절로 풀린다"""
        def grab():
            try:
                frame.grab_set()
            except tk.TclError:
                pass       # 아직 안 보이거나 이미 닫힌 경우
        frame.after(10, grab)

    @staticmethod
    def __round_rect(canvas, x1, y1, x2, y2, r, fill, outline):
        """모서리가 둥근 네모 (smooth 다각형)"""
        points = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
                  x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        canvas.create_polygon(points, smooth=True, fill=fill, outline=outline)
