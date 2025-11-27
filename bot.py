from dotenv import load_dotenv
load_dotenv() # Tải các biến môi trường từ file .env

import os
import asyncio
from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from keep_alive import keep_alive
from mcstatus import JavaServer
import discord
from discord import app_commands
from discord.ext import commands
from riotwatcher import LolWatcher, RiotWatcher, ApiError

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

# Kiểm tra biến môi trường
if not all([DISCORD_TOKEN, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, RIOT_API_KEY]):
    print("LỖI: Thiếu biến môi trường! Hãy kiểm tra lại cài đặt trên Render hoặc file .env.")
    exit()

# Kết nối Azure
credential = ClientSecretCredential(
    tenant_id=AZURE_TENANT_ID,
    client_id=AZURE_CLIENT_ID,
    client_secret=AZURE_CLIENT_SECRET,
)
compute_client = ComputeManagementClient(credential, AZURE_SUBSCRIPTION_ID)


# --- THIẾT LẬP BOT CLASS ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("✅ Đã đồng bộ Slash Commands (/start, /stop, /status) thành công!")

# --- HÀM TỰ PING ĐỂ CHỐNG NGỦ ---
async def self_ping():
    # THAY LINK RENDER CỦA BẠN VÀO DƯỚI ĐÂY:
    url = "https://anh-nghaispkt.onrender.com"

    print(f"🔄 Đã kích hoạt chế độ tự ping mỗi 10 phút vào: {url}")

    while True:
        try:
            await asyncio.sleep(300)

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        print("✅ Tự ping thành công (Bot vẫn sống)")
                    else:
                        print(f"⚠️ Tự ping thất bại: {resp.status}")
        except Exception as e:
            print(f"❌ Lỗi tự ping: {e}")
            # Nếu lỗi thì chờ 1 phút rồi thử lại, tránh spam lỗi
            await asyncio.sleep(60)

bot = MyBot()

@bot.event
async def on_ready():
    print(f'🤖 Đăng nhập thành công: {bot.user}')
    # Đổi trạng thái hiển thị
    await bot.change_presence(activity=discord.Game(name="/start để chơi"))
    bot.loop.create_task(self_ping())


# --- HÀM PHỤ TRỢ: LẤY TRẠNG THÁI ---
def get_vm_status():
    try:
        vm = compute_client.virtual_machines.instance_view(RESOURCE_GROUP, VM_NAME)
        for s in vm.statuses:
            # Azure trả về nhiều status, ta cần tìm cái PowerState/running hoặc deallocated
            if "PowerState" in s.code:
                return s.display_status
        return "Unknown"
    except Exception as e:
        return f"Error: {str(e)}"


# --- LỆNH 1: STATUS (KIỂM TRA TRẠNG THÁI) ---
@bot.tree.command(name="status", description="Kiểm tra xem Server đang Bật hay Tắt")
async def status(interaction: discord.Interaction):
    await interaction.response.defer()  # Hoãn trả lời để chờ Azure

    current_status = get_vm_status()

    if "running" in current_status.lower():
        await interaction.followup.send(f"✅ **Server đang hoạt động!** ({current_status})\nIP: `20.210.194.120`")
    elif "deallocated" in current_status.lower() or "stopped" in current_status.lower():
        await interaction.followup.send(f"zzz **Server đang tắt** ({current_status}).\nDùng lệnh `/start` để bật.")
    else:
        await interaction.followup.send(f"⚠️ **Trạng thái:** {current_status}")


# --- LỆNH 2: START (BẬT SERVER) ---
@bot.tree.command(name="start", description="Khởi động Server Minecraft Azure")
async def start(interaction: discord.Interaction):
    await interaction.response.defer()

    status = get_vm_status()

    if "running" in status.lower():
        await interaction.followup.send(f"✅ **Server đang chạy rồi!**\nIP: `20.210.194.120`")
        return

    msg = await interaction.followup.send(f"🚀 **Đang kích hoạt máy ảo Azure...**\n(Trạng thái hiện tại: {status})")

    try:
        compute_client.virtual_machines.begin_start(RESOURCE_GROUP, VM_NAME)

        # Vòng lặp chờ (3 phút)
        for i in range(20):
            await asyncio.sleep(10)
            current_status = get_vm_status()

            await msg.edit(content=f"⏳ Đang khởi động... ({current_status}) - {i * 10}s")

            if "running" in current_status.lower():
                await interaction.followup.send(
                    "🎉 **SERVER ĐÃ ONLINE!**\n💡 Đợi thêm 30s để Minecraft load map.\nIP: `20.210.194.120`")
                return

        await interaction.followup.send("⚠️ Server khởi động lâu hơn dự kiến. Hãy dùng `/status` để kiểm tra lại sau.")

    except Exception as e:
        await interaction.followup.send(f"❌ Lỗi khi bật: {str(e)}")


# --- LỆNH 3: STOP (TẮT AN TOÀN) ---
@bot.tree.command(name="stop", description="Tắt Server an toàn (Lưu map -> Tắt máy)")
async def stop(interaction: discord.Interaction):
    await interaction.response.defer()

    status = get_vm_status()

    if "running" not in status.lower():
        await interaction.followup.send(f"zzz **Server đang tắt rồi** ({status}). Không cần tắt nữa!")
        return

    await interaction.followup.send("🛑 **Đang gửi tín hiệu tắt an toàn...**")

    try:
        # Chạy script tự hủy bên trong Linux
        run_command_parameters = {
            'command_id': 'RunShellScript',
            'script': [
                # Sửa dòng này trỏ đến file manual_stop.sh
                'chmod +x /home/holetinnghia/manual_stop.sh',
                'nohup /home/holetinnghia/manual_stop.sh > /dev/null 2>&1 &'
            ]
        }

        compute_client.virtual_machines.begin_run_command(
            RESOURCE_GROUP,
            VM_NAME,
            run_command_parameters
        )

        await interaction.followup.send(
            "✅ **Đã kích hoạt quy trình tự hủy!**\nServer sẽ lưu map và tắt hẳn sau khoảng 1 phút nữa.")

    except Exception as e:
        await interaction.followup.send(f"❌ Lỗi khi gửi lệnh tắt: {str(e)}")

# --- LỆNH 4: RESTART (KHỞI ĐỘNG LẠI GAME) ---
@bot.tree.command(name="restart", description="Khởi động lại Java Server (Không tắt máy Azure)")
async def restart(interaction: discord.Interaction):
    await interaction.response.defer()

    status = get_vm_status()
    if "running" not in status.lower():
        await interaction.followup.send("❌ Máy Azure đang tắt, không thể restart. Hãy dùng `/start`.")
        return

    await interaction.followup.send(
        "🔄 **Đang khởi động lại Server Minecraft...**\n(Map sẽ được lưu, vui lòng đợi khoảng 30-60 giây)")

    try:
        # Script combo: Stop -> Wait -> Start
        restart_script = [
            'screen -S mc -p 0 -X stuff "stop^M"',
            'sleep 20',
            '/home/holetinnghia/minecraft/start.sh'
        ]

        run_command_parameters = {
            'command_id': 'RunShellScript',
            'script': restart_script
        }

        compute_client.virtual_machines.begin_run_command(
            RESOURCE_GROUP,
            VM_NAME,
            run_command_parameters
        )

        await interaction.followup.send(
            "✅ **Đã gửi lệnh Restart!**\nHãy thử ping `/status` hoặc `/online` sau 1 phút nữa.")

    except Exception as e:
        await interaction.followup.send(f"❌ Lỗi: {str(e)}")

@bot.tree.command(name="online", description="Xem ai đang chơi trong server")
async def online(interaction: discord.Interaction):
    await interaction.response.defer()

    server_ip = "20.210.194.120"  # IP Server của bạn

    try:
        # Ping thử vào cổng game
        server = JavaServer.lookup(server_ip)
        status = server.status()

        # Lấy danh sách người chơi
        player_count = status.players.online
        latency = round(status.latency)

        msg = f"🟢 **Server Online** (Ping: {latency}ms)\n"
        msg += f"👥 **Người chơi ({player_count}/{status.players.max}):**\n"

        if status.players.sample:
            for p in status.players.sample:
                msg += f"- `{p.name}`\n"
        else:
            msg += "_(Không có ai)_"

        await interaction.followup.send(msg)

    except Exception:
        # Nếu lỗi nghĩa là Server Java chưa bật hoặc đang khởi động
        await interaction.followup.send(
            "🔴 **Không kết nối được vào Minecraft!**\n(Có thể máy Azure đang tắt, hoặc Java đang khởi động, hãy thử lại sau 1 phút)")

@bot.tree.command(name="cmd", description="Gửi lệnh Admin vào Console Server (Ví dụ: time set day)")
@app_commands.describe(command="Nhập lệnh Minecraft (không cần dấu /)")
async def cmd(interaction: discord.Interaction, command: str):
    # Bảo mật: Chỉ cho phép Admin dùng (Check ID hoặc Role)
    if interaction.user.id != 458620943015608320:  # Thay ID Discord của bạn vào đây
        await interaction.response.send_message("❌ Bạn không có quyền Admin!", ephemeral=True)
        return

    await interaction.response.defer()

    # Xử lý lệnh (bỏ dấu / nếu người dùng lỡ nhập)
    cmd_clean = command.replace("/", "")

    try:
        # Kỹ thuật Injection vào Screen:
        # -p 0: Chọn cửa sổ đầu tiên
        # -X stuff: Nhồi ký tự vào
        # ^M: Giả lập phím Enter
        shell_script = [
            f"sudo -u holetinnghia screen -S mc -p 0 -X stuff '{cmd_clean}\r'"
        ]

        run_command_parameters = {
            'command_id': 'RunShellScript',
            'script': shell_script
        }

        compute_client.virtual_machines.begin_run_command(
            RESOURCE_GROUP,
            VM_NAME,
            run_command_parameters
        )

        await interaction.followup.send(f"✅ Đã gửi lệnh: `/{cmd_clean}`")

    except Exception as e:
        await interaction.followup.send(f"❌ Lỗi: {str(e)}")

@bot.tree.command(name="health", description="Xem RAM và CPU của máy ảo Azure")
async def health(interaction: discord.Interaction):
    await interaction.response.defer()

    try:
        # Chạy lệnh Linux để lấy thông tin
        # free -h: Xem RAM
        # uptime: Xem tải CPU (Load average)
        run_command_parameters = {
            'command_id': 'RunShellScript',
            'script': ['free -h && echo "---" && uptime']
        }

        poller = compute_client.virtual_machines.begin_run_command(
            RESOURCE_GROUP,
            VM_NAME,
            run_command_parameters
        )

        # Lấy kết quả trả về từ Linux
        result = poller.result()
        output = result.value[0].message

        await interaction.followup.send(f"📊 **Tình trạng sức khỏe VPS:**\n```\n{output}\n```")

    except Exception as e:
        await interaction.followup.send(f"❌ Máy ảo đang tắt hoặc lỗi: {str(e)}")





# CẤU HÌNH
REGION = 'vn2'  # Server Việt Nam hiện tại là vn2

lol_watcher = LolWatcher(RIOT_API_KEY)
riot_watcher = RiotWatcher(RIOT_API_KEY)

# (Giữ nguyên phần khởi tạo bot của ông)

@bot.tree.command(name="lolprofile", description="Xem rank LoL")
@app_commands.describe(riot_id="Nhập dạng Tên#Tag (VD: SofM#VN2)")
async def lolprofile(interaction: discord.Interaction, riot_id: str):
    await interaction.response.defer()

    try:
        if "#" not in riot_id:
            await interaction.followup.send("❌ Nhập sai rồi bro! Phải có dấu # (VD: Yasuo#VN2)")
            return

        game_name, tag_line = riot_id.split("#")

        # 1. Lấy PUUID
        account_data = riot_watcher.account.by_riot_id('asia', game_name, tag_line)
        puuid = account_data['puuid']

        # 2. Lấy Summoner Info
        summoner_data = lol_watcher.summoner.by_puuid(REGION, puuid)
        encrypted_summoner_id = summoner_data.get('id')

        # Biến để lưu info trận cuối (nếu có)
        last_match_info = "Không có dữ liệu"

        # --- XỬ LÝ ZOMBIE ACCOUNT ---
        if not encrypted_summoner_id:
            print(f"⚠️ Account Zombie: {riot_id}. Đang đi đường vòng...")
            try:
                MATCH_ROUTING = 'sea'
                matches = lol_watcher.match.matchlist_by_puuid(MATCH_ROUTING, puuid, count=1)

                if matches:
                    last_match = lol_watcher.match.by_id(MATCH_ROUTING, matches[0])
                    # Lấy ID từ trận đấu
                    for p in last_match['info']['participants']:
                        if p['puuid'] == puuid:
                            encrypted_summoner_id = p['summonerId']
                            # Tiện tay lấy luôn thông tin trận vừa đánh
                            champ = p['championName']
                            kda = f"{p['kills']}/{p['deaths']}/{p['assists']}"
                            win = "Thắng" if p['win'] else "Thua"
                            last_match_info = f"**{champ}** ({win})\nKDA: {kda}"
                            break
                else:
                    await interaction.followup.send("❌ Acc lỗi ID và chưa đánh trận nào. Bó tay.")
                    return
            except Exception as e:
                print(f"Lỗi đường vòng: {e}")
                await interaction.followup.send("❌ Lỗi dữ liệu nghiêm trọng từ Riot.")
                return
        # ----------------------------

        # 3. Lấy Rank (Bọc trong Try-Except riêng để không chết bot)
        rank_display = "Chưa phân hạng (Unranked)"
        try:
            if encrypted_summoner_id:
                rank_data = lol_watcher.league.by_summoner(REGION, encrypted_summoner_id)
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
                print(f"Lỗi 403 Rank: {err}")
            else:
                rank_display = "⚠️ Lỗi API Rank"

        # 4. Hiển thị
        embed = discord.Embed(title=f"Hồ sơ: {riot_id}", color=0x00ff00)
        icon_id = summoner_data.get('profileIconId', 29)
        embed.set_thumbnail(url=f"http://ddragon.leagueoflegends.com/cdn/14.23.1/img/profileicon/{icon_id}.png")

        embed.add_field(name="Cấp độ", value=summoner_data.get('summonerLevel', 'N/A'), inline=True)
        embed.add_field(name="Rank Đơn/Đôi", value=rank_display, inline=False)

        # Thêm dòng này để vớt vát danh dự cho cái acc lỗi
        if last_match_info != "Không có dữ liệu":
            embed.add_field(name="Trận gần nhất", value=last_match_info, inline=False)

        await interaction.followup.send(embed=embed)

    except ApiError as err:
        if err.response.status_code == 404:
            await interaction.followup.send(f"❌ Không tìm thấy user **{riot_id}**.")
        elif err.response.status_code == 403:
            await interaction.followup.send("⚠️ API Key hết hạn rồi bro.")
        else:
            await interaction.followup.send(f"⚠️ Lỗi API Tổng: {err.response.status_code}")
    except Exception as e:
        print(f"Lỗi lạ: {e}")
        await interaction.followup.send(f"⚠️ Toang: {str(e)}")

# Bật Web Server giả
keep_alive()

# Chạy Bot
bot.run(DISCORD_TOKEN)