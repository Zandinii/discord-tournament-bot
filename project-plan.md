# Discord Turnerings Bot - Detaljerad Projektplan

## 📋 Projektöversikt

En komplett turnerings-bot för Discord som hanterar veckovisa community-turneringar med automatisk matchhantering, voice channel-management, ELO-system och statistik.

**Tech Stack:**

- Python 3.11+
- Discord.py 2.3+
- PostgreSQL (gratis via Supabase/Railway)
- Hosting: Railway.app (gratis tier) eller lokal körning

---

## 🎯 Fas 1: Setup & Grundläggande Infrastruktur

### 1.1 Projektinitiering (Dag 1)

- [x] Skapa Discord Application på [Discord Developer Portal](https://discord.com/developers/applications)
  - [x] Aktivera "Message Content Intent"
  - [x] Aktivera "Server Members Intent"
  - [x] Notera Bot Token (spara säkert!)
- [x] Sätt bot-permissions:
  - [x] Manage Channels
  - [x] Manage Roles
  - [x] Move Members
  - [x] Send Messages
  - [x] Embed Links
  - [x] Use Slash Commands
  - [x] View Channels
  - [x] Connect & Speak (för VC)
- [x] Generera OAuth2 invite-länk med rätt permissions
- [x] Bjud in botten till din test-server

### 1.2 Lokal Utvecklingsmiljö (Dag 1)

```bash
# Skapa projekt
mkdir discord-tournament-bot
cd discord-tournament-bot
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installera dependencies
pip install discord.py python-dotenv asyncpg sqlalchemy alembic aiohttp
```

- [x] Skapa `.env` fil:
- [x] Skapa `.gitignore`:
- [x] Skapa projektstruktur:

```
discord-tournament-bot/
├── bot.py                 # Main entry point
├── .env
├── .gitignore
├── requirements.txt
├── README.md
├── cogs/
│   ├── __init__.py
│   ├── admin.py          # Admin-kommandon
│   ├── tournament.py     # Turnerings-logik
│   ├── player.py         # Spelare-kommandon
│   ├── match.py          # Match-hantering
│   └── voice.py          # VC-management
├── database/
│   ├── __init__.py
│   ├── models.py         # SQLAlchemy models
│   ├── database.py       # DB connection
│   └── migrations/       # Alembic migrations
├── utils/
│   ├── __init__.py
│   ├── bracket.py        # Bracket-generering
│   ├── elo.py           # ELO-beräkningar
│   ├── embeds.py        # Discord embeds
│   └── permissions.py   # Permission checks
└── config/
    ├── __init__.py
    └── settings.py      # Konfiguration
```

---

## 🗄️ Fas 2: Databas Setup (Dag 2-3)

### 2.1 PostgreSQL Setup (Gratis Alternativ)

**Välj ett:**

**Alternativ A: Supabase (Rekommenderat för gratis hosting)**

- [ ] Skapa konto på [supabase.com](https://supabase.com)
- [ ] Skapa nytt projekt
- [ ] Kopiera "Connection String" till `.env`

**Alternativ B: Railway.app**

- [ ] Skapa konto på [railway.app](https://railway.app)
- [ ] Skapa PostgreSQL database
- [ ] Kopiera connection string

**Alternativ C: Lokal PostgreSQL**

```bash
# macOS
brew install postgresql
brew services start postgresql

# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### 2.2 Databasschema (`database/models.py`)

- [x] Definiera SQLAlchemy models:

**Tabeller att skapa:**

1. **guilds** - Server-konfiguration

   - guild_id (PK)
   - tournament_channel_id
   - lobby_voice_channel_id
   - notification_role_id
   - created_at

2. **tournaments** - Turnerings-info

   - id (PK)
   - guild_id (FK)
   - name
   - game_mode (1v1, 2v2, 5v5)
   - game_type (Single Elim, Double Elim, Round Robin)
   - max_participants
   - start_time
   - status (SIGNUP, ONGOING, COMPLETED)
   - prize_description
   - created_by (user_id)
   - created_at

3. **teams** - Lag-information

   - id (PK)
   - name
   - tag
   - captain_id (user_id)
   - created_at
   - total_wins
   - total_losses

4. **team_members** - Lag-medlemmar

   - id (PK)
   - team_id (FK)
   - user_id
   - joined_at

5. **tournament_participants** - Anmälningar

   - id (PK)
   - tournament_id (FK)
   - participant_id (user/team ID)
   - participant_type (USER/TEAM)
   - signup_time
   - seed (för bracket)

6. **matches** - Matcher

   - id (PK)
   - tournament_id (FK)
   - round_number
   - match_number
   - participant1_id
   - participant2_id
   - winner_id
   - score_p1
   - score_p2
   - status (PENDING, ONGOING, COMPLETED)
   - voice_channel_id
   - started_at
   - completed_at

7. **players** - Spelarprofiler & statistik

   - user_id (PK)
   - guild_id (FK)
   - username
   - elo_rating (default 1000)
   - total_matches
   - total_wins
   - total_losses
   - tournaments_won
   - created_at

8. **match_participants** - Spelare i matcher

   - id (PK)
   - match_id (FK)
   - user_id
   - team_id (nullable)
   - side (1 eller 2)

9. **notifications** - Schemalagda notiser

   - id (PK)
   - tournament_id (FK)
   - message
   - scheduled_time
   - sent (boolean)

10. **champion_history** - Vinnare-historik
    - id (PK)
    - tournament_id (FK)
    - winner_id (user/team)
    - winner_type
    - prize_awarded
    - awarded_at

### 2.3 Alembic Setup (Database Migrations)

```bash
# Initiera Alembic
alembic init database/migrations

# Skapa första migration
alembic revision --autogenerate -m "Initial schema"

# Kör migration
alembic upgrade head
```

- [ ] Konfigurera Alembic i `alembic.ini`
- [ ] Skapa initial migration
- [ ] Testa att köra migrations

---

## 🤖 Fas 3: Bot Core & Kommandon (Dag 4-7)

### 3.1 Main Bot Setup (`bot.py`)

- [ ] Skapa bot instance med intents
- [ ] Läs in alla cogs
- [ ] Setup event handlers:
  - [ ] `on_ready` - Synka slash commands
  - [ ] `on_guild_join` - Initiera server i DB
  - [ ] `on_member_join` - Skapa spelarprofil
- [ ] Error handling för commands

### 3.2 Admin Cog (`cogs/admin.py`)

**Kommandon att implementera:**

- [ ] `/tournament create` - Tournament Wizard (Modal)

  - [ ] Input: Namn, spel, mode (1v1/2v2/5v5), typ (single/double elim)
  - [ ] Input: Max deltagare, starttid, prisbeskrivning
  - [ ] Skapa turnering i DB
  - [ ] Skapa announcement embed
  - [ ] Öppna anmälningar

- [ ] `/tournament edit [tournament_id]` - Redigera turnering

  - [ ] Select menu för att välja vad som ska ändras
  - [ ] Modal för nya värden

- [ ] `/tournament delete [tournament_id]` - Ta bort turnering

  - [ ] Bekräftelseknapp
  - [ ] Cleanup av alla relaterade data

- [ ] `/tournament start [tournament_id]` - Starta turnering manuellt

  - [ ] Stäng anmälningar
  - [ ] Generera bracket
  - [ ] Skicka schema

- [ ] `/tournament cancel [tournament_id]` - Avbryt turnering

- [ ] `/tournament list` - Visa alla turneringar (filter: aktiva/gamla)

- [ ] `/setup` - Initial server-setup

  - [ ] Välj turnerings-kanal
  - [ ] Välj lobby voice channel
  - [ ] Välj notifikations-roll
  - [ ] Spara i DB

- [ ] `/champion award [@user] [tournament_id]` - Ge champion-roll

  - [ ] Tilldela roll
  - [ ] Logga i champion_history
  - [ ] Skicka grattis-meddelande

- [ ] `/stats server` - Server-statistik
  - [ ] Totalt antal turneringar
  - [ ] Aktiva spelare
  - [ ] Mest aktiva spelare

### 3.3 Player Cog (`cogs/player.py`)

**Kommandon att implementera:**

- [ ] `/signup [tournament_id]` - Anmäl sig till turnering

  - [ ] Kolla om turnering är öppen
  - [ ] Kolla om redan anmäld
  - [ ] Lägg till i tournament_participants
  - [ ] Bekräftelsemeddelande

- [ ] `/withdraw [tournament_id]` - Dra sig ur

  - [ ] Ta bort från participants
  - [ ] Uppdatera bracket om turnering startat

- [ ] `/my-tournaments` - Visa mina pågående turneringar

- [ ] `/my-matches` - Visa mina kommande matcher

- [ ] `/my-stats` - Visa personlig statistik

  - [ ] ELO rating
  - [ ] Vinster/förluster
  - [ ] Turneringar vunna
  - [ ] Win rate

- [ ] `/leaderboard` - Visa top 10 spelare (ELO)

  - [ ] Buttons för att byta kategori (Wins, Tournaments, etc)

- [ ] `/profile [@user]` - Visa spelarprofil

  - [ ] Statistik
  - [ ] Senaste matcher
  - [ ] Lag-medlemskap

- [ ] `/team create [name]` - Skapa lag

  - [ ] Modal för lagnamn och tag
  - [ ] Sätt dig som captain
  - [ ] Skapa i DB

- [ ] `/team invite [@user]` - Bjud in till lag

  - [ ] Skicka invite-button till användaren
  - [ ] Timeout efter 5 min

- [ ] `/team leave` - Lämna lag

- [ ] `/team info [team_name]` - Visa lag-info

- [ ] `/team list` - Visa alla lag på servern

### 3.4 Match Cog (`cogs/match.py`)

**Kommandon att implementera:**

- [ ] `/match report-win [match_id]` - Rapportera vinst (endast lagkaptener)

  - [ ] Kräv bekräftelse från båda sidor
  - [ ] Uppdatera match i DB
  - [ ] Uppdatera ELO
  - [ ] Flytta till nästa match i bracket
  - [ ] Cleanup voice channels

- [ ] `/match dispute [match_id]` - Tvista resultat

  - [ ] Notifiera admins
  - [ ] Vänta på admin-bekräftelse

- [ ] `/match info [match_id]` - Visa match-detaljer

- [ ] `/match schedule` - Visa kommande matcher för turnering
  - [ ] Select menu för att välja turnering

**Auto-funktioner:**

- [ ] Auto-starta match när schemalagd tid nås
  - [ ] Skapa VC-kanaler
  - [ ] Flytta spelare
  - [ ] Skicka notis

---

## 🎙️ Fas 4: Voice Channel Management (Dag 8-9)

### 4.1 Voice Cog (`cogs/voice.py`)

**Funktioner att implementera:**

- [ ] `create_match_channels(match_id)` - Skapa temporära VC

  - [ ] Skapa "Team 1 - Match X" kanal
  - [ ] Skapa "Team 2 - Match X" kanal
  - [ ] Sätt permissions (endast lag-medlemmar kan joina)
  - [ ] Spara channel IDs i match-tabellen

- [ ] `move_players_to_channels(match_id)` - Flytta spelare

  - [ ] Hämta alla spelare i matchen
  - [ ] Flytta till respektive lag-kanal
  - [ ] Skicka meddelande i text-kanalen

- [ ] `cleanup_match_channels(match_id)` - Ta bort kanaler

  - [ ] Flytta alla spelare tillbaka till lobby
  - [ ] Ta bort VC-kanaler
  - [ ] Logga eventuella fel

- [ ] Auto-cleanup vid match-completion

  - [ ] Hook in i report-win command
  - [ ] Delay 30 sek innan cleanup

- [ ] Emergency cleanup command för admins:
  - [ ] `/voice cleanup-all` - Ta bort alla match-kanaler

**Error Handling:**

- [ ] Hantera offline spelare
- [ ] Hantera spelare som inte är i lobby
- [ ] Retry-logik för voice operations

---

## 🏆 Fas 5: Bracket & Match System (Dag 10-12)

### 5.1 Bracket Generator (`utils/bracket.py`)

**Implementera bracket-typer:**

- [ ] **Single Elimination**

  - [ ] Beräkna antal rounds
  - [ ] Seed spelare/lag
  - [ ] Generera match-pairing
  - [ ] Hantera byes

- [ ] **Double Elimination**

  - [ ] Winner bracket
  - [ ] Loser bracket
  - [ ] Grand finals logik

- [ ] **Round Robin** (för mindre grupper)
  - [ ] Generera alla matcher
  - [ ] Poängräkning

**Funktioner:**

- [ ] `generate_bracket(tournament_id, bracket_type)`
- [ ] `seed_participants(participants, seeding_type)`
  - Seeding baserat på: Random, ELO, Admin-ordning
- [ ] `advance_winner(match_id, winner_id)`
- [ ] `get_next_match(tournament_id, participant_id)`

### 5.2 Bracket Visualization

- [ ] Skapa Discord embed som visar bracket
- [ ] Uppdatera embed när matcher slutförs
- [ ] Använd emojis för att visa status (✅ ❌ ⏳)

**Exempel bracket-layout:**

```
🏆 TOURNAMENT BRACKET - Round of 8

Match 1: Team Alpha ⚔️ Team Beta [⏳ Pending]
Match 2: Team Gamma ✅ vs Team Delta ❌
Match 3: Player1 vs Player2 [⏳ Pending]
Match 4: Player3 vs Player4 [⏳ Pending]
```

---

## 📊 Fas 6: ELO & Statistik System (Dag 13-14)

### 6.1 ELO Calculator (`utils/elo.py`)

- [ ] Implementera ELO-algoritm:

```python
def calculate_elo(winner_elo, loser_elo, k_factor=32):
    expected_winner = 1 / (1 + 10 ** ((loser_elo - winner_elo) / 400))
    expected_loser = 1 - expected_winner

    new_winner_elo = winner_elo + k_factor * (1 - expected_winner)
    new_loser_elo = loser_elo + k_factor * (0 - expected_loser)

    return round(new_winner_elo), round(new_loser_elo)
```

- [ ] Olika K-factors baserat på antal matcher:

  - [ ] Nya spelare (< 10 matcher): K=40
  - [ ] Etablerade spelare: K=32
  - [ ] Masters (> 100 matcher): K=24

- [ ] Team ELO som genomsnitt av medlemmar

### 6.2 Statistik-tracking

- [ ] Uppdatera spelarstatistik efter varje match:

  - [ ] Wins/losses
  - [ ] ELO rating
  - [ ] Tournament participations
  - [ ] Win streaks

- [ ] Lag-statistik:

  - [ ] Team ELO
  - [ ] Sammanspelade matcher
  - [ ] Turneringar tillsammans

- [ ] Turnerings-statistik:
  - [ ] Mest aktiv spelare
  - [ ] Högst ELO-gain
  - [ ] Flest upsets

---

## 🔔 Fas 7: Notifikationssystem (Dag 15-16)

### 7.1 Notification Manager

**Typer av notifikationer:**

- [ ] **Turnerings-påminnelser**

  - [ ] 24h före start
  - [ ] 1h före start
  - [ ] Vid start

- [ ] **Match-notiser**

  - [ ] 15 min före match
  - [ ] Vid match-start
  - [ ] När opponent är redo

- [ ] **Resultat-notiser**

  - [ ] När match är klar
  - [ ] När du går vidare
  - [ ] När du blir eliminerad

- [ ] **Turnerings-sammanfattning**
  - [ ] Efter turnering
  - [ ] Vinnare-announcement
  - [ ] Top 3 prestationer

### 7.2 Background Task System

- [ ] Skapa background task med discord.py tasks
- [ ] Check varje minut för scheduled notifications
- [ ] Skicka notiser till rätt kanal/användare
- [ ] Markera som "sent" i DB

```python
@tasks.loop(minutes=1)
async def check_notifications():
    # Hämta alla osända notiser som ska skickas nu
    # Skicka meddelanden
    # Uppdatera DB
```

### 7.3 Notification Settings

- [ ] Låt användare välja vilka notiser de vill ha
- [ ] `/notifications settings` - Toggle olika typer
- [ ] DM vs Channel notifications

---

## 🎨 Fas 8: UI/UX & Embeds (Dag 17-18)

### 8.1 Embed Designer (`utils/embeds.py`)

**Skapa templates för:**

- [ ] **Tournament Announcement**

  - [ ] Titel, beskrivning, game mode
  - [ ] Starttid, max deltagare
  - [ ] Signup button
  - [ ] Thumbnail med spel-ikon

- [ ] **Bracket Display**

  - [ ] Visuell representation
  - [ ] Färgkodade status
  - [ ] Uppdateras live

- [ ] **Match Card**

  - [ ] Team 1 vs Team 2
  - [ ] Starttid
  - [ ] Buttons: Ready Up, Report Win

- [ ] **Player Profile**

  - [ ] Stats översikt
  - [ ] ELO graf (text-baserad)
  - [ ] Senaste resultat

- [ ] **Leaderboard**
  - [ ] Top 10 med emojis (🥇🥈🥉)
  - [ ] Färggradient för ranks
  - [ ] Update button

### 8.2 Interactive Components

**Buttons:**

- [ ] Signup/Withdraw buttons på tournament announcement
- [ ] Ready up button för matcher
- [ ] Report win/loss buttons
- [ ] Pagineringsknappar för leaderboards

**Select Menus:**

- [ ] Välj turnering att anmäla sig till
- [ ] Välj spel-mode vid skapande
- [ ] Välj lag för team-turneringar

**Modals:**

- [ ] Tournament creation wizard
- [ ] Team creation form
- [ ] Match dispute form

---

## 🤝 Fas 9: Team System (Dag 19-20)

### 9.1 Team Management

**Implementera:**

- [ ] Team creation med captain-system
- [ ] Invite system med buttons
- [ ] Team roster (visa medlemmar)
- [ ] Captain kan kicka medlemmar
- [ ] Transfer captain role

### 9.2 Team Tournaments

- [ ] Teams kan anmäla sig till turneringar
- [ ] Auto-check att alla medlemmar är online
- [ ] Team ELO som genomsnitt
- [ ] Team statistik och historik

### 9.3 Team Persistence

- [ ] Lag stannar mellan turneringar
- [ ] Lag-historik (turneringar, resultat)
- [ ] `/team history` kommando

---

## 🎮 Fas 10: Game Mode Logic (Dag 21-22)

### 10.1 Implementera olika modes

**1v1 Mode:**

- [ ] Simpel pairing
- [ ] Direkt bracket
- [ ] Voice channels per match

**2v2 Mode:**

- [ ] Par kan anmäla sig tillsammans
- [ ] Auto-pairing av solos
- [ ] 2 voice channels per match (team1, team2)

**5v5 Mode:**

- [ ] Lag-baserat (måste ha lag)
- [ ] Eller auto-split av 10 solos
- [ ] Voice channels per team

### 10.2 Draft System (för solos i team modes)

- [ ] Captain väljer spelare
- [ ] Snake draft (1-2-2-2-1)
- [ ] Buttons för att välja spelare

---

## 📈 Fas 11: Advanced Features (Dag 23-25)

### 11.1 Säsongs-system

- [ ] Skapa säsonger (S1, S2, etc)
- [ ] ELO reset mellan säsonger (soft reset)
- [ ] Säsongs-leaderboards
- [ ] Season rewards

### 11.2 Achievement System

- [ ] Definiera achievements:
  - [ ] "First Blood" - Vinna första turneringen
  - [ ] "Unstoppable" - 5 vinster i rad
  - [ ] "Underdog" - Vinna mot högre ELO
  - [ ] "Champion" - Vinna turnering
- [ ] Tilldela badges/roles för achievements

### 11.3 Match History

- [ ] `/history [@user]` - Visa match-historik
- [ ] Filtrera på turnering, opponent, datum
- [ ] Export till CSV (för admins)

### 11.4 Automated Tournament Scheduling

- [ ] Återkommande turneringar (varje vecka)
- [ ] Auto-creation på specifika dagar/tider
- [ ] Template system

---

## 🌐 Fas 12: Web Dashboard (OPTIONAL - Dag 26-30)

### 12.1 Basic Web Interface

**Om du vill ha web-dashboard (gratis hosting):**

**Tech:** Flask/FastAPI + HTML/CSS/JS
**Hosting:** Render.com (gratis tier)

**Features:**

- [ ] Live bracket viewer
- [ ] Leaderboards
- [ ] Player profiles
- [ ] Match history
- [ ] Tournament schedule

**Implementation:**

- [ ] Skapa enkel REST API
- [ ] Read-only endpoints från DB
- [ ] Simple HTML templates
- [ ] Auto-refresh för live data

**Alternativ:** Skip web-dashboard, allt kan göras i Discord

---

## 🚀 Fas 13: Hosting & Deployment (Dag 31-32)

### 13.1 Railway.app Setup (Rekommenderat GRATIS)

**Steg:**

1. [ ] Skapa konto på [railway.app](https://railway.app)
2. [ ] Länka GitHub repo
3. [ ] Lägg till PostgreSQL service
4. [ ] Deploy bot service
5. [ ] Sätt environment variables
6. [ ] Testa att botten startar

**Railway.app Free Tier:**

- $5 credit/månad
- Räcker för en bot + databas
- 500 execution hours

### 13.2 Alternativ Hosting (om Railway inte räcker)

**Alternativ A: Render.com**

- [ ] Deploy som web service (keep alive trick)
- [ ] Gratis PostgreSQL
- [ ] Auto-sleep efter inaktivitet

**Alternativ B: Lokal körning (billigast)**

- [ ] Kör på egen dator/Raspberry Pi
- [ ] Setup systemd service (Linux)
- [ ] Auto-restart vid krasch

**Alternativ C: Oracle Cloud (alltid gratis)**

- [ ] Gratis VPS forever
- [ ] Mer setup krävs
- [ ] 1GB RAM + 1 vCPU

### 13.3 Production Checklist

- [ ] Environment variables korrekt satta
- [ ] Database migrations körda
- [ ] Logging konfigurerat
- [ ] Error notifications (till admin DM)
- [ ] Backup-strategi för databas
- [ ] Rate limiting för commands
- [ ] Caching för leaderboards

---

## 🧪 Fas 14: Testing & Polish (Dag 33-35)

### 14.1 Testing

**Testa varje feature:**

- [ ] Tournament creation → signup → bracket → match → completion flow
- [ ] Voice channel creation/cleanup
- [ ] Team system
- [ ] ELO calculations
- [ ] Notifications
- [ ] Edge cases:
  - [ ] Odd antal spelare
  - [ ] Spelare disconnect under match
  - [ ] Disputed results
  - [ ] Concurrent tournaments

### 14.2 Error Handling

- [ ] Try-catch på alla discord operations
- [ ] Graceful degradation
- [ ] User-friendly error messages
- [ ] Admin error logs

### 14.3 Performance

- [ ] Database indexes på ofta queriade kolumner
- [ ] Cache leaderboards (update varje 5 min)
- [ ] Batch operations där möjligt
- [ ] Async operations för alla I/O

---

## 📚 Fas 15: Dokumentation (Dag 36-37)

### 15.1 Användar-dokumentation

- [ ] Skapa `/help` kommando
- [ ] Kategori-baserad hjälp (Admin, Player, Team)
- [ ] Tutorial för nya användare
- [ ] FAQ i Discord kanal

### 15.2 Admin Guide

- [ ] Setup instruktioner
- [ ] Hur man skapar turneringar
- [ ] Hur man hanterar disputes
- [ ] Troubleshooting

### 15.3 Developer Docs

- [ ] README med setup-instruktioner
- [ ] Code comments
- [ ] Architecture overview
- [ ] Contributing guidelines (om open source)

---

## 🎯 Fas 16: Launch & Monitoring (Dag 38-40)

### 16.1 Soft Launch

- [ ] Testa med liten grupp users
- [ ] Kör test-turnering
- [ ] Samla feedback
- [ ] Fixa buggar

### 16.2 Full Launch

- [ ] Announcement i servern
- [ ] Tutorial-session
- [ ] Första riktiga turneringen
- [ ] Monitor för errors

### 16.3 Monitoring & Maintenance

- [ ] Setup logging (Loguru eller standard logging)
- [ ] Monitor bot uptime
- [ ] Database backup schedule
- [ ] Regelbundna updates

---

## 🎨 Extra Features (Backlog - implementera efter behov)

### Nice-to-have features:

- [ ] **Game API Integration**

  - [ ] Riot API för League of Legends stats
  - [ ] Steam API för CS2/Dota stats
  - [ ] Auto-verify resultat

- [ ] **Betting System**

  - [ ] Virtuell valuta
  - [ ] Betta på matcher
  - [ ] Leaderboard för bettors

- [ ] **Replay System**

  - [ ] Ladda upp replays/clips
  - [ ] Highlight-reel av vinnare

- [ ] **Coaching System**

  - [ ] Coaches kan anmäla sig
  - [ ] Spelare kan booka coaching
  - [ ] Rating system för coaches

- [ ] **Clan Wars**

  - [ ] Clans tävlar mot varandra
  - [ ] Clan leaderboard
  - [ ] Clan-specifika priser

- [ ] **Stream Integration**
  - [ ] Auto-posta när någon streamar sin match
  - [ ] Twitch/YouTube notiser

---

## 📊 Estimerad Tidsplan

**Total tid: 6-8 veckor (part-time arbete)**

| Fas   | Dagar   | Beskrivning              |
| ----- | ------- | ------------------------ |
| 1-2   | 3 dagar | Setup & Database         |
| 3-4   | 6 dagar | Core Commands & Voice    |
| 5-6   | 4 dagar | Bracket & ELO            |
| 7-8   | 4 dagar | Notifications & UI       |
| 9-10  | 4 dagar | Teams & Game Modes       |
| 11    | 3 dagar | Advanced Features        |
| 12    | 5 dagar | Web Dashboard (optional) |
| 13    | 2 dagar | Deployment               |
| 14-16 | 5 dagar | Testing & Launch         |

---

## 💰 Kostnadsuppskattning (GRATIS Setup)

| Service             | Kostnad                               |
| ------------------- | ------------------------------------- |
| Railway.app         | **GRATIS** ($5 credit/månad)          |
| Supabase PostgreSQL | **GRATIS** (500MB storage)            |
| Discord Bot         | **GRATIS**                            |
| Domain (optional)   | **GRATIS** (använd Railway subdomain) |
| **TOTALT**          | **0 kr/månad** ✅                     |

**Om Railway credit tar slut:**

- Kör lokalt på egen dator (0 kr)
- Använd Render.com gratis tier
- Oracle Cloud Always Free tier

---

## 🛠️ Development Tools (Gratis)

- **Code Editor:** VS Code (gratis)
- **Git:** GitHub (gratis private repos)
- **Database GUI:** pgAdmin / DBeaver (gratis)
- **API Testing:** Postman (gratis tier)
- **Project Management:** Trello / Notion (gratis)

---

## 📝 Snabbreferens - Viktiga Kommandon

### Admin Kommandon

```
/setup                              # Initial server setup
/tournament create                  # Skapa ny turnering (modal)
/tournament start [id]              # Starta turnering manuellt
/tournament cancel [id]             # Avbryt turnering
/tournament list                    # Lista turneringar
/champion award [@user] [id]        # Ge champion-roll
/stats server                       # Server-statistik
/voice cleanup-all                  # Emergency VC cleanup
```

### Spelare Kommandon

```
/signup [tournament_id]             # Anmäl dig
/withdraw [tournament_id]           # Dra dig ur
/my-tournaments                     # Dina turneringar
/my-matches                         # Dina matcher
/my-stats                           # Din statistik
/leaderboard                        # Top spelare
/profile [@user]                    # Visa profil
/team create [name]                 # Skapa lag
/team invite [@user]                # Bjud in till lag
/team list                          # Visa alla lag
```

### Match Kommandon

```
/match report-win [match_id]        # Rapportera vinst
/match dispute [match_id]           # Tvista resultat
/match info [match_id]              # Match-detaljer
/match schedule                     # Kommande matcher
```

---

## 🔧 Teknisk Implementation - Code Snippets

### Bot Entry Point (`bot.py`)

```python
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from database.database import init_db
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('TournamentBot')

# Load environment
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Bot setup med intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    logger.info(f'{bot.user} har loggat in!')

    # Initialize database
    await init_db()

    # Synka slash commands
    await bot.tree.sync()
    logger.info('Slash commands synkade!')

    # Set status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="turneringar | /help"
        )
    )

@bot.event
async def on_guild_join(guild):
    # Setup guild i database
    from database.models import Guild
    await Guild.create_or_update(guild.id)
    logger.info(f'Bot tillagd till ny server: {guild.name}')

# Load cogs
async def load_cogs():
    cogs = ['admin', 'player', 'tournament', 'match', 'voice']
    for cog in cogs:
        try:
            await bot.load_extension(f'cogs.{cog}')
            logger.info(f'Loaded cog: {cog}')
        except Exception as e:
            logger.error(f'Failed to load {cog}: {e}')

@bot.event
async def setup_hook():
    await load_cogs()

# Error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('❌ Du har inte behörighet för det kommandot!')
    elif isinstance(error, commands.CommandNotFound):
        pass  # Ignorera
    else:
        logger.error(f'Error: {error}')
        await ctx.send(f'❌ Ett fel uppstod: {str(error)}')

if __name__ == '__main__':
    bot.run(TOKEN)
```

### Database Connection (`database/database.py`)

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

DATABASE_URL = os.getenv('DATABASE_URL')

# Convert postgres:// to postgresql+asyncpg:// för async support
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql+asyncpg://', 1)

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
```

### Example Model (`database/models.py`)

```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database.database import Base

class TournamentStatus(enum.Enum):
    SIGNUP = "signup"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Tournament(Base):
    __tablename__ = 'tournaments'

    id = Column(Integer, primary_key=True)
    guild_id = Column(Integer, nullable=False)
    name = Column(String(100), nullable=False)
    game_mode = Column(String(10))  # 1v1, 2v2, 5v5
    game_type = Column(String(20))  # single_elim, double_elim, round_robin
    max_participants = Column(Integer, default=32)
    start_time = Column(DateTime)
    status = Column(Enum(TournamentStatus), default=TournamentStatus.SIGNUP)
    prize_description = Column(String(500))
    created_by = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    participants = relationship("TournamentParticipant", back_populates="tournament")
    matches = relationship("Match", back_populates="tournament")

    def __repr__(self):
        return f"<Tournament(name='{self.name}', status='{self.status}')>"

class Player(Base):
    __tablename__ = 'players'

    user_id = Column(Integer, primary_key=True)
    guild_id = Column(Integer, nullable=False)
    username = Column(String(100))
    elo_rating = Column(Integer, default=1000)
    total_matches = Column(Integer, default=0)
    total_wins = Column(Integer, default=0)
    total_losses = Column(Integer, default=0)
    tournaments_won = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Player(username='{self.username}', elo={self.elo_rating})>"
```

### Example Cog - Admin Commands (`cogs/admin.py`)

```python
import discord
from discord import app_commands
from discord.ext import commands
from typing import Literal
import datetime

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        # Check om användare har admin-rättigheter
        return ctx.author.guild_permissions.administrator

    @app_commands.command(name="tournament-create", description="Skapa en ny turnering")
    @app_commands.describe(
        name="Turneringens namn",
        game_mode="Spelläge",
        tournament_type="Turneringstyp",
        max_players="Max antal deltagare"
    )
    async def tournament_create(
        self,
        interaction: discord.Interaction,
        name: str,
        game_mode: Literal['1v1', '2v2', '5v5'],
        tournament_type: Literal['single_elim', 'double_elim', 'round_robin'],
        max_players: int = 32
    ):
        """Skapa en ny turnering med wizard"""

        # Skapa modal för ytterligare detaljer
        modal = TournamentModal(name, game_mode, tournament_type, max_players)
        await interaction.response.send_modal(modal)

class TournamentModal(discord.ui.Modal, title='Turnerings Detaljer'):
    prize = discord.ui.TextInput(
        label='Pris',
        placeholder='Champion roll + skin',
        required=True,
        max_length=200
    )

    description = discord.ui.TextInput(
        label='Beskrivning',
        style=discord.TextStyle.paragraph,
        placeholder='Beskrivning av turneringen...',
        required=False,
        max_length=500
    )

    start_time = discord.ui.TextInput(
        label='Starttid (YYYY-MM-DD HH:MM)',
        placeholder='2024-12-25 18:00',
        required=True
    )

    def __init__(self, name, game_mode, tournament_type, max_players):
        super().__init__()
        self.name = name
        self.game_mode = game_mode
        self.tournament_type = tournament_type
        self.max_players = max_players

    async def on_submit(self, interaction: discord.Interaction):
        # Parse starttid
        try:
            start_time = datetime.datetime.strptime(
                self.start_time.value,
                '%Y-%m-%d %H:%M'
            )
        except ValueError:
            await interaction.response.send_message(
                '❌ Ogiltigt datumformat! Använd YYYY-MM-DD HH:MM',
                ephemeral=True
            )
            return

        # Skapa turnering i databas
        from database.models import Tournament, TournamentStatus
        from database.database import async_session

        async with async_session() as session:
            tournament = Tournament(
                guild_id=interaction.guild_id,
                name=self.name,
                game_mode=self.game_mode,
                game_type=self.tournament_type,
                max_participants=self.max_players,
                start_time=start_time,
                prize_description=self.prize.value,
                created_by=interaction.user.id,
                status=TournamentStatus.SIGNUP
            )
            session.add(tournament)
            await session.commit()

            # Skapa announcement embed
            embed = discord.Embed(
                title=f"🏆 {self.name}",
                description=self.description.value or "En ny turnering har skapats!",
                color=discord.Color.gold(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.add_field(name="Spelläge", value=self.game_mode, inline=True)
            embed.add_field(name="Typ", value=self.tournament_type.replace('_', ' ').title(), inline=True)
            embed.add_field(name="Max Deltagare", value=str(self.max_players), inline=True)
            embed.add_field(name="Starttid", value=f"<t:{int(start_time.timestamp())}:F>", inline=False)
            embed.add_field(name="Pris", value=self.prize.value, inline=False)
            embed.set_footer(text=f"Turnerings-ID: {tournament.id}")

            # Signup button
            view = SignupView(tournament.id)

            await interaction.response.send_message(
                content="@everyone 🎮 **NY TURNERING!**",
                embed=embed,
                view=view
            )

class SignupView(discord.ui.View):
    def __init__(self, tournament_id):
        super().__init__(timeout=None)
        self.tournament_id = tournament_id

    @discord.ui.button(label='Sign Up ✅', style=discord.ButtonStyle.green)
    async def signup(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Logic för signup (implementeras i player.py)
        from database.models import TournamentParticipant
        from database.database import async_session

        async with async_session() as session:
            # Kolla om redan anmäld
            # Lägg till participant
            # Skicka bekräftelse
            await interaction.response.send_message(
                '✅ Du är nu anmäld till turneringen!',
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
```

### ELO Calculator (`utils/elo.py`)

```python
def calculate_elo(winner_elo: int, loser_elo: int, winner_matches: int = 0) -> tuple[int, int]:
    """
    Beräkna nya ELO ratings efter en match.

    Args:
        winner_elo: Vinnarens nuvarande ELO
        loser_elo: Förlorarens nuvarande ELO
        winner_matches: Antal matcher vinnaren spelat (för K-factor)

    Returns:
        Tuple med (ny winner ELO, ny loser ELO)
    """

    # Bestäm K-factor baserat på antal matcher
    if winner_matches < 10:
        k_factor = 40  # Nya spelare
    elif winner_matches < 100:
        k_factor = 32  # Etablerade spelare
    else:
        k_factor = 24  # Masters

    # Beräkna förväntad vinst-sannolikhet
    expected_winner = 1 / (1 + 10 ** ((loser_elo - winner_elo) / 400))
    expected_loser = 1 - expected_winner

    # Beräkna nya ratings
    new_winner_elo = winner_elo + k_factor * (1 - expected_winner)
    new_loser_elo = loser_elo + k_factor * (0 - expected_loser)

    return round(new_winner_elo), round(new_loser_elo)

def calculate_team_elo(member_elos: list[int]) -> int:
    """Beräkna team ELO som genomsnitt av medlemmar"""
    return round(sum(member_elos) / len(member_elos))

def elo_change_description(old_elo: int, new_elo: int) -> str:
    """Skapa beskrivning av ELO-förändring"""
    change = new_elo - old_elo
    emoji = "📈" if change > 0 else "📉"
    sign = "+" if change > 0 else ""
    return f"{emoji} {old_elo} → {new_elo} ({sign}{change})"
```

### Bracket Generator (`utils/bracket.py`)

```python
import math
from typing import List, Tuple
from database.models import Match, TournamentParticipant

def generate_single_elimination(tournament_id: int, participants: List[TournamentParticipant]) -> List[Match]:
    """
    Generera single elimination bracket.

    Args:
        tournament_id: Turnerings-ID
        participants: Lista med anmälda deltagare

    Returns:
        Lista med Match-objekt för första rundan
    """

    num_participants = len(participants)

    # Beräkna antal rounds
    num_rounds = math.ceil(math.log2(num_participants))
    bracket_size = 2 ** num_rounds

    # Seed deltagare
    seeded = seed_participants(participants)

    # Lägg till byes om nödvändigt
    byes_needed = bracket_size - num_participants

    matches = []
    match_number = 1

    # Skapa första rundan
    for i in range(0, len(seeded), 2):
        p1 = seeded[i] if i < len(seeded) else None
        p2 = seeded[i + 1] if i + 1 < len(seeded) else None

        match = Match(
            tournament_id=tournament_id,
            round_number=1,
            match_number=match_number,
            participant1_id=p1.id if p1 else None,
            participant2_id=p2.id if p2 else None,
            status='pending'
        )

        # Om någon är None, automatisk vinst
        if p2 is None:
            match.winner_id = p1.id
            match.status = 'completed'

        matches.append(match)
        match_number += 1

    return matches

def seed_participants(participants: List[TournamentParticipant], method: str = 'elo') -> List[TournamentParticipant]:
    """
    Seed deltagare för bracket.

    Methods:
        - 'elo': Sortera efter ELO rating
        - 'random': Slumpmässig
        - 'signup': First come first serve
    """

    if method == 'elo':
        # Sortera efter ELO (högst först)
        return sorted(participants, key=lambda p: p.player.elo_rating, reverse=True)
    elif method == 'random':
        import random
        shuffled = participants.copy()
        random.shuffle(shuffled)
        return shuffled
    else:  # signup
        return sorted(participants, key=lambda p: p.signup_time)

def advance_winner(match: Match, winner_id: int, session) -> Match:
    """
    Skapa nästa match för vinnare.

    Returns:
        Nästa match som vinnaren ska spela, eller None om final
    """

    # Hitta eller skapa nästa match
    next_round = match.round_number + 1
    next_match_number = (match.match_number + 1) // 2

    # Kolla om next match redan finns
    next_match = session.query(Match).filter_by(
        tournament_id=match.tournament_id,
        round_number=next_round,
        match_number=next_match_number
    ).first()

    if not next_match:
        next_match = Match(
            tournament_id=match.tournament_id,
            round_number=next_round,
            match_number=next_match_number,
            status='pending'
        )
        session.add(next_match)

    # Sätt vinnare i rätt slot (om/jämn match nummer)
    if match.match_number % 2 == 1:  # Udda = participant1
        next_match.participant1_id = winner_id
    else:  # Jämn = participant2
        next_match.participant2_id = winner_id

    return next_match
```

---

## 🎨 Embed Examples (`utils/embeds.py`)

```python
import discord
from datetime import datetime

def create_tournament_announcement(tournament) -> discord.Embed:
    """Skapa announcement embed för ny turnering"""

    embed = discord.Embed(
        title=f"🏆 {tournament.name}",
        description=f"En ny **{tournament.game_mode}** turnering har skapats!",
        color=discord.Color.gold(),
        timestamp=datetime.utcnow()
    )

    # Mode & Type
    embed.add_field(
        name="📋 Format",
        value=f"**Mode:** {tournament.game_mode}\n**Type:** {tournament.game_type.replace('_', ' ').title()}",
        inline=True
    )

    # Players
    embed.add_field(
        name="👥 Deltagare",
        value=f"0/{tournament.max_participants}",
        inline=True
    )

    # Prize
    embed.add_field(
        name="🎁 Pris",
        value=tournament.prize_description,
        inline=False
    )

    # Start time
    timestamp = int(tournament.start_time.timestamp())
    embed.add_field(
        name="⏰ Starttid",
        value=f"<t:{timestamp}:F>\n(<t:{timestamp}:R>)",
        inline=False
    )

    embed.set_footer(text=f"Turnerings-ID: {tournament.id} | Använd knapparna nedan för att anmäla dig!")
    embed.set_thumbnail(url="https://i.imgur.com/tournament_icon.png")  # Din server-icon

    return embed

def create_match_embed(match, player1, player2) -> discord.Embed:
    """Skapa match-kort"""

    embed = discord.Embed(
        title=f"⚔️ Match #{match.match_number} - Round {match.round_number}",
        color=discord.Color.blue()
    )

    # Teams/Players
    embed.add_field(
        name="🔵 Team 1",
        value=f"**{player1.username}**\nELO: {player1.elo_rating}",
        inline=True
    )

    embed.add_field(
        name="🆚",
        value="\u200b",
        inline=True
    )

    embed.add_field(
        name="🔴 Team 2",
        value=f"**{player2.username}**\nELO: {player2.elo_rating}",
        inline=True
    )

    # Status
    status_emoji = {
        'pending': '⏳ Väntar',
        'ongoing': '🎮 Pågående',
        'completed': '✅ Avslutad'
    }
    embed.add_field(
        name="Status",
        value=status_emoji.get(match.status, '❓'),
        inline=False
    )

    embed.set_footer(text=f"Match ID: {match.id}")

    return embed

def create_player_profile(player, recent_matches) -> discord.Embed:
    """Skapa spelarprofil"""

    win_rate = (player.total_wins / player.total_matches * 100) if player.total_matches > 0 else 0

    embed = discord.Embed(
        title=f"👤 {player.username}",
        color=discord.Color.blue()
    )

    # Stats
    embed.add_field(
        name="📊 Statistik",
        value=f"**ELO:** {player.elo_rating}\n"
              f"**Matcher:** {player.total_matches}\n"
              f"**Vinster:** {player.total_wins}\n"
              f"**Förluster:** {player.total_losses}\n"
              f"**Win Rate:** {win_rate:.1f}%",
        inline=True
    )

    # Achievements
    embed.add_field(
        name="🏆 Prestationer",
        value=f"**Turneringar Vunna:** {player.tournaments_won}\n"
              f"**Högsta ELO:** {player.elo_rating}",  # Lägg till max_elo kolumn
        inline=True
    )

    # Recent matches (simplified)
    if recent_matches:
        recent_text = "\n".join([
            f"{'✅' if m.winner_id == player.user_id else '❌'} vs {m.opponent_name}"
            for m in recent_matches[:5]
        ])
        embed.add_field(
            name="📜 Senaste Matcher",
            value=recent_text,
            inline=False
        )

    embed.set_footer(text=f"Medlem sedan {player.created_at.strftime('%Y-%m-%d')}")

    return embed

def create_leaderboard(players, category='elo') -> discord.Embed:
    """Skapa leaderboard"""

    medals = ['🥇', '🥈', '🥉']

    embed = discord.Embed(
        title="🏆 Leaderboard",
        description=f"Top spelare sorterat efter **{category.upper()}**",
        color=discord.Color.gold()
    )

    leaderboard_text = []
    for i, player in enumerate(players[:10], 1):
        medal = medals[i-1] if i <= 3 else f"`#{i}`"

        if category == 'elo':
            value = f"{player.elo_rating} ELO"
        elif category == 'wins':
            value = f"{player.total_wins} vinster"
        elif category == 'tournaments':
            value = f"{player.tournaments_won} turneringar"

        leaderboard_text.append(f"{medal} **{player.username}** - {value}")

    embed.description += "\n\n" + "\n".join(leaderboard_text)
    embed.set_footer(text="Uppdateras varje 5 minuter")

    return embed
```

---

## 🚨 Common Issues & Solutions

### Issue 1: Bot inte svarar på slash commands

**Lösning:**

- Kolla att bot har rätt permissions i servern
- Verifiera att `bot.tree.sync()` körs i `on_ready`
- Vänta upp till 1 timme för Discord cache

### Issue 2: Voice channel operations failar

**Lösning:**

- Bot behöver "Move Members" permission
- Spelare måste vara i en voice channel först
- Använd try-except för alla voice operations

### Issue 3: Database connection errors

**Lösning:**

- Verifiera DATABASE_URL format
- För Railway/Supabase, använd `postgresql+asyncpg://`
- Kolla att databas är tillgänglig från botens IP

### Issue 4: ELO ratings blir skeva

**Lösning:**

- Kolla att K-factor är rimlig (32 är standard)
- Verifiera att båda spelare uppdateras
- Testa med manuella beräkningar

### Issue 5: Bracket generation failar med udda antal

**Lösning:**

- Implementera "bye" logic korrekt
- Testa med 3, 5, 7, 9 deltagare
- Hantera edge cases (1 eller 2 deltagare)

---

## 📱 Discord Bot Best Practices

### Performance

- ✅ Använd connection pooling för databas
- ✅ Cache leaderboards och stats
- ✅ Batch database operations
- ✅ Använd ephemeral messages för errors
- ❌ Skicka inte för många meddelanden snabbt (rate limits)

### Security

- ✅ Använd environment variables för tokens
- ✅ Validera all user input
- ✅ Använd permission checks
- ✅ Logga viktiga actions
- ❌ Exponera inte känslig data i embeds

### UX

- ✅ Använd emojis för tydlighet
- ✅ Ge feedback på alla actions
- ✅ Använd buttons och select menus
- ✅ Förklara errors tydligt
- ❌ Överväldiga inte med information

---

## 🎓 Läranderesurser

### Discord.py

- [Officiell dokumentation](https://discordpy.readthedocs.io/)
- [Discord.py Server](https://discord.gg/dpy)
- [Slash Commands Guide](https://gist.github.com/AbstractUmbra/a9c188797ae194e592efe05fa129c57f)

### PostgreSQL

- [PostgreSQL Tutorial](https://www.postgresqltutorial.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)

### Python Async

- [AsyncIO Documentation](https://docs.python.org/3/library/asyncio.html)
- [Real Python - AsyncIO](https://realpython.com/async-io-python/)

---

## ✅ Final Checklist innan Launch

- [ ] Alla kommandon testade
- [ ] Error handling implementerat överallt
- [ ] Database backups setup
- [ ] Logging konfigurerat
- [ ] Bot permissions korrekt satta
- [ ] Environment variables säkrade
- [ ] Rate limiting implementerat
- [ ] Help command komplett
- [ ] Admin guide skriven
- [ ] Test-turnering genomförd
- [ ] Monitoring setup (uptime)
- [ ] Backup-plan om botten kraschar

---

## 🎉 Nästa Steg

1. **Börja med Fas 1-2** - Setup och databas
2. **Implementera core commands** (Fas 3)
3. **Testa varje feature** innan du går vidare
4. **Deploy tidigt** till Railway för att testa i produktion
5. **Iterera baserat på feedback** från community

**Lycka till med projektet! 🚀**

Om du kör fast eller har frågor, ping mig här med specifika delar du behöver hjälp med!
