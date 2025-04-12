import os
import asyncio
import aiohttp
import logging
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

# Парсинг HTML вручну або через BeautifulSoup (це заглушка, потрібно замінити)
async def fetch_latest_announcement():
    url = 'https://www.binance.com/en/support/announcement/list/161'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                html = await resp.text()
                # TODO: Замінити цю заглушку на справжній парсинг заголовку
                title = "Приклад заголовка"
                return title
            else:
                logger.error(f"Помилка: {resp.status}")
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

# Обробник команди /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот працює. Очікую на нові оголошення 🔍")

# Основна функція
async def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))

    # Запуск фону
    asyncio.create_task(check_announcements(application.bot))

    print("🚀 Бот запущено.")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
