"""Crossroad - 클릭 위치에서 300m 이내 가장 가까운 교차로 찾기 (AD-04)."""
import math


class Crossroad:
    LIMIT_M = 300

    def __init__(self, nodes):
        """nodes = [(node_id:int, lat:float, lon:float), ...]  (오은찬이 DB에서 꺼내 넘김)"""
        self.__nodes = nodes
        # 대구 범위: nodes의 위도·경도 최솟값 ~ 최댓값
        lats = [n[1] for n in nodes]
        lons = [n[2] for n in nodes]
        self.__min_lat, self.__max_lat = min(lats), max(lats)
        self.__min_lon, self.__max_lon = min(lons), max(lons)

    def find_crossroad(self, lat, lon):
        """반환: 300m 이내 가장 가까운 교차로 번호(int) / 대구 밖 -1 / 300m 초과 -2"""
        if not (self.__min_lat <= lat <= self.__max_lat
                and self.__min_lon <= lon <= self.__max_lon):
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

    def __distance(self, lat1, lon1, lat2, lon2):
        """반환: 두 지점 거리(미터, float) - 하버사인 공식, 지구 반지름 6371000"""
        r = 6371000
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dp = p2 - p1
        dl = math.radians(lon2 - lon1)
        a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
        return 2 * r * math.asin(math.sqrt(a))
