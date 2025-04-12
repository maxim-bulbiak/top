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
    print("🔍 Отримую список USDT-пар з Binance...")
    url = "https://api.binance.com/api/v3/exchangeInfo"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                print(f"📡 Binance API статус: {resp.status}")
                if resp.status != 200:
                    print("❌ Не вдалося отримати exchangeInfo")
                    return []

                data = await resp.json()
                all_symbols = [
                    s['symbol'] for s in data.get('symbols', [])
                    if s.get('status') == 'TRADING' and s.get('quoteAsset') == 'USDT'
                ]
                first_10 = all_symbols[:10]
                print(f"✅ Знайдено {len(first_10)} пар: {first_10}")
                return first_10
        except Exception as e:
            print(f"🚨 Помилка при запиті exchangeInfo: {e}")
            return []

# --- Отримання ціни для пари
async def get_price(session, symbol):
    print(f"📈 Отримую ціну для: {symbol}")
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    try:
        async with session.get(url) as resp:
            print(f"🔄 Статус відповіді для {symbol}: {resp.status}")
            if resp.status != 200:
                print(f"⚠️ Пропускаю {symbol}, помилка статусу")
                return symbol, "N/A"
            data = await resp.json()
            price = data.get('price')
            print(f"→ {symbol}: {price}")
            return data.get('symbol'), price
    except Exception as e:
        print(f"❌ Помилка при отриманні ціни для {symbol}: {e}")
        return symbol, "Error"


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
    await send_start_message()
    await dp.start_polling(bot)

if __name__ == "__main__":
    print("🟢 Запускаємо головну подію...")
    asyncio.run(main())
