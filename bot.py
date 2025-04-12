import aiohttp
import asyncio
import os
from aiogram import Bot, Dispatcher

TOKEN = os.getenv("7478737876:AAH7CXfRuGhn8Jb1fyVUAcsGrQbTd1hK5K4")  # Витягуємо з env
CHAT_ID = os.getenv("5250184593")  # Витягуємо з env

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- Функція для отримання списку пар
async def get_symbols():
    url = "https://api.binance.com/api/v3/exchangeInfo"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            return [s['symbol'] for s in data.get('symbols', []) if s.get('status') == 'TRADING' and s.get('quoteAsset') == 'USDT']

# --- Функція для отримання змін за останні 2 години
async def get_last_2_hours_change(session, symbol):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=3"
    async with session.get(url) as resp:
        kline = await resp.json()
        if len(kline) < 3:
            return None

        prev2_close = float(kline[0][4])
        prev1_close = float(kline[1][4])
        current_close = float(kline[2][4])

        change_prev1 = ((prev1_close - prev2_close) / prev2_close) * 100
        change_current = ((current_close - prev1_close) / prev1_close) * 100

        if change_current > 1 or (change_prev1 > 1 and change_current > 1):
            return {
                "symbol": symbol,
                "prev2_close": prev2_close,
                "prev1_close": prev1_close,
                "current_close": current_close,
                "change_prev1": round(change_prev1, 2),
                "change_current": round(change_current, 2)
            }
        return None

# --- Парсимо монети
async def parse_top_coins():
    symbols = await get_symbols()
    async with aiohttp.ClientSession() as session:
        tasks = [get_last_2_hours_change(session, symbol) for symbol in symbols[:100]]
        results = await asyncio.gather(*tasks)
    return sorted([r for r in results if r], key=lambda x: x['change_current'], reverse=True)

# --- Повідомлення з ринку
async def send_price_updates():
    while True:
        coins = await parse_top_coins()

        if coins:
            response = "🔔 Топ токени з приростом:\n"
            for coin in coins[:10]:
                response += (
                    f"\n🔹 {coin['symbol']}\n"
                    f"Ціна 2 години тому: {coin['prev2_close']}\n"
                    f"Ціна 1 годину тому: {coin['prev1_close']}\n"
                    f"Поточна ціна: {coin['current_close']}\n"
                    f"Зміна за попередню годину: {coin['change_prev1']}%\n"
                    f"Зміна за поточну годину: {coin['change_current']}%\n"
                )
            await bot.send_message(CHAT_ID, response)

        await asyncio.sleep(300)  # 5 хвилин

async def send_start_message():
    await bot.send_message(CHAT_ID, "Привіт! Бот запущено ✅")

# --- Запуск
async def main():
    await send_start_message()
    asyncio.create_task(send_price_updates())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
