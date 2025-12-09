import asyncio
import aiohttp
import logging

async def self_ping_task():
    url = "https://anh-nghai-discord-bot.onrender.com"
    logging.info(f"Đã kích hoạt chế độ tự ping mỗi 5 phút vào: {url}")
    while True:
        await asyncio.sleep(300)  # 5 phút
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        logging.info("Tự ping thành công (Bot vẫn sống)")
                    else:
                        logging.warning(f"⚠️ Tự ping thất bại: {resp.status}")
        except aiohttp.ClientError as e:
            logging.error(f"❌ Lỗi tự ping: {e}")
            await asyncio.sleep(60)