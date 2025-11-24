import discord
import os
import asyncio
from discord import app_commands
from discord.ext import commands
from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from keep_alive import keep_alive
from mcstatus import JavaServer

# --- CẤU HÌNH BIẾN MÔI TRƯỜNG ---
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
AZURE_SUBSCRIPTION_ID = os.getenv('AZURE_SUBSCRIPTION_ID')
AZURE_CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
AZURE_CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')
AZURE_TENANT_ID = os.getenv('AZURE_TENANT_ID')

RESOURCE_GROUP = 'MinecraftServer_group'
VM_NAME = 'MinecraftServer'
# -------------------------------------------------

# Kiểm tra biến môi trường
if not all([DISCORD_TOKEN, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET]):
    print("LỖI: Thiếu biến môi trường! Hãy kiểm tra lại cài đặt trên Render.")
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


bot = MyBot()


@bot.event
async def on_ready():
    print(f'🤖 Đăng nhập thành công: {bot.user}')
    # Đổi trạng thái hiển thị
    await bot.change_presence(activity=discord.Game(name="/start để chơi"))


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

@bot.tree.command(name="cmd", description="Gửi lệnh Admin vào Console Server")
@app_commands.describe(command="Lệnh cần nhập (Ví dụ: time set day)")
async def cmd(interaction: discord.Interaction, command: str):
    # Bảo mật: Chỉ cho phép Admin dùng (Check ID hoặc Role)
    if interaction.user.id != holetinnghia:  # Thay ID Discord của bạn vào đây
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
            f'screen -S mc -p 0 -X stuff "{cmd_clean}^M"'
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

        await interaction.followup.send(f"✅ Đã gửi lệnh: `/{cmd_clean}` xuống server.")

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

# Bật Web Server giả
keep_alive()

# Chạy Bot
bot.run(DISCORD_TOKEN)