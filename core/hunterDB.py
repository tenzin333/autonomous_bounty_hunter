import os
import psycopg2 # Install with: pip install psycopg2-binary
from config import Config

class HunterDB:
    def __init__(self):
        # On the cloud, we pull the DB URL from environment variables
        self.db_url = Config.DATABASE_URL
        self.conn = psycopg2.connect(self.db_url)
        self.create_table()

    def create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS findings (
            id SERIAL PRIMARY KEY,
            repo TEXT,
            file TEXT,
            vuln_type TEXT,
            salt TEXT,
            commit_hash TEXT,
            pr_url TEXT,
            status TEXT DEFAULT 'Committed',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        with self.conn.cursor() as cur:
            cur.execute(query)
        self.conn.commit()