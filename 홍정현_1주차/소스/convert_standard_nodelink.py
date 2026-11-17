"""표준노드링크(SHP)에서 대구(군위 제외)만 잘라 data/node.csv, data/link.csv로 저장한다. (IF-003, AD-08)

준비:  pip install pyshp pyproj
사용:  python convert_standard_nodelink.py <MOCT_NODE.shp> <MOCT_LINK.shp>
       (교통 API 응답과의 번호 대조는 check_linkspeed.py 로 한다)

대구 거르기: 지역 번호 칸(STNL_REG)이 있으면 그 값(150~157)을 쓰고,
             없으면 NODE_ID / LINK_ID 의 앞 3자리(150~157)를 쓴다.
"""
import argparse
import csv
import math
import os
from collections import Counter

import shapefile                    # pyshp
from pyproj import Transformer

# 칸 이름 후보 (대문자로 비교한다)
FIELD_NODE_ID = ("NODE_ID",)
FIELD_NODE_NAME = ("NODE_NAME",)
FIELD_REGION = ("STNL_REG",)
FIELD_LINK_ID = ("LINK_ID",)
FIELD_F_NODE = ("F_NODE",)
FIELD_T_NODE = ("T_NODE",)
FIELD_LENGTH = ("LENGTH",)
FIELD_MAX_SPD = ("MAX_SPD",)

DAEGU_REGIONS = {str(c) for c in range(150, 158)}   # 150~157 (군위 제외)


def pick(names, candidates):
    for c in candidates:
        if c in names:
            return c
    return None


def open_shp(path):
    return shapefile.Reader(path, encoding="cp949")          # 한글이 깨지면 encoding="utf-8"


def field_names(reader):
    return [f[0].upper() for f in reader.fields[1:]]


def region_of(rec, f_reg, f_id):
    """지역 번호(문자열). 지역 칸이 있으면 그 값, 없으면 번호의 앞 3자리"""
    if f_reg and str(rec[f_reg]).strip():
        return str(rec[f_reg]).strip()
    return str(rec[f_id]).strip()[:3]


def meters(points):
    """도로 모양 좌표(미터 단위 EPSG:5186)를 이어 길이를 구한다. (LENGTH 칸이 없을 때만 사용)"""
    return sum(math.dist(points[i], points[i + 1]) for i in range(len(points) - 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("node_shp")
    ap.add_argument("link_shp")
    ap.add_argument("--out", default="data")
    args = ap.parse_args()

    # EPSG:5186(중부원점TM) -> EPSG:4326(위도·경도). always_xy=True 이므로 결과는 (경도, 위도) 순서
    tr = Transformer.from_crs("EPSG:5186", "EPSG:4326", always_xy=True)

    # ---- 교차로 ----
    nr = open_shp(args.node_shp)
    nnames = field_names(nr)
    print("[node 칸 이름]", nnames)
    f_id, f_name, f_reg = (pick(nnames, FIELD_NODE_ID), pick(nnames, FIELD_NODE_NAME), pick(nnames, FIELD_REGION))
    if not f_id:
        raise SystemExit("node 칸 이름(NODE_ID)을 찾지 못했다. 위 목록을 보고 FIELD_NODE_ID 를 고친다.")
    print("   지역 거르기 방법:", f_reg if f_reg else f"{f_id} 앞 3자리")
    nodes = {}
    node_regions = Counter()
    for sr in nr.iterShapeRecords():
        rec = {n: v for n, v in zip(nnames, sr.record)}
        reg = region_of(rec, f_reg, f_id)
        if reg not in DAEGU_REGIONS:
            continue
        x, y = sr.shape.points[0]
        lon, lat = tr.transform(x, y)                      # (경도, 위도) 순서 주의
        nodes[int(rec[f_id])] = (str(rec[f_name] or "").strip() if f_name else "", lat, lon)
        node_regions[reg] += 1

    # ---- 도로 구간 ----
    lr = open_shp(args.link_shp)
    lnames = field_names(lr)
    print("[link 칸 이름]", lnames)
    l_id, l_f, l_t = pick(lnames, FIELD_LINK_ID), pick(lnames, FIELD_F_NODE), pick(lnames, FIELD_T_NODE)
    l_reg, l_len, l_spd = pick(lnames, FIELD_REGION), pick(lnames, FIELD_LENGTH), pick(lnames, FIELD_MAX_SPD)
    if not (l_id and l_f and l_t):
        raise SystemExit("link 칸 이름(LINK_ID, F_NODE, T_NODE)을 찾지 못했다. 위 목록을 보고 FIELD_* 를 고친다.")
    print("   지역 거르기 방법:", l_reg if l_reg else f"{l_id} 앞 3자리",
          "/ 길이:", l_len if l_len else "도로 모양에서 계산", "/ 제한 속도:", l_spd if l_spd else "없음(0)")
    links = []
    for sr in lr.iterShapeRecords():
        rec = {n: v for n, v in zip(lnames, sr.record)}
        if region_of(rec, l_reg, l_id) not in DAEGU_REGIONS:
            continue
        f, t = int(rec[l_f]), int(rec[l_t])
        if f not in nodes or t not in nodes:               # 한쪽이라도 없으면 끊긴 길 -> 버린다
            continue
        length = float(rec[l_len]) if l_len and rec[l_len] else meters(sr.shape.points)
        spd = int(float(rec[l_spd])) if l_spd and rec[l_spd] else 0
        links.append((int(rec[l_id]), f, t, length, spd))

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "node.csv"), "w", newline="", encoding="utf-8") as fp:
        w = csv.writer(fp); w.writerow(["node_id", "node_name", "lat", "lon"])
        for nid, (name, lat, lon) in nodes.items():
            w.writerow([nid, name, lat, lon])
    with open(os.path.join(args.out, "link.csv"), "w", newline="", encoding="utf-8") as fp:
        w = csv.writer(fp); w.writerow(["link_id", "f_node_id", "t_node_id", "length_m", "max_spd"])
        w.writerows(links)

    # ---- 확인 (1주차 제출 때 캡처) ----
    print("\n[자르기] 남은 교차로 지역 번호별 개수:", dict(sorted(node_regions.items())))
    print("[개수] 교차로", len(nodes), "/ 도로 구간", len(links))
    print("[좌표] 교차로 3개 (위도, 경도) - 대구면 위도 35.x, 경도 128.x:")
    for nid in list(nodes)[:3]:
        print("   ", nid, nodes[nid][1], nodes[nid][2])
    broken = sum(1 for _, f, t, _, _ in links if f not in nodes or t not in nodes)
    print("[끊긴 길] f/t 교차로가 node.csv에 없는 도로:", broken, "개 (0이어야 함)")
    if links:
        no_spd = sum(1 for l in links if l[4] <= 0)
        print("[제한 속도 없음] max_spd가 0인 도로:", no_spd, "개 (속도 API에도 없으면 계산에서 빠짐)")


if __name__ == "__main__":
    main()