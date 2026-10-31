import sqlite3


class DatabaseManager:
    def __init__(self, db_name="mentor.db"):
        self.db_name = db_name
        # به محض ساخته شدن شیء، مطمئن می‌شویم جدول وجود دارد
        self.create_tables()

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_name)
        # این خط باعث می‌شود خروجی دیتابیس شبیه دیکشنری شود (دسترسی با نام ستون)
        self.conn.row_factory = sqlite3.Row
        return self.conn.cursor()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            print(f"خطایی رخ داد! تغییرات لغو شد: {exc_val}")
            self.conn.rollback()
        else:
            self.conn.commit()
        self.conn.close()

    def create_tables(self):
        with self as cursor:
            cursor.execute("""
                           CREATE TABLE IF NOT EXISTS chat_history
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               user_id
                               INTEGER
                               NOT
                               NULL,
                               role
                               TEXT
                               NOT
                               NULL,
                               content
                               TEXT
                               NOT
                               NULL,
                               created_at
                               TIMESTAMP
                               DEFAULT
                               CURRENT_TIMESTAMP
                           )
                           """)

    def add_message(self, user_id: int, role: str, content: str):
        # ذخیره پیام جدید با استفاده از ? برای جلوگیری از SQL Injection
        with self as cursor:
            cursor.execute(
                "INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)",
                (user_id, role, content)
            )

    def get_history(self, user_id: int, limit: int = 10):
        # خواندن آخرین پیام‌های یک کاربر خاص
        with self as cursor:
            cursor.execute(
                "SELECT role, content FROM chat_history WHERE user_id = ? ORDER BY id DESC LIMIT ?",
                (user_id, limit)
            )
            rows = cursor.fetchall()
            # برگرداندن لیست به ترتیب زمانی (از قدیمی به جدید)
            return list(reversed(rows))


# تست کردن ذخیره و خواندن اطلاعات
if __name__ == "__main__":
    db = DatabaseManager()

    # ۲. خواندن پیام‌ها از دیتابیس و چاپ کردنشان
    history = db.get_history(user_id=12345)
    for msg in history:
        print(f"[{msg['role']}]: {msg['content']}")