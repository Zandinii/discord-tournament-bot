# Contributing to Tournament Bot

Tack för ditt intresse att bidra till Tournament Bot! 🎉

## Kodstandard

### Python Style Guide

- Följ PEP 8
- Max 100 tecken per rad
- Använd type hints där det är möjligt
- Docstrings för alla funktioner

Exempel:

```python
async def create_tournament(
    name: str,
    game_mode: str,
    max_participants: int = 32
) -> Tournament:
    """
    Skapa en ny turnering.

    Args:
        name: Turneringens namn
        game_mode: Spelläge (1v1, 2v2, 5v5)
        max_participants: Max antal deltagare

    Returns:
        Tournament: Det skapade turnering-objektet
    """
    ...
```

### Commit Messages

Format: `[typ] Kort beskrivning`

Typer:

- `[feat]` - Ny feature
- `[fix]` - Buggfix
- `[docs]` - Dokumentation
- `[refactor]` - Code refactoring
- `[test]` - Test-relaterat
- `[chore]` - Maintenance

Exempel:

```
[feat] Lägg till double elimination bracket support
[fix] Fixa ELO calculation för team matches
[docs] Uppdatera README med nya commands
```

### Branch Naming

- `feature/feature-name` - Nya features
- `fix/bug-description` - Bugfixes
- `docs/documentation-update` - Dokumentation

## Development Workflow

### 1. Fork & Clone

```bash
git clone https://github.com/ditt-användarnamn/discord-tournament-bot.git
cd discord-tournament-bot
```

### 2. Skapa Branch

```bash
git checkout -b feature/my-new-feature
```

### 3. Setup Development Environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Gör Ändringar

- Skriv ren, dokumenterad kod
- Följ befintlig struktur
- Lägg till tests om möjligt

### 5. Testa Lokalt

```bash
python bot.py
```

Kör genom relevanta delar av TESTING_GUIDE.md

### 6. Commit & Push

```bash
git add .
git commit -m "[feat] Din feature-beskrivning"
git push origin feature/my-new-feature
```

### 7. Skapa Pull Request

- Beskriv vad du ändrat
- Referera till issues om relevanta
- Inkludera screenshots om UI-ändringar

## Projektstruktur

```
discord-tournament-bot/
├── bot.py                 # Entry point
├── cogs/                  # Command modules
│   ├── admin.py          # Admin commands
│   ├── player.py         # Player commands
│   ├── match.py          # Match system
│   ├── voice.py          # Voice management
│   ├── team.py           # Team system
│   ├── tournament.py     # Tournament logic
│   ├── season.py         # Seasons
│   ├── achievements.py   # Achievement system
│   ├── templates.py      # Auto-scheduling
│   └── help.py           # Help system
├── database/
│   ├── models.py         # SQLAlchemy models
│   └── database.py       # DB connection
├── utils/
│   ├── bracket.py        # Bracket generation
│   ├── elo.py           # ELO calculations
│   ├── embeds.py        # Discord embeds
│   ├── permissions.py   # Permission checks
│   ├── scheduler.py     # Notification scheduler
│   └── tournament_scheduler.py  # Tournament auto-creation
└── config/
    └── settings.py       # Configuration
```

## Lägga till Nya Features

### Exempel: Ny Cog

```python
# cogs/my_feature.py
import discord
from discord import app_commands
from discord.ext import commands
import logging

logger = logging.getLogger('TournamentBot.MyFeature')

class MyFeatureCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="my-command", description="Beskrivning")
    async def my_command(self, interaction: discord.Interaction):
        """Command implementation"""
        pass

async def setup(bot):
    await bot.add_cog(MyFeatureCog(bot))
```

Lägg till i `bot.py`:

```python
extensions = [..., 'cogs.my_feature']
```

### Exempel: Ny Database Model

```python
# database/models.py
class MyModel(Base):
    __tablename__ = 'my_table'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<MyModel(name='{self.name}')>"
```

## Debugging

### Logga Information

```python
logger.info('Information message')
logger.warning('Warning message')
logger.error('Error message', exc_info=True)
```

### Kolla Logs

```bash
tail -f bot.log
```

### Database Inspection

```python
# Öppna Python REPL
python

# Importera models
from database.database import async_session
from database.models import *
import asyncio

# Query database
async def test():
    async with async_session() as session:
        result = await session.execute(select(Tournament))
        tournaments = result.scalars().all()
        print(tournaments)

asyncio.run(test())
```

## Testing

Innan du submittar PR:

1. Kör bot lokalt
2. Testa din feature grundligt
3. Testa edge cases
4. Verifiera inga errors i logs
5. Kolla att befintlig funktionalitet inte påverkats

## Code Review Process

1. Maintainer reviewar din PR
2. Feedback ges om ändringar behövs
3. Du gör ändringar
4. Approve & merge när allt ser bra ut

## Rapportera Bugs

### Bug Report Template

```
**Beskrivning:**
Kort beskrivning av buggen

**Steg för att Reproducera:**
1. Gör X
2. Gör Y
3. Se error

**Förväntat Beteende:**
Vad som borde hända

**Faktiskt Beteende:**
Vad som händer istället

**Logs:**
```

Relevanta logs här

```

**Environment:**
- Python version:
- Discord.py version:
- OS:
```

## Feature Requests

### Feature Request Template

```
**Feature Beskrivning:**
Beskriv featuren du vill ha

**Use Case:**
Varför behövs denna feature?

**Förslag på Implementation:**
Hur skulle det kunna implementeras?

**Alternativ:**
Finns det alternativa lösningar?
```

## Frågor?

- Discord: [Din Discord Server]
- GitHub Issues: [Link]
- Email: [Din Email]
