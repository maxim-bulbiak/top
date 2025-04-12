import os
import asyncio
import aiohttp
import logging
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Завантаження .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Змінна для збереження останнього заголовка
last_title = None

# Отримання заголовку останньої новини Binance
async def fetch_latest_announcement():
    url = 'https://www.binance.com/en/support/announcement/list/161'
    headers = {'User-Agent': 'Mozilla/5.0'}  # інакше може не віддати HTML
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                html = await resp.text()
                soup = BeautifulSoup(html, 'html.parser')
                title_tag = soup.select_one("a.css-6f91y1")  # перший заголовок
                if title_tag:
                    return title_tag.text.strip()
                else:
                    logger.warning("Не вдалося знайти заголовок новини.")
                    return None
            else:
                logger.error(f"Помилка запиту: {resp.status}")
                return None

# Фоновий цикл перевірки
async def check_announcements(bot: Bot):
    global last_title
    while True:
        try:
            title = await fetch_latest_announcement()
            if title and title != last_title:
                last_title = title
                await bot.send_message(chat_id=CHAT_ID, text=f"🆕 Нова новина:\n{title}")
            else:
                logger.info("Нових новин немає.")
        except Exception as e:
            logger.error(f"Помилка у перевірці новин: {e}")
        await asyncio.sleep(300)  # Кожні 5 хв

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    latest = await fetch_latest_announcement()
    msg = f"🤖 Бот активний. Остання новина:\n{latest if latest else 'не вдалося отримати новину.'}"
    await update.message.reply_text(msg)

# Головна логіка
async def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))

    # Фоновий task
    asyncio.create_task(check_announcements(application.bot))

    logger.info("🤖 Бот запущено.")
    await application.run_polling()

# Обхід проблеми з event loop (Render, Jupyter тощо)
if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
