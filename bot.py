import discord
import os
import asyncio
from discord import app_commands
from discord.ext import commands
from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from keep_alive import keep_alive

# --- CẤU HÌNH: ĐỌC TỪ BIẾN MÔI TRƯỜNG ---
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


# --- THIẾT LẬP BOT CLASS ĐỂ HỖ TRỢ SLASH COMMAND ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        # Đồng bộ lệnh Slash lên Discord
        await self.tree.sync()
        print("Đã đồng bộ Slash Commands thành công!")


bot = MyBot()


@bot.event
async def on_ready():
    print(f'Đăng nhập thành công: {bot.user}')
    # Đổi trạng thái hiển thị cho ngầu
    await bot.change_presence(activity=discord.Game(name="/batserver để chơi"))


# --- LỆNH 1: BẬT SERVER (/start) ---
@bot.tree.command(name="start", description="Bật Server Minecraft Azure")
async def batserver(interaction: discord.Interaction):
    # Báo cho Discord biết là "Tao đang xử lý, đừng báo timeout"
    await interaction.response.defer()

    await interaction.followup.send("> 🤖 Đang kiểm tra trạng thái server...")

    try:
        # 1. Kiểm tra trạng thái ban đầu
        vm = compute_client.virtual_machines.instance_view(RESOURCE_GROUP, VM_NAME)
        status = "Unknown"
        for s in vm.statuses:
            if "PowerState" in s.code:
                status = s.display_status
                break

        if "running" in status.lower():
            await interaction.followup.send(f"> ✅ Server đang chạy rồi! IP: `20.210.194.120`")
            return

        # 2. Nếu máy chưa chạy -> Gửi lệnh bật
        msg = await interaction.followup.send(
            "> 🚀 Đã gửi lệnh BẬT Azure. Đang chờ máy khởi động... (Sẽ tự báo khi xong)")
        compute_client.virtual_machines.begin_start(RESOURCE_GROUP, VM_NAME)

        # 3. Vòng lặp chờ (Polling) - Kiểm tra mỗi 10 giây
        for i in range(20):
            await asyncio.sleep(10)

            # Kiểm tra lại trạng thái
            vm = compute_client.virtual_machines.instance_view(RESOURCE_GROUP, VM_NAME)
            current_status = "Unknown"
            for s in vm.statuses:
                if "PowerState" in s.code:
                    current_status = s.display_status
                    break

            # Cập nhật tin nhắn cũ
            await msg.edit(content=f"> ⏳ Đang khởi động... ({current_status}) - Lần {i + 1}/20")

            if "running" in current_status.lower():
                await interaction.followup.send("> 🎉 **SERVER ĐÃ ONLINE!** (Máy Azure đã bật)")
                await interaction.followup.send(
                    "> 💡 Đợi thêm khoảng 30s-1 phút để Minecraft Server load xong map.\n> IP: `20.210.194.120`")
                return

        await interaction.followup.send("> ⚠️ Có vẻ khởi động hơi lâu, bạn hãy tự kiểm tra lại sau nhé.")

    except Exception as e:
        await interaction.followup.send(f"> ❌ Lỗi: {str(e)}")


# --- LỆNH 2: TẮT SERVER (/stop) ---
@bot.tree.command(name="stop", description="Tắt Server an toàn (Lưu map -> Tắt máy)")
async def tatserver(interaction: discord.Interaction):
    await interaction.response.defer()
    await interaction.followup.send("> 🛑 Đang gửi tín hiệu tắt an toàn vào máy chủ...")

    try:
        # Lệnh chạy script bên trong Linux
        run_command_parameters = {
            'command_id': 'RunShellScript',
            'script': [
                'chmod +x /home/holetinnghia/autoshutdown.sh',
                'nohup /home/holetinnghia/autoshutdown.sh > /dev/null 2>&1 &'
            ]
        }

        # Gửi lệnh vào máy ảo
        compute_client.virtual_machines.begin_run_command(
            RESOURCE_GROUP,
            VM_NAME,
            run_command_parameters
        )

        await interaction.followup.send(
            "> ✅ Đã kích hoạt quy trình tự hủy! Server sẽ lưu map và tắt sau khoảng 1 phút nữa.")

    except Exception as e:
        await interaction.followup.send(f"> ❌ Lỗi khi gửi lệnh: {str(e)}")


# Bật Web Server giả
keep_alive()

# Chạy Bot
bot.run(DISCORD_TOKEN)