import psycopg2
from psycopg2 import OperationalError

passwords = ["password", "postgres", "admin", "123456", ""]
for pwd in passwords:
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password=pwd,
            host="localhost",
            port="5432"
        )
        print(f"SUCCESS: Password is '{pwd}'")
        conn.close()
        break
    except OperationalError as e:
        print(f"FAILED: '{pwd}' - {e}")
