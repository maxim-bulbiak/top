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

# --- Запасні символи, якщо Binance API не працює
FALLBACK_SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "SOLUSDT", "DOGEUSDT", "DOTUSDT", "MATICUSDT", "LTCUSDT"]

# --- Отримання перших 10 пар з Binance (з USDT)
async def get_first_10_symbols():
    print("🔍 Отримую список USDT-пар з Binance...")
    url = "https://api.binance.com/api/v3/exchangeInfo"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                print("🔢 Код відповіді Binance:", resp.status)
                if resp.status != 200:
                    print("❌ Binance API повернуло помилку. Використовую запасні пари.")
                    return FALLBACK_SYMBOLS
                data = await resp.json()
                symbols = [
                    s['symbol'] for s in data.get('symbols', [])
                    if s.get('status') == 'TRADING' and s.get('quoteAsset') == 'USDT'
                ]
                if not symbols:
                    print("⚠️ Отримано 0 пар. Використовую запасні.")
                    return FALLBACK_SYMBOLS
                print(f"✅ Отримано {len(symbols)} пар. Перші 10: {symbols[:10]}")
                return symbols[:10]
    except Exception as e:
        print(f"❗ Виняток при зверненні до Binance: {e}")
        return FALLBACK_SYMBOLS

# --- Отримання ціни для пари
async def get_price(session, symbol):
    print(f"📈 Отримую ціну для: {symbol}")
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    try:
        async with session.get(url) as resp:
            if resp.status != 200:
                print(f"⚠️ Не вдалося отримати ціну для {symbol}, код: {resp.status}")
                return symbol, "N/A"
            data = await resp.json()
            price = data.get('price', "N/A")
            print(f"→ {symbol}: {price}")
            return symbol, price
    except Exception as e:
        print(f"❗ Помилка для {symbol}: {e}")
        return symbol, "N/A"

# --- Команда /prices
@dp.message(Command("prices"))
async def handle_prices_command(message: types.Message):
    print(f"📬 Отримано команду /prices від {message.from_user.username}")
    await message.answer("📡 Отримую ціни для 10 пар...")

    symbols = await get_first_10_symbols()

    async with aiohttp.ClientSession() as session:
        tasks = [get_price(session, symbol) for symbol in symbols]
        prices = await asyncio.gather(*tasks)

    response = "💱 Поточні ціни:\n"
    for symbol, price in prices:
        response += f"• {symbol}: {price}\n"

    print("📤 Відправляю повідомлення з цінами")
    await message.answer(response)

# --- Повідомлення при старті
async def send_start_message():
    print("🚀 Бот запущено!")
    await bot.send_message(CHAT_ID, "🤖 Бот запущено. Команда /prices — покаже ціни 10 пар.")

# --- Головна функція
async def main():
    print("🟢 Запускаємо головну подію...")
    await send_start_message()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
