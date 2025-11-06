# 🧪 Tournament Bot - Komplett Testningsguide

## 📋 Översikt

Denna guide täcker alla aspekter av botten för att säkerställa att allt fungerar korrekt före launch.

---

## ✅ Pre-Test Setup

### Förberedelser

- [ ] Bot online och synkad med Discord
- [ ] Test-server med minst 5 användare (eller alt-konton)
- [ ] Admin-rättigheter för test-användare
- [ ] Minst 2 voice channels skapade
- [ ] Database ren (eller backup tagen)

---

## 🎯 Fas 1: Grundläggande Funktionalitet

### 1.1 Bot Status & Commands

- [ ] Bot visar online status
- [ ] Bot har korrekt "Watching" status
- [ ] `/help` visar alla kategorier
- [ ] `/help category:admin` fungerar
- [ ] `/help category:player` fungerar
- [ ] `/quickstart` visar snabbguide

**Förväntat resultat:** Alla commands svarar med embeds, inga errors.

---

## 👑 Fas 2: Admin Commands

### 2.1 Server Setup

/setup

- [ ] Guild skapas i databas
- [ ] Success embed visas
- [ ] Ingen error i logs

### 2.2 Lobby Setup

/set-lobby [välj voice channel]

- [ ] Lobby channel sparas
- [ ] Confirmation embed visas

### 2.3 Tournament Creation - 1v1

Perfekt! Låt oss skapa en komplett testningsguide! 🧪
Fas 13: Testing & Polish
Skapa TESTING_GUIDE.md
markdown# 🧪 Tournament Bot - Komplett Testningsguide

## 📋 Översikt

Denna guide täcker alla aspekter av botten för att säkerställa att allt fungerar korrekt före launch.

---

## ✅ Pre-Test Setup

### Förberedelser

- [ ] Bot online och synkad med Discord
- [ ] Test-server med minst 5 användare (eller alt-konton)
- [ ] Admin-rättigheter för test-användare
- [ ] Minst 2 voice channels skapade
- [ ] Database ren (eller backup tagen)

---

## 🎯 Fas 1: Grundläggande Funktionalitet

### 1.1 Bot Status & Commands

- [ ] Bot visar online status
- [ ] Bot har korrekt "Watching" status
- [ ] `/help` visar alla kategorier
- [ ] `/help category:admin` fungerar
- [ ] `/help category:player` fungerar
- [ ] `/quickstart` visar snabbguide

**Förväntat resultat:** Alla commands svarar med embeds, inga errors.

---

## 👑 Fas 2: Admin Commands

### 2.1 Server Setup

```
/setup
```

- [ ] Guild skapas i databas
- [ ] Success embed visas
- [ ] Ingen error i logs

### 2.2 Lobby Setup

```
/set-lobby [välj voice channel]
```

- [ ] Lobby channel sparas
- [ ] Confirmation embed visas

### 2.3 Tournament Creation - 1v1

```
/tournament-create
- Name: Test Tournament 1v1
- Game Mode: 1v1
- Type: single_elim
- Max Players: 8

Modal:
- Prize: Test Prize
- Description: Test beskrivning
- Start Time: [om 10 minuter från nu]
- Game: CS2
- Maps: Dust2, Mirage, Inferno, Nuke, Overpass, Vertigo, Ancient
- BO Format: 1
```

- [ ] Modal öppnas
- [ ] Tournament skapas i databas
- [ ] Announcement embed postas
- [ ] Signup/Withdraw buttons visas
- [ ] Turnerings-ID noterat: `_____`

### 2.4 Tournament Creation - 5v5

```
/tournament-create
- Name: Test Tournament 5v5
- Game Mode: 5v5
- Type: single_elim
- Max Players: 4 (2 lag)

Modal: [Samma som ovan]
```

- [ ] Tournament skapas
- [ ] Endast lag-captains kan signa upp
- [ ] Turnerings-ID noterat: `_____`

### 2.5 Tournament List

```
/tournament-list
```

- [ ] Alla turneringar visas
- [ ] Status korrekt (signup/ongoing/completed)
- [ ] Timestamps korrekta

### 2.6 Tournament Delete

```
/tournament-delete [test_tournament_id]
```

- [ ] Tournament raderas
- [ ] Alla relaterade data cleanup
- [ ] Success meddelande

---

## 🎮 Fas 3: Player Commands

### 3.1 Player Registration (Automatisk)

```
/my-stats
```

- [ ] Spelarprofil skapas automatiskt
- [ ] Default värden: ELO 1000, 0 matcher
- [ ] Profile embed visas

### 3.2 Signup - Solo (1v1)

**Test med 4+ användare:**

Användare 1:

```
/signup [tournament_id]
```

- [ ] Bekräftelse-meddelande
- [ ] Participant count uppdateras i announcement (1/8)

Användare 2-4: Upprepa

- [ ] Alla kan signa upp
- [ ] Counter uppdateras (4/8)

### 3.3 Withdraw

Användare 4:

```
/withdraw [tournament_id]
```

- [ ] Spelare tas bort
- [ ] Counter minskar (3/8)

### 3.4 Signup via Button

Användare 4: Klicka "Anmäl dig ✅"

- [ ] Fungerar identiskt som command
- [ ] Counter ökar (4/8)

### 3.5 My Tournaments

```
/my-tournaments
```

- [ ] Visar aktiva turneringar
- [ ] Korrekt information

### 3.6 Leaderboard

```
/leaderboard
```

- [ ] Visar spelare sorterade efter ELO
- [ ] Default top 10
- [ ] Embeds formaterat korrekt

### 3.7 Profile

```
/profile [@annan_användare]
```

- [ ] Visar annan spelares stats
- [ ] Korrekt ELO, matcher, etc

---

## 👥 Fas 4: Team System

### 4.1 Team Creation

Användare A (Captain):

```
/team-create
- Name: Alpha Squad
- Tag: ALPH
```

- [ ] Lag skapas
- [ ] Captain blir medlem automatiskt
- [ ] Team ID noterat: `_____`

Användare B (Captain):

```
/team-create
- Name: Beta Team
- Tag: BETA
```

- [ ] Andra laget skapas
- [ ] Team ID noterat: `_____`

### 4.2 Team Invite

Användare A:

```
/team-invite [@användare_C]
```

- [ ] Invite meddelande skickas
- [ ] Accept/Deny buttons visas
- [ ] Timeout fungerar (5 min)

Användare C: Klicka "Acceptera ✅"

- [ ] Går med i laget
- [ ] Bekräftelse-meddelande

### 4.3 Team Info

```
/team-info Alpha Squad
```

- [ ] Visar lag-info
- [ ] Captain och medlemmar listade
- [ ] Stats korrekt

### 4.4 Team List

```
/team-list
```

- [ ] Alla lag visas
- [ ] Sorterade efter ELO
- [ ] Medlemsantal korrekt

### 4.5 Team Signup (5v5)

Captain A:

```
/signup [5v5_tournament_id]
```

- [ ] Endast captain kan anmäla
- [ ] Lag registreras
- [ ] Counter uppdateras

Captain B: Upprepa

- [ ] Två lag registrerade (2/4)

### 4.6 Team Leave

Användare C:

```
/team-leave
```

- [ ] Lämnar laget
- [ ] Captain kan inte lämna (måste delete)

### 4.7 Team Delete

Captain A:

```
/team-delete
```

- [ ] Laget raderas
- [ ] Alla medlemmar tas bort
- [ ] Success meddelande

---

## 🏆 Fas 5: Tournament Flow - 1v1

### 5.1 Start Tournament

**Förberedelse:** Se till att 4+ spelare är anmälda

Admin:

```
/tournament-start [1v1_tournament_id]
```

- [ ] Status ändras till ONGOING
- [ ] Bracket genereras (single elimination)
- [ ] Första rundan skapas
- [ ] Embed visar matchups
- [ ] Voice channels skapas automatiskt
- [ ] Text channels skapas för varje match
- [ ] Map ban phase startar

**Verifiera:**

- [ ] Antal matcher korrekt (4 spelare = 2 matcher)
- [ ] Inga BYEs (eller korrekt hanterade)
- [ ] Match IDs noterade

### 5.2 Voice Channel Auto-Move

**Alla deltagare:** Gå in i lobby voice channel

- [ ] Spelare flyttas automatiskt till sina match-channels
- [ ] Team 1 i en channel, Team 2 i en annan
- [ ] Text channels visar map ban embed

### 5.3 Map Ban Phase

**Match 1 - Kapten för Team 1:**

- [ ] Ser map ban embed
- [ ] Endast kapten kan klicka ban-knappar
- [ ] Första kartan bannades

**Match 1 - Kapten för Team 2:**

- [ ] Nästa ban inom 30 sekunder
- [ ] Embed uppdateras live för båda lagen
- [ ] Andra kartan bannades

**Fortsätt alternerat:**

- [ ] Totalt rätt antal bans (för BO1: 6 bans, 1 kvar)
- [ ] Om timeout: Random ban sker
- [ ] Final embed visar:
  - [ ] Kvarvarande karta(or)
  - [ ] Slumpmässiga sidor (CT/T)
  - [ ] Ordning (för BO3)

### 5.4 Match Report - Match 1

Vinnare:

```
/report-win [match_1_id] 1 0
```

- [ ] Report-embed skickas
- [ ] Opponent taggad
- [ ] Bekräfta/Avvisa buttons visas

Opponent: Klicka "Bekräfta ✅"

- [ ] Match status → COMPLETED
- [ ] ELO uppdateras (visar change)
- [ ] Win/loss stats uppdateras
- [ ] Match history sparas
- [ ] Achievement check (First Blood, etc)
- [ ] Voice channels stängs efter 30 sek
- [ ] Spelare flyttas tillbaka till lobby
- [ ] Nästa match setup automatiskt (om applicable)

### 5.5 Bracket Progression

```
/bracket [tournament_id]
```

- [ ] Match 1 visar ✅ completed
- [ ] Vinnare avancerad till nästa round
- [ ] Round 2 match skapad (om applicable)

### 5.6 Match Info

```
/match-info [match_id]
```

- [ ] Visar match-detaljer
- [ ] Deltagare, status, resultat
- [ ] Timestamps korrekta

### 5.7 Disputed Match

**Alternative Flow:** Opponent klickar "Avvisa ❌"

- [ ] Match status → DISPUTED
- [ ] Notifikation till admin
- [ ] Voice channels stänger inte

Admin:

```
/resolve-dispute [match_id] [winner_id] 1 0
```

- [ ] Match resolved
- [ ] ELO uppdateras
- [ ] Progression fortsätter

### 5.8 Tournament Completion

**När sista matchen rapporteras:**

- [ ] Tournament status → COMPLETED
- [ ] Champion history sparas
- [ ] Winner får tournaments_won +1
- [ ] Achievement "Champion" check
- [ ] Winner announcement i chatten
- [ ] Voice channels cleanup

---

## 🎖️ Fas 6: Seasons & Statistics

### 6.1 Season Creation

```
/season-create
- Name: Season 1
- Duration: 90 days
```

- [ ] Season skapas
- [ ] Alla befintliga spelare får season stats
- [ ] Active season flagga satt

### 6.2 Season Info

```
/season-info
```

- [ ] Visar current season
- [ ] Startdatum, slutdatum
- [ ] Tid kvar
- [ ] Antal spelare/turneringar

### 6.3 Season Leaderboard

```
/season-leaderboard
```

- [ ] Visar top 10 för season
- [ ] Separata stats från overall

### 6.4 Match History

```
/match-history [@user]
```

- [ ] Visar senaste 10 matcherna
- [ ] Win/loss indikerat
- [ ] ELO change visas
- [ ] Opponent namn korrekt

### 6.5 Season End

```
/season-end
```

- [ ] Season avslutas
- [ ] Top 3 announcement
- [ ] Season flagga inactive
- [ ] Stats bevaras

### 6.6 Season List

```
/season-list
```

- [ ] Alla seasons listade
- [ ] Active/Completed status
- [ ] Kan se gamla season leaderboards

---

## 🏅 Fas 7: Achievements

### 7.1 Achievement Initialization

```
/achievement-init
```

- [ ] 12 default achievements skapas
- [ ] Success meddelande
- [ ] Inga duplicates

### 7.2 Achievement Unlock - First Blood

**Ny spelare vinner första matchen:**

- [ ] "First Blood" achievement unlocked
- [ ] Announcement i chatten med embed
- [ ] Achievement sparas i databas

### 7.3 Achievement Unlock - Win Streak

**Spelare vinner 3 i rad:**

- [ ] "Hot Streak" achievement
- [ ] Announcement

**Vinner 5 i rad:**

- [ ] "Unstoppable" achievement

**Förlorar en:**

- [ ] Win streak reset till 0

### 7.4 Achievement Unlock - ELO Milestone

**Spelare når 1200 ELO:**

- [ ] "Rising Star" unlocked
- [ ] Announcement

### 7.5 Achievement Unlock - Tournament Win

**Spelare vinner turnering:**

- [ ] "Champion" unlocked
- [ ] Announcement

### 7.6 View Achievements

```
/achievements
```

- [ ] Visar unlocked achievements
- [ ] Timestamps
- [ ] Counter (X/12)

```
/achievements [@annan_user]
```

- [ ] Visar andras achievements

### 7.7 List All Achievements

```
/achievements-list
```

- [ ] Alla 12 achievements listade
- [ ] Grupperade per typ
- [ ] Beskrivningar korrekta

---

## 🔄 Fas 8: Automated Scheduling

### 8.1 Template Creation

```
/template-create
- Name: Weekly CS2 Tournament
- Game Mode: 1v1
- Type: single_elim
- Recurring: True
- Day of Week: 5 (Fredag)
- Time: 18:00
- Recurrence: weekly

Modal: [Fyll i detaljer]
```

- [ ] Template skapas
- [ ] Scheduled info korrekt
- [ ] Template ID noterat

### 8.2 Template List

```
/template-list
```

- [ ] Template visas
- [ ] Status: Aktiv
- [ ] Schema korrekt
- [ ] Last created: null (första gången)

### 8.3 Auto-Creation Test

**Simulera scheduled tid (ändra tid till nu +5 min för test):**

Vänta tills scheduler körs (varje timme)

- [ ] Tournament skapas automatiskt
- [ ] Announcement i chatten
- [ ] Signup buttons fungerar
- [ ] Template last_created uppdaterad

### 8.4 Template Toggle

```
/template-toggle [template_id]
```

- [ ] Status ändras till Pausad
- [ ] Ingen auto-creation nästa gång

```
/template-toggle [template_id]
```

- [ ] Aktiv igen

### 8.5 Template Delete

```
/template-delete [template_id]
```

- [ ] Template raderad
- [ ] Inga fler auto-creations

---

## 🔔 Fas 9: Notifications

### 9.1 Tournament Reminders

**Skapa turnering som startar om 25 timmar:**

Vänta 23 timmar (eller ändra sistem tid för test)

- [ ] 24h reminder skickas
- [ ] Alla deltagare taggade
- [ ] Korrekt tid visad

**Vänta till 1 timme kvar:**

- [ ] 1h reminder skickas

**Vänta till 5 min kvar:**

- [ ] 5 min reminder skickas

### 9.2 Match Notifications

**När match startas:**

- [ ] Deltagare får notis
- [ ] Voice channel info inkluderad

---

## 🎙️ Fas 10: Voice System

### 10.1 Manual Setup

```
/setup-match [match_id]
```

- [ ] 2 voice channels skapas
- [ ] 2 text channels skapas
- [ ] Spelare flyttas (om i lobby)
- [ ] Map ban startar

### 10.2 Auto-Move on Join

**Spelare med aktiv match går in i lobby:**

- [ ] Flyttas automatiskt till match-channel
- [ ] Korrekt team-channel

### 10.3 Cleanup

**Efter match completion:**

- [ ] Voice channels raderas efter 30 sek
- [ ] Text channels raderas
- [ ] Spelare flyttas till lobby

### 10.4 Emergency Cleanup

```
/cleanup-all
```

- [ ] Alla match-channels raderas
- [ ] Kategorier rensas
- [ ] Inga errors

---

## 🐛 Fas 11: Edge Cases & Error Handling

### 11.1 Odd Number of Participants

**Skapa turnering, anmäl 3 spelare, starta:**

- [ ] BYE hanteras korrekt
- [ ] En spelare går direkt vidare
- [ ] Bracket balanserad

### 11.2 Player Disconnect During Match

**Spelare lämnar voice under match:**

- [ ] Match fortsätter
- [ ] Report fungerar ändå
- [ ] Cleanup fungerar

### 11.3 Concurrent Tournaments

**Skapa och kör 2 turneringar samtidigt:**

- [ ] Voice channels separerade
- [ ] Ingen konflikt i matcher
- [ ] Båda kan completeas oberoende

### 11.4 Permission Errors

**Ta bort bot permissions (Manage Channels):**

- [ ] Graceful error meddelande
- [ ] Loggas korrekt
- [ ] Ingen crash

**Återställ permissions:**

- [ ] Fungerar igen

### 11.5 Invalid Commands

```
/signup 99999
```

- [ ] "Tournament not found" error
- [ ] Ephemeral message

```
/report-win 99999 1 0
```

- [ ] "Match not found" error

### 11.6 Double Signup

**Samma användare:**

```
/signup [tournament_id]
/signup [tournament_id]
```

- [ ] Andra gången: "Already signed up"

### 11.7 Full Tournament

**Turnering med max 4, 4 anmälda:**

Femte användare:

```
/signup [tournament_id]
```

- [ ] "Tournament is full" error

### 11.8 Non-Admin Commands

**Vanlig användare försöker:**

```
/tournament-create
```

- [ ] Permission denied error

### 11.9 Database Connection Loss

**Simulera DB disconnect:**

- [ ] Errors loggade
- [ ] User-friendly error meddelande
- [ ] Ingen crash
- [ ] Auto-reconnect vid nästa command

---

## 📊 Fas 12: Performance & Load Testing

### 12.1 Large Tournament

**Skapa tournament med 64 deltagare:**

- [ ] Bracket genereras korrekt
- [ ] Alla 32 första round matcher
- [ ] Inte performance issues
- [ ] Memory usage ok (<500MB)

### 12.2 Rapid Commands

**Skicka 10 commands snabbt efter varandra:**

```
/my-stats
/leaderboard
/my-tournaments
... (repeat)
```

- [ ] Alla svarar
- [ ] Inga rate limit errors
- [ ] Ingen crash

### 12.3 Database Query Performance

**Check logs för slow queries (>1 sekund):**

- [ ] Leaderboard <1s
- [ ] Tournament list <1s
- [ ] Bracket generation <2s

### 12.4 Long-Running Bot

**Låt bot köra i 24+ timmar:**

- [ ] Ingen memory leak
- [ ] Notifications fungerar
- [ ] Schedulers fungerar
- [ ] Connections stabila

---

## ✅ Final Checklist

### Funktionalitet

- [ ] Alla commands fungerar
- [ ] Inga critical errors i logs
- [ ] Voice system 100% functional
- [ ] Map ban system fungerar
- [ ] ELO calculations korrekta
- [ ] Achievements unlocking
- [ ] Notifications skickas
- [ ] Auto-scheduling fungerar
- [ ] Seasons fungerar

### User Experience

- [ ] Alla embeds ser professionella ut
- [ ] Error messages hjälpsamma
- [ ] Response times <2 sekunder
- [ ] Buttons/modals responsiva
- [ ] Help commands kompletta

### Performance

- [ ] Memory usage <500MB
- [ ] CPU usage <50% under load
- [ ] Database queries optimerade
- [ ] Inga memory leaks
- [ ] Logs inte överflödade

### Security

- [ ] .env inte committad till git
- [ ] Permissions checks fungerar
- [ ] SQL injection skyddad (SQLAlchemy)
- [ ] Rate limiting implementerat
- [ ] Admin commands skyddade

### Reliability

- [ ] Auto-restart vid crash (systemd)
- [ ] Database backups schemalagda
- [ ] Error notifications till admin
- [ ] Logs roterade
- [ ] Uptime >99%

### Documentation

- [ ] README komplett
- [ ] Deployment guide testad
- [ ] Help commands uppdaterade
- [ ] Comments i kod där nödvändigt
- [ ] This testing guide genomförd ✅

---

## 🚀 Post-Testing Actions

### Om alla tester passerade:

1. ✅ Tag en full database backup
2. ✅ Dokumentera alla test results
3. ✅ Uppdatera version number
4. ✅ Gör en release commit: "v1.0.0 - Production Ready"
5. ✅ Deploy till production
6. ✅ Övervaka logs i 48 timmar

### Om tester failade:

1. 📝 Dokumentera alla failures
2. 🐛 Prioritera bugfixes
3. 🔧 Fixa issues
4. 🔄 Kör relevanta tester igen
5. ✅ Fortsätt till nästa test

---

## 📞 Support & Debugging

### Vanliga Problem & Lösningar

**Problem:** Commands syns inte i Discord

- **Lösning:** Kör bot restart, vänta 5 min, kör `/sync` om du har det

**Problem:** Voice channels skapas inte

- **Lösning:** Verifiera Manage Channels permission

**Problem:** ELO uppdateras inte

- **Lösning:** Check match completion logic, verifiera database commit

**Problem:** Scheduler fungerar inte

- **Lösning:** Restart bot, verifiera scheduler startad i logs

**Problem:** Database errors

- **Lösning:** Check connection string, verifiera database existerar

---

## 📈 Test Metrics

Efter alla tester, dokumentera:

- **Total Commands Tested:** **\_**
- **Commands Passed:** **\_**
- **Commands Failed:** **\_**
- **Bugs Found:** **\_**
- **Bugs Fixed:** **\_**
- **Average Response Time:** **\_** ms
- **Peak Memory Usage:** **\_** MB
- **Test Duration:** **\_** hours

---

**✅ Testing Complete!**

Om alla tester passerat, är botten redo för production!
