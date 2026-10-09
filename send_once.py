import os
import urllib.parse
from datetime import datetime
import pytz
import requests
from google import genai

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")
VERCEL_URL = os.getenv("VERCEL_URL")

# Вставьте сюда ваш ID (и позже ID мамы и дочки через запятую):
CHAT_IDS = [
    8206790033,  # <-- ЗАМЕНИТЕ НА ВАШИ ЦИФРЫ ИЗ @userinfobot
]

TOPICS = {
    "09": ("Утренний фокус", "Калибровка внимания, включение активного режима, отказ от автопилота текущего кадра и запуск внутреннего стартера 'Сделать сейчас же'."),
    "12": ("Разрыв рутины", "Антидот против мыслешейкера и скроллинга: метод декомпозиции 'лестница для фрисби' и список ключей разгрузки от застревания."),
    "15": ("Декомпрессия", "Техника открытого фокуса: снятие ментальной перегрузки, перевод внимания из частицы в волну и альфа-ритм."),
    "18": ("Сброс автопилота", "Закон Хебба и техника 'взмаха': перепрошивка привычных реакций усталости и прерывание стрессового сценария."),
    "23": ("Ночная интеграция", "Театр сновидений: передача задач подсознанию, техника растворения ментального диалога и погружение в глубокий покой.")
}

def get_current_slot():
    tz = pytz.timezone("Europe/Kyiv")
    hour = datetime.now(tz).strftime("%H")
    return TOPICS.get(hour, ("Перезагрузка", "Концентрация внимания, выход из ментальных ловушек и ясность ума"))

def main():
    if not CHAT_IDS or CHAT_IDS[0] == 123456789:
        print("Ошибка: укажите ваш реальный Telegram Chat ID в списке CHAT_IDS!")
        return

    category, theme = get_current_slot()
    ai_client = genai.Client(api_key=GEMINI_KEY)
    
    prompt = (
        f"Ты — глубокий нейрокоуч и наставник по системному мышлению. "
        f"Напиши практическую, захватывающую статью на тему: '{theme}'. "
        f"Категория выпуска: '{category}'. "
        "Опирайся на проверенные техники: управление вниманием и намерением, латеральное мышление, разгрузку оперативной памяти, работу с подсознанием и нейропластичность. "
        "Стиль: живой, образный, без воды, с научными метафорами и четкой микропрактикой в конце. "
        "Объем: 350-450 слов (на 10-15 минут вдумчивого чтения с упражнением). "
        "Формат: Первая строка — цепляющий заголовок (без знаков # и звездочек). Далее — структурированный текст с абзацами."
    )
    
    res = ai_client.models.generate_content(model='gemini-3.8-flash', contents=prompt)
    lines = res.text.strip().split("\n")
    title = lines[0].replace("*", "").strip()
    body = "\n".join(lines[1:]).strip()

    params = urllib.parse.urlencode({'cat': category, 'title': title, 'text': body})
    app_url = f"{VERCEL_URL}?{params}"

    text_msg = f"🔔 *Время перезагрузки ({category})*\n\n*{title}*\n\nНовый 15-минутный выпуск готов для чтения."
    keyboard = {
        "inline_keyboard": [[{"text": "📖 Открыть выпуск (~15 мин)", "web_app": {"url": app_url}}]]
    }

    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text_msg,
            "parse_mode": "Markdown",
            "reply_markup": keyboard
        }
        try:
            requests.post(url, json=payload, timeout=10)
        except Exception as e:
            print(f"Ошибка отправки пользователю {chat_id}: {e}")

if __name__ == "__main__":
    main()
