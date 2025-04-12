import asyncio
import aiohttp
import logging
from telegram import Bot
from telegram.ext import Application, CommandHandler

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ваш токен бота та ID чату
BOT_TOKEN = 'YOUR_BOT_TOKEN'
CHAT_ID = 'YOUR_CHAT_ID'

# URL сторінки оголошень Binance
BINANCE_ANNOUNCEMENTS_URL = 'https://www.binance.com/en/support/announcement/list/161'

# Зберігаємо останній заголовок для перевірки нових оголошень
last_title = None

async def fetch_latest_announcement():
    async with aiohttp.ClientSession() as session:
        async with session.get(BINANCE_ANNOUNCEMENTS_URL) as response:
            if response.status == 200:
                text = await response.text()
                # Тут потрібно реалізувати парсинг HTML, щоб витягти заголовок останнього оголошення
                # Наприклад, використовуючи регулярні вирази або бібліотеку BeautifulSoup
                # Для прикладу, припустимо, що ми отримали заголовок:
                latest_title = "Приклад заголовка"
                return latest_title
            else:
                logger.error(f"Помилка при отриманні сторінки: {response.status}")
                return None

async def check_for_new_announcement(bot):
    global last_title
    while True:
        latest_title = await fetch_latest_announcement()
        if latest_title and latest_title != last_title:
            last_title = latest_title
            await bot.send_message(chat_id=CHAT_ID, text=f"Нове оголошення: {latest_title}")
        await asyncio.sleep(300)  # Перевірка кожні 5 хвилин

async def start(update, context):
    await update.message.reply_text('Бот запущено!')

async def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))

    # Запуск задачі перевірки нових оголошень
    asyncio.create_task(check_for_new_announcement(application.bot))

    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
