import sqlite3

class DatabaseManager:
    def __init__(self, db_name="mentor.db"):
        self.db_name = db_name
        self._create_tables()

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_name)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        self.conn.close()

    def _create_tables(self):
        with self as cursor:
            # جدول تاریخچه چت
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                                                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                            user_id INTEGER,
                                                            role TEXT,
                                                            content TEXT,
                                                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # جدول جدید برای ذخیره نمرات و مباحث تمرین‌شده
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    topic TEXT,
                    score INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def add_message(self, user_id: int, role: str, content: str):
        with self as cursor:
            cursor.execute(
                "INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)",
                (user_id, role, content)
            )

    def get_history(self, user_id: int, limit: int = 10):
        with self as cursor:
            cursor.execute(
                "SELECT role, content FROM chat_history WHERE user_id = ? ORDER BY id DESC LIMIT ?",
                (user_id, limit)
            )
            rows = cursor.fetchall()
            return list(reversed(rows))

    def add_score(self, user_id: int, topic: str, score: int):
        with self as cursor:
            cursor.execute(
                "INSERT INTO progress (user_id, topic, score) VALUES (?, ?, ?)",
                (user_id, topic.strip(), score)
            )

    def get_progress(self, user_id: int):
        with self as cursor:
            cursor.execute(
                "SELECT topic, score, date(timestamp) as date FROM progress WHERE user_id = ? ORDER BY id ASC",
                (user_id,)
            )
            return cursor.fetchall()