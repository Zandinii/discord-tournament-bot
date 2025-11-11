import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from datetime import datetime
from database.database import async_session
from database.models import (
    Team, TeamMember, Player, Tournament, TournamentParticipant,
    TournamentStatus, ParticipantType
)
from utils.embeds import create_error_embed, create_success_embed
from sqlalchemy import select, and_
import logging

logger = logging.getLogger('TournamentBot.Team')

class TeamInviteView(discord.ui.View):
    """View för att acceptera/avvisa lag-inbjudningar"""
    
    def __init__(self, team_id: int, inviter_id: int, invited_id: int):
        super().__init__(timeout=300)  # 5 minuter
        self.team_id = team_id
        self.inviter_id = inviter_id
        self.invited_id = invited_id
    
    @discord.ui.button(label='Acceptera ✅', style=discord.ButtonStyle.green)
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Acceptera inbjudan"""
        
        if interaction.user.id != self.invited_id:
            await interaction.response.send_message(
                embed=create_error_embed('Denna inbjudan är inte till dig!'),
                ephemeral=True
            )
            return
        
        async with async_session() as session:
            try:
                team = await session.get(Team, self.team_id)
                
                if not team:
                    await interaction.response.send_message(
                        embed=create_error_embed('Laget hittades inte!'),
                        ephemeral=True
                    )
                    return
                
                # Kolla om användaren redan är i ett lag
                existing = await session.execute(
                    select(TeamMember).where(
                        TeamMember.user_id == self.invited_id,
                        TeamMember.team_id == Team.id
                    ).join(Team).where(Team.guild_id == interaction.guild_id)
                )
                
                if existing.scalar_one_or_none():
                    await interaction.response.send_message(
                        embed=create_error_embed('Du är redan medlem i ett lag!'),
                        ephemeral=True
                    )
                    return
                
                # Skapa/uppdatera spelarprofil
                player = await session.get(Player, self.invited_id)
                if not player:
                    player = Player(
                        user_id=self.invited_id,
                        guild_id=interaction.guild_id,
                        username=interaction.user.name
                    )
                    session.add(player)
                
                # Lägg till i lag
                member = TeamMember(
                    team_id=self.team_id,
                    user_id=self.invited_id
                )
                session.add(member)
                await session.commit()
                
                # Disable buttons
                for item in self.children:
                    item.disabled = True
                await interaction.message.edit(view=self)
                
                await interaction.response.send_message(
                    embed=create_success_embed(
                        f'✅ Du är nu medlem i **{team.name}**!'
                    )
                )
                
                logger.info(f'{interaction.user.name} gick med i lag {team.name}')
                
            except Exception as e:
                logger.error(f'Fel vid acceptering av inbjudan: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte gå med i laget: {str(e)}'),
                    ephemeral=True
                )
    
    @discord.ui.button(label='Avvisa ❌', style=discord.ButtonStyle.red)
    async def deny_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Avvisa inbjudan"""
        
        if interaction.user.id != self.invited_id:
            await interaction.response.send_message(
                embed=create_error_embed('Denna inbjudan är inte till dig!'),
                ephemeral=True
            )
            return
        
        # Disable buttons
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)
        
        await interaction.response.send_message(
            embed=create_success_embed('Du avvisade inbjudan.'),
            ephemeral=True
        )

class TeamCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="team-create", description="Skapa ett lag")
    @app_commands.describe(
        name="Lagets namn",
        tag="Lagets tag (valfritt, max 10 tecken)"
    )
    async def team_create(self, interaction: discord.Interaction, name: str, tag: Optional[str] = None):
        """Skapa ett nytt lag"""
        
        if len(name) > 100:
            await interaction.response.send_message(
                embed=create_error_embed('Lagets namn kan max vara 100 tecken!'),
                ephemeral=True
            )
            return
        
        if tag and len(tag) > 10:
            await interaction.response.send_message(
                embed=create_error_embed('Lagets tag kan max vara 10 tecken!'),
                ephemeral=True
            )
            return
        
        async with async_session() as session:
            try:
                # Kolla om användaren redan är captain
                existing_captain = await session.execute(
                    select(Team).where(
                        Team.captain_id == interaction.user.id,
                        Team.guild_id == interaction.guild_id
                    )
                )
                
                if existing_captain.scalar_one_or_none():
                    await interaction.response.send_message(
                        embed=create_error_embed('Du är redan captain för ett lag!'),
                        ephemeral=True
                    )
                    return
                
                # Kolla om användaren redan är medlem i ett lag
                existing_member = await session.execute(
                    select(TeamMember).where(
                        TeamMember.user_id == interaction.user.id
                    ).join(Team).where(Team.guild_id == interaction.guild_id)
                )
                
                if existing_member.scalar_one_or_none():
                    await interaction.response.send_message(
                        embed=create_error_embed('Du är redan medlem i ett lag!'),
                        ephemeral=True
                    )
                    return
                
                # Skapa lag
                team = Team(
                    guild_id=interaction.guild_id,
                    name=name,
                    tag=tag,
                    captain_id=interaction.user.id
                )
                session.add(team)
                
                # Lägg till captain som medlem
                member = TeamMember(
                    team_id=team.id,
                    user_id=interaction.user.id
                )
                
                # Skapa/uppdatera spelarprofil
                player = await session.get(Player, interaction.user.id)
                if not player:
                    player = Player(
                        user_id=interaction.user.id,
                        guild_id=interaction.guild_id,
                        username=interaction.user.name
                    )
                    session.add(player)
                
                await session.flush()  # Få team.id
                member.team_id = team.id
                session.add(member)
                
                await session.commit()
                await session.refresh(team)
                
                embed = discord.Embed(
                    title="🎉 Lag Skapat!",
                    description=f"**{name}** {f'[{tag}]' if tag else ''} har skapats!",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
                
                embed.add_field(
                    name="👑 Captain",
                    value=interaction.user.mention,
                    inline=True
                )
                
                embed.add_field(
                    name="🆔 Team ID",
                    value=str(team.id),
                    inline=True
                )
                
                embed.set_footer(text="Använd /team-invite för att bjuda in medlemmar!")
                
                await interaction.response.send_message(embed=embed)
                
                logger.info(f'{interaction.user.name} skapade lag: {name}')
                
            except Exception as e:
                logger.error(f'Fel vid skapande av lag: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte skapa lag: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(name="team-invite", description="Bjud in någon till ditt lag")
    @app_commands.describe(user="Användaren att bjuda in")
    async def team_invite(self, interaction: discord.Interaction, user: discord.User):
        """Bjud in användare till lag"""
        
        if user.id == interaction.user.id:
            await interaction.response.send_message(
                embed=create_error_embed('Du kan inte bjuda in dig själv!'),
                ephemeral=True
            )
            return
        
        if user.bot:
            await interaction.response.send_message(
                embed=create_error_embed('Du kan inte bjuda in bottar!'),
                ephemeral=True
            )
            return
        
        async with async_session() as session:
            try:
                # Hitta användarens lag
                result = await session.execute(
                    select(Team).where(
                        Team.captain_id == interaction.user.id,
                        Team.guild_id == interaction.guild_id
                    )
                )
                team = result.scalar_one_or_none()
                
                if not team:
                    await interaction.response.send_message(
                        embed=create_error_embed('Du är inte captain för något lag!'),
                        ephemeral=True
                    )
                    return
                
                # Kolla om användaren redan är i ett lag
                existing = await session.execute(
                    select(TeamMember).where(
                        TeamMember.user_id == user.id
                    ).join(Team).where(Team.guild_id == interaction.guild_id)
                )
                
                if existing.scalar_one_or_none():
                    await interaction.response.send_message(
                        embed=create_error_embed(f'{user.mention} är redan medlem i ett lag!'),
                        ephemeral=True
                    )
                    return
                
                # Skicka inbjudan
                view = TeamInviteView(team.id, interaction.user.id, user.id)
                
                embed = discord.Embed(
                    title="📨 Lag-inbjudan",
                    description=f"{user.mention}, du har blivit inbjuden att gå med i **{team.name}** {f'[{team.tag}]' if team.tag else ''}!",
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                
                embed.add_field(
                    name="👑 Captain",
                    value=interaction.user.mention,
                    inline=True
                )
                
                embed.set_footer(text="Inbjudan går ut om 5 minuter")
                
                await interaction.response.send_message(
                    content=user.mention,
                    embed=embed,
                    view=view
                )
                
                logger.info(f'{interaction.user.name} bjöd in {user.name} till lag {team.name}')
                
            except Exception as e:
                logger.error(f'Fel vid inbjudan: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte skicka inbjudan: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(name="team-leave", description="Lämna ditt lag")
    async def team_leave(self, interaction: discord.Interaction):
        """Lämna lag"""
        
        async with async_session() as session:
            try:
                # Hitta användarens lag
                result = await session.execute(
                    select(TeamMember, Team).join(
                        Team, TeamMember.team_id == Team.id
                    ).where(
                        TeamMember.user_id == interaction.user.id,
                        Team.guild_id == interaction.guild_id
                    )
                )
                
                member_team = result.first()
                
                if not member_team:
                    await interaction.response.send_message(
                        embed=create_error_embed('Du är inte medlem i något lag!'),
                        ephemeral=True
                    )
                    return
                
                member, team = member_team
                
                # Kolla om användaren är captain
                if team.captain_id == interaction.user.id:
                    await interaction.response.send_message(
                        embed=create_error_embed(
                            'Du är captain! Använd `/team-delete` för att ta bort laget eller `/team-transfer` för att överföra captain-rollen.'
                        ),
                        ephemeral=True
                    )
                    return
                
                # Ta bort medlem
                await session.delete(member)
                await session.commit()
                
                await interaction.response.send_message(
                    embed=create_success_embed(f'Du har lämnat **{team.name}**'),
                    ephemeral=True
                )
                
                logger.info(f'{interaction.user.name} lämnade lag {team.name}')
                
            except Exception as e:
                logger.error(f'Fel vid lämnande av lag: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte lämna laget: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(name="team-info", description="Visa information om ett lag")
    @app_commands.describe(team_name="Lagets namn (valfritt, visar ditt lag om inget anges)")
    async def team_info(self, interaction: discord.Interaction, team_name: Optional[str] = None):
        """Visa lag-information"""
        
        async with async_session() as session:
            try:
                if team_name:
                    # Sök efter lag med namn
                    result = await session.execute(
                        select(Team).where(
                            Team.name.ilike(f'%{team_name}%'),
                            Team.guild_id == interaction.guild_id
                        )
                    )
                    team = result.scalar_one_or_none()
                else:
                    # Hitta användarens lag
                    result = await session.execute(
                        select(Team).join(
                            TeamMember, Team.id == TeamMember.team_id
                        ).where(
                            TeamMember.user_id == interaction.user.id,
                            Team.guild_id == interaction.guild_id
                        )
                    )
                    team = result.scalar_one_or_none()
                
                if not team:
                    await interaction.response.send_message(
                        embed=create_error_embed('Laget hittades inte!'),
                        ephemeral=True
                    )
                    return
                
                # Hämta medlemmar
                members_result = await session.execute(
                    select(TeamMember).where(TeamMember.team_id == team.id)
                )
                members = members_result.scalars().all()
                
                embed = discord.Embed(
                    title=f"🏆 {team.name} {f'[{team.tag}]' if team.tag else ''}",
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                
                # Captain
                embed.add_field(
                    name="👑 Captain",
                    value=f"<@{team.captain_id}>",
                    inline=True
                )
                
                # Stats
                win_rate = (team.total_wins / (team.total_wins + team.total_losses) * 100) if (team.total_wins + team.total_losses) > 0 else 0
                
                embed.add_field(
                    name="📊 Statistik",
                    value=f"**ELO:** {team.elo_rating}\n"
                          f"**Vinster:** {team.total_wins}\n"
                          f"**Förluster:** {team.total_losses}\n"
                          f"**Win Rate:** {win_rate:.1f}%",
                    inline=True
                )
                
                # Medlemmar
                members_text = "\n".join([f"<@{m.user_id}>" for m in members])
                embed.add_field(
                    name=f"👥 Medlemmar ({len(members)})",
                    value=members_text or "Inga medlemmar",
                    inline=False
                )
                
                embed.set_footer(text=f"Team ID: {team.id} | Skapat {team.created_at.strftime('%Y-%m-%d')}")
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
            except Exception as e:
                logger.error(f'Fel vid hämtning av lag-info: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte hämta lag-info: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(name="team-list", description="Visa alla lag på servern")
    async def team_list(self, interaction: discord.Interaction):
        """Lista alla lag"""
        
        async with async_session() as session:
            try:
                result = await session.execute(
                    select(Team).where(
                        Team.guild_id == interaction.guild_id
                    ).order_by(Team.elo_rating.desc())
                )
                teams = result.scalars().all()
                
                if not teams:
                    await interaction.response.send_message(
                        embed=create_error_embed('Inga lag hittades!'),
                        ephemeral=True
                    )
                    return
                
                embed = discord.Embed(
                    title="🏆 Alla Lag",
                    color=discord.Color.gold(),
                    timestamp=datetime.utcnow()
                )
                
                for i, team in enumerate(teams[:15], 1):  # Max 15
                    # Räkna medlemmar
                    members_result = await session.execute(
                        select(TeamMember).where(TeamMember.team_id == team.id)
                    )
                    member_count = len(members_result.scalars().all())
                    
                    embed.add_field(
                        name=f"{i}. {team.name} {f'[{team.tag}]' if team.tag else ''}",
                        value=f"**ELO:** {team.elo_rating} | **Medlemmar:** {member_count}\n"
                              f"**Captain:** <@{team.captain_id}>",
                        inline=False
                    )
                
                embed.set_footer(text=f"Totalt {len(teams)} lag")
                
                await interaction.response.send_message(embed=embed)
                
            except Exception as e:
                logger.error(f'Fel vid listning av lag: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte lista lag: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(name="team-delete", description="Ta bort ditt lag (endast captain)")
    async def team_delete(self, interaction: discord.Interaction):
        """Ta bort lag (endast captain)"""
        
        async with async_session() as session:
            try:
                team = await session.execute(
                    select(Team).where(
                        Team.captain_id == interaction.user.id,
                        Team.guild_id == interaction.guild_id
                    )
                )
                team = team.scalar_one_or_none()
                
                if not team:
                    await interaction.response.send_message(
                        embed=create_error_embed('Du är inte captain för något lag!'),
                        ephemeral=True
                    )
                    return
                
                team_name = team.name
                await session.delete(team)
                await session.commit()
                
                await interaction.response.send_message(
                    embed=create_success_embed(f'Lag **{team_name}** har tagits bort!'),
                    ephemeral=True
                )
                
                logger.info(f'{interaction.user.name} tog bort lag {team_name}')
                
            except Exception as e:
                logger.error(f'Fel vid borttagning av lag: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte ta bort laget: {str(e)}'),
                    ephemeral=True
                )

    @app_commands.command(name="team-transfer", description="Överför captain-rollen till en annan lagmedlem")
    @app_commands.describe(new_captain="Den nya captainen")
    async def team_transfer(self, interaction: discord.Interaction, new_captain: discord.User):
        """Överför captain-rollen till en annan spelare i laget"""
        
        if new_captain.bot:
            await interaction.response.send_message(
                embed=create_error_embed('Du kan inte göra en bot till captain!'),
                ephemeral=True
            )
            return
        
        if new_captain.id == interaction.user.id:
            await interaction.response.send_message(
                embed=create_error_embed('Du är redan captain!'),
                ephemeral=True
            )
            return
        
        async with async_session() as session:
            try:
                # Hitta användarens lag där de är captain
                result = await session.execute(
                    select(Team).where(
                        Team.captain_id == interaction.user.id,
                        Team.guild_id == interaction.guild_id
                    )
                )
                team = result.scalar_one_or_none()
                
                if not team:
                    await interaction.response.send_message(
                        embed=create_error_embed('Du är inte captain för något lag!'),
                        ephemeral=True
                    )
                    return
                
                # Kolla om den nya captainen är i laget
                member_check = await session.execute(
                    select(TeamMember).where(
                        TeamMember.team_id == team.id,
                        TeamMember.user_id == new_captain.id
                    )
                )
                
                if not member_check.scalar_one_or_none():
                    await interaction.response.send_message(
                        embed=create_error_embed(f'{new_captain.mention} är inte medlem i ditt lag!'),
                        ephemeral=True
                    )
                    return
                
                # Överför captain-rollen
                old_captain_name = interaction.user.name
                team.captain_id = new_captain.id
                await session.commit()
                
                embed = discord.Embed(
                    title="👑 Captain Överförd!",
                    description=f"Captain-rollen för **{team.name}** har överförts!",
                    color=discord.Color.gold(),
                    timestamp=datetime.utcnow()
                )
                
                embed.add_field(
                    name="Tidigare Captain",
                    value=interaction.user.mention,
                    inline=True
                )
                
                embed.add_field(
                    name="Ny Captain",
                    value=new_captain.mention,
                    inline=True
                )
                
                await interaction.response.send_message(embed=embed)
                
                # Meddela nya captainen
                try:
                    dm_embed = discord.Embed(
                        title="👑 Du är nu Captain!",
                        description=f"Du har blivit utsedd till captain för **{team.name}** {f'[{team.tag}]' if team.tag else ''}",
                        color=discord.Color.gold()
                    )
                    dm_embed.add_field(
                        name="Dina nya rättigheter",
                        value="• Bjuda in nya medlemmar\n"
                            "• Anmäla laget till turneringar\n"
                            "• Överföra captain-rollen\n"
                            "• Ta bort laget",
                        inline=False
                    )
                    await new_captain.send(embed=dm_embed)
                except:
                    pass
                
                logger.info(f'{old_captain_name} överförde captain till {new_captain.name} för lag {team.name}')
                
            except Exception as e:
                logger.error(f'Fel vid överföring av captain: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte överföra captain: {str(e)}'),
                    ephemeral=True
                )

async def setup(bot):
    await bot.add_cog(TeamCog(bot))