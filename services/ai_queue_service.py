import asyncio
import discord
import logging
from services.ai_service import ask_ai

# Hàng đợi (Queue) để chứa các yêu cầu xử lý AI
# Mỗi item trong queue sẽ là một tuple: (câu hỏi, tin nhắn gốc để trả lời)
_queue = asyncio.Queue()

def get_queue_size():
    """Lấy số lượng yêu cầu đang chờ trong hàng đợi."""
    return _queue.qsize()

async def add_to_queue(question: str, message: discord.Message):
    """
    Thêm một yêu cầu mới vào hàng đợi và gửi tin nhắn xác nhận cho người dùng.
    """
    # Thông báo cho người dùng rằng yêu cầu đã được tiếp nhận
    queue_position = get_queue_size() + 1
    await message.reply(f"Đã nhận được câu hỏi của mày. Mày là người thứ {queue_position} trong hàng chờ.")
    
    # Đưa yêu cầu vào hàng đợi
    await _queue.put((question, message))

async def ai_worker():
    """
    "Nhân viên" chạy nền, liên tục kiểm tra và xử lý các yêu cầu từ hàng đợi.
    """
    logging.info("AI Worker đã được khởi động và sẵn sàng xử lý yêu cầu.")
    while True:
        # Lấy một yêu cầu từ hàng đợi. Dòng này sẽ tạm dừng cho đến khi có yêu cầu mới.
        question, message = await _queue.get()
        
        logging.info(f"Đang xử lý yêu cầu từ '{message.author}'. Hàng chờ còn lại: {get_queue_size()}")
        
        try:
            # Báo hiệu bot đang "suy nghĩ"
            async with message.channel.typing():
                # Gọi hàm xử lý AI thực sự
                ai_response = await ask_ai(question)
                # Trả lời tin nhắn gốc
                await message.reply(ai_response)
        except Exception as e:
            logging.error(f"Lỗi khi xử lý yêu cầu AI từ hàng đợi: {e}")
            await message.reply("Lỗi rồi, tao xử lý câu hỏi của mày không được.")
        finally:
            # Đánh dấu là đã xử lý xong yêu cầu này
            _queue.task_done()