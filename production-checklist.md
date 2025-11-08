# Production Deployment Checklist

## Pre-Deployment

- [ ] Alla features testade lokalt
- [ ] Error handling implementerat överallt
- [ ] Logging konfigurerat korrekt
- [ ] `.env` fil med riktiga credentials
- [ ] `.gitignore` innehåller `.env` och `tournament.db`
- [ ] `requirements.txt` uppdaterad
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
