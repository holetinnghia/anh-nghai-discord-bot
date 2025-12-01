import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import logging
from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
import os

RESOURCE_GROUP = 'MinecraftServer_group'
VM_NAME = 'MinecraftServer'
AZURE_SUBSCRIPTION_ID = os.getenv('AZURE_SUBSCRIPTION_ID')
AZURE_CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
AZURE_CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')
AZURE_TENANT_ID = os.getenv('AZURE_TENANT_ID')

credential = ClientSecretCredential(
    tenant_id=AZURE_TENANT_ID,
    client_id=AZURE_CLIENT_ID,
    client_secret=AZURE_CLIENT_SECRET,
)
compute_client = ComputeManagementClient(credential, AZURE_SUBSCRIPTION_ID)

async def get_vm_status_async():
    try:
        vm = await asyncio.to_thread(compute_client.virtual_machines.instance_view, RESOURCE_GROUP, VM_NAME)
        for s in vm.statuses:
            if "PowerState" in s.code:
                return s.display_status
        return "Unknown"
    except Exception as e:
        logging.error(f"Lỗi khi lấy trạng thái VM: {e}")
        return f"Error: {str(e)}"

class AzureCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    azure = app_commands.Group(name="azure", description="Các lệnh quản lý Azure")

    @azure.command(name="status", description="Kiểm tra xem máy ảo Azure đang Bật hay Tắt")
    async def status(self, interaction: discord.Interaction):
        await interaction.response.defer()
        current_status = await get_vm_status_async()
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
            def run_command_sync():
                run_command_parameters = {'command_id': 'RunShellScript', 'script': ['free -h && echo "---" && uptime']}
                poller = compute_client.virtual_machines.begin_run_command(RESOURCE_GROUP, VM_NAME, run_command_parameters)
                return poller.result().value[0].message

            output = await asyncio.to_thread(run_command_sync)
            await interaction.followup.send(f"**Tình trạng sức khỏe VPS:**\n```\n{output}\n```")
        except Exception as e:
            logging.error(f"Lỗi khi kiểm tra health: {e}")
            await interaction.followup.send(f"❌ Máy ảo đang tắt hoặc lỗi: {str(e)}")

    @azure.command(name="start", description="Khởi động Server Minecraft Azure")
    async def start(self, interaction: discord.Interaction):
        await interaction.response.defer()
        status = await get_vm_status_async()
        if "running" in status.lower():
            await interaction.followup.send(f"**Server đang chạy rồi!**\nIP: `20.210.194.120`")
            return
        
        msg = await interaction.followup.send(f"**Đang kích hoạt máy ảo Azure...**\n(Trạng thái hiện tại: {status})")
        try:
            await asyncio.to_thread(compute_client.virtual_machines.begin_start, RESOURCE_GROUP, VM_NAME)
            
            for i in range(20):
                await asyncio.sleep(10)
                current_status = await get_vm_status_async()
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
        status = await get_vm_status_async()
        if "running" not in status.lower():
            await interaction.followup.send(f"**Server đang tắt rồi** ({status}). Không cần tắt nữa!")
            return
        
        await interaction.followup.send("**Đang gửi tín hiệu tắt an toàn...**")
        try:
            def run_stop_command_sync():
                run_command_parameters = {
                    'command_id': 'RunShellScript',
                    'script': [
                        'chmod +x /home/holetinnghia/manual_stop.sh',
                        'nohup /home/holetinnghia/manual_stop.sh > /dev/null 2>&1 &'
                    ]
                }
                compute_client.virtual_machines.begin_run_command(RESOURCE_GROUP, VM_NAME, run_command_parameters)

            await asyncio.to_thread(run_stop_command_sync)
            await interaction.followup.send("**Đã kích hoạt quy trình tự hủy!**\nServer sẽ lưu map và tắt hẳn sau khoảng 1 phút nữa.")
        except Exception as e:
            logging.error(f"Lỗi khi gửi lệnh tắt: {e}")
            await interaction.followup.send(f"❌ Lỗi khi gửi lệnh tắt: {str(e)}")

async def setup(bot: commands.Bot):
    await bot.add_cog(AzureCog(bot))