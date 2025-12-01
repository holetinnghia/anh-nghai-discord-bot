import discord
from discord.ext import commands
import logging
from utils.ping_util import self_ping_task
from utils.hf_ping_util import hf_ping_task

class GeneralCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f'Đăng nhập thành công: {self.bot.user}')
        
        await self.bot.change_presence(activity=discord.Game(name="ước gì t bớt đẳng cấp 1 chuuts"))
        
        self.bot.loop.create_task(self_ping_task())
        self.bot.loop.create_task(hf_ping_task())

async def setup(bot: commands.Bot):
    await bot.add_cog(GeneralCog(bot))