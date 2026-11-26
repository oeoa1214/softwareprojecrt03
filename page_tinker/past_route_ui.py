"""PastRouteUi - 과거 경로 화면 (UI/UX 설계서 3.14 과거 경로 화면 · 3.15 검색 · 3.16 삭제 · 3.17 돌아가기)
저장된 과거 경로 목록을 보여 주고, 검색 · 삭제 · 메뉴로 돌아가기를 받는다.
이 화면은 DB를 직접 쓰지 않고, 넘겨받은 manager(PastRouteManager)의
search · suggest · count · delete 네 메소드만 부른다. 입력 형식 확인과 문구 결정은 manager가 한다."""
import os
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from page_tinker.style import COLOR, FONT, DISPLAY_NAME, IMAGE_DIR
from page_tinker.message import Message

DATE_HINT = ("2022", "12", "04")   # 날짜 칸 연한 회색 예시 (연 · 월 · 일)


class PastRouteUi:
    def __init__(self, root, manager, on_back):
        """root = Tk 창, manager = PastRouteManager (오은찬),
        on_back = ← 를 누르면 부를 함수 (Ui.back_from_past)"""
        self.root = root
        self.manager = manager
        self.on_back = on_back
        self.past_screen = None      # 과거 경로 화면 Frame. back_to_menu에서 destroy()
        self.back_icon = None        # ← 아이콘. 변수로 잡아 두지 않으면 그림이 사라진다
        self.id_entry = None         # 식별 번호 칸
        self.name_entry = None       # 병원명 칸
        self.date_entries = []       # 저장 날짜 칸 세 개 (연 · 월 · 일)
        self.tree = None             # 과거 경로 목록. 줄 이름(iid)은 route_id
        self.empty_label = None      # 빈 목록 안내
        self.suggest_tree = None     # 병원명 추천 목록
        self.name_box = None         # 병원명 칸을 감싼 Frame (추천 목록 · 문구를 이 밑에 둔다)
        self.msg_frame = None        # 병원명 칸 밑 문구 묶음
        self.msg_name = None         # 병원명 칸 밑 문구의 병원 이름 (밑줄)
        self.msg_text = None         # 병원명 칸 밑 문구의 뒤 문구
        self.confirm_win = None      # 삭제 확인창
        self.delete_btn = None       # 삭제 버튼 (2초 안내를 이 위에 띄운다)
        self.hover_row = ""          # 추천 목록에서 마우스가 올라간 줄

    # ------------------------------------------------------------ 3.14 화면 만들기
    def show(self):
        """past_screen에 위 줄 · 입력칸 줄 · 목록 · 삭제 버튼을 만들고 전체 기록으로 목록을 채운다"""
        self._apply_style()
        self.past_screen = tk.Frame(self.root, bg="white")
        self.past_screen.pack(fill="both", expand=True)
        self._build_top_bar()
        self._build_inputs()
        self._build_delete_button()      # 아래 칸을 먼저 차지해 두고, 남은 칸에 목록을 채운다
        self._build_list()
        # 만들어 두기만 하고 필요할 때 place하는 부품
        self.empty_label = tk.Label(self.past_screen, text="\n".join(Message.EMPTY_PAST), font=FONT["m"],
                                    fg=COLOR["text_hint"], bg="white", justify="center")
        self.suggest_tree = ttk.Treeview(self.past_screen, columns=("name",), show="",
                                         selectmode="browse", style="Suggest.Treeview")
        self.suggest_tree.column("name", width=260, anchor="w", stretch=False)
        self.suggest_tree.tag_configure("hover", background=COLOR["hover"])
        self.suggest_tree.bind("<Motion>", self.on_suggest_motion)
        self.suggest_tree.bind("<ButtonRelease-1>", self.on_suggest_click)
        self.msg_frame = tk.Frame(self.past_screen, bg="white")
        self.msg_name = tk.Label(self.msg_frame, text="", font=FONT["m_link"], fg=COLOR["text_sub"],
                                 bg="white", cursor="hand2")
        self.msg_name.pack(side="left")
        self.msg_name.bind("<Button-1>", self._on_guess_click)
        self.msg_text = tk.Label(self.msg_frame, text="", font=FONT["m"], fg=COLOR["text_sub"], bg="white")
        self.msg_text.pack(side="left")
        # 처음에는 전체 기록
        rows, _ = self.manager.search("", "", "", "", "")
        self.fill(rows)
        self.update_empty()

    def fill(self, rows):
        """목록을 비우고 rows를 넣는다.
        rows = [(route_id, calculated_at, hospital_name, beds, eta_minutes, distance_m, node_count), ...]"""
        self.tree.delete(*self.tree.get_children())
        name_font = tkfont.Font(font=FONT["m"])
        for route_id, calculated_at, hospital_name, beds, eta_minutes, distance_m, node_count in rows:
            # 병원명이 칸(260px)보다 길면 표시 이름(DISPLAY_NAME)으로 바꾼다
            shown = hospital_name
            if name_font.measure(hospital_name) > 260:
                shown = DISPLAY_NAME.get(hospital_name, hospital_name)
            values = (route_id, calculated_at.strftime("%Y/%m/%d"), shown,
                      "-" if beds is None else beds,
                      f"{round(eta_minutes)}분", f"{distance_m / 1000:.1f}km", node_count)
            self.tree.insert("", "end", iid=str(route_id), values=values)

    def update_empty(self):
        """manager.count()가 0이면 빈 목록 안내를 보이고, 아니면 숨긴다.
        (검색 결과만 비었을 때는 count()가 0이 아니므로 안내를 띄우지 않는다)"""
        if self.manager.count() == 0:
            self.empty_label.place(in_=self.tree, relx=0.5, rely=0.5, anchor="center")
            self.empty_label.lift()
        else:
            self.empty_label.place_forget()

    def on_focus_in(self, event):
        """날짜 칸을 누르면 연한 회색 예시를 지운다"""
        entry = event.widget
        if str(entry.cget("fg")) == COLOR["placeholder"]:
            entry.delete(0, "end")
            entry.config(fg="black")

    # ------------------------------------------------------------ 3.15 검색
    def search_past(self):
        """검색 버튼. 칸 글자를 모아 manager.search로 기록을 찾아 목록을 다시 채운다.
        병원명 확인 결과(notice)가 ("guess", 정식 이름)이면 「쓰려던 건가요?」, "invalid"이면 「음, …」를 띄운다"""
        self.clear_msg()
        self.suggest_tree.place_forget()
        id_text = self.id_entry.get()
        name_text = self.name_entry.get()
        year, month, day = (self._date_text(e) for e in self.date_entries)
        rows, notice = self.manager.search(id_text, name_text, year, month, day)
        if isinstance(notice, tuple) and notice[0] == "guess":
            self.show_guess(notice[1])
        elif notice == "invalid":
            self.show_invalid()
        # 어느 경우든 목록을 다시 채운다 (맞는 기록이 없으면 글 없이 목록만 빈다)
        self.fill(rows)
        self.update_empty()

    def next_box(self, event):
        """연이 4자리 · 월이 2자리가 되면 다음 칸으로 focus()를 옮긴다"""
        entry = event.widget
        if str(entry.cget("fg")) == COLOR["placeholder"]:
            return          # 예시 글자는 입력이 아니다
        key = event.keysym.replace("KP_", "")   # 숫자 패드의 1은 "KP_1"
        if not key.isdigit():
            return          # Tab · Shift · 화살표를 뗄 때는 넘어가지 않는다 (Shift+Tab으로 앞 칸에 돌아갈 수 있게)
        year, month, day = self.date_entries
        if entry is year and len(entry.get()) == 4:
            month.focus()
        elif entry is month and len(entry.get()) == 2:
            day.focus()

    def update_suggest(self, event):
        """병원명 칸에서 키를 뗄 때: 문구를 지우고, 추천 목록을 띄우거나 숨긴다"""
        self.clear_msg()
        names = self.manager.suggest(self.name_entry.get())
        if not names:
            self.suggest_tree.place_forget()
            return
        self.suggest_tree.delete(*self.suggest_tree.get_children())
        for i, name in enumerate(names):
            self.suggest_tree.insert("", "end", iid=str(i), values=(name,))
        self.hover_row = ""
        # 병원명 칸 바로 밑 2px, 폭 260, 줄 높이 44 x 줄 수
        self.suggest_tree.place(in_=self.name_box, x=0, rely=1.0, y=2, width=260, height=44 * len(names))
        self.suggest_tree.lift()

    def on_suggest_motion(self, event):
        """마우스가 올라간 추천 줄에 hover 색"""
        row = self.suggest_tree.identify_row(event.y)
        if row == self.hover_row:
            return
        if self.hover_row:
            self.suggest_tree.item(self.hover_row, tags=())
        if row:
            self.suggest_tree.item(row, tags=("hover",))
        self.hover_row = row

    def on_suggest_click(self, event):
        """누른 추천 줄의 이름을 병원명 칸에 채우고 목록을 숨긴다"""
        row = self.suggest_tree.identify_row(event.y)
        if not row:
            return
        name = self.suggest_tree.item(row, "values")[0]
        self._set_name(name)
        self.suggest_tree.place_forget()

    def show_guess(self, name):
        """병원명 칸 밑에 「(정식 이름)이라고 쓰려던 건가요?」. 이름(밑줄)을 누르면 칸에 채워진다"""
        self.msg_name.config(text=name)
        self.msg_text.config(text=Message.GUESS_TAIL)
        self.msg_frame.place(in_=self.name_box, x=0, rely=1.0, y=6)

    def show_invalid(self):
        """병원명 칸 밑에 「음, 이 병원은 유효하지 않은 것 같네요.」 한 줄 (첫 문장만)"""
        self.msg_name.config(text="")
        self.msg_text.config(text=Message.INVALID_NAME[0])
        self.msg_frame.place(in_=self.name_box, x=0, rely=1.0, y=6)

    def clear_msg(self):
        """병원명 칸 밑 문구를 지운다"""
        self.msg_frame.place_forget()
        self.msg_name.config(text="")
        self.msg_text.config(text="")

    # ------------------------------------------------------------ 3.16 삭제
    def delete_click(self):
        """삭제 버튼. 고른 행이 없으면 2초 안내, 있으면 확인창"""
        sel = self.tree.selection()
        if not sel:
            Message.show_toast(Message.NO_DELETE_SELECT, self.delete_btn)
            return
        route_id = int(self.tree.item(sel[0], "values")[0])
        self.confirm_delete(route_id)

    def confirm_delete(self, route_id):
        """「n번 경로를 삭제할까요?」 확인창 (취소 | 삭제하기). Message 경고창과 같은 모양이라 직접 만든다"""
        win = tk.Frame(self.root, bg=COLOR["border"])   # 새 창 없이 root 안에 올리는 확인창
        body = tk.Frame(win, bg=COLOR["white"])
        body.pack(fill="both", expand=True, padx=1, pady=1)
        tk.Label(body, text=Message.DELETE_ASK.format(route_id), font=FONT["l_bold"], fg="black",
                 bg=COLOR["white"]).pack(fill="x", pady=(24, 0), padx=20)
        tk.Label(body, text=Message.DELETE_WARN, font=FONT["m"], fg=COLOR["warning"],
                 bg=COLOR["white"]).pack(fill="x", pady=(6, 0), padx=20)
        tk.Frame(body, height=1, bg=COLOR["line"]).pack(fill="x", pady=(24, 0))
        buttons = tk.Frame(body, height=48, bg=COLOR["white"])
        buttons.pack(fill="x")
        buttons.pack_propagate(False)
        cancel = tk.Label(buttons, text="취소", font=FONT["l_bold"], fg="black", bg=COLOR["white"])
        cancel.pack(side="left", fill="both", expand=True)
        tk.Frame(buttons, width=1, bg=COLOR["line"]).pack(side="left", fill="y")   # 가운데 세로선
        ok = tk.Label(buttons, text="삭제하기", font=FONT["l_bold"], fg="black", bg=COLOR["white"])
        ok.pack(side="left", fill="both", expand=True)
        # 누르는 동안 white_press, 뗄 때 동작
        for label, action in ((cancel, win.destroy), (ok, lambda: self.do_delete(route_id))):
            label.bind("<ButtonPress-1>", lambda e, l=label: l.configure(bg=COLOR["white_press"]))
            label.bind("<ButtonRelease-1>", lambda e, a=action: a())
        win.place(relx=0.5, rely=0.5, anchor="center", width=400)
        win.lift()
        Message.hold_clicks(win)   # 확인창이 떠 있는 동안 ← · 삭제 · 목록을 누를 수 없게
        self.confirm_win = win

    def do_delete(self, route_id):
        """확인창을 닫고 manager.delete. True면 그 행만 지우고, False면 경고창(행은 그대로)"""
        self.confirm_win.destroy()
        ok = self.manager.delete(route_id)
        if ok:
            self.tree.delete(str(route_id))
            self.update_empty()      # 마지막 행이었으면 빈 목록 안내
        else:
            Message.show_alert(*Message.DELETE_FAIL)

    # ------------------------------------------------------------ 3.17 돌아가기
    def back_to_menu(self):
        """← 버튼. 이 화면을 지우고 on_back을 부른다 (지도 화면은 Ui가 다시 띄운다)"""
        self.past_screen.destroy()
        self.on_back()

    # ------------------------------------------------------------ 안에서만 쓰는 도우미 (설계서에 없음)
    def _apply_style(self):
        """목록 · 머리줄 · 추천 목록 · 스크롤 막대 모양 (Ui 3.9와 같은 값)"""
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", font=FONT["m"], rowheight=27,
                        background="white", fieldbackground="white")
        style.map("Treeview", background=[("selected", COLOR["select"])],
                  foreground=[("selected", "black")])
        style.configure("Treeview.Heading", background=COLOR["surface"],
                        foreground=COLOR["text_sub"], font=FONT["s_bold"])
        style.configure("Suggest.Treeview", rowheight=44, font=FONT["m"],
                        background="white", fieldbackground="white")
        style.configure("Vertical.TScrollbar", troughcolor=COLOR["track"],
                        background=COLOR["border"], arrowsize=0)

    def _build_top_bar(self):
        """위 줄(높이 76, primary): ← 버튼과 제목 「과거 경로」"""
        bar = tk.Frame(self.past_screen, bg=COLOR["primary"], height=76)
        bar.pack(side="top", fill="x")
        bar.pack_propagate(False)
        back_box = tk.Frame(bar, bg=COLOR["primary_press"], width=48, height=48)
        back_box.pack(side="left", padx=(16, 0), pady=14)
        back_box.pack_propagate(False)
        self.back_icon = tk.PhotoImage(file=os.path.join(IMAGE_DIR, "icon_back.png"))
        tk.Button(back_box, image=self.back_icon, bg=COLOR["primary_press"],
                  activebackground=COLOR["primary_press"], relief="flat", bd=0,
                  command=self.back_to_menu).pack(fill="both", expand=True)
        tk.Label(bar, text="과거 경로", font=FONT["2xl"], fg=COLOR["white"],
                 bg=COLOR["primary"]).pack(side="left", padx=(16, 0))

    def _build_inputs(self):
        """입력칸 줄: 식별 번호 | 병원명 | 저장 날짜(연 / 월 / 일) | 검색"""
        row = tk.Frame(self.past_screen, bg="white")
        row.pack(side="top", fill="x", padx=16, pady=(16, 0))

        self.id_entry, _ = self._field(row, "식별 번호", 120, first=True, digits=10)

        self.name_entry, self.name_box = self._field(row, "병원명", 260)
        self.name_entry.bind("<KeyRelease>", self.update_suggest)

        # 저장 날짜: 연 76 / 월 48 / 일 48. 가운데 「/」는 폭 22
        date_group = tk.Frame(row, bg="white")
        date_group.pack(side="left", padx=(40, 0))
        tk.Label(date_group, text="저장 날짜", font=FONT["s_bold"], fg=COLOR["text_sub"],
                 bg="white").pack(anchor="w")
        date_row = tk.Frame(date_group, bg="white")
        date_row.pack()
        self.date_entries = []
        for i, (width, limit) in enumerate(((76, 4), (48, 2), (48, 2))):
            if i > 0:
                slash = tk.Frame(date_row, width=22, height=40, bg="white")
                slash.pack(side="left")
                slash.pack_propagate(False)
                tk.Label(slash, text="/", font=FONT["m_bold"], fg=COLOR["text_sub"],
                         bg="white").pack(fill="both", expand=True)
            box, entry = self._entry_box(date_row, width, digits=limit, center=True)
            box.pack(side="left")
            entry.insert(0, DATE_HINT[i])
            entry.config(fg=COLOR["placeholder"])
            entry.bind("<FocusIn>", self.on_focus_in)
            self.date_entries.append(entry)
        self.date_entries[0].bind("<KeyRelease>", self.next_box)
        self.date_entries[1].bind("<KeyRelease>", self.next_box)

        # 검색 버튼 76x40 (칸 이름 줄만큼 아래로 내려 다른 칸과 높이를 맞춘다)
        btn_group = tk.Frame(row, bg="white")
        btn_group.pack(side="left", padx=(40, 0))
        tk.Label(btn_group, text=" ", font=FONT["s_bold"], bg="white").pack(anchor="w")
        btn_box = tk.Frame(btn_group, width=76, height=40, bg="white")
        btn_box.pack()
        btn_box.pack_propagate(False)
        tk.Button(btn_box, text="검색", font=FONT["l_bold"], fg="white", bg=COLOR["dark"],
                  activebackground=COLOR["dark_press"], activeforeground="white",
                  relief="flat", bd=0, command=self.search_past).pack(fill="both", expand=True)

    def _field(self, parent, title, width, first=False, digits=None):
        """칸 이름(위) + 입력칸(아래) 묶음. (Entry, 칸을 감싼 Frame)을 돌려준다"""
        group = tk.Frame(parent, bg="white")
        group.pack(side="left", padx=(0 if first else 40, 0))
        tk.Label(group, text=title, font=FONT["s_bold"], fg=COLOR["text_sub"], bg="white").pack(anchor="w")
        box, entry = self._entry_box(group, width, digits=digits)
        box.pack()
        return entry, box

    def _entry_box(self, parent, width, digits=None, center=False):
        """폭 width, 높이 40, 테두리 1px(border)의 입력칸. digits가 있으면 숫자만 그 자릿수까지 받는다"""
        box = tk.Frame(parent, width=width, height=40, bg="white", highlightthickness=1,
                       highlightbackground=COLOR["border"], highlightcolor=COLOR["border"])
        box.pack_propagate(False)
        options = {"font": FONT["m"], "bg": "white", "fg": "black", "relief": "flat", "bd": 0,
                   "insertbackground": "black"}
        if center:
            options["justify"] = "center"
        if digits is not None:
            # 숫자만 받는다: %P = 친 뒤 칸 전체 글자. False를 돌려주면 그 글자는 안 들어간다 (붙여넣기도 막는다)
            options["validate"] = "key"
            options["validatecommand"] = (self.root.register(self._digits_only(digits)), "%P")
        entry = tk.Entry(box, **options)
        entry.pack(fill="both", expand=True, padx=8)
        return box, entry

    @staticmethod
    def _digits_only(limit):
        def check(after):
            return after == "" or (after.isascii() and after.isdecimal() and len(after) <= limit)
        return check

    def _build_delete_button(self):
        """삭제 버튼 160x44: 목록 아래 16 · 오른쪽 16"""
        # 테두리 1px은 버튼이 아니라 바깥 Frame에 준다 (Windows 버튼은 highlightthickness 테두리가 안 보인다)
        box = tk.Frame(self.past_screen, width=160, height=44, bg="white", highlightthickness=1,
                       highlightbackground=COLOR["border"], highlightcolor=COLOR["border"])
        box.pack(side="bottom", anchor="e", padx=16, pady=16)
        box.pack_propagate(False)
        self.delete_btn = tk.Button(box, text="삭제", font=FONT["l_bold"], fg=COLOR["text_sub"], bg="white",
                                    activebackground=COLOR["white_press"], relief="flat", bd=0,
                                    highlightthickness=0, command=self.delete_click)
        self.delete_btn.pack(fill="both", expand=True)

    def _build_list(self):
        """7열 목록 (식별 번호 90 · 저장 날짜 120 · 병원명 260 · 병상 수 86 · 도착 시간 120 · 거리 110 · 교차로 수 130)"""
        holder = tk.Frame(self.past_screen, bg="white")
        holder.pack(side="top", fill="both", expand=True, padx=16, pady=(28, 0))
        columns = ("id", "date", "hospital", "beds", "eta", "distance", "nodes")
        heads = ("식별 번호", "저장 날짜", "병원명", "병상 수", "도착 시간", "거리", "교차로 수")
        widths = (90, 120, 260, 86, 120, 110, 130)
        self.tree = ttk.Treeview(holder, columns=columns, show="headings", selectmode="browse")
        for name, head, width in zip(columns, heads, widths):
            self.tree.heading(name, text=head)
            self.tree.column(name, width=width, anchor="w" if name == "hospital" else "center", stretch=False)
        scroll = ttk.Scrollbar(holder, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

    @staticmethod
    def _date_text(entry):
        """날짜 칸 글자. 연한 회색 예시 글자 상태이면 입력이 아니므로 ""로 본다"""
        return "" if str(entry.cget("fg")) == COLOR["placeholder"] else entry.get()

    def _set_name(self, name):
        """병원명 칸을 name으로 채운다"""
        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, name)

    def _on_guess_click(self, event):
        """「쓰려던 건가요?」의 이름을 누르면 병원명 칸에 채운다 (자동으로 검색하지는 않는다)"""
        name = self.msg_name.cget("text")
        if name:
            self._set_name(name)
            self.clear_msg()
