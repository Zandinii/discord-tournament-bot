# Discord Turnerings Bot - Detaljerad Projektplan

## 📋 Projektöversikt

En komplett turnerings-bot för Discord som hanterar veckovisa community-turneringar med automatisk matchhantering, voice channel-management, ELO-system och statistik.

**Tech Stack:**

- Python 3.11+
- Discord.py 2.3+
- PostgreSQL (gratis via Supabase/Railway)
- Hosting: Railway.app (gratis tier) eller lokal körning

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
