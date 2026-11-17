"""linkspeed.json(대구 교통소통정보 API 응답 저장 파일)으로 하는 확인 두 가지.

  ① 번호 대조: STD_LINK_ID를 int로 바꿔 link.csv의 link_id와 맞는 개수를 센다.
  ② 실제 데이터로 돌려 보기: (번호, 속도)로 speeds를 만들어 link.csv와 함께 ShortestRoad에 넣는다.

사용:  python check_linkspeed.py linkspeed.json [--link data/link.csv] [--node data/node.csv] [--start 교차로번호]

※ 같은 번호가 여러 번 나와도(평균은 오은찬이 만든다) 고치지 않고 그대로 넣는다.
"""
import argparse
import json
import os
import random

from road_api import RoadApi
from shortest_road import ShortestRoad


def read_speeds(json_path):
    """반환: [(link_id:int, speed_kmh:float), ...]  (body -> items -> item 목록의 STD_LINK_ID, LINK_SPEED)"""
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    items = data["body"]["items"]
    if isinstance(items, dict):
        items = items["item"]
    if isinstance(items, dict):          # item이 하나뿐이면 딕셔너리로 올 수 있다
        items = [items]
    speeds = []
    for it in items:
        speeds.append((int(it["STD_LINK_ID"]), float(it["LINK_SPEED"])))
    return speeds


def compare_ids(speeds, links):
    """반환: (서로 다른 번호 수, link.csv에 있는 번호 수, 없는 번호 목록)"""
    ids = {i for i, _ in speeds}
    have = {l[0] for l in links}
    missing = sorted(ids - have)
    return len(ids), len(ids) - len(missing), missing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json_path")
    ap.add_argument("--link", default="data/link.csv")
    ap.add_argument("--node", default="data/node.csv")
    ap.add_argument("--start", type=int, default=None)
    args = ap.parse_args()

    nodes, links, is_dummy = RoadApi(args.node, args.link).load_node_link()
    if is_dummy:
        raise SystemExit("data/node.csv, data/link.csv를 읽지 못했다. convert_standard_nodelink.py를 먼저 돌린다.")
    speeds = read_speeds(args.json_path)

    total, matched, missing = compare_ids(speeds, links)
    print(f"[① 번호 대조] 응답 {len(speeds)}행, 서로 다른 번호 {total}개 중 link.csv에 있는 것 {matched}개 "
          f"({matched / total:.1%})")
    if missing:
        print("   없는 번호(제출 목록, 앞 30개):", missing[:30])

    start = args.start if args.start is not None else nodes[0][0]
    sr = ShortestRoad(links, speeds)
    dist = sr.dijkstra(start)
    print(f"[② 실제 데이터] 사고 교차로 {start}에서 닿는 교차로 {len(dist)}개 / 전체 {len(nodes)}개")
    random.seed(0)
    hospitals = [(f"h{i}", f"임시병원{i}", n[0], 1) for i, n in enumerate(random.sample(nodes, min(5, len(nodes))))]
    for row in sr.sort_hospitals(hospitals):
        print(f"   {row[1]}: {row[3]:.1f}분, {row[4] / 1000:.2f}km, 교차로 {row[5]}개")
    print("오류 없이 끝남")


if __name__ == "__main__":
    main()
