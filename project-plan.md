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

## 🚀 Fas 12: Hosting & Deployment (Dag 31-32)

### 12.1 Oracle Cloud Always Free Tier Setup (Rekommenderat GRATIS)

**Steg:**

1. [ ] Skapa konto på [Oracle Cloud](https://www.oracle.com/cloud/free/)
2. [ ] Skapa en "Compute Instance" (VPS)
3. [ ] Installera Python, PostgreSQL på VPS
4. [ ] Klona ditt GitHub repo
5. [ ] Sätt upp systemd service för att köra botten
6. [ ] Konfigurera miljövariabler
7. [ ] Starta botten och verifiera att den körs

**Oracle Cloud Always Free Tier:**

- Gratis VPS med 1GB RAM och 1 vCPU
- Gratis databaser (Autonomous Database)
- 2TB lagring

### 12.2 Production Checklist

- [ ] Environment variables korrekt satta
- [ ] Database migrations körda
- [ ] Logging konfigurerat
- [ ] Error notifications (till admin DM)
- [ ] Backup-strategi för databas
- [ ] Rate limiting för commands
- [ ] Caching för leaderboards

---

## 🧪 Fas 13: Testing & Polish (Dag 33-35)

### 13.1 Testing

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

### 13.2 Error Handling

- [ ] Try-catch på alla discord operations
- [ ] Graceful degradation
- [ ] User-friendly error messages
- [ ] Admin error logs

### 13.3 Performance

- [ ] Database indexes på ofta queriade kolumner
- [ ] Cache leaderboards (update varje 5 min)
- [ ] Batch operations där möjligt
- [ ] Async operations för alla I/O

---

## 📚 Fas 14: Dokumentation (Dag 36-37)

### 14.1 Användar-dokumentation

- [ ] Skapa `/help` kommando
- [ ] Kategori-baserad hjälp (Admin, Player, Team)
- [ ] Tutorial för nya användare
- [ ] FAQ i Discord kanal

### 14.2 Admin Guide

- [ ] Setup instruktioner
- [ ] Hur man skapar turneringar
- [ ] Hur man hanterar disputes
- [ ] Troubleshooting

### 14.3 Developer Docs

- [ ] README med setup-instruktioner
- [ ] Code comments
- [ ] Architecture overview
- [ ] Contributing guidelines (om open source)

---

## 🎯 Fas 15: Launch & Monitoring (Dag 38-40)

### 15.1 Soft Launch

- [ ] Testa med liten grupp users
- [ ] Kör test-turnering
- [ ] Samla feedback
- [ ] Fixa buggar

### 15.2 Full Launch

- [ ] Announcement i servern
- [ ] Tutorial-session
- [ ] Första riktiga turneringen
- [ ] Monitor för errors

### 15.3 Monitoring & Maintenance

- [ ] Setup logging (Loguru eller standard logging)
- [ ] Monitor bot uptime
- [ ] Database backup schedule
- [ ] Regelbundna updates

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
