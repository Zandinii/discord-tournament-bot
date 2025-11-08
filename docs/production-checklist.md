# Production Deployment Checklist

## Pre-Deployment

- [x] Alla features testade lokalt
- [x] Error handling implementerat överallt
- [ ] Logging konfigurerat korrekt
- [x] `.env` fil med riktiga credentials
- [x] `.gitignore` innehåller `.env` och `tournament.db`
- [x] `requirements.txt` uppdaterad
- [ ] Database migrations körda
- [ ] Backup-strategi planerad

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

- Fixa ELO systemet så att det blir jämnare, manuellt skriva in faceit elo och premier elo för CS2
- Gör den bara anpassad för CS2
- Lägg till fler turneringsformat (t.ex. Swiss)
- Lägg till så att en specifik roll får admin rättigheter i boten
- Implementera Xplay server för att automatiskt skapa spelservrar för matcherna till CS2
- Testa och optimera för större turneringar (100+ deltagare)
- Implementera en webbsida för att visa turneringsstatus, resultat, brackets och statistik.
- Lägg till priser och belöningar för vinnare och deltagare vid säsongsslut.
- profile och my-stats kommandon för spelare är likadant, gör så my stats är för aktiv season bara medan profil är stats för totala statistiken.
- uppdatera /help kommandot och lägg till alla kommandon som saknas som tillexempel season, team kommandon som saknas. Gå igenom alla filer för att se vilka som saknas.
- Lägg till en funktion för att hantera avstängningar och varningar för spelare som bryter mot reglerna.
- Implementera funktionen team-transfer om kommandot inte redan finns, används för att föra över kapten rollen i ett lag till en annan spelare i laget.
- Fixa så att alla embed meddelanden har en konsekvent design och färgschema samt är implementerade i embed.py filen och sen används i koden där dem ska.
