import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import logging
import sys

# Fix for Windows console encoding (Support emojis without issues)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')

if not DISCORD_TOKEN:
    logger.error("DISCORD_TOKEN is not set in the environment variables.")
    exit(1)

# Bot setup with intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

async def load_extensions():
    extensions = ['cogs.admin', 'cogs.player', 'cogs.tournament', 'cogs.match', 'cogs.voice']
    for ext in extensions:
        try:
            await bot.load_extension(ext)
            logger.info(f'✅ Laddade extension: {ext}')
        except Exception as e:
            logger.error(f'❌ Misslyckades med att ladda extension {ext}: {e}', exc_info=True)

@bot.event
async def on_ready():
    logger.info(f'✅ {bot.user} har loggat in!')
    logger.info(f'Bot ID: {bot.user.id}')
    logger.info(f'Discord.py version: {discord.__version__}')
    logger.info(f'Ansluten till {len(bot.guilds)} servrar')

    # Intialize database
    from database.database import init_db
    await init_db()
    logger.info("✅ Databas initierad och ansluten.")

    # Load extensions (cogs)
    await load_extensions()

    # Publish commands globally (clear guild-specific commands first to avoid duplicates)
    try:
        # Clear per-guild commands so only global commands remain
        for g in bot.guilds:
            try:
                bot.tree.clear_commands(guild=discord.Object(id=g.id))
                logger.info(f'✅ Cleared guild-specific commands for guild {g.id}.')
            except Exception as e:
                logger.warning(f'⚠️ Kunde inte rensa guild-kommandon för {g.id}: {e}')

        # Sync globally
        synced = await bot.tree.sync()
        logger.info(f'✅ Synkade {len(synced)} global(a) kommandon.')

        # Log registered global commands for debugging
        try:
            for cmd in bot.tree.get_commands():
                logger.info(f'🔹 Registered (global) command: {cmd.name}')
        except Exception:
            pass
    except Exception as e:
        logger.error(f'❌ Misslyckades med att synka globala kommandon: {e}', exc_info=True)
    
    # Set bot status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="Joina nästa turnering!🎮"
        )
    )

@bot.event
async def on_guild_join(guild):
    logger.info(f'✅ Gick med i servern: {guild.name} (ID: {guild.id})')

@bot.event
async def on_guild_remove(guild):
    logger.info(f'❌ Lämnade servern: {guild.name} (ID: {guild.id})')

# Global error handler
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Du har inte tillräckliga behörigheter för att köra detta kommando.")
    elif isinstance(error, commands.CommandNotFound):
        pass # Ignore unknown commands
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Saknar argument: {error.param.name}")
    else:
        logger.error(f'❌ Ett oväntat fel uppstod: {error}', exc_info=True)
        await ctx.send("❌ Ett oväntat fel uppstod: " + str(error) + ". Vänligen kontakta administratören.")

if __name__ == "__main__":
    logger.info("🚀 Startar bot...")
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        logger.critical(f'❌ Misslyckades med att starta boten: {e}', exc_info=True)

