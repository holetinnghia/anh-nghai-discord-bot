import discord
import os
from discord.ext import commands
from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from keep_alive import keep_alive
import asyncio

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
    await ctx.send("🤖 Đang kiểm tra trạng thái server...")

    # 1. Kiểm tra trạng thái ban đầu
    vm = compute_client.virtual_machines.instance_view(RESOURCE_GROUP, VM_NAME)
    status = "Unknown"
    for s in vm.statuses:
        if "PowerState" in s.code:
            status = s.display_status
            break

    if "running" in status.lower():
        await ctx.send(f"✅ Server đang chạy rồi! IP: 20.210.194.120")
        return  # Thoát luôn nếu máy đang chạy

    # 2. Nếu máy chưa chạy -> Gửi lệnh bật
    status_msg = await ctx.send("🚀 Đã gửi lệnh BẬT Azure. Đang chờ máy khởi động... (Sẽ tự báo khi xong)")
    compute_client.virtual_machines.begin_start(RESOURCE_GROUP, VM_NAME)

    # 3. Vòng lặp chờ (Polling) - Kiểm tra mỗi 10 giây
    # Thử tối đa 20 lần (khoảng 3-4 phút)
    for i in range(20):
        await asyncio.sleep(10)  # Chờ 10 giây

        # Kiểm tra lại trạng thái
        vm = compute_client.virtual_machines.instance_view(RESOURCE_GROUP, VM_NAME)
        current_status = "Unknown"
        for s in vm.statuses:
            if "PowerState" in s.code:
                current_status = s.display_status
                break

        # Cập nhật tin nhắn cho người dùng đỡ sốt ruột
        await status_msg.edit(content=f"⏳ Đang khởi động... ({current_status}) - Lần kiểm tra thứ {i + 1}/20")

        if "running" in current_status.lower():
            await ctx.send("🎉 **SERVER ĐÃ ONLINE!** (Máy Azure đã bật)")
            await ctx.send(
                "💡 Lưu ý: Đợi thêm khoảng 30s-1 phút để Minecraft Server load xong map nhé. IP: `20.210.194.120`")
            return

    await ctx.send("⚠️ Có vẻ khởi động hơi lâu, bạn hãy tự kiểm tra lại sau nhé.")


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