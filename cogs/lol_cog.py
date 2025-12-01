import discord
from discord import app_commands
from discord.ext import commands
import logging
from riotwatcher import LolWatcher, RiotWatcher, ApiError
import os
import asyncio

RIOT_API_KEY = os.getenv('RIOT_API_KEY')

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

            def get_lol_data_sync():
                account_data = self.riot_watcher.account.by_riot_id(routing, game_name, tag_line)
                puuid = account_data['puuid']
                summoner_data = self.lol_watcher.summoner.by_puuid(region, puuid)
                encrypted_summoner_id = summoner_data.get('id')
                
                if not encrypted_summoner_id:
                    logging.warning(f"Account Zombie: {riot_id}. Đang đi đường vòng...")
                    matches = self.lol_watcher.match.matchlist_by_puuid(match_routing, puuid, count=1)
                    if not matches:
                        return None, None, None, "Acc lỗi ID và chưa đánh trận nào. Bó tay."
                    
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
                    last_match_info = "Không có dữ liệu"

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
                
                return summoner_data, rank_display, last_match_info, None

            summoner_data, rank_display, last_match_info, error_message = await asyncio.to_thread(get_lol_data_sync)

            if error_message:
                await interaction.followup.send(f"❌ {error_message}")
                return

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

async def setup(bot: commands.Bot):
    await bot.add_cog(LOLCog(bot))