from dotenv import load_dotenv
load_dotenv() # Tải các biến môi trường từ file .env

import os
import asyncio
import logging
from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from keep_alive import keep_alive
from mcstatus import JavaServer
import discord
from discord import app_commands
from discord.ext import commands
from riotwatcher import LolWatcher, RiotWatcher, ApiError
import aiohttp

# --- CẤU HÌNH BIẾN MÔI TRƯỜNG ---
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
AZURE_SUBSCRIPTION_ID = os.getenv('AZURE_SUBSCRIPTION_ID')
AZURE_CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
AZURE_CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')
AZURE_TENANT_ID = os.getenv('AZURE_TENANT_ID')
RIOT_API_KEY = os.getenv('RIOT_API_KEY')

RESOURCE_GROUP = 'MinecraftServer_group'
VM_NAME = 'MinecraftServer'
# -------------------------------------------------

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Kiểm tra biến môi trường
if not all([DISCORD_TOKEN, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, RIOT_API_KEY]):
    logging.error("LỖI: Thiếu biến môi trường! Hãy kiểm tra lại cài đặt trên Render hoặc file .env.")
    exit()

# Kết nối Azure
credential = ClientSecretCredential(
    tenant_id=AZURE_TENANT_ID,
    client_id=AZURE_CLIENT_ID,
    client_secret=AZURE_CLIENT_SECRET,
)
compute_client = ComputeManagementClient(credential, AZURE_SUBSCRIPTION_ID)

# --- HÀM PHỤ TRỢ: LẤY TRẠNG THÁI ---
def get_vm_status():
    try:
        vm = compute_client.virtual_machines.instance_view(RESOURCE_GROUP, VM_NAME)
        for s in vm.statuses:
            if "PowerState" in s.code:
                return s.display_status
        return "Unknown"
    except Exception as e:
        logging.error(f"Lỗi khi lấy trạng thái VM: {e}")
        return f"Error: {str(e)}"

# --- COG CHO CÁC LỆNH AZURE ---
class AzureCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    azure = app_commands.Group(name="azure", description="Các lệnh quản lý Azure")

    @azure.command(name="status", description="Kiểm tra xem máy ảo Azure đang Bật hay Tắt")
    async def status(self, interaction: discord.Interaction):
        await interaction.response.defer()
        current_status = get_vm_status()
        if "running" in current_status.lower():
            await interaction.followup.send(f"**Server đang hoạt động!** ({current_status})\nIP: `20.210.194.120`")
        elif "deallocated" in current_status.lower() or "stopped" in current_status.lower():
            await interaction.followup.send(f"**Server đang tắt** ({current_status}).\nDùng lệnh `/azure start` để bật.")
        else:
            await interaction.followup.send(f"⚠️ **Trạng thái:** {current_status}")

    @azure.command(name="health", description="Xem RAM và CPU của máy ảo Azure")
    async def health(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            run_command_parameters = {'command_id': 'RunShellScript', 'script': ['free -h && echo "---" && uptime']}
            poller = compute_client.virtual_machines.begin_run_command(RESOURCE_GROUP, VM_NAME, run_command_parameters)
            result = poller.result()
            output = result.value[0].message
            await interaction.followup.send(f"**Tình trạng sức khỏe VPS:**\n```\n{output}\n```")
        except Exception as e:
            logging.error(f"Lỗi khi kiểm tra health: {e}")
            await interaction.followup.send(f"❌ Máy ảo đang tắt hoặc lỗi: {str(e)}")

    @azure.command(name="start", description="Khởi động Server Minecraft Azure")
    async def start(self, interaction: discord.Interaction):
        await interaction.response.defer()
        status = get_vm_status()
        if "running" in status.lower():
            await interaction.followup.send(f"**Server đang chạy rồi!**\nIP: `20.210.194.120`")
            return
        msg = await interaction.followup.send(f"**Đang kích hoạt máy ảo Azure...**\n(Trạng thái hiện tại: {status})")
        try:
            compute_client.virtual_machines.begin_start(RESOURCE_GROUP, VM_NAME)
            for i in range(20):
                await asyncio.sleep(10)
                current_status = get_vm_status()
                await msg.edit(content=f"Đang khởi động... ({current_status}) - {i * 10}s")
                if "running" in current_status.lower():
                    await interaction.followup.send("**SERVER ĐÃ ONLINE!**\nĐợi thêm 30s để Minecraft load map.\nIP: `20.210.194.120`")
                    return
            await interaction.followup.send("⚠️ Server khởi động lâu hơn dự kiến. Hãy dùng `/azure status` để kiểm tra lại sau.")
        except Exception as e:
            logging.error(f"Lỗi khi bật VM: {e}")
            await interaction.followup.send(f"❌ Lỗi khi bật: {str(e)}")

    @azure.command(name="stop", description="Tắt Server an toàn (Lưu map -> Tắt máy)")
    async def stop(self, interaction: discord.Interaction):
        await interaction.response.defer()
        status = get_vm_status()
        if "running" not in status.lower():
            await interaction.followup.send(f"**Server đang tắt rồi** ({status}). Không cần tắt nữa!")
            return
        await interaction.followup.send("**Đang gửi tín hiệu tắt an toàn...**")
        try:
            run_command_parameters = {
                'command_id': 'RunShellScript',
                'script': [
                    'chmod +x /home/holetinnghia/manual_stop.sh',
                    'nohup /home/holetinnghia/manual_stop.sh > /dev/null 2>&1 &'
                ]
            }
            compute_client.virtual_machines.begin_run_command(RESOURCE_GROUP, VM_NAME, run_command_parameters)
            await interaction.followup.send("**Đã kích hoạt quy trình tự hủy!**\nServer sẽ lưu map và tắt hẳn sau khoảng 1 phút nữa.")
        except Exception as e:
            logging.error(f"Lỗi khi gửi lệnh tắt: {e}")
            await interaction.followup.send(f"❌ Lỗi khi gửi lệnh tắt: {str(e)}")

# --- COG CHO CÁC LỆNH MINECRAFT ---
class MinecraftCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    mc = app_commands.Group(name="mc", description="Các lệnh quản lý Minecraft")

    @mc.command(name="restart", description="Khởi động lại Java Server (Không tắt máy Azure)")
    async def restart(self, interaction: discord.Interaction):
        await interaction.response.defer()
        status = get_vm_status()
        if "running" not in status.lower():
            await interaction.followup.send("Máy Azure đang tắt, không thể restart.")
            return
        await interaction.followup.send("**Đang khởi động lại Server Minecraft...**\n(Map sẽ được lưu, vui lòng đợi khoảng 30-60 giây)")
        try:
            restart_script = ['screen -S mc -p 0 -X stuff "stop^M"', 'sleep 20', '/home/holetinnghia/minecraft/start.sh']
            run_command_parameters = {'command_id': 'RunShellScript', 'script': restart_script}
            compute_client.virtual_machines.begin_run_command(RESOURCE_GROUP, VM_NAME, run_command_parameters)
            await interaction.followup.send("**Đã gửi lệnh Restart!**\nHãy thử lại sau 1 phút nữa.")
        except Exception as e:
            logging.error(f"Lỗi khi restart server: {e}")
            await interaction.followup.send(f"❌ Lỗi: {str(e)}")

    @mc.command(name="online", description="Xem ai đang chơi trong Server Minecraft")
    async def online(self, interaction: discord.Interaction):
        await interaction.response.defer()
        server_ip = "20.210.194.120"
        try:
            server = await JavaServer.async_lookup(server_ip)
            status = await server.async_status()
            player_count = status.players.online
            latency = round(status.latency)
            msg = f"**Server Online** (Ping: {latency}ms)\n**Người chơi ({player_count}/{status.players.max}):**\n"
            if status.players.sample:
                msg += "\n".join([f"- `{p.name}`" for p in status.players.sample])
            else:
                msg += "_(Không có ai)_"
            await interaction.followup.send(msg)
        except Exception as e:
            logging.warning(f"Không kết nối được vào Minecraft server: {e}")
            await interaction.followup.send("🔴 **Không kết nối được vào Minecraft!**\n(Có thể máy Azure đang tắt, hoặc Java đang khởi động, hãy thử lại sau 1 phút)")

    @mc.command(name="console", description="Gửi lệnh Admin vào Console Server")
    @app_commands.describe(command="Nhập lệnh Minecraft (không cần dấu /)")
    async def console(self, interaction: discord.Interaction, command: str):
        if interaction.user.id != 458620943015608320:
            await interaction.response.send_message("❌ Bạn không có quyền Admin!", ephemeral=True)
            return
        await interaction.response.defer()
        cmd_clean = command.replace("/", "")
        try:
            shell_script = [f"sudo -u holetinnghia screen -S mc -p 0 -X stuff '{cmd_clean}\r'"]
            run_command_parameters = {'command_id': 'RunShellScript', 'script': shell_script}
            compute_client.virtual_machines.begin_run_command(RESOURCE_GROUP, VM_NAME, run_command_parameters)
            await interaction.followup.send(f"Đã gửi lệnh: `/{cmd_clean}`")
        except Exception as e:
            logging.error(f"Lỗi khi gửi lệnh console: {e}")
            await interaction.followup.send(f"❌ Lỗi: {str(e)}")

# --- COG CHO CÁC LỆNH LOL ---
class LOLCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.lol_watcher = LolWatcher(RIOT_API_KEY)
        self.riot_watcher = RiotWatcher(RIOT_API_KEY)

    lol = app_commands.Group(name="lol", description="Các lệnh liên quan đến League of Legends")

    @lol.command(name="profile", description="Xem rank LoL")
    @app_commands.describe(riot_id="Nhập dạng Tên#Tag (VD: SofM#VN2)")
    async def profile(self, interaction: discord.Interaction, riot_id: str):
        await interaction.response.defer()
        try:
            if "#" not in riot_id:
                await interaction.followup.send("❌ Nhập sai rồi bro! Phải có dấu # (VD: Yasuo#VN2)")
                return

            game_name, tag_line = riot_id.split("#")
            region = 'vn2'
            routing = 'asia'
            match_routing = 'sea'

            account_data = self.riot_watcher.account.by_riot_id(routing, game_name, tag_line)
            puuid = account_data['puuid']
            summoner_data = self.lol_watcher.summoner.by_puuid(region, puuid)
            encrypted_summoner_id = summoner_data.get('id')
            last_match_info = "Không có dữ liệu"

            if not encrypted_summoner_id:
                logging.warning(f"Account Zombie: {riot_id}. Đang đi đường vòng...")
                try:
                    matches = self.lol_watcher.match.matchlist_by_puuid(match_routing, puuid, count=1)
                    if matches:
                        last_match = self.lol_watcher.match.by_id(match_routing, matches[0])
                        for p in last_match['info']['participants']:
                            if p['puuid'] == puuid:
                                encrypted_summoner_id = p['summonerId']
                                champ = p['championName']
                                kda = f"{p['kills']}/{p['deaths']}/{p['assists']}"
                                win = "Thắng" if p['win'] else "Thua"
                                last_match_info = f"**{champ}** ({win})\nKDA: {kda}"
                                break
                    else:
                        await interaction.followup.send("❌ Acc lỗi ID và chưa đánh trận nào. Bó tay.")
                        return
                except ApiError as e:
                    logging.error(f"Lỗi đường vòng khi xử lý account zombie: {e}")
                    await interaction.followup.send("❌ Lỗi dữ liệu nghiêm trọng từ Riot.")
                    return

            rank_display = "Chưa phân hạng (Unranked)"
            if encrypted_summoner_id:
                try:
                    rank_data = self.lol_watcher.league.by_summoner(region, encrypted_summoner_id)
                    for queue in rank_data:
                        if queue['queueType'] == 'RANKED_SOLO_5x5':
                            tier = queue['tier']
                            rank = queue['rank']
                            lp = queue['leaguePoints']
                            winrate = round((queue['wins'] / (queue['wins'] + queue['losses'])) * 100, 1)
                            rank_display = f"**{tier} {rank}** - {lp} LP\nWR: {winrate}%"
                            break
                except ApiError as err:
                    if err.response.status_code == 403:
                        rank_display = "⚠️ **Lỗi Riot (403)**\nAcc này bị Riot chặn xem Rank."
                        logging.warning(f"Lỗi 403 Rank: {err}")
                    else:
                        rank_display = "⚠️ Lỗi API Rank"
                        logging.error(f"Lỗi API Rank: {err}")

            embed = discord.Embed(title=f"Hồ sơ: {riot_id}", color=0x00ff00)
            icon_id = summoner_data.get('profileIconId', 29)
            embed.set_thumbnail(url=f"https://ddragon.leagueoflegends.com/cdn/14.23.1/img/profileicon/{icon_id}.png")
            embed.add_field(name="Cấp độ", value=summoner_data.get('summonerLevel', 'N/A'), inline=True)
            embed.add_field(name="Rank Đơn/Đôi", value=rank_display, inline=False)
            if last_match_info != "Không có dữ liệu":
                embed.add_field(name="Trận gần nhất", value=last_match_info, inline=False)
            await interaction.followup.send(embed=embed)

        except ApiError as err:
            if err.response.status_code == 404:
                await interaction.followup.send(f"❌ Không tìm thấy user **{riot_id}**.")
            elif err.response.status_code == 403:
                await interaction.followup.send("⚠️ API Key hết hạn rồi bro.")
            else:
                logging.error(f"Lỗi API Tổng: {err}")
                await interaction.followup.send(f"⚠️ Lỗi API Tổng: {err.response.status_code}")
        except Exception as e:
            logging.error(f"Lỗi lạ trong lol profile: {e}")
            await interaction.followup.send(f"⚠️ Toang: {str(e)}")

# --- HÀM TỰ PING ĐỂ CHỐNG NGỦ ---
async def self_ping():
    url = "https://anh-nghai-bot.onrender.com"
    logging.info(f"Đã kích hoạt chế độ tự ping mỗi 5 phút vào: {url}")
    while True:
        await asyncio.sleep(300)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        logging.info("Tự ping thành công (Bot vẫn sống)")
                    else:
                        logging.warning(f"⚠️ Tự ping thất bại: {resp.status}")
        except aiohttp.ClientError as e:
            logging.error(f"❌ Lỗi tự ping: {e}")
            await asyncio.sleep(60)

# --- THIẾT LẬP BOT CLASS ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        await self.add_cog(AzureCog(self))
        await self.add_cog(MinecraftCog(self))
        await self.add_cog(LOLCog(self))
        await self.tree.sync()
        logging.info("Cây lệnh đã được đồng bộ.")

bot = MyBot()

@bot.event
async def on_ready():
    logging.info(f'Đăng nhập thành công: {bot.user}')
    await bot.change_presence(activity=discord.Game(name="ước gì t bớt đẳng cấp 1 chuuts"))
    bot.loop.create_task(self_ping())

# Bật Web Server giả và chạy Bot
if __name__ == "__main__":
    keep_alive()
    bot.run(DISCORD_TOKEN)