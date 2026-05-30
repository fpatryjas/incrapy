import sqlite3
import os
from scraper.config import database

class DatabaseManager:
    def __init__(self):
        os.makedirs(os.path.dirname(database), exist_ok=True)
        self.conn = sqlite3.connect(database)
        self.cursor = self.conn.cursor()
        self._init_tables()

    def _init_tables(self):
        tables = ["must_read", "off_topic", "inceldom"]
        schema = '''(
            title TEXT, thread_id INT, latest_activity TEXT, user_id INT, user_name TEXT,
            user_title TEXT, rank TEXT, n_stars INT, date TEXT, n_posts INT,
            time_online TEXT, datetime DATE, n_post INT, message TEXT,
            quote_host TEXT, quote_url TEXT, quoted_user TEXT, qu_id TEXT
        )'''
        
        for table in tables:
            self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {table} {schema}")
        self.conn.commit()

    def insert_post(self, table_name, data_tuple):
        query = f"INSERT INTO {table_name} VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
        try:
            self.cursor.execute(query, data_tuple)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"SQL error when inserting: {table_name}: {e}")

    def close(self):
        self.conn.close()