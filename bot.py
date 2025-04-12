import os
import aiohttp
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- Отримання перших 10 пар з Binance (з USDT)
async def get_first_10_symbols():
    url = "https://api.binance.com/api/v3/exchangeInfo"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            all_symbols = [
                s['symbol'] for s in data.get('symbols', [])
                if s.get('status') == 'TRADING' and s.get('quoteAsset') == 'USDT'
            ]
            return all_symbols[:10]

# --- Отримання ціни для пари
async def get_price(session, symbol):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    async with session.get(url) as resp:
        data = await resp.json()
        return data.get('symbol'), data.get('price')

# --- Команда /prices
@dp.message(Command("prices"))
async def handle_prices_command(message: types.Message):
    await message.answer("📡 Отримую ціни для 10 пар...")
    symbols = await get_first_10_symbols()

    async with aiohttp.ClientSession() as session:
        tasks = [get_price(session, symbol) for symbol in symbols]
        prices = await asyncio.gather(*tasks)

    response = "💱 Поточні ціни:\n"
    for symbol, price in prices:
        response += f"• {symbol}: {price}\n"

    await message.answer(response)

# --- Повідомлення при старті
async def send_start_message():
    await bot.send_message(CHAT_ID, "🤖 Бот запущено. Команда /prices — покаже ціни 10 пар.")

# --- Головна функція
async def main():
    await send_start_message()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
