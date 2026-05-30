import sqlite3
import os
from scraper.config import database, known_subforums

class DatabaseManager:
    def __init__(self):
        os.makedirs(os.path.dirname(database), exist_ok=True)
        self.conn = sqlite3.connect(database)
        self.cursor = self.conn.cursor()
        self._init_tables()

    def _init_tables(self):
        schema = '''(
            title TEXT, thread_id INT, latest_activity TEXT, user_id INT, user_name TEXT,
            user_title TEXT, rank TEXT, n_stars INT, date TEXT, n_posts INT,
            time_online TEXT, datetime DATE, n_post INT, message TEXT,
            quote_host TEXT, quote_url TEXT, quoted_user TEXT, qu_id TEXT,
            UNIQUE(thread_id, n_post)
        )'''

        for table in known_subforums:
            self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {table} {schema}")
            self.cursor.execute(
                f"CREATE UNIQUE INDEX IF NOT EXISTS idx_{table}_unique "
                f"ON {table}(thread_id, n_post)"
            )

        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS progress "
            "(url TEXT PRIMARY KEY, scraped_at TEXT NOT NULL)"
        )
        self.conn.commit()

    def mark_scraped(self, url):
        self.cursor.execute(
            "INSERT OR IGNORE INTO progress(url, scraped_at) VALUES(?, datetime('now'))",
            (url,),
        )

    def get_scraped_urls(self):
        self.cursor.execute("SELECT url FROM progress")
        return {row[0] for row in self.cursor.fetchall()}

    def insert_post(self, table_name, data_tuple):
        if table_name not in known_subforums:
            raise ValueError(f"Unknown table: {table_name!r}")
        query = f"INSERT OR IGNORE INTO {table_name} VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
        try:
            self.cursor.execute(query, data_tuple)
        except sqlite3.Error as e:
            print(f"SQL error when inserting into {table_name}: {e}")

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()
