"""시연용 공통 접속 설정. 비밀번호를 Git에 저장하지 않는다."""
import os
from getpass import getpass
import oracledb

def connect():
    user = os.environ.get("ORACLE_USER", "AIRPORT")
    dsn = os.environ.get("ORACLE_DSN", "localhost:1521/FREEPDB1")
    password = os.environ.get("ORACLE_PASSWORD") or getpass("Oracle password: ")
    return oracledb.connect(user=user, password=password, dsn=dsn)
