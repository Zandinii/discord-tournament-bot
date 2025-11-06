# Discord Tournament Bot - Deployment Guide

## Oracle Cloud Always Free Tier Setup

### 1. Skapa Oracle Cloud Konto

1. Gå till https://www.oracle.com/cloud/free/
2. Skapa konto (kräver kreditkort men debiteras aldrig)
3. Bekräfta email

### 2. Skapa Compute Instance (VPS)

1. Logga in på Oracle Cloud Console
2. Gå till "Compute" → "Instances"
3. Klicka "Create Instance"
4. Konfigurera:
   - **Name:** tournament-bot
   - **Image:** Ubuntu 22.04 (Always Free Eligible)
   - **Shape:** VM.Standard.E2.1.Micro (Always Free)
   - **Network:** Använd default VCN
5. Ladda ner SSH private key (.pem fil)
6. Klicka "Create"

### 3. Konfigurera Firewall (Security List)

1. Gå till instance details
2. Klicka på subnet → Security Lists
3. Lägg till ingress rule:
   - **Source CIDR:** 0.0.0.0/0
   - **Destination Port:** 22 (SSH)

### 4. SSH till servern

```bash
# Sätt rätt permissions på key
chmod 400 ~/Downloads/ssh-key.pem

# SSH in
ssh -i ~/Downloads/ssh-key.pem ubuntu@<PUBLIC_IP>
```

### 5. Installera Dependencies på Servern

```bash
# Uppdatera system
sudo apt update && sudo apt upgrade -y

# Installera Python 3.11+
sudo apt install python3 python3-pip python3-venv git -y

# Installera PostgreSQL (eller använd SQLite)
sudo apt install postgresql postgresql-contrib -y

# Starta PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 6. Setup PostgreSQL (Om du vill använda istället för SQLite)

```bash
# Växla till postgres user
sudo -u postgres psql

# I PostgreSQL prompt:
CREATE DATABASE tournament_db;
CREATE USER tournament_user WITH PASSWORD 'ditt_starka_lösenord';
GRANT ALL PRIVILEGES ON DATABASE tournament_db TO tournament_user;
\q
```

### 7. Klona och Setup Bot

```bash
# Klona repo (eller ladda upp filer)
cd ~
git clone https://github.com/ditt-användarnamn/discord-tournament-bot.git
cd discord-tournament-bot

# Skapa virtual environment
python3 -m venv venv
source venv/bin/activate

# Installera dependencies
pip install -r requirements.txt
```

### 8. Konfigurera Environment Variables

```bash
# Skapa .env fil
nano .env
```

Lägg in:

```env
DISCORD_TOKEN=din_bot_token_här
GUILD_ID=din_server_id_här

# För PostgreSQL:
DATABASE_URL=postgresql+asyncpg://tournament_user:ditt_lösenord@localhost/tournament_db

# För SQLite (enklare):
# DATABASE_URL=sqlite+aiosqlite:///tournament.db
```

Spara med `Ctrl+X`, `Y`, `Enter`

### 9. Testa Botten

```bash
python bot.py
```

Om allt fungerar, tryck `Ctrl+C` för att stoppa.

### 10. Setup Systemd Service

```bash
# Kopiera service fil
sudo cp tournament-bot.service /etc/systemd/system/

# Redigera om nödvändigt (byt användarnamn om du inte är 'ubuntu')
sudo nano /etc/systemd/system/tournament-bot.service

# Reload systemd
sudo systemctl daemon-reload

# Starta botten
sudo systemctl start tournament-bot

# Kolla status
sudo systemctl status tournament-bot

# Aktivera auto-start vid reboot
sudo systemctl enable tournament-bot
```

### 11. Hantera Botten

```bash
# Starta
sudo systemctl start tournament-bot

# Stoppa
sudo systemctl stop tournament-bot

# Restart
sudo systemctl restart tournament-bot

# Se logs
tail -f ~/discord-tournament-bot/bot.log

# Se errors
tail -f ~/discord-tournament-bot/error.log
```

### 12. Uppdatera Botten

```bash
cd ~/discord-tournament-bot

# Stoppa botten
sudo systemctl stop tournament-bot

# Pull nya ändringar
git pull

# Aktivera venv
source venv/bin/activate

# Uppdatera dependencies om nödvändigt
pip install -r requirements.txt

# Starta igen
sudo systemctl start tournament-bot
```

## Backup Strategy

### Automatisk Databas Backup

Skapa backup script `backup.sh`:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/ubuntu/backups"

mkdir -p $BACKUP_DIR

# Backup SQLite
cp ~/discord-tournament-bot/tournament.db $BACKUP_DIR/tournament_$DATE.db

# Eller backup PostgreSQL
# pg_dump -U tournament_user tournament_db > $BACKUP_DIR/tournament_$DATE.sql

# Ta bort backups äldre än 30 dagar
find $BACKUP_DIR -type f -mtime +30 -delete

echo "Backup complete: $DATE"
```

Gör körbar:

```bash
chmod +x backup.sh
```

Setup cron job för dagliga backups:

```bash
crontab -e

# Lägg till (backup kl 03:00 varje dag):
0 3 * * * /home/ubuntu/discord-tournament-bot/backup.sh
```

## Monitoring

### Setup Log Rotation

```bash
sudo nano /etc/logrotate.d/tournament-bot
```

Lägg in:

```
/home/ubuntu/discord-tournament-bot/bot.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 ubuntu ubuntu
}

/home/ubuntu/discord-tournament-bot/error.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 ubuntu ubuntu
}
```

## Troubleshooting

### Botten startar inte

```bash
# Kolla status
sudo systemctl status tournament-bot

# Kolla logs
tail -100 ~/discord-tournament-bot/error.log

# Kolla permissions
ls -la ~/discord-tournament-bot/
```

### Database connection errors

```bash
# För PostgreSQL, testa connection
psql -U tournament_user -d tournament_db -h localhost

# För SQLite, kolla permissions
ls -la ~/discord-tournament-bot/tournament.db
```

### Port inte öppen

```bash
# Kolla firewall
sudo ufw status

# Öppna port om nödvändigt (för web dashboard etc)
sudo ufw allow 8080
```

## Security Best Practices

1. ✅ Använd starka lösenord
2. ✅ Håll system uppdaterat: `sudo apt update && sudo apt upgrade`
3. ✅ Använd SSH keys istället för lösenord
4. ✅ Backup regelbundet
5. ✅ Övervaka logs för errors
6. ✅ Använd `.env` för känslig data
7. ✅ Sätt rätt file permissions: `chmod 600 .env`

## Cost Breakdown

| Service          | Cost                     |
| ---------------- | ------------------------ |
| Oracle Cloud VPS | **GRATIS** (Always Free) |
| Database         | **GRATIS** (Ingår i VPS) |
| Discord Bot      | **GRATIS**               |
| **TOTALT**       | **0 kr/månad** ✅        |

Oracle Cloud Always Free Tier ger:

- 2 x VM.Standard.E2.1.Micro (1GB RAM vardera)
- 200GB block storage
- 10TB utgående trafik/månad
- **Permanent gratis - inget kreditkort debiteras**
