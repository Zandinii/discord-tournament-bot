import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from datetime import datetime
from database.database import async_session
from database.models import (
    Achievement, PlayerAchievement, Player, Tournament,
    Match, MatchHistory, ChampionHistory
)
from utils.embeds import create_error_embed, create_success_embed
from sqlalchemy import select, func, and_, desc
import logging

logger = logging.getLogger('TournamentBot.Achievements')

class AchievementsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Predefinierade achievements
        self.default_achievements = [
            {
                'name': 'First Blood',
                'description': 'Vinn din första match',
                'icon': '🩸',
                'requirement_type': 'first_win',
                'requirement_value': 1
            },
            {
                'name': 'Champion',
                'description': 'Vinn din första turnering',
                'icon': '🏆',
                'requirement_type': 'tournament_win',
                'requirement_value': 1
            },
            {
                'name': 'Hot Streak',
                'description': 'Vinn 3 matcher i rad',
                'icon': '🔥',
                'requirement_type': 'win_streak',
                'requirement_value': 3
            },
            {
                'name': 'Unstoppable',
                'description': 'Vinn 5 matcher i rad',
                'icon': '⚡',
                'requirement_type': 'win_streak',
                'requirement_value': 5
            },
            {
                'name': 'Legendary',
                'description': 'Vinn 10 matcher i rad',
                'icon': '👑',
                'requirement_type': 'win_streak',
                'requirement_value': 10
            },
            {
                'name': 'Underdog',
                'description': 'Vinn mot någon med minst 200 högre ELO',
                'icon': '🐕',
                'requirement_type': 'underdog_win',
                'requirement_value': 200
            },
            {
                'name': 'Rising Star',
                'description': 'Nå 1200 ELO',
                'icon': '⭐',
                'requirement_type': 'elo_milestone',
                'requirement_value': 1200
            },
            {
                'name': 'Elite',
                'description': 'Nå 1500 ELO',
                'icon': '💎',
                'requirement_type': 'elo_milestone',
                'requirement_value': 1500
            },
            {
                'name': 'Grandmaster',
                'description': 'Nå 1800 ELO',
                'icon': '👑',
                'requirement_type': 'elo_milestone',
                'requirement_value': 1800
            },
            {
                'name': 'Veteran',
                'description': 'Spela 50 matcher',
                'icon': '🎖️',
                'requirement_type': 'matches_played',
                'requirement_value': 50
            },
            {
                'name': 'Tournament Regular',
                'description': 'Delta i 10 turneringar',
                'icon': '🎮',
                'requirement_type': 'tournaments_played',
                'requirement_value': 10
            },
            {
                'name': 'Triple Crown',
                'description': 'Vinn 3 turneringar',
                'icon': '👑',
                'requirement_type': 'tournament_win',
                'requirement_value': 3
            }
        ]
    
    async def initialize_achievements(self, guild_id: int):
        """Initiera default achievements för en guild"""
        async with async_session() as session:
            try:
                for ach_data in self.default_achievements:
                    # Kolla om achievement redan finns
                    existing = await session.execute(
                        select(Achievement).where(
                            Achievement.name == ach_data['name']
                        )
                    )
                    
                    if not existing.scalar_one_or_none():
                        achievement = Achievement(**ach_data)
                        session.add(achievement)
                
                await session.commit()
                logger.info(f'Initierade achievements för guild {guild_id}')
                
            except Exception as e:
                logger.error(f'Fel vid initiering av achievements: {e}', exc_info=True)
    
    async def check_and_award_achievements(self, user_id: int, guild_id: int, trigger_type: str, **kwargs):
        """Kolla och tilldela achievements baserat på trigger"""
        async with async_session() as session:
            try:
                player = await session.get(Player, user_id)
                if not player:
                    return
                
                # Hämta alla achievements som matchar trigger type
                achievements = await session.execute(
                    select(Achievement).where(
                        Achievement.requirement_type == trigger_type
                    )
                )
                achievements = achievements.scalars().all()
                
                for achievement in achievements:
                    # Kolla om spelaren redan har achievement
                    has_achievement = await session.execute(
                        select(PlayerAchievement).where(
                            PlayerAchievement.user_id == user_id,
                            PlayerAchievement.achievement_id == achievement.id,
                            PlayerAchievement.guild_id == guild_id
                        )
                    )
                    
                    if has_achievement.scalar_one_or_none():
                        continue  # Redan har achievement
                    
                    # Kolla om requirement är uppfyllt
                    earned = False
                    
                    if trigger_type == 'first_win':
                        earned = player.total_wins >= achievement.requirement_value
                    
                    elif trigger_type == 'win_streak':
                        earned = player.win_streak >= achievement.requirement_value
                    
                    elif trigger_type == 'tournament_win':
                        earned = player.tournaments_won >= achievement.requirement_value
                    
                    elif trigger_type == 'elo_milestone':
                        earned = player.elo_rating >= achievement.requirement_value
                    
                    elif trigger_type == 'matches_played':
                        earned = player.total_matches >= achievement.requirement_value
                    
                    elif trigger_type == 'tournaments_played':
                        earned = player.tournaments_participated >= achievement.requirement_value
                    
                    elif trigger_type == 'underdog_win':
                        # Kolla om senaste vinsten var en underdog win
                        elo_diff = kwargs.get('elo_difference', 0)
                        earned = elo_diff >= achievement.requirement_value
                    
                    # Tilldela achievement om earned
                    if earned:
                        player_achievement = PlayerAchievement(
                            user_id=user_id,
                            guild_id=guild_id,
                            achievement_id=achievement.id
                        )
                        session.add(player_achievement)
                        await session.commit()
                        
                        # Skicka notifikation
                        await self.notify_achievement(user_id, guild_id, achievement)
                        
                        logger.info(f'Spelare {user_id} fick achievement: {achievement.name}')
            
            except Exception as e:
                logger.error(f'Fel vid check av achievements: {e}', exc_info=True)
    
    async def notify_achievement(self, user_id: int, guild_id: int, achievement: Achievement):
        """Skicka notifikation om nytt achievement"""
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return
            
            member = guild.get_member(user_id)
            if not member:
                return
            
            # Skapa embed
            embed = discord.Embed(
                title="🎉 Achievement Unlocked!",
                description=f"**{achievement.icon} {achievement.name}**\n\n{achievement.description}",
                color=discord.Color.gold(),
                timestamp=datetime.utcnow()
            )
            
            embed.set_footer(text=f"Grattis {member.display_name}!")
            
            # Hitta första text channel
            channel = guild.text_channels[0] if guild.text_channels else None
            
            if channel:
                await channel.send(content=member.mention, embed=embed)
            
            # Tilldela roll om det finns
            if achievement.reward_role_name:
                role = discord.utils.get(guild.roles, name=achievement.reward_role_name)
                if role:
                    await member.add_roles(role)
                    logger.info(f'Tilldela roll {role.name} till {member.name}')
        
        except Exception as e:
            logger.error(f'Fel vid notifiering av achievement: {e}', exc_info=True)
    
    @app_commands.command(name="achievements", description="Visa dina achievements")
    @app_commands.describe(user="Användare att visa achievements för (valfritt)")
    async def achievements(
        self, 
        interaction: discord.Interaction,
        user: Optional[discord.User] = None
    ):
        """Visa achievements"""
        
        target_user = user or interaction.user
        
        async with async_session() as session:
            try:
                # Hämta spelarens achievements
                result = await session.execute(
                    select(PlayerAchievement, Achievement).join(
                        Achievement, PlayerAchievement.achievement_id == Achievement.id
                    ).where(
                        PlayerAchievement.user_id == target_user.id,
                        PlayerAchievement.guild_id == interaction.guild_id
                    ).order_by(PlayerAchievement.earned_at.desc())
                )
                
                player_achievements = result.all()
                
                # Hämta alla achievements
                all_achievements = await session.execute(
                    select(Achievement)
                )
                total_achievements = len(all_achievements.scalars().all())
                
                embed = discord.Embed(
                    title=f"🏆 {target_user.display_name}'s Achievements",
                    description=f"**{len(player_achievements)}/{total_achievements}** upplåsta",
                    color=discord.Color.gold(),
                    timestamp=datetime.utcnow()
                )
                
                if player_achievements:
                    achievements_text = ""
                    for player_ach, achievement in player_achievements[:15]:  # Max 15
                        achievements_text += f"{achievement.icon} **{achievement.name}**\n"
                        achievements_text += f"└ {achievement.description}\n"
                        achievements_text += f"   *<t:{int(player_ach.earned_at.timestamp())}:R>*\n\n"
                    
                    embed.add_field(
                        name="✅ Upplåsta Achievements",
                        value=achievements_text,
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="ℹ️ Inga Achievements Än",
                        value="Börja spela turneringar för att låsa upp achievements!",
                        inline=False
                    )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
            except Exception as e:
                logger.error(f'Fel vid hämtning av achievements: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte hämta achievements: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(name="achievements-list", description="Lista alla tillgängliga achievements")
    async def achievements_list(self, interaction: discord.Interaction):
        """Lista alla achievements"""
        
        async with async_session() as session:
            try:
                result = await session.execute(
                    select(Achievement).order_by(Achievement.requirement_value)
                )
                achievements = result.scalars().all()
                
                if not achievements:
                    await interaction.response.send_message(
                        embed=create_error_embed('Inga achievements hittades!'),
                        ephemeral=True
                    )
                    return
                
                embed = discord.Embed(
                    title="🏆 Alla Achievements",
                    description=f"Totalt **{len(achievements)}** achievements att låsa upp!",
                    color=discord.Color.gold(),
                    timestamp=datetime.utcnow()
                )
                
                # Gruppera per typ
                types = {}
                for ach in achievements:
                    if ach.requirement_type not in types:
                        types[ach.requirement_type] = []
                    types[ach.requirement_type].append(ach)
                
                type_names = {
                    'first_win': '🩸 Första Vinsten',
                    'win_streak': '🔥 Win Streaks',
                    'tournament_win': '🏆 Turneringsvinster',
                    'elo_milestone': '📈 ELO Milstolpar',
                    'matches_played': '🎮 Matcher Spelade',
                    'tournaments_played': '🎖️ Turneringsdeltagande',
                    'underdog_win': '🐕 Underdog'
                }
                
                for type_key, achs in types.items():
                    type_text = ""
                    for ach in achs:
                        type_text += f"{ach.icon} **{ach.name}**\n"
                        type_text += f"└ {ach.description}\n\n"
                    
                    embed.add_field(
                        name=type_names.get(type_key, type_key),
                        value=type_text,
                        inline=False
                    )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
            except Exception as e:
                logger.error(f'Fel vid listning av achievements: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte lista achievements: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(name="achievement-init", description="[ADMIN] Initiera achievements för servern")
    @app_commands.checks.has_permissions(administrator=True)
    async def achievement_init(self, interaction: discord.Interaction):
        """Initiera achievements"""
        
        await interaction.response.defer(ephemeral=True)
        
        await self.initialize_achievements(interaction.guild_id)
        
        await interaction.followup.send(
            embed=create_success_embed(
                f'✅ Initierade {len(self.default_achievements)} achievements!'
            ),
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(AchievementsCog(bot))