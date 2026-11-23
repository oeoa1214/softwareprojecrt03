"""Save - 선택한 병원까지의 경로를 저장한다 (오은찬 담당, FR-03)."""


class Save:
    def __init__(self, repo):
        """repo = main에서 만든 Repository (DB 연결을 같이 쓴다)"""
        self.__repo = repo

    def save_route(self, acc_lat, acc_lon, acc_node_id, results, selected_hpid, route_nodes):
        """경로 저장 버튼을 누르면 사고 지점과 선택한 병원 경로를 저장한다 (FR-03 시퀀스 2~11).
        acc_lat, acc_lon = 클릭한 사고 위치 / acc_node_id = 사고 교차로 번호
        results = ShortestRoad.sort_hospitals 결과 [(hpid, name, beds, eta_min, distance_m, node_count), ...]
                  (맨 앞이 추천 병원)
        selected_hpid = 심볼을 눌러 선택한 병원 번호, 선택 안 했으면 None
        route_nodes = ShortestRoad.make_route 결과 [사고 교차로, ..., 병원 교차로]
        반환: 저장한 결과 번호(route_id, 1 이상) → 「경로가 저장되었습니다.」
              -1 병원을 선택하지 않음 → 「병원을 먼저 선택해주세요.」 (EX-11)
              -2 DB 저장 실패 → 「경로 저장이 실패했습니다.」 (EX-12)"""
        selected = None
        # 추천 목록(results)에서 사용자가 고른 병원(selected_hpid)의 줄을 찾는다
        for row in results:
            if row[0] == selected_hpid:
                selected = row
                break
        # 병원을 안 골랐거나 목록에 없는 번호이면 -1 (EX-11)
        if selected is None:
            return -1
        # sort_hospitals 결과 한 줄을 변수 6개로 풀어 쓴다 (튜플 언패킹)
        hpid, name, beds, eta_min, distance_m, node_count = selected
        is_recommended = (results[0][0] == hpid)      # 맨 앞(추천) 병원을 골랐는지
        # DB에는 사고 지점, 경로 결과, 지나는 교차로 표 3개가 한 번에 저장된다 (Repository가 처리)
        route_id = self.__repo.save_route(acc_lat, acc_lon, acc_node_id, hpid, eta_min, distance_m,
                                          node_count, beds, is_recommended, route_nodes)
        # Repository는 저장에 실패하면 None을 준다. 이때 -2 (EX-12)
        if route_id is None:
            return -2
        return route_id