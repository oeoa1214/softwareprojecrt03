"""ShortestRoad - 통행 시간 계산 + 다익스트라 + 병원 비교 (AD-02, AD-05, AD-07, FR-01)."""
import heapq


class ShortestRoad:
    MIN_SPEED = 1
    MAX_SPEED = 150

    def __init__(self, links, speeds):
        """links  = [(link_id, f_node_id, t_node_id, length_m, max_spd), ...]
        speeds = [(link_id, speed_kmh), ...]   (둘 다 오은찬이 DB에서 꺼내 넘김)"""
        self.__graph = {}      # {교차로: [(다음 교차로, 통행 시간(초), 길이(m)), ...]}
        self.__dist = {}       # {교차로: 사고 교차로에서 최소 시간(초)}
        self.__prev = {}       # {교차로: 최소 시간 경로에서 바로 앞 교차로}
        self.__prev_len = {}   # {교차로: 바로 앞 교차로에서 오는 도로 길이(m)}
        self.__start = None

        speed_by_link = {link_id: spd for link_id, spd in speeds}
        for link_id, f_node, t_node, length_m, max_spd in links:
            # 속도 API 값이 없으면 제한 속도(max_spd)를 쓴다.
            speed = speed_by_link.get(link_id, max_spd)
            if speed is None or not (self.MIN_SPEED <= speed <= self.MAX_SPEED):
                continue       # 속도가 1~150km/h 밖인 도로는 graph에 넣지 않는다.
            time_s = self.passway_time(length_m, speed)
            self.__graph.setdefault(f_node, []).append((t_node, time_s, length_m))
            self.__graph.setdefault(t_node, [])

    def passway_time(self, length, speed):
        """반환: 통행 시간(초) = 길이(m) / (속도(km/h) x 1000 / 3600)"""
        return length / (speed * 1000 / 3600)

    def dijkstra(self, start):
        """반환: dist 딕셔너리 {교차로: 최소 시간(초)}"""
        dist = {start: 0}
        prev = {start: None}
        prev_len = {}
        heap = [(0, start)]
        done = set()
        while heap:
            d, k = heapq.heappop(heap)
            if k in done:
                continue
            done.add(k)
            for u, time_s, length_m in self.__graph.get(k, []):
                nd = d + time_s
                if u not in dist or nd < dist[u]:
                    dist[u] = nd
                    prev[u] = k
                    prev_len[u] = length_m
                    heapq.heappush(heap, (nd, u))
        self.__dist, self.__prev, self.__prev_len, self.__start = dist, prev, prev_len, start
        return dist

    def sort_hospitals(self, hospitals):
        """hospitals = [(hpid:str, name:str, node_id:int, beds:int 또는 None), ...]
        반환: [(hpid, name, beds, eta_min:float, distance_m:float, node_count:int), ...]
              도착 시간 순, 병상 0 이하·None은 맨 뒤 (그 안에서도 도착 시간 순)"""
        if self.__start is None:
            raise ValueError("dijkstra를 먼저 불러야 합니다")
        rows = []
        for hpid, name, node_id, beds in hospitals:
            if node_id not in self.__dist:
                continue       # 갈 수 없는 병원은 목록에서 뺀다.
            route = self.make_route(node_id)
            eta_min = self.__dist[node_id] / 60
            distance_m = sum(self.__prev_len[n] for n in route[1:])
            rows.append((hpid, name, beds, eta_min, distance_m, len(route)))
        no_bed = lambda r: 0 if (r[2] is not None and r[2] > 0) else 1
        rows.sort(key=lambda r: (no_bed(r), r[3]))
        return rows

    def make_route(self, hospital_node):
        """반환: [사고 교차로, ..., 병원 교차로] 순서의 교차로 번호 목록 (갈 수 없으면 [])"""
        if hospital_node not in self.__dist:
            return []
        route = []
        node = hospital_node
        while node is not None:
            route.append(node)
            node = self.__prev[node]
        route.reverse()
        return route
