import os
import asyncio
import aiohttp
import logging
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Завантаження змінних середовища
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальна змінна для збереження останнього заголовка
last_title = None

# Функція отримання останнього оголошення з Binance
async def fetch_latest_announcement():
    url = 'https://www.binance.com/en/support/announcement/list/161'
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                html = await resp.text()
                soup = BeautifulSoup(html, 'lxml')
                items = soup.select('a.css-1ej4hfo')  # це CSS клас оголошень
                if items:
                    return items[0].get_text(strip=True)
            logger.error(f"Помилка під час запиту Binance: {resp.status}")
            return None

# Цикл перевірки новин
async def check_announcements(bot: Bot):
    global last_title
    while True:
        title = await fetch_latest_announcement()
        if title and title != last_title:
            last_title = title
            await bot.send_message(chat_id=CHAT_ID, text=f"🆕 Нове оголошення:\n{title}")
        await asyncio.sleep(300)  # Перевірка кожні 5 хв

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current = await fetch_latest_announcement()
    await update.message.reply_text(
        f"👋 Бот працює!\nОстаннє оголошення Binance:\n\n📰 {current if current else 'Не вдалося отримати'}"
    )

# Головна функція
async def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))

    # Фонове завдання
    asyncio.create_task(check_announcements(application.bot))

    logger.info("🤖 Бот запущено.")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
