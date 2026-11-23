"""style - 모든 화면이 같이 쓰는 글자 크기 · 색 · 병원 표시 이름
(UI/UX 설계서 2장 표 3 글자 크기 표준 · 표 4 색 표준, 3.9 표 32 병원 표시 이름).
값을 고치지 않는다. 바꿀 일이 생기면 두 사람이 같이 바꾼다."""
import os

# 글자 크기 (표 3). 크기를 음수로 주면 pt가 아니라 픽셀(px)
FONT = {
    "2xl":    ("Pretendard", -32, "bold"),
    "xl":     ("Pretendard", -20, "bold"),
    "l":      ("Pretendard", -16),
    "l_bold": ("Pretendard", -16, "bold"),
    "m":      ("Pretendard", -15),
    "m_bold": ("Pretendard", -15, "bold"),     # 3.14 날짜 칸 「/」 (표 3에 없어 더함)
    "m_link": ("Pretendard", -15, "bold underline"),
    "s":      ("Pretendard", -13),
    "s_bold": ("Pretendard", -13, "bold"),
    "xs":     ("Pretendard", -11),
}

# 색 (표 4)
COLOR = {
    "primary": "#E86C25", "primary_press": "#C95A1D",
    "dark": "#515151", "dark_press": "#3A3A3A",
    "text_sub": "#3C3C3C", "text_hint": "#787878",
    "placeholder": "#B0B0B0", "disabled": "#B4B4B4",
    "hover": "#E8EEF6", "warning": "#F5B400", "select": "#FFF1B8",
    "white": "#FFFFFF", "surface": "#F6F6F6", "white_press": "#F0F0F0",
    "line": "#D2D2D2", "route_outline": "#5A5A5A",
    "border": "#BEBEBE", "track": "#E1E1E1",
    "boundary": "#E53935", "shade": "#333333",
}

# 병원 표시 이름 (표 32): 정식 이름이 11글자보다 긴 5곳 (3.9 병원 목록, 3.14 과거 경로 목록)
DISPLAY_NAME = {
    "(재)미리내천주성삼성직수도회천주성삼병원": "미리내천주성삼병원",
    "대구가톨릭대학교칠곡가톨릭병원": "칠곡대구가톨릭병원",
    "의료법인구의료재단구병원": "구의료재단구병원",
    "의료법인백천의료재단바로본병원": "백천의료재단바로본병원",
    "한국보훈복지의료공단대구보훈병원": "대구보훈병원",
}

# 그림 파일 폴더 (어디서 실행해도 page_tinker/images를 가리킨다)
IMAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")