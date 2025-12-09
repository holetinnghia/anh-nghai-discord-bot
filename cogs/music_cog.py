import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
import logging
import ctypes.util
import os

# --- CẤU HÌNH LOAD OPUS ĐA NỀN TẢNG ---
# Tự động tìm thư viện Opus trên hệ thống (Linux/Mac)
opus_name = ctypes.util.find_library('opus')
# Nếu không tìm thấy tự động (trường hợp Mac cài brew đôi khi bị ẩn), mới fallback về đường dẫn cứng
if not opus_name:
    # Check xem có phải đang chạy trên Mac không (Darwin)
    import platform

    if platform.system() == 'Darwin':
        opus_name = '/opt/homebrew/lib/libopus.dylib'
    else:
        opus_name = 'libopus.so.0'  # Tên mặc định trên Linux

try:
    discord.opus.load_opus(opus_name)
    print(f"Đã load Opus: {opus_name}")
except Exception as e:
    print(f"Lỗi load Opus (có thể bỏ qua nếu chạy trên Docker đã setup sẵn): {e}")
# ---------------------------------------

YTDL_FORMAT_OPTIONS = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0'
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(YTDL_FORMAT_OPTIONS)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)

        # SỬA Ở ĐÂY: Không dùng đường dẫn tuyệt đối nữa, chỉ dùng 'ffmpeg'
        # Trên Mac, đảm bảo ffmpeg đã trong PATH hoặc code tự tìm.
        # Trên Render (Docker), mình sẽ cài ffmpeg vào PATH.
        return cls(discord.FFmpegPCMAudio(filename, executable='ffmpeg', **FFMPEG_OPTIONS), data=data)


class MusicCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="join", description="Mời bot vào kênh thoại")
    async def join(self, interaction: discord.Interaction):
        if not interaction.user.voice:
            await interaction.response.send_message("Bạn cần vào kênh thoại trước.", ephemeral=True)
            return
        channel = interaction.user.voice.channel
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.move_to(channel)
        else:
            await channel.connect()
        await interaction.response.send_message(f"Đã vào kênh: {channel.name}")

    @app_commands.command(name="play", description="Phát nhạc")
    @app_commands.describe(search="Tên bài hát hoặc link")
    async def play(self, interaction: discord.Interaction, *, search: str):
        if not interaction.user.voice:
            await interaction.response.send_message("Bạn cần vào kênh thoại trước.", ephemeral=True)
            return

        if not interaction.guild.voice_client:
            await interaction.user.voice.channel.connect()

        if interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.stop()

        await interaction.response.defer()

        try:
            player = await YTDLSource.from_url(search, loop=self.bot.loop, stream=True)

            def after_playing(error):
                if error:
                    logging.error(f'Lỗi player: {error}')

            interaction.guild.voice_client.play(player, after=after_playing)
            await interaction.followup.send(f'Đang phát: **{player.title}**')

        except Exception as e:
            logging.error(f"Lỗi play: {e}")
            await interaction.followup.send(f'Lỗi: {e}')

    @app_commands.command(name="leave", description="Cho bot nghỉ")
    async def leave(self, interaction: discord.Interaction):
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message("Bye bye!")
        else:
            await interaction.response.send_message("Bot không ở trong kênh nào.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))