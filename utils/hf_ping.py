import asyncio
import aiohttp
import logging

async def hf_ping_task():
    url = "https://holetinnghia-anh-nghai-ai-api.hf.space"
    logging.info(f"Đã kích hoạt chế độ ping Hugging Face mỗi 8 tiếng vào: {url}")

    await asyncio.sleep(10)

    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(url) as resp:
                    if resp.status == 200:
                        logging.info("Ping Hugging Face AI thành công (Dịch vụ AI vẫn sống)")
                    else:
                        logging.warning(f"⚠️ Ping Hugging Face AI thất bại: {resp.status}")
        except aiohttp.ClientError as e:
            logging.error(f"❌ Lỗi khi ping Hugging Face AI: {e}")
        
        await asyncio.sleep(28800)