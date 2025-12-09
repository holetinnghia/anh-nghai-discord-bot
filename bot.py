import os
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv
from utils.keep_alive import keep_alive

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

cookie_content = os.getenv('YOUTUBE_COOKIES')

if cookie_content:
    # Nếu có, tạo file cookies.txt từ nội dung đó
    with open('cookies.txt', 'w') as f:
        f.write(cookie_content)
    print("Đã tạo file cookies.txt từ biến môi trường thành công!")
else:
    print("Không tìm thấy biến YOUTUBE_COOKIES, bot sẽ chạy không cần cookies (có thể lỗi).")

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
if not DISCORD_TOKEN:
    logging.error("LỖI: Thiếu DISCORD_TOKEN! Hãy kiểm tra lại file .env.")
    exit()

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    logging.info(f"Đã tải thành công: {filename}")
                except Exception as e:
                    logging.error(f"Lỗi khi tải {filename}: {e}")

        await self.tree.sync()
        logging.info("Cây lệnh đã được đồng bộ.")

if __name__ == "__main__":
    bot = MyBot()
    keep_alive()
    bot.run(DISCORD_TOKEN)