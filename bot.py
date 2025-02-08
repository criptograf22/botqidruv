import logging
import asyncio
import requests
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils import executor
from telethon import TelegramClient
from dotenv import load_dotenv

# .env faylni yuklash
load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
client = TelegramClient('session_name', API_ID, API_HASH)

@dp.message_handler(commands=["start", "help"])
async def send_welcome(message: Message):
    await message.reply("Salom! Guruhlarni qidirish uchun /search [kalit so‘z] kiriting.")

@dp.message_handler(commands=["search"])
async def search_groups(message: Message):
    args = message.get_args()
    if not args:
        await message.reply("Iltimos, kalit so‘z kiriting. Masalan: /search biznes")
        return
    
    search_results = await search_google(args)
    if search_results:
        filtered_results = await filter_groups_by_members(search_results)
        response = "Topilgan guruhlar:\n" + "\n".join(filtered_results) if filtered_results else "Mos keladigan guruh topilmadi."
    else:
        response = "Hech qanday guruh topilmadi."
    
    await message.reply(response)

async def search_google(query):
    url = f"https://www.googleapis.com/customsearch/v1?q={query}+Telegram+group&key={GOOGLE_API_KEY}&cx={GOOGLE_CSE_ID}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        results = response.json()
    except requests.RequestException as e:
        logging.error(f"Google qidiruvida xatolik: {e}")
        return []
    
    groups = [item.get("link", "") for item in results.get("items", []) if "t.me" in item.get("link", "")]
    return groups

async def filter_groups_by_members(group_links):
    try:
        await client.start()
        valid_groups = []
        for link in group_links:
            try:
                entity = await client.get_entity(link)
                if hasattr(entity, 'participants_count') and entity.participants_count >= 1000:
                    valid_groups.append(link)
            except Exception as e:
                logging.warning(f"Guruhni tekshirishda xatolik: {e}")
        return valid_groups
    except Exception as e:
        logging.error(f"Telethon mijozini ishga tushirishda xatolik: {e}")
        return []
    finally:
        await client.disconnect()

if __name__ == "__main__":
    try:
        executor.start_polling(dp, skip_updates=True)
    except Exception as e:
        logging.critical(f"Botni ishga tushirishda xatolik: {e}")
