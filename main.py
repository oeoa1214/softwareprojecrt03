"""main - 프로그램 시작 흐름 (계획서 3.4.2 핵심 프로세스 흐름도 60쪽, README 4.1). 오은찬 담당."""
# csv: 아래 except에서 csv.Error를 잡으려고 가져온다
import csv
# sys: sys.exit(1)로 프로그램을 오류 종료할 때 쓴다
import sys
# time: 시작 준비에 몇 초 걸렸는지 잰다 (기준 5초 이내)
import time

# 아래 import들은 모두 우리 프로젝트의 클래스 파일이다. main.py가 이들을 만들어 서로 연결한다
from repository import Repository
from road_api import RoadApi
from hospital_api import HospitalApi
from crossroad import Crossroad
from shortest_road import ShortestRoad
from hospital_search import HospitalSearch
from save import Save
from past_route_manager import PastRouteManager

# 계획서 2.6 EX 표 문구 그대로
MSG_HOSPITAL_FAIL = "병원 API 호출 실패했습니다. 가상 데이터로 실행됩니다."        # EX-01
MSG_SPEED_FAIL = "도로 API 호출 실패했습니다. 가상 데이터로 실행됩니다."           # EX-02
MSG_ROAD_FAIL = "표준노드링크 파일 읽기 실패했습니다. 가상 데이터로 실행됩니다"     # EX-03
# 흐름도의 「안내 후 종료」 문구 (계획서 EX 표에 없어서 새로 정함, D-8)
MSG_NO_ROAD = "도로 정보를 불러올 수 없어 프로그램을 종료합니다."
MSG_NO_HOSPITAL = "병원 정보를 불러올 수 없어 프로그램을 종료합니다."


def attach_nodes(rows, crossroad):
    """병원마다 가장 가까운 교차로 번호(node_id)를 붙인다 (흐름도 4 「가장 가까운 교차로 연결」).
    find_crossroad를 그대로 쓴다: 대구 밖(-1)이거나 300m 안에 교차로가 없으면(-2) None → 경로 계산에서 빠진다.
    (11/18 확인: 실제 병원 25곳 모두 189m 안이라 전부 연결된다)"""
    result = []
    # 병원은 지도에는 진짜 위치로 두고, 경로 계산용으로만 가장 가까운 교차로 번호를 붙인다
    for hpid, name, lat, lon, node_id, addr, tel, beds in rows:
        # 사고 지점 찾기에 쓰는 같은 메소드를 병원 위치에도 쓴다
        node = crossroad.find_crossroad(lat, lon)
        # -1(대구 밖) 또는 -2(300m 밖)이면 None으로 두어 경로 계산에서 뺀다
        result.append((hpid, name, lat, lon, None if node in (-1, -2) else node, addr, tel, beds))
    return result


def prepare(repo, road_api, hospital_api):
    """흐름도 2~6번: 데이터를 준비하고 화면이 쓸 객체를 만든다.
    반환: (parts, messages)
      parts = 화면이 쓸 객체 묶음(dict), 종료해야 하면 None
      messages = 화면에 차례대로 띄울 안내 문구 목록"""
    # 화면에 띄울 안내 문구를 순서대로 모은다 (지금은 print, 2주차에 Message 창으로 바꾼다)
    messages = []

    # 2. 도로망 CSV를 읽는다. 못 읽으면 RoadApi가 더미 CSV를 읽는다 (EX-03). 더미도 없으면 안내 후 종료
    try:
        # RoadApi.load_node_link: (교차로, 도로, 더미 여부)를 돌려받는다
        nodes, links, road_dummy = road_api.load_node_link()
    except (OSError, ValueError, KeyError, csv.Error):
        return None, [MSG_NO_ROAD]
    if road_dummy:
        messages.append(MSG_ROAD_FAIL)

    # 3. DB에 도로망이 없으면 넣는다 (있으면 save_road가 건너뛴다)
    # DB에 도로망을 저장한다. 이미 있으면 건너뛰므로 매번 켜도 중복 저장되지 않는다
    repo.save_road(nodes, links)
    # DB의 교차로 전체(번호, 위도, 경도)로 Crossroad를 만든다
    crossroad = Crossroad(repo.get_crossroad_points())

    # 4. 병원 API → 실패하면 ① DB에 저장된 병원 ② 더미 병원 파일 ③ 둘 다 없으면 안내 후 종료 (D-8)
    # 병원 API를 부른다. 실패하면 hospital_dummy가 True가 된다
    rows, hospital_dummy = hospital_api.load_hospitals()
    if not hospital_dummy:
        repo.save_hospitals(attach_nodes(rows, crossroad))
    else:
        messages.append(MSG_HOSPITAL_FAIL)
        if repo.get_hospitals():
            pass                                                   # 지난번에 저장한 병원을 쓴다
        elif rows:
            repo.save_hospitals(attach_nodes(rows, crossroad))     # 더미 병원을 저장해서 쓴다
        else:
            messages.append(MSG_NO_HOSPITAL)
            return None, messages

    # 5. 속도 API → 성공하면 저장, 실패하면 저장된 속도 (그것도 없으면 ShortestRoad가 제한 속도를 쓴다)
    # 도로 속도 API를 부른다. 성공하면 DB에 저장한다 (같은 시각 속도를 또 저장하면 키 중복 오류가 나는 알려진 문제가 이 아래 save_speeds에 있다)
    speeds, collected_at, speed_dummy = road_api.load_speeds()
    if speed_dummy:
        messages.append(MSG_SPEED_FAIL)
    else:
        repo.save_speeds(speeds, collected_at)

    # 6. 그래프를 만들고 가중치(통행 시간)를 계산한다
    # DB에서 꺼낸 도로 목록과 가장 최근 속도로 그래프를 만든다. 속도가 없는 도로는 ShortestRoad가 제한 속도를 쓴다
    road = ShortestRoad(repo.get_links(), repo.get_latest_speeds())

    # 2주차 화면(Ui)이 쓸 객체들을 사전 하나로 묶어 넘긴다
    parts = {
        "repo": repo,
        "crossroad": crossroad,                    # FR-01 사고 지점 → 교차로
        "road": road,                              # FR-01 · 02 다익스트라, 병원 정렬, 경로
        "hospital_search": HospitalSearch(repo),   # FR-05
        "save": Save(repo),                        # FR-03
        "past_route": PastRouteManager(repo),      # FR-04
    }
    return parts, messages


def main():
    # 시작 시각을 기록한다
    start = time.time()
    # 1. 프로그램 시작: traffic.db를 열고 테이블 7개를 만든다 (이미 있으면 그대로 둔다)
    repo = Repository("traffic.db")
    parts, messages = prepare(repo, RoadApi(), HospitalApi())

    # 안내 문구 (2주차에 Message 창으로 바꾼다)
    for message in messages:
        print("[안내]", message)
    if parts is None:
        repo.close()
        # 종료 번호 1 = 오류로 끝났다는 뜻
        sys.exit(1)

    print(f"시작 준비 완료: {time.time() - start:.1f}초 (기준 5초 이내)")
    print("병원", len(repo.get_hospitals()), "곳 / 경로 계산에 들어가는 병원",
          len(repo.get_hospitals_for_sort()), "곳 / 도로 속도", len(repo.get_latest_speeds()), "개")

    # 7. 지도 표시: 2주차에 StartUi → Ui를 띄우고 parts를 넘긴다
    repo.close()


# 이 파일을 직접 실행(py main.py)할 때만 main()이 돌아간다. 다른 파일이 import할 때는 돌지 않는다
if __name__ == "__main__":
    main()