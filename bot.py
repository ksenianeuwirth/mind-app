import asyncio
import logging
import os
import urllib.parse
from datetime import datetime
import pytz

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, MenuButtonWebApp
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from google import genai

# Переменные окружения считываются из настроек сервера
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")
VERCEL_URL = os.getenv("VERCEL_URL")
TIMEZONE = "Europe/Kyiv"

subscribers = set()
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler(timezone=pytz.timezone(TIMEZONE))
ai_client = genai.Client(api_key=GEMINI_KEY)

# Темы для слотов расписания
TOPICS = {
    "09:00": ("Утренний фокус", "Практика калибровки лобной доли, отказ от утреннего автопилота и техника свободных ассоциаций для правого полушария."),
    "12:00": ("Разрыв рутины", "Антидот против мыслешейкера, снятие дофаминовой усталости от соцсетей и переход в мягкую зону."),
    "15:00": ("Декомпрессия", "Техника открытого фокуса доктора Леса Феми, переход из частицы в волну и перевод мозговых ритмов в альфа-диапазон."),
    "18:00": ("Сброс автопилота", "Закон Хебба, управление привычками усталости и разотождествление с дневным стрессом."),
    "23:00": ("Ночная интеграция", "Театр сновидений, доверие подсознанию и правильный запрос перед отходом ко сну.")
}

def generate_article(slot_key: str):
    """Генерация статьи через бесплатный Gemini Flash API."""
    category, theme = TOPICS.get(slot_key, ("Перезагрузка", "Концентрация и снятие стресса"))
    prompt = (
        f"Ты — мудрый нейрокоуч и наставник. Напиши увлекательную, глубокую статью на тему: '{theme}'. "
        f"Категория выпуска: '{category}'. "
        "Стиль: захватывающий, ясный, с научными нейробиологическими метафорами, практическими выводами и пошаговой микропрактикой. "
        "Объем: около 350-450 слов (идеально для 10-15 минут вдумчивого чтения с практикой). "
        "Формат: Первая строка — яркий заголовок (без знаков решетки #). Далее — текст статьи с понятными абзацами."
    )
    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        lines = response.text.strip().split("\n")
        title = lines[0].replace("*", "").strip()
        body = "\n".join(lines[1:]).strip()
        return category, title, body
    except Exception as e:
        logging.error(f"Gemini error: {e}")
        return category, "Фокус внимания", "Сделайте три глубоких вдоха. Сосредоточьтесь на настоящем моменте."

def make_webapp_url(cat: str, title: str, body: str) -> str:
    """Кодирует статью в URL, чтобы Mini App открыл её на телефоне."""
    params = urllib.parse.urlencode({'cat': cat, 'title': title, 'text': body})
    return f"{VERCEL_URL}?{params}"

def get_keyboard(url: str, text="📖 Читать статью"):
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=text, web_app=WebAppInfo(url=url))]]
    )

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    subscribers.add(message.chat.id)
    # Кнопка слева в Telegram
    await bot.set_chat_menu_button(
        chat_id=message.chat.id,
        menu_button=MenuButtonWebApp(text="Фокус", web_app=WebAppInfo(url=VERCEL_URL))
    )
    welcome = (
        "✨ **Добро пожаловать в личный ридер!**\n\n"
        "Статьи для тренировки мозга будут приходить в 09:00, 12:00, 15:00, 18:00 и 23:00.\n\n"
        "Если чувствуете перегруз прямо сейчас — нажмите кнопку ниже вместо скроллинга соцсетей."
    )
    cat, title, body = generate_article("12:00")
    url = make_webapp_url(cat, title, body)
    await message.answer(welcome, reply_markup=get_keyboard(url, "⚡ Переключиться сейчас"), parse_mode="Markdown")

async def send_scheduled(slot_key: str):
    """Рассылка по времени."""
    if not subscribers:
        return
    cat, title, body = generate_article(slot_key)
    url = make_webapp_url(cat, title, body)
    msg_text = f"🔔 **Выпуск ({slot_key}): {title}**\n\nНовая практика готова для чтения."
    for user_id in list(subscribers):
        try:
            await bot.send_message(user_id, msg_text, reply_markup=get_keyboard(url, "📖 Открыть выпуск (~15 мин)"))
        except Exception as e:
            logging.error(f"Ошибка отправки {user_id}: {e}")

def setup_schedule():
    for slot in ["09:00", "12:00", "15:00", "18:00", "23:00"]:
        h, m = map(int, slot.split(":"))
        scheduler.add_job(send_scheduled, "cron", hour=h, minute=m, args=[slot])

async def main():
    setup_schedule()
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
