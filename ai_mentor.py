import os
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types
from database import DatabaseManager

load_dotenv()

SYSTEM_PROMPT = """
تو یک منتور، همکار ارشد و معلم دلسوز مهندسی نرم‌افزار (پایتون، OOP، SQL، لینوکس و Git) هستی.
دانشجوی تو در بوت‌کمپ مکتب شریف است و می‌خواهد تا ۳ ماه دیگر آماده بازار کار شود.

قانون تو برای آموزش هر مبحث این ۳ مرحله است (هر بار فقط یک مرحله را جلو ببر و منتظر پاسخ دانشجو بمان):
۱. آموزش و پرسش: مبحث درخواستی را به زبان ساده و با مثال کاربردی توضیح بده. در انتهای پیام، دقیقا ۳ سوال مفهومی کوتاه بپرس تا مطمئن شوی مطلب را گرفته است.
۲. بررسی و تعریف تسک: پاسخ دانشجو به ۳ سوال را بررسی کن. اگر اشتباهی داشت اصلاح کن و سپس ۱ تسک کدنویسی عملی مرتبط با همان مبحث به او بده.
۳. ریویو کد و نمره‌دهی (Code Review): کدی که دانشجو می‌فرستد را بررسی کن. اگر باگ اساسی داشت راهنمایی کن تا اصلاح کند. اما به محض اینکه کد قابل قبول بود، به او از ۱۰۰ نمره بده و در خط آخر پیامت دقیقا با همین فرمت انگلیسی بنویس:
[SCORE: 95 | TOPIC: نام مبحث]
(مثال: [SCORE: 90 | TOPIC: Python Context Managers])
"""


class AIMentor:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("کلید GEMINI_API_KEY در فایل .env پیدا نشد!")

        self.client = genai.Client(api_key=api_key)
        self.db = DatabaseManager()
        self.models = [
            "gemini-3.5-flash",
            "gemini-3.1-flash-lite",
            "gemini-3.6-flash",
            "gemini-3.7-flash",
            "gemini-3.8-flash",
        ]

    def ask(self, user_id: int, user_message: str) -> str:
        history_rows = self.db.get_history(user_id, limit=10)

        contents = []
        for row in history_rows:
            role = "user" if row["role"] == "user" else "model"
            contents.append(
                types.Content(role=role, parts=[types.Part.from_text(text=row["content"])])
            )

        contents.append(
            types.Content(role="user", parts=[types.Part.from_text(text=user_message)])
        )

        last_error = None
        reply_text = None

        for model_name in self.models:
            try:
                print(f"در حال امتحان کردن مدل {model_name}...")
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.4,
                    )
                )
                reply_text = response.text
                print(f"پاسخ با موفقیت از مدل {model_name} دریافت شد!")
                break
            except Exception as e:
                print(f"مدل {model_name} در دسترس نبود: {e}")
                last_error = e

        if reply_text is None:
            raise last_error

        self.db.add_message(user_id, "user", user_message)
        self.db.add_message(user_id, "model", reply_text)

        # شکار خودکار نمره و مبحث از داخل متن پاسخ هوش مصنوعی با Regex
        match = re.search(r"\[SCORE:\s*(\d+)\s*\|\s*TOPIC:\s*(.+?)\]", reply_text)
        if match:
            score = int(match.group(1))
            topic = match.group(2)
            self.db.add_score(user_id, topic, score)
            reply_text += f"\n\n✅ نمره {score} برای مبحث «{topic}» در کارنامه‌ات ثبت شد!"

        return reply_text