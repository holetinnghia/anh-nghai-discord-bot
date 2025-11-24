import discord
import os
from discord.ext import commands
from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from keep_alive import keep_alive

# --- CẤU HÌNH: ĐỌC TỪ BIẾN MÔI TRƯỜNG (AN TOÀN TUYỆT ĐỐI) ---
# Nếu chạy trên máy Mac để test, bạn phải set biến môi trường hoặc điền tạm vào đây (nhưng đừng commit lên git).
# Khi chạy trên Render, nó sẽ tự lấy từ mục Environment Variables.

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
AZURE_SUBSCRIPTION_ID = os.getenv('AZURE_SUBSCRIPTION_ID')
AZURE_CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
AZURE_CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')
AZURE_TENANT_ID = os.getenv('AZURE_TENANT_ID')

RESOURCE_GROUP = 'MinecraftServer_group'
VM_NAME = 'MinecraftServer'
# -------------------------------------------------

# Kiểm tra xem đã nạp đủ biến chưa (Tránh lỗi ngớ ngẩn)
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

# Thiết lập Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'Bot đã đăng nhập thành công: {bot.user}')


@bot.command()
async def batserver(ctx):
    await ctx.send("🤖 Đang kết nối tới Azure để kiểm tra...")

    try:
        # Lấy trạng thái máy ảo
        vm = compute_client.virtual_machines.instance_view(RESOURCE_GROUP, VM_NAME)
        # Tìm trạng thái PowerState (thường nằm trong list statuses)
        status = "Unknown"
        for s in vm.statuses:
            if "PowerState" in s.code:
                status = s.display_status
                break

        if "running" in status.lower():
            await ctx.send(f"✅ Server đang chạy rồi ({status})! Vào game chiến thôi IP: 20.210.194.120")
        else:
            await ctx.send("🚀 Đã gửi lệnh BẬT máy ảo Azure... Vui lòng đợi 2-3 phút để Minecraft khởi động.")
            compute_client.virtual_machines.begin_start(RESOURCE_GROUP, VM_NAME)

    except Exception as e:
        await ctx.send(f"❌ Có lỗi xảy ra: {str(e)}")


@bot.command()
async def tatserver(ctx):
    await ctx.send("🛑 Đang gửi lệnh TẮT máy (Deallocate)...")
    try:
        compute_client.virtual_machines.begin_deallocate(RESOURCE_GROUP, VM_NAME)
        await ctx.send("zzZ Server đang đi ngủ... Hẹn gặp lại!")
    except Exception as e:
        await ctx.send(f"❌ Lỗi khi tắt: {str(e)}")


# Bật Web Server giả trước khi chạy bot
keep_alive()

# Chạy Bot
bot.run(DISCORD_TOKEN)