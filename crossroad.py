"""Crossroad - 클릭 위치에서 300m 이내 가장 가까운 교차로 찾기 (AD-04)."""
import json
import math
import os

# 대구 경계선 파일 (행정동 142개의 바깥선, 군위군 제외). crossroad.py 옆 data 폴더에 있다.
BOUNDARY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "daegu_boundary.json")


class Crossroad:
    LIMIT_M = 300

    def __init__(self, nodes, boundary_path=BOUNDARY_PATH):
        """nodes = [(node_id:int, lat:float, lon:float), ...]  (오은찬이 DB에서 꺼내 넘김)
        boundary_path = 대구 경계선 파일. 안 넣으면 data/daegu_boundary.json"""
        self.__nodes = nodes
        # 대구 범위: 행정동 경계선 (계획서 EX-04 · EX-05 기준)
        with open(boundary_path, encoding="utf-8") as f:
            self.__rings = json.load(f)["rings"]   # [[[lat, lon], ...], ...] 경계선 142개

    def find_crossroad(self, lat, lon):
        """반환: 300m 이내 가장 가까운 교차로 번호(int) / 대구 밖 -1 / 300m 초과 -2"""
        if not self.__in_daegu(lat, lon):
            return -1
        best_id, best_dist = None, None
        for node_id, n_lat, n_lon in self.__nodes:
            d = self.__distance(lat, lon, n_lat, n_lon)
            if best_dist is None or d < best_dist:
                best_id, best_dist = node_id, d
        # 300m 딱 맞으면 정상 (부동소수점 오차 방지를 위해 소수 6자리까지만 비교)
        if round(best_dist, 6) <= self.LIMIT_M:
            return best_id
        return -2

    def __in_daegu(self, lat, lon):
        """반환: 대구 경계선 안이면 True, 밖이면 False.
        점에서 오른쪽(경도가 커지는 쪽)으로 선을 그어 경계선을 몇 번 지나는지 센다. 홀수면 안이다.
        경계선 142개 중 하나라도 안이면 대구 안이다."""
        for ring in self.__rings:
            inside = False
            j = len(ring) - 1
            for i in range(len(ring)):
                lat_i, lon_i = ring[i]
                lat_j, lon_j = ring[j]
                if (lat_i > lat) != (lat_j > lat):  # 이 변이 점의 위도를 가로지르면
                    cross_lon = (lon_j - lon_i) * (lat - lat_i) / (lat_j - lat_i) + lon_i
                    if lon < cross_lon:  # 가로지르는 곳이 점의 오른쪽이면 1번 지남
                        inside = not inside
                j = i
            if inside:
                return True
        return False

    def __distance(self, lat1, lon1, lat2, lon2):
        """반환: 두 지점 거리(미터, float) - 하버사인 공식, 지구 반지름 6371000"""
        r = 6371000
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dp = p2 - p1
        dl = math.radians(lon2 - lon1)
        a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
        return 2 * r * math.asin(math.sqrt(a))