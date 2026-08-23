import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = (
    os.getenv("DATABASE_URL")
    or "postgresql://neondb_owner:npg_XvLrKc3TyRf7@ep-noisy-math-azvrgb2d.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"
)

with psycopg.connect(DATABASE_URL) as conn:
    print("Connected to Neon!")

    with conn.cursor() as cur:
        cur.execute("SELECT * FROM aiops;")
        rows = cur.fetchall()
        for row in rows:
            print(row)
