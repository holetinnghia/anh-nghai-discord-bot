import discord
from discord.ext import commands
import logging
from utils.render_ping import self_ping_task
from utils.hf_ping import hf_ping_task

class GeneralCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """Được gọi khi bot đã kết nối thành công với Discord."""
        logging.info(f'Đăng nhập thành công: {self.bot.user}')
        
        # Đặt trạng thái hoạt động cho bot
        await self.bot.change_presence(activity=discord.Game(name="ước gì t bớt đẳng cấp 1 chuuts"))
        
        # Khởi chạy các tác vụ nền
        self.bot.loop.create_task(self_ping_task())
        self.bot.loop.create_task(hf_ping_task())
        # Không khởi động ai_worker nữa

async def setup(bot: commands.Bot):
    """Hàm setup để bot có thể tải Cog này."""
    await bot.add_cog(GeneralCog(bot))