"""Crossroad - 클릭 위치에서 300m 이내 가장 가까운 교차로 찾기 (AD-04)."""
#🌙 객체 생성->cell호출->튜플을 키로하고 리스트를 값으로 하는 딕셔너리 생성
#🌙 파인드 크로스 로드(사용자가 클릭시 호출)->cell()호출,in_daugu()호출,_distance()호출
#🌙 객체 내부 저장 데이터 self_grid,
# json: 대구 경계선 파일(.json)을 읽을 때 쓴다
import json
# math: 하버사인 거리 계산에 sin, cos, asin, sqrt, radians를 쓴다
import math
# os: 이 파일(crossroad.py)이 있는 폴더를 찾아 data 폴더 경로를 만든다
import os

# 대구 경계선 파일 (행정동 142개의 바깥선, 군위군 제외). crossroad.py 옆 data 폴더에 있다.
#⭐바운드리 패스: 현재 파일의 위치를 기준으로 대구 경계선 JSON파일의 경로를 생성한다.
BOUNDARY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "daegu_boundary.json")


class Crossroad:
#⭐격자의 가로와 세로를 300m보다 크게 설정한 이유: 현재 격자와 인접한 8개 격자만 조사해도 300m 이내의 교차로를 빠뜨리지 않도록 하기 위해서 
    # 사고 지점에서 교차로까지 허용하는 최대 거리(미터). 딱 300m까지는 정상
#⭐ LIMIT_M:	사고 지점에서 교차로까지 허용하는 최대 거리
    LIMIT_M = 300
    # 그리드 칸 크기(도). 한 변이 300m보다 커야 주변 9칸만 봐도 빠짐이 없다
#⭐CELL_LAT: 격자 한 칸의 세로 길이	위도 0.0028도 (약 311m)
#⭐CELL_LON:	격자 한 칸의 가로 길이	경도 0.0034도 (약 307m)
    CELL_LAT = 0.0028   # 위도 0.0028도 = 약 311m
    CELL_LON = 0.0034   # 경도 0.0034도 = 대구에서 약 307m
#⭐ 생성자 역할: 전체 교차로를 격자별로 분류하여 딕셔너리에 저장하는 것
    def __init__(self, nodes, boundary_path=BOUNDARY_PATH):
        """nodes = [(node_id:int, lat:float, lon:float), ...]  
        boundary_path = 대구 경계선 파일. 안 넣으면 data/daegu_boundary.json"""
#⭐nodes: DB에서 가져온 전체 교차로 데이터의 목록
        self.__nodes = nodes
        #그리드: 교차로마다 칸 키를 계산해 같은 칸끼리 한 목록에 넣는다 (시작할 때 한 번)
#⭐self.__grid: 그리드 딕셔너리이름(튜플을 Key로 하고, 리스트를 Value로 하는 딕셔너리)      
        self.__grid = {}
        #🌠모든 교차로를 하나씩 가져와서 _cell()함수를 호출
        for node_id, n_lat, n_lon in nodes:
        #🌠 딕셔너리의 키  
            key = self.__cell(n_lat, n_lon)
#⭐setdefault: key가 없으면 기본값을 추가한다.  key가 있으면 아무일도 하지 않는다.    
#       #🌠 
            self.__grid.setdefault(key, []).append((node_id, n_lat, n_lon))
        # 대구 범위: 행정동 경계선 (계획서 EX-04 · EX-05 기준)
        #🌠생성자에서 대구 경계선인 rings를 jason에서 가져온다.
        #🌠self.변수명으로 대입하면 멤버 변수
        with open(boundary_path, encoding="utf-8") as f:
            self.__rings = json.load(f)["rings"]   # [[[lat, lon], ...], ...] 경계선 142개
#⭐lat: 사용자가 지도에서 클릭한 사고 지점의 위도
#⭐lon: 사용자가 지도에서 클릭한 사고 지점의 경도
    def find_crossroad(self, lat, lon):
        """반환: 300m 이내 가장 가까운 교차로 번호(int) / 대구 밖 -1 / 300m 초과 -2"""
        # 1단계: 대구 경계선 밖이면 거리를 잴 필요 없이 바로 -1 (EX-04). 대구 판정을 먼저 한다
         #🌠만약 반환값이 Fasls면 실행한다.
        if not self.__in_daegu(lat, lon):
            return -1
        # 2단계: 모든 교차로와의 거리를 하나씩 재서 가장 가까운 교차로를 기억한다 (AD-04)
#⭐ 베스트디스트: 클릭한 지점에서 부터 현재 까지 찾은 가장 가까운 교차로
#⭐ 베스트아이디: 클릭한 지점에서 부터 현재 까지 찾은 가장 가까운 교차로의 아이디
        best_id, best_dist = None, None
        row, col = self.__cell(lat, lon)
          #🌠dr에 -1, 0, 1을 순서대로 대입하면서 총 3번 반복
        for dr in (-1, 0, 1):                   # 위 · 같은 줄 · 아래
            for dc in (-1, 0, 1):               # 왼쪽 · 같은 칸 · 오른쪽
                for node_id, n_lat, n_lon in self.__grid.get((row + dr, col + dc), []):
          #🌠indague에서 distance를 호출해서 두 지점 중에 짧은 걸 찾아서 대입한다. 
          #🌠만약에 best_dist가 존재하지 않거나 best_dist보다 d가 작다면 갱신한다.               
                    d = self.__distance(lat, lon, n_lat, n_lon)
                    if best_dist is None or d < best_dist:
                        best_id, best_dist = node_id, d
       
        if best_dist is None:                   # 9칸에 교차로가 하나도 없으면 300m 초과
            return -2
        # 300m 딱 맞으면 정상 (부동소수점 오차 방지를 위해 소수 6자리까지만 비교)
        # 3단계: 300m 이하면 그 교차로 번호, 넘으면 -2 (EX-05). round는 300.0000001 같은 계산 오차를 막는다
        if round(best_dist, 6) <= self.LIMIT_M:
            return best_id
        return -2
#⭐위도와 경도를 각각 0.0028도와 0.0034도로 나눈다
    def __cell(self, lat, lon):
        """좌표가 들어가는 칸 키 (행, 열). 칸 크기로 나눈 몫"""
        #🌈(3,4)이런식으로 나옴 (3,4)가 딕셔너리의 key
        return (int(lat // self.CELL_LAT), int(lon // self.CELL_LON))
       
#🪐 레이 캐스팅(Ray Casting) 알고리즘
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
#🪐 하버사인 공식 사고 지점과 교차로 사이의 거리를 계산하는 함수
        #🌠하버사인의 공식 제1형  # a = sin²(두지점의 위도차이/2) + cos(사고지점위도) × cos(교차로의 위도) × sin²(두지점의 경도차이/2)
        #🌠하버사인의 공식 제2형  # d = 2 × r × asin(√a)
    def __distance(self, lat1, lon1, lat2, lon2):
         #🌠파인드 크로스로드에서 호출됨
        """반환: 두 지점 거리(미터, float) - 하버사인 공식, 지구 반지름 6371000"""
#⭐ dp = 두 지점의 위도 차이 (라디안)
#⭐ dl = 두 지점의 경도 차이 (라디안)
#⭐ p1 = 사고 지점의 위도 (라디안)
#⭐ p2 = 교차로의 위도 (라디안)
#⭐ r = 지구 반지름 (6371000m)
#⭐ a = 하버사인 공식 제1형
#⭐ d = 두점 사이의 거리 (하버사인 공식 제2형)
        # 지구 반지름(m)
        r = 6371000
        #🌠각도를 라디안으로 변환
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dp = p2 - p1
        dl = math.radians(lon2 - lon1)
        # 하버사인 공식: 지구 표면 위 두 점 사이 거리를 위도·경도 차이로 구한다
        a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
        # 호의 길이 = 2 x 반지름 x asin(sqrt(a)). 단위는 미터
        return 2 * r * math.asin(math.sqrt(a))