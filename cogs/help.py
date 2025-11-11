import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from datetime import datetime
import logging
from utils.embeds import create_error_embed

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
        has_tournament_admin = discord.utils.get(interaction.user.roles, name="Tournament Admin") is not None
        
        embed = discord.Embed(
            title="🚀 Snabbguide - Tournament Bot",
            description="Så här kommer du igång!",
            color=0xFFD700,
            timestamp=datetime.utcnow()
        )
        
        if is_admin or has_tournament_admin:
            embed.add_field(
                name="1️⃣ Setup (En gång)",
                value="Kör `/setup` för att initiera botten\n"
                      "Kör `/set-lobby [voice channel]` för att sätta lobby\n"
                      "Kör `/set-moderation-channel [text channel]` för moderation logs",
                inline=False
            )
            
            embed.add_field(
                name="2️⃣ Skapa Turnering",
                value="Använd `/tournament-create`\n"
                      "• Välj namn, mode (1v1/2v2/5v5), typ (single_elim/round_robin)\n"
                      "• Fyll i pris, starttid, kartor och beskrivning i modal\n"
                      "• Turnering postas i kanalen med signup-knappar!",
                inline=False
            )
            
            embed.add_field(
                name="3️⃣ Vänta på Anmälningar",
                value="Spelare anmäler sig via knapparna eller `/signup`\n"
                      "För 2v2/5v5: Lag-captains anmäler sina lag\n"
                      "**OBS:** Spelare måste sätta sin ELO först med `/set-elo`",
                inline=False
            )
            
            embed.add_field(
                name="4️⃣ Starta Turnering",
                value="När tillräckligt många anmält sig:\n"
                      "`/tournament-start [tournament_id]` eller vänta på automatisk start\n"
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
            
            embed.add_field(
                name="🛡️ Moderation",
                value="• `/warn [user] [reason]` - Varna spelare\n"
                      "• `/ban-player [user] [reason]` - Stäng av spelare\n"
                      "• 3 varningar = automatisk 2 turneringar ban",
                inline=False
            )
        else:
            embed.add_field(
                name="1️⃣ Sätt Din ELO (VIKTIGT!)",
                value="**DU MÅSTE GÖRA DETTA FÖRST:**\n"
                      "Använd `/set-elo` och välj:\n"
                      "• **Premier**: Din CS2 Premier ELO (0-35000)\n"
                      "• **Faceit**: Din Faceit Level (1-10)\n\n"
                      "Detta krävs för att anmäla dig till turneringar!",
                inline=False
            )
            
            embed.add_field(
                name="2️⃣ Anmäl dig till Turnering",
                value="När en turnering skapas, klicka på '**Anmäl dig ✅**' knappen\n"
                      "Eller använd `/signup [tournament_id]`",
                inline=False
            )
            
            embed.add_field(
                name="3️⃣ (Valfritt) Skapa Lag",
                value="För 2v2/5v5 turneringar:\n"
                      "• `/team-create [namn] [tag]`\n"
                      "• `/team-invite [@spelare]` för att bjuda in\n"
                      "• Endast captain kan anmäla laget!",
                inline=False
            )
            
            embed.add_field(
                name="4️⃣ Vänta på Start",
                value="När turneringen startar:\n"
                      "• Du får en notis\n"
                      "• Voice channels skapas\n"
                      "• Du flyttas automatiskt!",
                inline=False
            )
            
            embed.add_field(
                name="5️⃣ Spela Matchen",
                value="Se dina matcher: `/my-matches`\n"
                      "Gå in i lobby voice channel så flyttas du automatiskt!",
                inline=False
            )
            
            embed.add_field(
                name="6️⃣ Rapportera Resultat",
                value="Efter matchen:\n"
                      "`/report-win [match_id] [dina_poäng] [opponents_poäng]`\n"
                      "• Din opponent måste bekräfta\n"
                      "• ELO uppdateras automatiskt\n"
                      "• Nästa match sätts upp automatiskt!",
                inline=False
            )
        
        embed.add_field(
            name="📊 Se Statistik",
            value="• `/my-stats` - Din säsongs-statistik\n"
                  "• `/profile [@spelare]` - All-time profil\n"
                  "• `/leaderboard` - Topp-spelare\n"
                  "• `/match-history` - Din match-historik",
            inline=False
        )
        
        embed.set_footer(text="Använd /help för att se alla kommandon!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def show_overview(self, interaction: discord.Interaction):
        """Visa översikt av alla kategorier"""
        
        embed = discord.Embed(
            title="🏆 Tournament Bot - Hjälp",
            description="Välkommen till Tournament Bot! Här är en översikt av alla funktioner.",
            color=0xFFD700,
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
        
        # Season kommandon
        embed.add_field(
            name="📅 Säsong Kommandon",
            value="Hantera och se säsongs-statistik\n"
                  "`/help category:season` för detaljer",
            inline=False
        )
        
        # Moderation kommandon
        embed.add_field(
            name="🛡️ Moderation Kommandon",
            value="Varna och stänga av spelare\n"
                  "`/help category:moderation` för detaljer",
            inline=False
        )
        
        embed.set_footer(text="Använd /help category:<kategori> för att se alla kommandon i en kategori")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def show_category(self, interaction: discord.Interaction, category: str):
        """Visa kommandon för en specifik kategori"""
        
        if category == "admin":
            embed = discord.Embed(
                title="👑 Admin Kommandon",
                description="Kommandon för att hantera turneringar (kräver Tournament Admin-rollen eller Administrator)",
                color=0xFF0000,
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
                ("set-moderation-channel", "Sätt moderation log kanal"),
                ("resolve-dispute", "Lös en tvistad match manuellt"),
                ("template-create", "Skapa återkommande turnerings-template"),
                ("template-list", "Lista alla templates"),
                ("template-toggle", "Aktivera/pausera en template"),
                ("template-delete", "Ta bort en template"),
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
                color=0x0099FF,
                timestamp=datetime.utcnow()
            )
            
            commands_list = [
                ("set-elo", "⚠️ **VIKTIGT!** Sätt din CS2 Premier eller Faceit ELO (krävs för att anmäla sig)"),
                ("signup", "Anmäl dig till en turnering (använd tournament ID)"),
                ("withdraw", "Dra dig ur en turnering"),
                ("my-tournaments", "Visa dina pågående turneringar"),
                ("my-matches", "Visa dina aktiva matcher"),
                ("my-stats", "Visa din statistik för aktiv säsong"),
                ("profile", "Visa en spelares totala profil (alla säsonger)"),
                ("leaderboard", "Visa top 10 spelare (ELO, vinster, etc)"),
                ("match-history", "Visa din match-historik"),
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
                color=0x00FF00,
                timestamp=datetime.utcnow()
            )
            
            commands_list = [
                ("team-create", "Skapa ett nytt lag (du blir captain)"),
                ("team-invite", "Bjud in en spelare till ditt lag (endast captain)"),
                ("team-leave", "Lämna ditt nuvarande lag"),
                ("team-transfer", "Överför captain-rollen till annan lagmedlem (endast captain)"),
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
                      "Endast captain kan anmäla laget till turneringar.\n"
                      "Om captain lämnar servern tas hela laget bort.\n"
                      "Om vanlig medlem lämnar servern tas de bort från laget automatiskt.",
                inline=False
            )
        
        elif category == "match":
            embed = discord.Embed(
                title="⚔️ Match Kommandon",
                description="Kommandon för att hantera matcher",
                color=0xFF9900,
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
                      "2. Gå in i lobby voice channel - du flyttas automatiskt\n"
                      "3. Map ban-fasen sker i voice channel text chat\n"
                      "4. Spela matchen\n"
                      "5. Rapportera vinst med `/report-win [match_id]`\n"
                      "6. Opponent bekräftar eller avvisar resultatet\n"
                      "7. ELO uppdateras och nästa match sätts upp automatiskt!",
                inline=False
            )
        
        elif category == "tournament":
            embed = discord.Embed(
                title="🏅 Turnering Kommandon",
                description="Kommandon för att visa turnerings-information",
                color=0x9B59B6,
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
                      "• `swiss` - Swiss System\n"
                      "• `double_elim` - Double Elimination (kommer snart)",
                inline=False
            )
        
        elif category == "season":
            embed = discord.Embed(
                title="📅 Säsong Kommandon",
                description="Kommandon för säsonger och säsongs-statistik",
                color=0x3498DB,
                timestamp=datetime.utcnow()
            )
            
            commands_list = [
                ("season-create", "[ADMIN] Skapa en ny säsong"),
                ("season-end", "[ADMIN] Avsluta nuvarande säsong"),
                ("season-info", "Visa information om nuvarande säsong"),
                ("season-leaderboard", "Visa säsongens leaderboard"),
                ("season-list", "Lista alla säsonger"),
            ]
            
            for cmd, desc in commands_list:
                embed.add_field(
                    name=f"/{cmd}",
                    value=desc,
                    inline=False
                )
            
            embed.add_field(
                name="ℹ️ Om Säsonger",
                value="Säsonger används för att återställa statistik periodiskt.\n"
                      "• `/my-stats` visar endast aktiv säsong\n"
                      "• `/profile` visar all-time total statistik\n"
                      "När en säsong avslutas sparas all statistik",
                inline=False
            )
        
        elif category == "moderation":
            embed = discord.Embed(
                title="🛡️ Moderation Kommandon",
                description="Kommandon för att hantera spelare och regelbrott",
                color=0xE74C3C,
                timestamp=datetime.utcnow()
            )
            
            commands_list = [
                ("warn", "[ADMIN] Varna en spelare"),
                ("ban-player", "[ADMIN] Stäng av en spelare från turneringar"),
                ("unban-player", "[ADMIN] Ta bort avstängning"),
                ("clear-warnings", "[ADMIN] Rensa varningar för en spelare"),
                ("moderation-info", "[ADMIN] Visa moderation info för en spelare"),
            ]
            
            for cmd, desc in commands_list:
                embed.add_field(
                    name=f"/{cmd}",
                    value=desc,
                    inline=False
                )
            
            embed.add_field(
                name="⚠️ Varningssystem",
                value="• Spelare kan få upp till 3 varningar\n"
                      "• Vid 3 varningar: Automatisk 2 turneringar ban\n"
                      "• All moderation loggas i tournament-log kanalen\n"
                      "• Admins kan manuellt banna för permanent eller temporär tid",
                inline=False
            )
        
        else:
            await interaction.response.send_message(
                embed=create_error_embed(
                    f"Kategorin `{category}` finns inte!\n\n"
                    "Tillgängliga kategorier: `admin`, `player`, `team`, `match`, `tournament`, `season`, `moderation`"
                ),
                ephemeral=True
            )
            return
        
        embed.set_footer(text="Använd /help för att se alla kategorier")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))