import os
import psycopg
from dotenv import load_dotenv

from tests.db import DATABASE_URL

load_dotenv()


class Store:
    def __init__(self):
        DATABASE_URL = os.getenv("DATABASE_URL")

        if not DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is not set.")
        self.conn = psycopg.connect(DATABASE_URL)
        self.conn.autocommit = True  # Enable autocommit mode

    def execute_query(self, query, params=None):
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            if cur.description:  # Check if the query returns rows
                return cur.fetchall()
            return None

    def insert_data(self, data):
        query = """
            INSERT INTO aiops ()
        """

    def close(self):
        self.conn.close()
