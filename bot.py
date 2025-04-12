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

# --- Отримання пар з Binance
async def get_symbols():
    url = "https://api.binance.com/api/v3/exchangeInfo"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            return [s['symbol'] for s in data.get('symbols', []) if s.get('status') == 'TRADING' and s.get('quoteAsset') == 'USDT']

# --- Зміни за 2 години
async def get_last_2_hours_change(session, symbol):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=3"
    try:
        async with session.get(url) as resp:
            kline = await resp.json()
            if len(kline) < 3:
                return None
            prev2 = float(kline[0][4])
            prev1 = float(kline[1][4])
            current = float(kline[2][4])

            change1 = ((prev1 - prev2) / prev2) * 100
            change2 = ((current - prev1) / prev1) * 100

            if change2 > 1 or (change1 > 1 and change2 > 1):
                print(f"[DEBUG] {symbol} пройшов фільтр: {change1:.2f}% → {change2:.2f}%")
                return {
                    "symbol": symbol,
                    "prev2": prev2,
                    "prev1": prev1,
                    "current": current,
                    "change1": round(change1, 2),
                    "change2": round(change2, 2)
                }
            else:
                print(f"[DEBUG] {symbol} не пройшов фільтр: {change1:.2f}% → {change2:.2f}%")
    except Exception as e:
        print(f"[ERROR] Не вдалося обробити {symbol}: {e}")
    return None

# --- Парсинг топ монет
async def parse_top_coins():
    symbols = await get_symbols()
    async with aiohttp.ClientSession() as session:
        tasks = [get_last_2_hours_change(session, symbol) for symbol in symbols[:900]]
        results = await asyncio.gather(*tasks)
    return sorted([r for r in results if r], key=lambda x: x['change2'], reverse=True)
    


# --- Команда /top
@dp.message(Command("top"))
async def handle_top_command(message: types.Message):
    await message.answer("⏳ Збираю дані...")
    coins = await parse_top_coins()
    if not coins:
        await message.answer("Нічого не знайдено 😕")
        return

    response = "🔝 Топ токени з приростом:\n"
    for coin in coins[:10]:
        response += (
            f"\n🔹 {coin['symbol']}\n"
            f"2 год тому: {coin['prev2']}\n"
            f"1 год тому: {coin['prev1']}\n"
            f"Зараз: {coin['current']}\n"
            f"Зміна за годину: {coin['change1']}%\n"
            f"Зміна зараз: {coin['change2']}%\n"
        )
    await message.answer(response)

# --- Повідомлення при старті
async def send_start_message():
    await bot.send_message(CHAT_ID, "🤖 Бот запущено та слухає команди!")

# --- Головна функція
async def main():
    await send_start_message()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
