import discord
from discord.ext import commands
from services.ai_service import ask_ai

class AICog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return

        if self.bot.user.mentioned_in(message):
            question = message.content.replace(f'<@!{self.bot.user.id}>', '').replace(f'<@{self.bot.user.id}>', '').strip()

            if question:
                async with message.channel.typing():
                    ai_response = await ask_ai(question)
                await message.reply(ai_response)

async def setup(bot: commands.Bot):
    await bot.add_cog(AICog(bot))