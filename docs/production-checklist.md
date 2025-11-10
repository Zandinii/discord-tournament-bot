# Production Deployment Checklist

## Server Setup

- [ ] VPS/Server skapad
- [ ] SSH access konfigurerat
- [ ] Firewall konfigurerad
- [ ] Python 3.11+ installerat
- [ ] PostgreSQL/SQLite installerat
- [ ] Git installerat

## Bot Deployment

- [ ] Kod uppladdat till server
- [ ] Virtual environment skapat
- [ ] Dependencies installerade
- [ ] `.env` fil skapad med production värden
- [ ] Database initierad
- [ ] Bot testad manuellt
- [ ] Systemd service konfigurerad
- [ ] Service startad och enabled
- [ ] Logs verifierade

## Post-Deployment

- [ ] Bot online i Discord
- [ ] Slash commands synkade
- [ ] Test-turnering genomförd
- [ ] Notifications fungerar
- [ ] Voice channels fungerar
- [ ] Database backups schemalagda
- [ ] Log rotation konfigurerad
- [ ] Monitoring setup
- [ ] Dokumentation uppdaterad
- [ ] Admin team informerat

## Monitoring

- [ ] Setup uptime monitoring (UptimeRobot gratis)
- [ ] Error logging till Discord admin channel
- [ ] Database backup alerts
- [ ] Disk space monitoring

## Maintenance Plan

- [ ] Veckovis: Kolla logs för errors
- [ ] Månadsvis: Uppdatera dependencies
- [ ] Kvartalsvis: Full system update
- [ ] Vid behov: Backup restore test

## TODOs for Future Improvements

- Gör den bara anpassad för CS2
- Lägg till fler turneringsformat som Swiss (Om det inte är som round robin?)
- Lägg till så att en specifik roll får admin rättigheter i boten
- Implementera så att jag kan skicka all statistik för spelare och lag, samt bracket för turneringar till en webbsida för att göra det mer användarvänligt och lättillgängligt.
- profile och my-stats kommandon för spelare är likadant, gör så my stats är för aktiv season bara medan profil är stats för totala statistiken.
- uppdatera /help kommandot och lägg till alla kommandon som saknas som tillexempel season, team kommandon som saknas. Gå igenom alla filer för att se vilka som saknas.
- Lägg till en funktion för att hantera avstängningar och varningar för spelare som bryter mot reglerna. Gör också så att admins kan se vilka spelare är bannad eller varnade sen innan i ett embed som uppdateras automatiskt i en separat text kanal som jag sätter upp bara för admin info embeds.
- Implementera funktionen team-transfer om kommandot inte redan finns, används för att föra över kapten rollen i ett lag till en annan spelare i laget.
- Fixa så att alla embed meddelanden har en konsekvent design och färgschema samt är implementerade i embed.py filen och sen används i koden där dem ska.
- Skapa cs2 servrar automatiskt för matcherna via cs2 mods med rätt inställningar, om man kan göra det själv via cs2 mods och egen server hosting. Gör en guide för hur jag sätter upp allt sånt här så att botten kan skapa lobbies automatiskt för matcherna som ska spelas i turneringarna. Går det att använda Oracle Cloud free tier eller blir det för mycket om vi också ska hosta botten där?
- Samla all statistik från cs2 match serverna automatiskt via cs2 mods eller annan tjänst för att få mer detaljerad statistik om spelarna och matcherna.
- Bug fixes and performance optimizations based on user feedback:
  - För match rummet så ska vi inte skapa 2 separata text kanaler utan all kommunikation för en match ska ske i voice kanal text chatten.
  - Lägg till Match ID i embed meddelanden för match för enklare referens.
  - Optimera databasanrop för att minska latens vid höga belastningar.
  - Lägg till så att bracketen visas i voice lobby kanalens text chat och uppdateras automatiskt efter varje match.
  - Fixa så att när en spelare lämnar ett lag så tas den bort från laget i databasen direkt utan att behöva köra /update-team kommandot manuellt.
  - Fixa potentiella errors som uppkommer.
- Gör alla embed meddelanden mer användarvänliga och informativa så att en som inte har någon koll alls förstår vad som behövs göras och inte behöver fråga om hjälp hela tiden. Kolla över alla embeds och lägg till fler där det behövs samt lägg till mer information i befintliga embeds.
- Fixa ELO systemet så att det blir jämnare, manuellt skriva in faceit elo och premier elo för CS2. Se exempel nedan för hur premier eller faceit ranken ska översättas till bottens elo.
- Ta bort så man inte singlar slant om vem som börjar som T eller CT utan sätt upp servern så att man börjar med knife round som vanligt i CS2 turneringar.
- Testa och optimera för större turneringar (100+ deltagare)
