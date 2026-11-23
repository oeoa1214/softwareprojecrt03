"""ShortestRoad - 통행 시간 계산 + 다익스트라 + 병원 비교 (AD-02, AD-05, AD-07, FR-01)."""
# heapq: 가장 작은 값을 빨리 꺼내는 '최소 힙'. 다익스트라에서 지금까지 가장 빠른 교차로를 꺼낼 때 쓴다
import heapq


class ShortestRoad:
    # 이 범위(1~150km/h) 밖의 속도는 비정상 값으로 보고 그 도로를 계산에서 뺀다 (계획서 2.5.1)
    MIN_SPEED = 1
    MAX_SPEED = 150

    def __init__(self, links, speeds):
        """links  = [(link_id, f_node_id, t_node_id, length_m, max_spd), ...]
        speeds = [(link_id, speed_kmh), ...]   (둘 다 오은찬이 DB에서 꺼내 넘김)"""
        # graph(인접 리스트): 교차로마다 '갈 수 있는 다음 교차로, 걸리는 시간(초), 길이(m)'를 모아 둔 사전
        self.__graph = {}      # {교차로: [(다음 교차로, 통행 시간(초), 길이(m)), ...]}
        self.__dist = {}       # {교차로: 사고 교차로에서 최소 시간(초)}
        self.__prev = {}       # {교차로: 최소 시간 경로에서 바로 앞 교차로}
        self.__prev_len = {}   # {교차로: 바로 앞 교차로에서 오는 도로 길이(m)}
        self.__start = None

        # 속도 목록을 {도로 번호: 속도} 사전으로 바꾸면 도로마다 바로 찾을 수 있다
        speed_by_link = {link_id: spd for link_id, spd in speeds}
        # 도로 구간 하나씩 본다. f_node(출발) -> t_node(도착) 방향이 있다
        for link_id, f_node, t_node, length_m, max_spd in links:
            # 속도 API 값이 없으면 제한 속도(max_spd)를 쓴다.
            speed = speed_by_link.get(link_id, max_spd)
            if speed is None or not (self.MIN_SPEED <= speed <= self.MAX_SPEED):
                continue       # 속도가 1~150km/h 밖인 도로는 graph에 넣지 않는다.
            # 도로의 가중치 = 이 도로를 지나는 데 걸리는 시간(초). 거리가 아니라 시간으로 계산한다
            time_s = self.passway_time(length_m, speed)
            # setdefault: f_node 칸이 없으면 빈 목록을 만들고, 있으면 그대로 쓴 뒤 도로 하나를 추가한다
            self.__graph.setdefault(f_node, []).append((t_node, time_s, length_m))
            # 도착 교차로도 칸을 만들어 둔다. 나가는 도로가 없는 막다른 교차로도 graph에 있어야 오류가 안 난다
            self.__graph.setdefault(t_node, [])

    def passway_time(self, length, speed):
        """반환: 통행 시간(초) = 길이(m) / (속도(km/h) x 1000 / 3600)"""
        # km/h를 m/s로 바꾸려면 x1000 ÷3600. 시간(초) = 길이(m) ÷ 속도(m/s)
        return length / (speed * 1000 / 3600)

    def dijkstra(self, start):
        """반환: dist 딕셔너리 {교차로: 최소 시간(초)}"""
        # dist: 사고 교차로에서 각 교차로까지 지금까지 찾은 최소 시간(초). 출발점은 0초
        dist = {start: 0}
        # prev: 그 최소 시간으로 올 때 바로 앞 교차로. 나중에 경로를 거꾸로 따라가는 데 쓴다
        prev = {start: None}
        # prev_len: 바로 앞 교차로에서 오는 도로의 길이(m). 병원까지 총 거리를 구할 때 더한다
        prev_len = {}
        # heap: (걸린 시간, 교차로) 쌍. heappop은 시간이 가장 작은 쌍을 꺼낸다
        heap = [(0, start)]
        # done: 이미 최소 시간이 확정된 교차로. 같은 교차로를 두 번 처리하지 않는다
        done = set()
        while heap:
            # 아직 처리하지 않은 교차로 중 시간이 가장 짧은 것을 꺼낸다
            d, k = heapq.heappop(heap)
            # 같은 교차로가 heap에 여러 번 들어 있을 수 있어서, 이미 확정된 것은 건너뛴다
            if k in done:
                continue
            done.add(k)
            # k에서 갈 수 있는 이웃 교차로 u를 하나씩 본다 (나가는 도로가 없으면 빈 목록)
            for u, time_s, length_m in self.__graph.get(k, []):
                # k를 거쳐 u로 가는 새 후보 시간
                nd = d + time_s
                # u를 처음 보거나 기존보다 더 빠르면 기록을 새로 쓰고 heap에 넣는다. 이것이 다익스트라의 핵심이다
                if u not in dist or nd < dist[u]:
                    dist[u] = nd
                    prev[u] = k
                    prev_len[u] = length_m
                    heapq.heappush(heap, (nd, u))
        # 결과를 객체에 저장해 둔다. sort_hospitals, make_route가 나중에 쓴다
        self.__dist, self.__prev, self.__prev_len, self.__start = dist, prev, prev_len, start
        return dist

    def sort_hospitals(self, hospitals):
        """hospitals = [(hpid:str, name:str, node_id:int, beds:int 또는 None), ...]
        반환: [(hpid, name, beds, eta_min:float, distance_m:float, node_count:int), ...]
              도착 시간 순, 병상 0 이하·None은 맨 뒤 (그 안에서도 도착 시간 순)"""
        # dijkstra를 먼저 부르지 않았으면 계산 결과가 없으므로 오류를 낸다
        if self.__start is None:
            raise ValueError("dijkstra를 먼저 불러야 합니다")
        rows = []
        for hpid, name, node_id, beds in hospitals:
            if node_id not in self.__dist:
                continue       # 갈 수 없는 병원은 목록에서 뺀다.
            # 사고 교차로에서 병원 교차로까지 지나는 교차로 순서
            route = self.make_route(node_id)
            # 초를 분으로 바꾼다
            eta_min = self.__dist[node_id] / 60
            # 첫 교차로(사고 지점)는 오는 도로가 없으므로 route[1:]부터 도로 길이를 더한다. 사고 교차로=병원 교차로면 0m
            distance_m = sum(self.__prev_len[n] for n in route[1:])
            rows.append((hpid, name, beds, eta_min, distance_m, len(route)))
        # 병상이 있으면 0, 없거나 모르면(None) 1. 이 값으로 정렬하면 병상 있는 병원이 앞에 온다
        no_bed = lambda r: 0 if (r[2] is not None and r[2] > 0) else 1
        # 1순위는 병상 유무, 2순위는 도착 시간(분) 오름차순
        rows.sort(key=lambda r: (no_bed(r), r[3]))
        return rows

    def make_route(self, hospital_node):
        """반환: [사고 교차로, ..., 병원 교차로] 순서의 교차로 번호 목록 (갈 수 없으면 [])"""
        # dist에 없다 = 도로로 닿을 수 없는 병원이므로 빈 목록을 돌려준다
        if hospital_node not in self.__dist:
            return []
        route = []
        node = hospital_node
        # prev를 따라 거슬러 올라간다. 출발점의 prev는 None이라 거기서 멈춘다
        while node is not None:
            route.append(node)
            node = self.__prev[node]
        # 병원에서 사고 지점 방향으로 모았으므로 뒤집어서 '사고 -> 병원' 순서로 만든다
        route.reverse()
        return route
