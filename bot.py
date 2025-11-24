import discord
from discord.ext import commands
from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from keep_alive import keep_alive

# --- CẤU HÌNH (ĐIỀN THÔNG TIN CỦA BẠN VÀO ĐÂY) ---
DISCORD_TOKEN = 'MTQ0MjM2MzY4MTAyNjQ3ODE3MQ.GHGVqH.kT7swoI2sB1Ol6YJ8Ojh1wSbWe_qM-QRLIhGu0'
AZURE_SUBSCRIPTION_ID = '04f8e0a3-8243-4807-bac7-aed74ae2f3e6'
AZURE_CLIENT_ID = '75332000-8fc1-4aa4-b223-e3ed146cc3c0'
AZURE_CLIENT_SECRET = 'v4L8Q~G-ssc1b5hOQ3euaNl8dOPHDNxzZEmmfcHP'
AZURE_TENANT_ID = 'bf211279-d710-4098-bd05-9e98ba43ea71'

RESOURCE_GROUP = 'MinecraftServer_group'  # Tên Resource Group trên Azure (Xem trên web)
VM_NAME = 'MinecraftServer'  # Tên máy ảo (Xem trên web)
# -------------------------------------------------

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
    print(f'Bot đã sẵn sàng: {bot.user}')


@bot.command()
async def batserver(ctx):
    await ctx.send("🤖 Đang kiểm tra trạng thái server...")

    # Lấy trạng thái máy ảo
    vm = compute_client.virtual_machines.instance_view(RESOURCE_GROUP, VM_NAME)
    status = vm.statuses[1].display_status  # Thường index 1 là trạng thái Power

    if "running" in status.lower():
        await ctx.send("✅ Server đang chạy rồi! Vào game chiến thôi.")
    else:
        await ctx.send("🚀 Đang gửi lệnh bật máy ảo Azure... Vui lòng đợi 1-2 phút.")
        # Lệnh bật máy
        compute_client.virtual_machines.begin_start(RESOURCE_GROUP, VM_NAME)
        await ctx.send("⏳ Tín hiệu đã gửi! Server sẽ online sau khoảng 2 phút nữa.")


@bot.command()
async def tatserver(ctx):
    await ctx.send("🛑 Đang gửi lệnh tắt máy (Deallocate)...")
    compute_client.virtual_machines.begin_deallocate(RESOURCE_GROUP, VM_NAME)
    await ctx.send("zzZ Server đang đi ngủ...")

keep_alive()
bot.run(DISCORD_TOKEN)
bot.run(DISCORD_TOKEN)