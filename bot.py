import os
import asyncio
import aiohttp
import logging
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Завантажуємо змінні середовища
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальна змінна для збереження останнього заголовка
last_title = None

# Отримати останню новину з Binance
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

                # Шукаємо перший заголовок оголошення
                latest = soup.find('a', class_='css-1ej4hfo')
                if latest:
                    title = latest.get_text(strip=True)
                    return title
                else:
                    logger.warning("⚠️ Не вдалося знайти заголовок оголошення.")
                    return None
            else:
                logger.error(f"❌ Помилка HTTP: {resp.status}")
                return None

# Цикл перевірки новин
async def check_announcements(bot: Bot):
    global last_title
    while True:
        title = await fetch_latest_announcement()
        if title:
            if last_title != title:
                last_title = title
                await bot.send_message(chat_id=CHAT_ID, text=f"🆕 Нова новина:\n<b>{title}</b>", parse_mode="HTML")
            else:
                logger.info("ℹ️ Нових новин немає.")
        await asyncio.sleep(300)  # Перевірка кожні 5 хв

# /start команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = await fetch_latest_announcement()
    await update.message.reply_text(
        f"🤖 Бот активний.\n\n📢 Остання новина:\n<b>{title}</b>",
        parse_mode="HTML"
    )

# Головна функція
async def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))

    asyncio.create_task(check_announcements(application.bot))

    print("🚀 Бот запущено.")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
