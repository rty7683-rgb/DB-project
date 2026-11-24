"""Oracle 접속/테이블 조회 시연용 (재작성)."""
from db_config import connect

with connect() as con, con.cursor() as cur:
    print("Oracle 접속 성공:", con.version)
    cur.execute("SELECT USER, SYS_CONTEXT('USERENV', 'SERVICE_NAME') FROM dual")
    print("사용자 / 서비스:", cur.fetchone())
    cur.execute("SELECT table_name FROM user_tables ORDER BY table_name")
    print("테이블 목록:")
    for row in cur:
        print(row[0])
