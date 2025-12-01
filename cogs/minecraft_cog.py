import discord
from discord import app_commands
from discord.ext import commands
import logging
import asyncio
from mcstatus import JavaServer
from azure.mgmt.compute import ComputeManagementClient
from azure.identity import ClientSecretCredential
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

class MinecraftCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    mc = app_commands.Group(name="mc", description="Các lệnh quản lý Minecraft")

    @mc.command(name="restart", description="Khởi động lại Java Server (Không tắt máy Azure)")
    async def restart(self, interaction: discord.Interaction):
        await interaction.response.defer()
        status = await get_vm_status_async()
        if "running" not in status.lower():
            await interaction.followup.send("Máy Azure đang tắt, không thể restart.")
            return
        
        await interaction.followup.send("**Đang khởi động lại Server Minecraft...**\n(Map sẽ được lưu, vui lòng đợi khoảng 30-60 giây)")
        try:
            def run_restart_script_sync():
                restart_script = ['screen -S mc -p 0 -X stuff "stop^M"', 'sleep 20', '/home/holetinnghia/minecraft/start.sh']
                run_command_parameters = {'command_id': 'RunShellScript', 'script': restart_script}
                compute_client.virtual_machines.begin_run_command(RESOURCE_GROUP, VM_NAME, run_command_parameters)

            await asyncio.to_thread(run_restart_script_sync)
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
            def run_console_command_sync():
                shell_script = [f"sudo -u holetinnghia screen -S mc -p 0 -X stuff '{cmd_clean}\r'"]
                run_command_parameters = {'command_id': 'RunShellScript', 'script': shell_script}
                compute_client.virtual_machines.begin_run_command(RESOURCE_GROUP, VM_NAME, run_command_parameters)

            await asyncio.to_thread(run_console_command_sync)
            await interaction.followup.send(f"Đã gửi lệnh: `/{cmd_clean}`")
        except Exception as e:
            logging.error(f"Lỗi khi gửi lệnh console: {e}")
            await interaction.followup.send(f"❌ Lỗi: {str(e)}")

async def setup(bot: commands.Bot):
    await bot.add_cog(MinecraftCog(bot))