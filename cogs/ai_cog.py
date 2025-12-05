import discord
from discord.ext import commands
from services.ai_service import ask_ai
from services.ai_lock_service import is_ai_busy, get_ai_lock

class AICog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.id == self.bot.user.id:
            return

        if self.bot.user.mentioned_in(message):
            if is_ai_busy():
                await message.reply("Tao đang bận trả lời đứa khác. Hỏi sau đi.")
                return

            question = message.content.replace(f'<@!{self.bot.user.id}>', '').replace(f'<@{self.bot.user.id}>', '').strip()

            if question:
                ai_lock = get_ai_lock()
                async with ai_lock:
                    async with message.channel.typing():
                        ai_response = await ask_ai(question)
                        
                        if not ai_response or not ai_response.strip():
                            await message.reply("Tao không nghĩ ra được câu trả lời. Hỏi câu khác đi.")
                        else:
                            if len(ai_response) <= 1900:
                                await message.reply(ai_response)
                            else:
                                chunks = [ai_response[i:i + 1900] for i in range(0, len(ai_response), 1900)]

                                await message.reply(chunks[0])

                                for chunk in chunks[1:]:
                                    await message.channel.send(chunk)
async def setup(bot: commands.Bot):
    await bot.add_cog(AICog(bot))