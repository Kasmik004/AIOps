import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = (
    os.getenv("DATABASE_URL")
)

with psycopg.connect(DATABASE_URL) as conn:
    print("Connected to Neon!")

    with conn.cursor() as cur:
        cur.execute("SELECT * FROM aiops;")
        rows = cur.fetchall()
        for row in rows:
            print(row)
