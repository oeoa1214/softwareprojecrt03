import csv, time
from crossroad import Crossroad

# 교차로 목록 읽기 (node.csv)
nodes = []
with open("data/node.csv", encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        nodes.append((int(r["node_id"]), float(r["lat"]), float(r["lon"])))

c = Crossroad(nodes)

def measure(lat, lon, times=50):
    start = time.perf_counter()          # 시작 시각
    for _ in range(times):
        result = c.find_crossroad(lat, lon)
    end = time.perf_counter()            # 끝 시각
    avg = (end - start) / times          # 한 번 평균(초)
    print(f"({lat}, {lon}) 결과 {result}, 평균 {avg:.5f}초")

measure(35.871, 128.601)   # 대구시청
measure(35.815, 128.585)   # 앞산 쪽 산속 (-2)