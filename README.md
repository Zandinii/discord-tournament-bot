# Discord Turnerings Bot

En komplett turnerings-bot för Discord communities som automatiserar hela turneringsflödet från anmälan till vinnare-kröning med ett rikt utbud av funktioner och skräddarsydd ELO-baserad ranking.

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Discord.py](https://img.shields.io/badge/discord.py-2.3+-blue.svg)

## Features

### Turnerings-System

- **Flera spellägen**: 1v1, 2v2, 5v5
- **Bracket-typer**: Single Elimination, Round Robin
- **Auto-scheduling**: Återkommande veckovisa turneringar
- **Map ban system**: CS2-stil map picks & bans
- **Automatisk bracket**: Generering och progression

### Voice Management

- **Auto voice channels**: Skapas automatiskt per match
- **Auto-flytt**: Spelare flyttas automatiskt vid match-start
- **Auto-cleanup**: Channels raderas efter match
- **Text channels**: För varje team med map ban interface

### Statistik & Ranking

- **ELO system**: K-factor baserat på experience
- **Säsonger**: Resettable seasons med leaderboards
- **Match history**: Full historik med ELO changes
- **Achievements**: 12+ unlockable achievements
- **Leaderboards**: Real-time rankings

### Lag-System

- **Permanent teams**: Lag som består mellan turneringar
- **Team ELO**: Baserat på medlemmars genomsnitt
- **Invite system**: Med accept/deny buttons
- **Captain roles**: Special permissions för captains

### Notifikationer

- **Auto-reminders**: 24h, 1h, 5min före turnering
- **Match notifications**: När din match startar
- **Achievement notifications**: När du unlocking achievements

### Achievements

- First Blood, Champion, Hot Streak, Unstoppable
- Rising Star, Elite, Grandmaster
- Veteran, Tournament Regular, Triple Crown
- Underdog victories

## Quick Start

### Prerequisites

- Python 3.11+
- Discord Bot Token
- PostgreSQL eller SQLite

### Installation

```bash
# Klona repo
git clone https://github.com/yourusername/discord-tournament-bot.git
cd discord-tournament-bot

# Skapa virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installera dependencies
pip install -r requirements.txt

# Skapa .env fil
# Redigera .env med din bot token

# Starta botten
python bot.py
```

### Discord Setup

1. Skapa bot på [Discord Developer Portal](https://discord.com/developers/applications)
2. Aktivera intents:
   - Message Content Intent
   - Server Members Intent
   - Presence Intent
3. Permissions: Administrator (eller specific permissions)
4. Invite bot med OAuth2 URL

## 📖 Usage

### För Admins

```bash
# Initial setup
/setup
/set-lobby [voice_channel]

# Skapa turnering
/tournament-create
# Följ wizard-prompten

# Starta turnering
/tournament-start [tournament_id]

# Hantera
/tournament-list
/tournament-cancel [id]
/tournament-delete [id]
```

### För Spelare

```bash
# Anmäl dig
/signup [tournament_id]

# Visa dina matcher
/my-matches

# Rapportera resultat
/report-win [match_id] [your_score] [opponent_score]

# Statistik
/my-stats
/leaderboard
/profile [@user]

# Achievements
/achievements
/achievements-list
```

### För Lag

```bash
# Skapa lag
/team-create [name] [tag]

# Bjud in
/team-invite [@user]

# Visa info
/team-info
/team-list
```

## Projektstruktur

```
discord-tournament-bot/
├── bot.py                    # Entry point
├── cogs/                     # Command modules
│   ├── admin.py
│   ├── player.py
│   ├── match.py
│   ├── voice.py
│   ├── team.py
│   ├── tournament.py
│   ├── season.py
│   ├── achievements.py
│   ├── templates.py
│   └── help.py
├── database/
│   ├── models.py            # SQLAlchemy models
│   └── database.py          # DB connection
├── utils/
│   ├── bracket.py           # Bracket generation
│   ├── elo.py              # ELO calculations
│   ├── embeds.py           # Discord embeds
│   ├── permissions.py      # Permission checks
│   ├── scheduler.py        # Notification scheduler
│   └── tournament_scheduler.py
└── docs/
    ├── TESTING_GUIDE.md
    ├── API_REFERENCE.md
    └── CONTRIBUTING.md
```

## Configuration

### Environment Variables (.env file)

```env
DISCORD_TOKEN=your_bot_token
GUILD_ID=your_server_id
DATABASE_URL=sqlite+aiosqlite:///tournament.db
# eller för PostgreSQL:
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dbname
```

## Database Schema

Huvudtabeller:

- `guilds` - Server configuration
- `tournaments` - Tournament data
- `players` - Player profiles & stats
- `teams` - Team information
- `matches` - Match results
- `tournament_participants` - Signups
- `seasons` - Season tracking
- `achievements` - Achievement definitions
- `player_achievements` - Unlocked achievements
- `match_history` - Full match logs
- `map_bans` - Map ban history
- `tournament_templates` - Auto-scheduling

## 📄 License

Ingen användning av koden eller dess delar får ske i personliga eller kommersiella syften utan uttryckligt tillstånd från upphovsmannen.
