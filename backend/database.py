import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

class PostgresDriver:
    def __init__(self):
        # 1. Look for the full cloud URL first (Neon / Render)
        self.database_url = os.getenv("DATABASE_URL")

        # 2. Fallbacks for local development if DATABASE_URL is missing
        self.dbname = os.getenv("PG_DB", "sap_data")
        self.user = os.getenv("PG_USER", "postgres")
        self.password = os.getenv("PG_PASSWORD", "admin")
        self.host = os.getenv("PG_HOST", "localhost")
        self.port = os.getenv("PG_PORT", "5432")

    def get_connection(self):
        # If we have a Neon/Cloud URL, use it directly
        if self.database_url:
            return psycopg2.connect(self.database_url)
        
        # Otherwise, connect locally
        return psycopg2.connect(
            dbname=self.dbname, user=self.user, password=self.password, host=self.host, port=self.port
        )

    def test_connection(self):
        try:
            conn = self.get_connection()
            conn.close()
            print("[POSTGRES SUCCESS]: Connected to the database successfully.")
            return True
        except Exception as e:
            print(f"\n[POSTGRES ERROR]: {e}\n")
            return False

    def query(self, query_string, parameters=None):
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query_string, parameters)
            
            if query_string.strip().upper().startswith("SELECT"):
                result = cursor.fetchall()
                conn.close()
                return [dict(row) for row in result]
            else:
                conn.commit()
                conn.close()
                return []
        except Exception as e:
            print(f"SQL Error: {e}")
            return []

db = PostgresDriver()