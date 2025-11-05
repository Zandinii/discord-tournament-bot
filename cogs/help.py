import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from datetime import datetime
import logging

logger = logging.getLogger('TournamentBot.Help')

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="help", description="Visa alla tillgängliga kommandon")
    @app_commands.describe(category="Välj en specifik kategori")
    async def help_command(
        self, 
        interaction: discord.Interaction,
        category: Optional[str] = None
    ):
        """Visa hjälp för kommandon"""
        
        if category:
            # Visa specifik kategori
            await self.show_category(interaction, category.lower())
        else:
            # Visa översikt
            await self.show_overview(interaction)

    @app_commands.command(name="quickstart", description="Snabbguide för att komma igång")
    async def quickstart(self, interaction: discord.Interaction):
        """Visa en snabbguide"""
        
        is_admin = interaction.user.guild_permissions.administrator
        
        embed = discord.Embed(
            title="🚀 Snabbguide - Tournament Bot",
            description="Så här kommer du igång!",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        
        if is_admin:
            embed.add_field(
                name="1️⃣ Setup (En gång)",
                value="Kör `/setup` för att initiera botten\n"
                      "Kör `/set-lobby [voice channel]` för att sätta lobby",
                inline=False
            )
            
            embed.add_field(
                name="2️⃣ Skapa Turnering",
                value="Använd `/tournament-create`\n"
                      "• Välj namn, mode (1v1/2v2/5v5), typ (single_elim/round_robin)\n"
                      "• Fyll i pris, starttid och beskrivning i modal\n"
                      "• Turnering postas i kanalen med signup-knappar!",
                inline=False
            )
            
            embed.add_field(
                name="3️⃣ Vänta på Anmälningar",
                value="Spelare anmäler sig via knapparna\n"
                      "För 2v2/5v5: Lag-captains anmäler sina lag",
                inline=False
            )
            
            embed.add_field(
                name="4️⃣ Starta Turnering",
                value="När tillräckligt många anmält sig:\n"
                      "`/tournament-start [tournament_id] eller vänta på automatisk start`\n"
                      "• Bracket genereras automatiskt\n"
                      "• Voice channels skapas\n"
                      "• Spelare flyttas automatiskt!",
                inline=False
            )
            
            embed.add_field(
                name="5️⃣ Följ Turneringen",
                value="• Se bracket: `/bracket [tournament_id]`\n"
                      "• Spelare rapporterar resultat själva\n"
                      "• Allt är automatiskt härifrån!",
                inline=False
            )
        else:
            embed.add_field(
                name="1️⃣ Anmäl dig till Turnering",
                value="När en turnering skapas, klicka på '**Anmäl dig ✅**' knappen\n"
                      "Eller använd `/signup [tournament_id]`",
                inline=False
            )
            
            embed.add_field(
                name="2️⃣ (Valfritt) Skapa Lag",
                value="För 2v2/5v5 turneringar:\n"
                      "• `/team-create [namn] [tag]`\n"
                      "• `/team-invite [@spelare]` för att bjuda in\n"
                      "• Endast captain kan anmäla laget!",
                inline=False
            )
            
            embed.add_field(
                name="3️⃣ Vänta på Start",
                value="När turneringen startar:\n"
                      "• Du får en notis\n"
                      "• Voice channels skapas\n"
                      "• Du flyttas automatiskt!",
                inline=False
            )
            
            embed.add_field(
                name="4️⃣ Spela Matchen",
                value="Se dina matcher: `/my-matches`\n"
                      "Gå in i lobby voice channel så flyttas du automatiskt!",
                inline=False
            )
            
            embed.add_field(
                name="5️⃣ Rapportera Resultat",
                value="Efter matchen:\n"
                      "`/report-win [match_id] [dina_poäng] [opponents_poäng]`\n"
                      "• Din opponent måste bekräfta\n"
                      "• ELO uppdateras automatiskt\n"
                      "• Nästa match sätts upp automatiskt!",
                inline=False
            )
        
        embed.add_field(
            name="📊 Se Statistik",
            value="• `/my-stats` - Din statistik\n"
                  "• `/leaderboard` - Topp-spelare\n"
                  "• `/profile [@spelare]` - Annan spelares profil",
            inline=False
        )
        
        embed.set_footer(text="Använd /help för att se alla kommandon!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def show_overview(self, interaction: discord.Interaction):
        """Visa översikt av alla kategorier"""
        
        embed = discord.Embed(
            title="🏆 Tournament Bot - Hjälp",
            description="Välkommen till Tournament Bot! Här är en översikt av alla funktioner.",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        
        # Admin kommandon
        embed.add_field(
            name="👑 Admin Kommandon",
            value="Hantera turneringar och server-inställningar\n"
                  "`/help category:admin` för detaljer",
            inline=False
        )
        
        # Spelare kommandon
        embed.add_field(
            name="🎮 Spelare Kommandon",
            value="Anmäl dig, se statistik och matcher\n"
                  "`/help category:player` för detaljer",
            inline=False
        )
        
        # Lag kommandon
        embed.add_field(
            name="👥 Lag Kommandon",
            value="Skapa och hantera lag\n"
                  "`/help category:team` för detaljer",
            inline=False
        )
        
        # Match kommandon
        embed.add_field(
            name="⚔️ Match Kommandon",
            value="Rapportera resultat och se match-info\n"
                  "`/help category:match` för detaljer",
            inline=False
        )
        
        # Turnering kommandon
        embed.add_field(
            name="🏅 Turnering Kommandon",
            value="Visa bracket och turnerings-info\n"
                  "`/help category:tournament` för detaljer",
            inline=False
        )
        
        embed.set_footer(text="Använd /help category:<kategori> för att se alla kommandon i en kategori")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def show_category(self, interaction: discord.Interaction, category: str):
        """Visa kommandon för en specifik kategori"""
        
        if category == "admin":
            embed = discord.Embed(
                title="👑 Admin Kommandon",
                description="Kommandon för att hantera turneringar (kräver Administrator-rättigheter)",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            
            commands_list = [
                ("setup", "Initiera bot-inställningar för servern"),
                ("tournament-create", "Skapa en ny turnering med wizard"),
                ("tournament-start", "Starta en turnering och generera bracket"),
                ("tournament-list", "Lista alla turneringar (kan filtrera på status)"),
                ("tournament-delete", "Ta bort en turnering permanent"),
                ("tournament-cancel", "Avbryt en pågående turnering"),
                ("setup-match", "Manuellt skapa voice channels för en match"),
                ("cleanup-match", "Ta bort voice channels för en match"),
                ("cleanup-all", "Emergency cleanup av alla match-channels"),
                ("set-lobby", "Sätt lobby voice channel för servern"),
                ("resolve-dispute", "Lös en tvistad match manuellt"),
            ]
            
            for cmd, desc in commands_list:
                embed.add_field(
                    name=f"/{cmd}",
                    value=desc,
                    inline=False
                )
        
        elif category == "player":
            embed = discord.Embed(
                title="🎮 Spelare Kommandon",
                description="Kommandon för spelare att delta i turneringar",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            commands_list = [
                ("signup", "Anmäl dig till en turnering (använd tournament ID)"),
                ("withdraw", "Dra dig ur en turnering"),
                ("my-tournaments", "Visa dina pågående turneringar"),
                ("my-matches", "Visa dina aktiva matcher"),
                ("my-stats", "Visa din personliga statistik och ELO"),
                ("profile", "Visa en spelares profil och statistik"),
                ("leaderboard", "Visa top 10 spelare (ELO, vinster, etc)"),
            ]
            
            for cmd, desc in commands_list:
                embed.add_field(
                    name=f"/{cmd}",
                    value=desc,
                    inline=False
                )
        
        elif category == "team":
            embed = discord.Embed(
                title="👥 Lag Kommandon",
                description="Kommandon för att skapa och hantera lag",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            commands_list = [
                ("team-create", "Skapa ett nytt lag (du blir captain)"),
                ("team-invite", "Bjud in en spelare till ditt lag"),
                ("team-leave", "Lämna ditt nuvarande lag"),
                ("team-info", "Visa information om ett lag"),
                ("team-list", "Lista alla lag på servern"),
                ("team-delete", "Ta bort ditt lag (endast captain)"),
            ]
            
            for cmd, desc in commands_list:
                embed.add_field(
                    name=f"/{cmd}",
                    value=desc,
                    inline=False
                )
            
            embed.add_field(
                name="ℹ️ Lag i Turneringar",
                value="För **2v2** och **5v5** turneringar måste du vara i ett lag.\n"
                      "Endast captain kan anmäla laget till turneringar.",
                inline=False
            )
        
        elif category == "match":
            embed = discord.Embed(
                title="⚔️ Match Kommandon",
                description="Kommandon för att hantera matcher",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            
            commands_list = [
                ("report-win", "Rapportera att du/ditt lag vann en match"),
                ("match-info", "Visa detaljerad information om en match"),
                ("my-matches", "Visa alla dina aktiva matcher"),
            ]
            
            for cmd, desc in commands_list:
                embed.add_field(
                    name=f"/{cmd}",
                    value=desc,
                    inline=False
                )
            
            embed.add_field(
                name="ℹ️ Match Flow",
                value="1. Se dina matcher med `/my-matches`\n"
                      "2. Spela matchen\n"
                      "3. Rapportera vinst med `/report-win [match_id]`\n"
                      "4. Opponent bekräftar eller avvisar resultatet\n"
                      "5. ELO uppdateras och nästa match sätts upp automatiskt!",
                inline=False
            )
        
        elif category == "tournament":
            embed = discord.Embed(
                title="🏅 Turnering Kommandon",
                description="Kommandon för att visa turnerings-information",
                color=discord.Color.purple(),
                timestamp=datetime.utcnow()
            )
            
            commands_list = [
                ("bracket", "Visa turnerings-bracket (kan välja specifikt round)"),
                ("tournament-list", "Lista alla turneringar på servern"),
                ("my-tournaments", "Visa dina pågående turneringar"),
            ]
            
            for cmd, desc in commands_list:
                embed.add_field(
                    name=f"/{cmd}",
                    value=desc,
                    inline=False
                )
            
            embed.add_field(
                name="ℹ️ Turneringstyper",
                value="**Game Modes:**\n"
                      "• `1v1` - Individuella spelare\n"
                      "• `2v2` - Lag med 2 spelare\n"
                      "• `5v5` - Lag med 5 spelare\n\n"
                      "**Bracket Types:**\n"
                      "• `single_elim` - Single Elimination\n"
                      "• `round_robin` - Alla möter alla\n"
                      "• `double_elim` - Double Elimination (kommer snart)",
                inline=False
            )
        
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Fel",
                    description=f"Kategorin `{category}` finns inte!\n\n"
                               "Tillgängliga kategorier: `admin`, `player`, `team`, `match`, `tournament`",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
            return
        
        embed.set_footer(text="Använd /help för att se alla kategorier")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))