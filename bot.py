import aiohttp
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command

TOKEN = '7478737876:AAH7CXfRuGhn8Jb1fyVUAcsGrQbTd1hK5K4'
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- Функція для отримання списку пар
async def get_symbols():
    url = "https://api.binance.com/api/v3/exchangeInfo"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            return [s['symbol'] for s in data['symbols'] if s['status'] == 'TRADING' and s['quoteAsset'] == 'USDT']

# --- Функція для отримання змін за годину
async def get_last_hour_change(session, symbol):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=2"
    async with session.get(url) as resp:
        kline = await resp.json()
        if len(kline) < 2:
            return None
        prev_close = float(kline[0][4])
        current_close = float(kline[1][4])
        change_percent = ((current_close - prev_close) / prev_close) * 100
        if change_percent > 3:
            return {
                "symbol": symbol,
                "prev_close": prev_close,
                "current_close": current_close,
                "change_1h": round(change_percent, 2)
            }
        return None

# --- Функція яка парсить всі монети
async def parse_top_coins():
    symbols = await get_symbols()
    async with aiohttp.ClientSession() as session:
        tasks = [get_last_hour_change(session, symbol) for symbol in symbols[:900]]
        results = await asyncio.gather(*tasks)
    filtered = [r for r in results if r]
    filtered = sorted(filtered, key=lambda x: x['change_1h'], reverse=True)
    return filtered

# --- ТУТ вставляєш твій обробник команди /top
@dp.message(Command("top"))
async def handle_top_command(message: Message):
    await message.answer("Збираю дані... будь ласка зачекай ⏳")
    coins = await parse_top_coins()

    if not coins:
        await message.answer("Жоден токен не виріс більше ніж на 1% за останню годину.")
        return

    response = "Топ токени з приростом за останню годину:\n"
    for coin in coins[:10]:  # Топ 10
        response += (
            f"\n🔹 {coin['symbol']}\n"
            f"Ціна закриття минулої години: {coin['prev_close']}\n"
            f"Ціна закриття поточної години: {coin['current_close']}\n"
            f"Зміна за 1h: {coin['change_1h']}%\n"
        )

    await message.answer(response)

@dp.message()
async def get_chat_id(message: Message):
    await message.answer(f"Ваш chat_id: {message.chat.id}")


# --- Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
