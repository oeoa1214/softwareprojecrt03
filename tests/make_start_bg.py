"""메인 화면 바탕 그림(page_tinker/images/start_bg.png)을 만든다. 한 번만 돌리면 된다.
가운데 #F67453 -> 가장자리 #FE9A3F로 퍼지는 주황, 960x650 (UI/UX 설계서 3.1)
실행: py tests/make_start_bg.py  (프로젝트 맨 위 폴더에서)"""
import os
from PIL import Image

W, H = 960, 650
inner, outer = (0xF6, 0x74, 0x53), (0xFE, 0x9A, 0x3F)   # 가운데 -> 가장자리
cx, cy = W / 2, H / 2
far = (cx ** 2 + cy ** 2) ** 0.5                          # 가운데에서 모서리까지 거리
img = Image.new("RGB", (W, H))
for y in range(H):
    for x in range(W):
        t = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 / far  # 0(가운데) ~ 1(모서리)
        img.putpixel((x, y), tuple(round(a + (b - a) * t) for a, b in zip(inner, outer)))
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "page_tinker", "images", "start_bg.png")
img.save(out)
print("저장:", os.path.normpath(out))
