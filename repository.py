from datetime import datetime

# duckdb: 파일 하나(traffic.db)에 표(테이블)를 저장하는 DB. SQL 문장으로 저장·조회한다
import duckdb


class Repository:
    """traffic.db에 테이블을 만들고 저장 · 조회 · 삭제를 맡는다 (계획서 3.3.4).
    번호(node_id, link_id)는 클래스 밖에서 int, DB 안에서 Varchar다. 바꾸는 일은 여기서만 한다."""


 #객체를 만들때마다 db 파일을 열고 테이블을 만든다.
 #init 뜻: 생성자
 #db_path 뜻: DB파일 이름을 받는 변수, 아무값도 안넣고 부르면 traffic.db를 쓴다.
 # self 뜻 = 객체 자신
    def __init__(self, db_path="traffic.db"):
        # DB 파일에 연결한다. 파일이 없으면 새로 만든다
        self.__con = duckdb.connect(db_path)
        self.create_tables()

#테이블 생성 함수
    def create_tables(self):
#sqls뜻 create_tables에서 만든 변수 이름
        sqls = [
            # 사고 번호 · 결과 번호를 1, 2, 3 ... 으로 자동으로 매기는 번호표
            "CREATE SEQUENCE IF NOT EXISTS accident_seq START 1",
            "CREATE SEQUENCE IF NOT EXISTS route_seq START 1",

            """CREATE TABLE IF NOT EXISTS node (
                node_id    VARCHAR PRIMARY KEY,
                node_name  VARCHAR,
                lat        DOUBLE,
                lon        DOUBLE
            )""",

            """CREATE TABLE IF NOT EXISTS link (
                link_id    VARCHAR PRIMARY KEY,
                f_node_id  VARCHAR REFERENCES node(node_id),
                t_node_id  VARCHAR REFERENCES node(node_id),
                length_m   DOUBLE,
                max_spd    INTEGER
            )""",

            """CREATE TABLE IF NOT EXISTS link_speed (
                link_id      VARCHAR REFERENCES link(link_id),
                collected_at TIMESTAMP,
                speed_kmh    DOUBLE,
                PRIMARY KEY (link_id, collected_at)
            )""",

            """CREATE TABLE IF NOT EXISTS hospital (
                hpid     VARCHAR PRIMARY KEY,
                name     VARCHAR,
                lat      DOUBLE,
                lon      DOUBLE,
                node_id  VARCHAR REFERENCES node(node_id),
                addr     VARCHAR,
                tel      VARCHAR,
                beds     INTEGER
            )""",

            """CREATE TABLE IF NOT EXISTS accident_point (
                accident_id  INTEGER DEFAULT nextval('accident_seq') PRIMARY KEY,
                lat          DOUBLE,
                lon          DOUBLE,
                created_at   TIMESTAMP,
                node_id      VARCHAR REFERENCES node(node_id)
            )""",

            """CREATE TABLE IF NOT EXISTS route_result (
                route_id        INTEGER DEFAULT nextval('route_seq') PRIMARY KEY,
                calculated_at   TIMESTAMP,
                eta_minutes     DOUBLE,
                distance_m      DOUBLE,
                node_count      INTEGER,
                is_recommended  BOOLEAN,
                accident_id     INTEGER REFERENCES accident_point(accident_id),
                hospital_hpid   VARCHAR REFERENCES hospital(hpid),
                is_selected     BOOLEAN,
                beds            INTEGER
            )""",

            """CREATE TABLE IF NOT EXISTS route_node (
                route_id  INTEGER REFERENCES route_result(route_id),
                seq       INTEGER,
                node_id   VARCHAR REFERENCES node(node_id),
                PRIMARY KEY (route_id, seq)
            )""",
        ]
    #sql 뜻 sql문장하나를 담는 변수   
        for sql in sqls:
            self.__con.execute(sql)
    #con.execute 뜻: duckdb 라이브러리의 SQL실행 메소드


    def table_names(self):
        """만들어진 테이블 이름 목록 (테스트용)"""
    #fetchall: select결과 모두 꺼내기
        rows = self.__con.execute("SHOW TABLES").fetchall()
        return [r[0] for r in rows]

    # ------------------------------------------------------------------ 1단계: 교차로 · 도로


    def has_road(self):
        """node 테이블에 행이 있으면 True (시작 흐름도 3: DB에 도로망이 있다)"""
        count = self.__con.execute("SELECT COUNT(*) FROM node").fetchone()[0]
        return count > 0
    
    def save_road(self, nodes, links):
        """교차로와 도로 구간을 한 번에 저장한다.
        nodes = [(node_id:int, node_name, lat, lon), ...]               (RoadApi.load_node_link의 nodes)
        links = [(link_id:int, f_node_id:int, t_node_id:int, length_m, max_spd), ...]
        반환: 저장했으면 True, 이미 도로망이 있어서 건너뛰었으면 False 


        //「프로그램을 켤 때마다 데이터를 저장하되, 이미 DB에 있는 교차로·도로는 다시 넣지 않고, 병원은 병상 수만 바꾼다.」
        중간에 오류가 나면 둘 다 저장하지 않고(ROLLBACK) 오류를 그대로 올린다."""
        # 이미 도로망이 들어 있으면 다시 넣지 않는다 (교차로 2만 8천 개를 매번 넣으면 느리고 중복 오류가 난다)
        if self.has_road():
            return False
        # 코드 안에서는 번호가 int, DB 안에서는 글자(Varchar)로 저장하므로 여기서 str()로 바꾼다
        node_rows = [(str(n[0]), n[1], float(n[2]), float(n[3])) for n in nodes]
        link_rows = [(str(l[0]), str(l[1]), str(l[2]), float(l[3]),
                      None if l[4] is None else int(l[4])) for l in links]
        # begin ~ commit: 여러 저장을 '전부 성공 아니면 전부 취소'로 묶는다 (트랜잭션)
        self.__con.begin()
        try:
            # 외래키 때문에 node를 먼저, link를 나중에 넣는다
            self.__insert_many("node", ["node_id", "node_name", "lat", "lon"], node_rows)
            self.__insert_many("link", ["link_id", "f_node_id", "t_node_id", "length_m", "max_spd"], link_rows)
            self.__con.commit()
        except Exception:
            # 중간에 오류가 나면 이미 넣은 것까지 되돌린다
            self.__con.rollback()
            raise
        return True

    def get_nodes(self):
        """반환: [(node_id:int, node_name, lat, lon), ...]  테이블 칸 순서"""
        rows = self.__con.execute("SELECT node_id, node_name, lat, lon FROM node").fetchall()
        return [(int(r[0]), r[1], r[2], r[3]) for r in rows]

    def get_crossroad_points(self):
        """반환: [(node_id:int, lat, lon), ...]  Crossroad(nodes)에 그대로 넘긴다 (결정 D-1a)"""
        rows = self.__con.execute("SELECT node_id, lat, lon FROM node").fetchall()
        return [(int(r[0]), r[1], r[2]) for r in rows]

    def get_links(self):
        """반환: [(link_id:int, f_node_id:int, t_node_id:int, length_m, max_spd), ...]
        ShortestRoad(links, speeds)의 links에 그대로 넘긴다"""
        rows = self.__con.execute(
            "SELECT link_id, f_node_id, t_node_id, length_m, max_spd FROM link").fetchall()
        return [(int(r[0]), int(r[1]), int(r[2]), r[3], r[4]) for r in rows]

    # ------------------------------------------------------------------ 도로 속도 (link_speed)
    def save_speeds(self, speeds, collected_at):
        """도로 속도를 저장한다 (시작 흐름도 5: 속도 저장).
        speeds = [(link_id:int, speed_kmh), ...]   같은 번호는 한 번만 (평균은 RoadApi가 미리 낸다)
        collected_at = 속도를 잰 시간 (datetime)
        link 테이블에 있는 번호만 저장한다 (없는 번호는 외래키 오류가 나므로 뺀다).
        반환: 저장한 개수"""
        # link 표에 있는 도로 번호만 저장한다. 없는 번호를 넣으면 외래키(REFERENCES) 오류가 난다 (속도 API에는 우리 link.csv에 없는 번호 82개가 있다)
        known = {r[0] for r in self.__con.execute("SELECT link_id FROM link").fetchall()}
        rows = [(str(link_id), collected_at, float(speed))
                for link_id, speed in speeds if str(link_id) in known]
        self.__con.begin()
        try:
            self.__insert_many("link_speed", ["link_id", "collected_at", "speed_kmh"], rows)
            self.__con.commit()
        except Exception:
            self.__con.rollback()
            raise
        return len(rows)

    def get_latest_speeds(self):
        """반환: [(link_id:int, speed_kmh), ...]  가장 최근에 잰 속도만 (FR-01 15)
        ShortestRoad(links, speeds)의 speeds에 그대로 넘긴다"""
        rows = self.__con.execute(
            """SELECT link_id, speed_kmh FROM link_speed
               WHERE collected_at = (SELECT MAX(collected_at) FROM link_speed)""").fetchall()
        return [(int(r[0]), r[1]) for r in rows]

    # ------------------------------------------------------------------ 병원 (hospital)
    def save_hospitals(self, rows):
        """병원을 저장한다 (시작 흐름도 4: 근처 병원 저장).
        rows = [(hpid, name, lat, lon, node_id:int 또는 None, addr, tel, beds), ...]  테이블 칸 순서
        처음 보는 병원은 새로 넣고, 이미 있는 병원은 병상 수(beds)만 바꾼다."""
        self.__con.begin()
        try:
            for hpid, name, lat, lon, node_id, addr, tel, beds in rows:
                node = None if node_id is None else str(node_id)
                # 이미 있는 병원인지 먼저 센다
                exists = self.__con.execute(
                    "SELECT COUNT(*) FROM hospital WHERE hpid = ?", [hpid]).fetchone()[0]
                # 있으면 병상 수만 갱신(UPDATE), 없으면 새로 추가(INSERT). 병원 정보는 거의 안 바뀌고 병상 수만 계속 바뀌기 때문이다
                if exists:
                    self.__con.execute("UPDATE hospital SET beds = ? WHERE hpid = ?", [beds, hpid])
                else:
                    self.__con.execute(
                        "INSERT INTO hospital VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        [hpid, name, lat, lon, node, addr, tel, beds])
            self.__con.commit()
        except Exception:
            self.__con.rollback()
            raise

    def get_hospitals(self):
        """반환: [(hpid, name, lat, lon, node_id:int 또는 None, addr, tel, beds), ...]  테이블 칸 순서"""
        rows = self.__con.execute(
            "SELECT hpid, name, lat, lon, node_id, addr, tel, beds FROM hospital").fetchall()
        return [self.__hospital_row(r) for r in rows]

    def get_hospitals_for_sort(self):
        """반환: [(hpid, name, node_id:int, beds), ...]  ShortestRoad.sort_hospitals에 그대로 넘긴다 (FR-01 15)
        가까운 교차로가 없는(node_id가 비어 있는) 병원은 뺀다."""
        rows = self.__con.execute(
            "SELECT hpid, name, node_id, beds FROM hospital WHERE node_id IS NOT NULL").fetchall()
        return [(r[0], r[1], int(r[2]), r[3]) for r in rows]

    def get_hospital(self, hpid):
        """선택한 병원 한 곳 (FR-02 3~6). 반환: 병원 한 줄 (get_hospitals와 같은 모양) 또는 None"""
        row = self.__con.execute(
            "SELECT hpid, name, lat, lon, node_id, addr, tel, beds FROM hospital WHERE hpid = ?",
            [hpid]).fetchone()
        return None if row is None else self.__hospital_row(row)

    def find_hospital_by_name(self, name):
        """이름이 정확히 같은 병원 (FR-05 3~6). 반환: 병원 한 줄 또는 None"""
        row = self.__con.execute(
            "SELECT hpid, name, lat, lon, node_id, addr, tel, beds FROM hospital WHERE name = ?",
            [name]).fetchone()
        return None if row is None else self.__hospital_row(row)

    # ------------------------------------------------------------------ 경로 (accident_point · route_result · route_node)
    def save_route(self, acc_lat, acc_lon, acc_node_id, hpid, eta_minutes, distance_m,
                   node_count, beds, is_recommended, route_nodes, saved_at=None):
        """사고 지점, 병원까지의 결과, 지나는 교차로를 한 번에 저장한다 (FR-03 3~10).
        acc_lat, acc_lon = 클릭한 위치 / acc_node_id = 사고 교차로 번호(int)
        hpid ~ beds = 선택한 병원의 결과 / is_recommended = 추천 여부
        route_nodes = [사고 교차로, ..., 병원 교차로] 교차로 번호(int) 목록 (make_route 결과)
        saved_at = 저장 시각 (안 넣으면 지금)
        반환: 저장한 결과 번호(route_id) / 실패하면 None (그때는 아무것도 남기지 않는다)"""
        saved_at = saved_at or datetime.now()
        self.__con.begin()
        try:
            # RETURNING: 방금 넣은 줄의 자동 번호(accident_id)를 바로 돌려받는다. 다음 표에 연결할 때 쓴다
            accident_id = self.__con.execute(
                """INSERT INTO accident_point (lat, lon, created_at, node_id)
                   VALUES (?, ?, ?, ?) RETURNING accident_id""",
                [acc_lat, acc_lon, saved_at, str(acc_node_id)]).fetchone()[0]
            route_id = self.__con.execute(
                """INSERT INTO route_result (calculated_at, eta_minutes, distance_m, node_count,
                                             is_recommended, accident_id, hospital_hpid, is_selected, beds)
                   VALUES (?, ?, ?, ?, ?, ?, ?, TRUE, ?) RETURNING route_id""",
                [saved_at, eta_minutes, distance_m, node_count,
                 is_recommended, accident_id, hpid, beds]).fetchone()[0]
            # 경로의 교차로를 순서(seq 1, 2, 3 ...)와 함께 한 줄씩 저장한다. 순서를 저장해야 나중에 경로를 그대로 다시 그릴 수 있다
            for seq, node_id in enumerate(route_nodes, start=1):
                self.__con.execute("INSERT INTO route_node VALUES (?, ?, ?)",
                                   [route_id, seq, str(node_id)])
            self.__con.commit()
            return route_id
        except Exception:
            self.__con.rollback()
            return None

    def search_routes(self, route_id=None, hospital_name=None, date=None):
        """저장된 경로를 찾는다 (FR-04 7~10). 넣은 조건만 쓰고, 아무것도 안 넣으면 전체.
        route_id = 식별 번호(int) / hospital_name = 병원 명 / date = "2026-11-09" 형식 글자
        반환: [(route_id, calculated_at, hospital_name, beds, eta_minutes, distance_m, node_count), ...]
        입력이 맞는 형식인지는 확인하지 않는다 (PastRouteManager가 한다)."""
        # 세 표(route_result, accident_point, hospital)를 JOIN으로 이어 병원 이름까지 한 번에 가져온다. WHERE 1 = 1은 아래에서 AND 조건을 편하게 이어 붙이려는 관용구다
        sql = """SELECT r.route_id, r.calculated_at, h.name, r.beds,
                        r.eta_minutes, r.distance_m, r.node_count
                 FROM route_result r
                 JOIN accident_point a ON r.accident_id = a.accident_id
                 JOIN hospital h ON r.hospital_hpid = h.hpid
                 WHERE 1 = 1"""
        params = []
        # 값이 들어온 조건만 WHERE에 붙인다. ?는 값이 들어갈 자리이고, 이렇게 하면 SQL 주입을 막는다
        if route_id is not None:
            sql += " AND r.route_id = ?"
            params.append(route_id)
        if hospital_name is not None:
            sql += " AND h.name = ?"
            params.append(hospital_name)
        if date is not None:
            sql += " AND CAST(r.calculated_at AS DATE) = CAST(? AS DATE)"
            params.append(date)
        # 식별 번호 순서로 정렬한다
        sql += " ORDER BY r.route_id"
        return self.__con.execute(sql, params).fetchall()

    def delete_route(self, route_id):
        """저장된 경로 하나를 지운다 (FR-04 16~19).
        참조하는 쪽부터 route_node → route_result → accident_point 순서로 지운다.
        반환: 지웠으면 True, 그 번호가 없거나 실패하면 False"""
        row = self.__con.execute(
            "SELECT accident_id FROM route_result WHERE route_id = ?", [route_id]).fetchone()
        if row is None:
            return False
        accident_id = row[0]
        try:
            # 한 단계씩 확정하면서 지운다 (앞 단계가 끝나야 다음 테이블의 참조가 사라진다)
            # 다른 표가 참조하는 쪽(route_node)부터 지워야 외래키 오류가 나지 않는다
            self.__con.execute("DELETE FROM route_node WHERE route_id = ?", [route_id])
            self.__con.execute("DELETE FROM route_result WHERE route_id = ?", [route_id])
            self.__con.execute("DELETE FROM accident_point WHERE accident_id = ?", [accident_id])
        except Exception:
            return False
        return True

    # ------------------------------------------------------------------ 공통
    def __hospital_row(self, r):
        """DB에서 꺼낸 병원 한 줄의 node_id를 int로 바꾼다"""
        return (r[0], r[1], r[2], r[3], None if r[4] is None else int(r[4]), r[5], r[6], r[7])

    def __insert_many(self, table, columns, rows):
        """행이 많아도 빨리 넣는다. pandas가 있으면 표째로 한 번에, 없으면 한 줄씩."""
        if not rows:
            return
        cols = ", ".join(columns)
        try:
            # pandas가 있으면 표 형태로 한 번에 넣어 훨씬 빠르다 (교차로 2만 8천 개). 없으면 아래처럼 한 줄씩 넣는다
            import pandas as pd
        except ImportError:
            marks = ", ".join(["?"] * len(columns))
            self.__con.executemany(f"INSERT INTO {table} ({cols}) VALUES ({marks})", rows)
            return
        frame = pd.DataFrame(rows, columns=columns)
        # pandas 표를 DB가 임시 표(tmp_rows)로 볼 수 있게 등록한다
        self.__con.register("tmp_rows", frame)
        try:
            self.__con.execute(f"INSERT INTO {table} ({cols}) SELECT {cols} FROM tmp_rows")
        finally:
            self.__con.unregister("tmp_rows")

    def close(self):
        self.__con.close()