from repository import Repository


def main():
    # 1. DB 준비: traffic.db를 열고 테이블 7개를 만든다 (이미 있으면 그대로 둔다)
    repo = Repository("traffic.db")
    print("DB 준비 완료:", repo.table_names())

    # 2. 병원 · 도로 데이터 받아 저장 (HospitalApi, RoadApi 만든 뒤 추가)
    # 3. 시작 화면 띄움 (StartUi 받은 뒤 추가)

    repo.close()


if __name__ == "__main__":
    main()