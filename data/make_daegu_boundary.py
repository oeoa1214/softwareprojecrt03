"""
대구 경계 파일 만들기 (한 번만 실행)

입력: 행정동 경계 GeoJSON (vuski/admdongkor, ver20260701)
      https://raw.githubusercontent.com/vuski/admdongkor/master/ver20260701/HangJeongDong_ver20260701.geojson
출력: data/daegu_boundary.json
      대구광역시(군위군 제외) 행정동의 바깥 테두리 목록
      {"source": ..., "rings": [ [[위도, 경도], [위도, 경도], ...], ... ]}

실행: py make_daegu_boundary.py HangJeongDong_ver20260701.geojson
"""
import json
import os
import sys

SRC_NAME = "vuski/admdongkor ver20260701 행정동 경계"


def make(geojson_path, out_path="data/daegu_boundary.json"):
    with open(geojson_path, encoding="utf-8") as f:
        data = json.load(f)

    rings = []
    dong_count = 0
    for feature in data["features"]:
        prop = feature["properties"]
        # 대구광역시만, 군위군은 제외
        if prop.get("sidonm") != "대구광역시":
            continue
        if prop.get("sggnm") == "군위군":
            continue
        dong_count += 1

        geom = feature["geometry"]
        if geom["type"] == "Polygon":
            polygons = [geom["coordinates"]]
        else:  # MultiPolygon
            polygons = geom["coordinates"]

        for polygon in polygons:
            outer = polygon[0]  # 바깥 테두리만 (구멍은 다른 대구 동이 채움)
            # GeoJSON은 [경도, 위도] 순서 → [위도, 경도]로 바꿔 저장
            ring = [[round(lat, 6), round(lon, 6)] for lon, lat in outer]
            rings.append(ring)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"source": SRC_NAME, "rings": rings}, f, ensure_ascii=False)

    points = sum(len(r) for r in rings)
    print("행정동", dong_count, "개 / 테두리", len(rings), "개 / 꼭짓점", points, "개")
    print("저장:", out_path)


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "HangJeongDong_ver20260701.geojson"
    make(src)
