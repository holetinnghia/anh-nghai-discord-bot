import asyncio
import discord
import logging
from services.ai_service import ask_ai

_queue = asyncio.Queue()

def get_queue_size():
    return _queue.qsize()

async def add_to_queue(question: str, message: discord.Message):
    queue_position = get_queue_size() + 1
    await message.reply(f"Đã nhận được câu hỏi của mày. Mày là người thứ {queue_position} trong hàng chờ.")
    
    await _queue.put((question, message))

async def ai_worker():
    logging.info("AI Worker đã được khởi động và sẵn sàng xử lý yêu cầu.")
    while True:
        question, message = await _queue.get()
        
        logging.info(f"Đang xử lý yêu cầu từ '{message.author}'. Hàng chờ còn lại: {get_queue_size()}")
        
        try:
            async with message.channel.typing():
                ai_response = await ask_ai(question)
                await message.reply(ai_response)
        except Exception as e:
            logging.error(f"Lỗi khi xử lý yêu cầu AI từ hàng đợi: {e}")
            await message.reply("Lỗi rồi, tao xử lý câu hỏi của mày không được.")
        finally:
            _queue.task_done()