"""Crossroad - 클릭 위치에서 300m 이내 가장 가까운 교차로 찾기 (AD-04)."""
# json: 대구 경계선 파일(.json)을 읽을 때 쓴다
import json
# math: 하버사인 거리 계산에 sin, cos, asin, sqrt, radians를 쓴다
import math
# os: 이 파일(crossroad.py)이 있는 폴더를 찾아 data 폴더 경로를 만든다
import os

# 대구 경계선 파일 (행정동 142개의 바깥선, 군위군 제외). crossroad.py 옆 data 폴더에 있다.
BOUNDARY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "daegu_boundary.json")


class Crossroad:
    # 사고 지점에서 교차로까지 허용하는 최대 거리(미터). 딱 300m까지는 정상
    LIMIT_M = 300

    def __init__(self, nodes, boundary_path=BOUNDARY_PATH):
        """nodes = [(node_id:int, lat:float, lon:float), ...]  (오은찬이 DB에서 꺼내 넘김)
        boundary_path = 대구 경계선 파일. 안 넣으면 data/daegu_boundary.json"""
        self.__nodes = nodes
        # 대구 범위: 행정동 경계선 (계획서 EX-04 · EX-05 기준)
        # 경계선 파일은 객체를 만들 때 한 번만 읽어 둔다. 클릭할 때마다 읽으면 느리다
        with open(boundary_path, encoding="utf-8") as f:
            self.__rings = json.load(f)["rings"]   # [[[lat, lon], ...], ...] 경계선 142개

    def find_crossroad(self, lat, lon):
        """반환: 300m 이내 가장 가까운 교차로 번호(int) / 대구 밖 -1 / 300m 초과 -2"""
        # 1단계: 대구 경계선 밖이면 거리를 잴 필요 없이 바로 -1 (EX-04). 대구 판정을 먼저 한다
        if not self.__in_daegu(lat, lon):
            return -1
        # 2단계: 모든 교차로와의 거리를 하나씩 재서 가장 가까운 교차로를 기억한다 (AD-04)
        best_id, best_dist = None, None
        for node_id, n_lat, n_lon in self.__nodes:
            d = self.__distance(lat, lon, n_lat, n_lon)
            # 처음 본 교차로이거나, 지금까지 본 것보다 더 가까우면 갱신한다
            if best_dist is None or d < best_dist:
                best_id, best_dist = node_id, d
        # 300m 딱 맞으면 정상 (부동소수점 오차 방지를 위해 소수 6자리까지만 비교)
        # 3단계: 300m 이하면 그 교차로 번호, 넘으면 -2 (EX-05). round는 300.0000001 같은 계산 오차를 막는다
        if round(best_dist, 6) <= self.LIMIT_M:
            return best_id
        return -2

    def __in_daegu(self, lat, lon):
        """반환: 대구 경계선 안이면 True, 밖이면 False.
        점에서 오른쪽(경도가 커지는 쪽)으로 선을 그어 경계선을 몇 번 지나는지 센다. 홀수면 안이다.
        경계선 142개 중 하나라도 안이면 대구 안이다."""
        # ring = 행정동 하나의 바깥 경계선(점을 이어 만든 도형). 142개 중 하나라도 안이면 대구 안이다
        for ring in self.__rings:
            # 점에서 오른쪽으로 선을 그었을 때 경계선을 지난 횟수가 홀수면 True(안)가 된다
            inside = False
            # j는 i의 바로 앞 점이다. 처음에는 마지막 점과 첫 점을 이어 도형을 닫는다
            j = len(ring) - 1
            for i in range(len(ring)):
                lat_i, lon_i = ring[i]
                lat_j, lon_j = ring[j]
                if (lat_i > lat) != (lat_j > lat):  # 이 변이 점의 위도를 가로지르면
                    # 이 변이 점의 위도 높이에서 어느 경도를 지나는지 비례식으로 계산한다
                    cross_lon = (lon_j - lon_i) * (lat - lat_i) / (lat_j - lat_i) + lon_i
                    if lon < cross_lon:  # 가로지르는 곳이 점의 오른쪽이면 1번 지남
                        inside = not inside
                j = i
            if inside:
                return True
        return False

    def __distance(self, lat1, lon1, lat2, lon2):
        """반환: 두 지점 거리(미터, float) - 하버사인 공식, 지구 반지름 6371000"""
        # 지구 반지름(m)
        r = 6371000
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dp = p2 - p1
        dl = math.radians(lon2 - lon1)
        # 하버사인 공식: 지구 표면 위 두 점 사이 거리를 위도·경도 차이로 구한다
        a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
        # 호의 길이 = 2 x 반지름 x asin(sqrt(a)). 단위는 미터
        return 2 * r * math.asin(math.sqrt(a))