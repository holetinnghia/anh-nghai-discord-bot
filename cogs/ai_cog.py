import discord
from discord.ext import commands
from services.ai_service import ask_ai
from services.ai_lock_service import is_ai_busy, get_ai_lock

class AICog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # FIX CƠ CH BẢN: Dùng ID check để đảm bảo không bị lỗi object reference
        if message.author.id == self.bot.user.id:
            return

        if self.bot.user.mentioned_in(message):
            # ... (Phần Concurrency và Logic gọi AI giữ nguyên)
            if is_ai_busy():
                await message.reply("Tao đang bận trả lời đứa khác. Hỏi sau đi.")
                return

            question = message.content.replace(f'<@!{self.bot.user.id}>', '').replace(f'<@{self.bot.user.id}>', '').strip()

            if question:
                ai_lock = get_ai_lock()
                async with ai_lock:
                    async with message.channel.typing():
                        ai_response = await ask_ai(question)
                        
                        # --- THÊM BƯỚC KIỂM TRA ---
                        # Nếu AI trả về rỗng hoặc chỉ có khoảng trắng, gửi tin nhắn dự phòng
                        if not ai_response or not ai_response.strip():
                            await message.reply("Tao không nghĩ ra được câu trả lời. Hỏi câu khác đi.")
                        else:
                            # Nếu có nội dung, gửi câu trả lời của AI
                            # ... code xử lý AI ở trên ...

                            # Thêm đoạn này vào trước dòng message.reply
                            print(
                                f"--- DEBUG AI RESPONSE ---\nType: {type(ai_response)}\nLength: {len(str(ai_response)) if ai_response else 0}\nContent: {ai_response}\n-------------------------")

                            await message.reply(ai_response)
async def setup(bot: commands.Bot):
    await bot.add_cog(AICog(bot))