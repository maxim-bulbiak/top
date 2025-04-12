import aiohttp
import asyncio
import os

from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.webhook.fastapi import WebhookRequestHandler

API_TOKEN = os.getenv("BOT_TOKEN", "7478737876:AAH7CXfRuGhn8Jb1fyVUAcsGrQbTd1hK5K4")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://your-app-name.onrender.com/webhook")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
app = FastAPI()

# --- Binance парсинг
async def get_symbols():
    url = "https://api.binance.com/api/v3/exchangeInfo"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            return [s['symbol'] for s in data['symbols'] if s['status'] == 'TRADING' and s['quoteAsset'] == 'USDT']

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

async def parse_top_coins():
    symbols = await get_symbols()
    async with aiohttp.ClientSession() as session:
        tasks = [get_last_hour_change(session, symbol) for symbol in symbols[:900]]
        results = await asyncio.gather(*tasks)
    filtered = [r for r in results if r]
    filtered = sorted(filtered, key=lambda x: x['change_1h'], reverse=True)
    return filtered

# --- Обробники
@dp.message(Command("top"))
async def handle_top_command(message: Message):
    await message.answer("Збираю дані... будь ласка зачекай ⏳")
    coins = await parse_top_coins()

    if not coins:
        await message.answer("Жоден токен не виріс більше ніж на 1% за останню годину.")
        return

    response = "Топ токени з приростом за останню годину:\n"
    for coin in coins[:10]:
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

# --- FastAPI маршрути
@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)
    print(f"Webhook set to {WEBHOOK_URL}")

@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook()

# Обробка запитів Telegram → FastAPI → Dispatcher
app.post("/webhook")(WebhookRequestHandler(dp, bot).handle)
