# 🚀 Hosta Discord Bot GRATIS på Oracle Cloud

## ✅ Är det möjligt?

**JA!** Oracle Cloud Free Tier är perfekt för en Discord bot och är **permanent gratis** (inte bara trial).

---

## 📊 Vad får du GRATIS?

### Compute (VM Instances)

- **2x AMD-baserade VMs** med 1 GB RAM vardera
- **ELLER 1x ARM-baserad VM** med upp till 4 OCPUs + 24 GB RAM
- **REKOMMENDATION:** Använd ARM VM (Ampere A1) - mycket kraftfullare!

### Storage

- **200 GB Block Volume** (disk space)
- **10 GB Object Storage**

### Nätverk

- **10 TB utgående trafik per månad** (inkommande obegränsad)

### Databas

- **2x Oracle Autonomous Database** (20 GB vardera)
- **ELLER använd PostgreSQL/MySQL på din VM**

---

## 🎯 Kapacitet för din Bot

Med ARM VM (4 OCPUs + 24 GB RAM):

| Funktion              | Kapacitet                        |
| --------------------- | -------------------------------- |
| Discord Guilds        | 100+ servers                     |
| Samtidiga användare   | 10,000+                          |
| CS2 Server Automation | 2-4 servrar (beroende på config) |
| Databas               | Flera miljoner rader             |
| Uptime                | 99.9%+                           |

**Din bot kommer ALDRIG nå gränsen på Free Tier!**

---

## 💰 Kommer du behöva betala?

### ❌ NEJ om du:

- Håller dig till **Always Free** resurser
- Inte uppgraderar manuellt till "Pay As You Go"
- Inte skapar resurser utanför Free Tier

### ⚠️ Oracle's säkerhetssystem:

- **Automatisk spärr:** Om du försöker skapa något som kostar, får du varning
- **Ingen auto-charge:** Free Tier resurser kan ALDRIG börja kosta
- **Tydlig markering:** Always Free resurser är tydligt märkta

### 🛡️ Extra säkerhet:

- Sätt **Spending Limit: $0** i konto-inställningar
- Du får email-notiser om något händer
- Kan inte ens ladda upp kreditkort för Free Tier

---

## 📝 TODO: Setup Guide

### 1️⃣ Skapa Oracle Cloud Konto

---

### 2️⃣ Skapa VM Instance (ARM Ampere)

```bash
□ Logga in på Oracle Cloud Console
□ Gå till: Menu → Compute → Instances
□ Klicka "Create Instance"

□ Konfigurera:
  Name: discord-tournament-bot

  □ Image:
    - Edit → Image Source
    - Välj "Ubuntu 22.04" (eller 24.04)
    - Shape Series: Ampere

  □ Shape:
    - Click "Change Shape"
    - Välj "VM.Standard.A1.Flex"
    - OCPUs: 2-4 (rekommenderat: 4)
    - RAM: 12-24 GB (rekommenderat: 24 GB)
    ⚠️ VIKTIGT: Detta är GRATIS!

  □ Networking:
    - Create new VCN (standard)
    - Assign public IP: Yes

  □ SSH Keys:
    - Generate SSH key pair
    - Ladda ner BÅDA (private + public)
    - Spara säkert!

  □ Boot Volume:
    - 50-100 GB (inom Free Tier)

□ Klicka "Create"
```

**⏱️ Tid: 5 minuter + 2-5 min provisioning**

**⚠️ OBS:** Om du får fel "Out of capacity" för ARM:

- Prova olika Availability Domains (AD1, AD2, AD3)
- Försök igen senare (ARM är populärt)
- Temporary lösning: Använd 2x AMD VMs istället

---

### 3️⃣ Konfigurera Firewall

```bash
□ I VM Instance → Resources → Attached VNICs
□ Klicka på Subnet
□ Security Lists → Default Security List
□ Klicka "Add Ingress Rule"

Regel 1 - SSH:
  Source CIDR: 0.0.0.0/0
  IP Protocol: TCP
  Destination Port: 22

Regel 2 - Discord Bot (om du vill ha web dashboard):
  Source CIDR: 0.0.0.0/0
  IP Protocol: TCP
  Destination Port: 8080
```

**⏱️ Tid: 2 minuter**

---

### 4️⃣ Connecta till VM

**Windows:**

```powershell
□ Ladda ner PuTTY eller använd Windows Terminal
□ SSH: ssh -i path/to/private_key ubuntu@<VM_PUBLIC_IP>
□ Första gången: Accept fingerprint
```

**Mac/Linux:**

```bash
□ chmod 600 ~/path/to/private_key
□ ssh -i ~/path/to/private_key ubuntu@<VM_PUBLIC_IP>
```

**⏱️ Tid: 2 minuter**

---

### 5️⃣ Installera Dependencies på VM

```bash
# Update system
□ sudo apt update && sudo apt upgrade -y

# Install Python 3.11+
□ sudo apt install python3.11 python3.11-venv python3-pip -y

# Install PostgreSQL
□ sudo apt install postgresql postgresql-contrib -y
□ sudo systemctl start postgresql
□ sudo systemctl enable postgresql

# Install Git
□ sudo apt install git -y

# Install build tools (för vissa Python packages)
□ sudo apt install build-essential libssl-dev libffi-dev python3-dev -y
```

**⏱️ Tid: 10 minuter**

---

### 6️⃣ Setup PostgreSQL Database

```bash
□ sudo -u postgres psql

# I PostgreSQL prompt:
CREATE DATABASE tournament_bot;
CREATE USER botuser WITH PASSWORD 'ditt_säkra_lösenord';
GRANT ALL PRIVILEGES ON DATABASE tournament_bot TO botuser;
\q

# Tillåt lokal access
□ sudo nano /etc/postgresql/*/main/pg_hba.conf

# Ändra denna rad:
local   all             all                                     peer
# Till:
local   all             all                                     md5

□ sudo systemctl restart postgresql
```

**⏱️ Tid: 5 minuter**

---

### 7️⃣ Clona & Konfigurera Bot

```bash
# Skapa bot directory
□ mkdir ~/discord-bot
□ cd ~/discord-bot

# Clona din repo (eller ladda upp via SFTP)
□ git clone https://github.com/ditt-repo/tournament-bot.git .

# Skapa virtual environment
□ python3.11 -m venv venv
□ source venv/bin/activate

# Installera dependencies
□ pip install --upgrade pip
□ pip install -r requirements.txt
```

**⏱️ Tid: 5-10 minuter**

---

### 8️⃣ Konfigurera Environment Variables

```bash
□ nano .env

# Lägg till:
DISCORD_TOKEN=din_bot_token
DATABASE_URL=postgresql://botuser:ditt_lösenord@localhost/tournament_bot

# CS2 Server config
PTERO_API_KEY=din_api_key
PTERO_PANEL_URL=https://ditt-panel.com
PTERO_SERVER1_UUID=uuid1
PTERO_SERVER2_UUID=uuid2
CS2_SERVER_IP=din_server_ip
CS2_SERVER1_PORT=27015
CS2_SERVER2_PORT=27016
CS2_RCON_PASSWORD=rcon_password
CS2_SERVER_PASSWORD=none

# Spara: Ctrl+X → Y → Enter
```

**⏱️ Tid: 3 minuter**

---

### 9️⃣ Setup Systemd Service (Auto-start)

```bash
□ sudo nano /etc/systemd/system/discord-bot.service

# Lägg till:
[Unit]
Description=Discord Tournament Bot
After=network.target postgresql.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/discord-bot
Environment="PATH=/home/ubuntu/discord-bot/venv/bin"
ExecStart=/home/ubuntu/discord-bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# Spara och aktivera:
□ sudo systemctl daemon-reload
□ sudo systemctl enable discord-bot
□ sudo systemctl start discord-bot

# Kolla status:
□ sudo systemctl status discord-bot

# Se logs:
□ sudo journalctl -u discord-bot -f
```

**⏱️ Tid: 5 minuter**

---

### 🔟 Setup Firewall på VM (UFW)

```bash
□ sudo ufw allow 22/tcp    # SSH
□ sudo ufw allow 8080/tcp  # Optional web dashboard
□ sudo ufw enable
□ sudo ufw status
```

**⏱️ Tid: 2 minuter**

---

## 🔧 Underhåll & Monitoring

### Hantera Bot Service

```bash
# Starta
sudo systemctl start discord-bot

# Stoppa
sudo systemctl stop discord-bot

# Restart
sudo systemctl restart discord-bot

# Status
sudo systemctl status discord-bot

# Logs (live)
sudo journalctl -u discord-bot -f

# Logs (senaste 100 rader)
sudo journalctl -u discord-bot -n 100
```

### Update Bot

```bash
cd ~/discord-bot
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart discord-bot
```

### Database Backup (viktigt!)

```bash
# Skapa backup script
nano ~/backup.sh

#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U botuser tournament_bot > ~/backups/db_backup_$DATE.sql

# Gör körbar
chmod +x ~/backup.sh

# Setup cron (daglig backup kl 03:00)
crontab -e
0 3 * * * /home/ubuntu/backup.sh
```

---

## 📊 Monitoring & Alerts

### Setup Simple Monitoring

```bash
# Install htop för resource monitoring
sudo apt install htop

# Kör htop för att se CPU/RAM
htop

# Kolla disk space
df -h

# Kolla RAM usage
free -h
```

### Optional: Setup Email Alerts

```bash
# Install monitoring tool
sudo apt install monit

# Konfigurera monit för att övervaka bot
sudo nano /etc/monit/conf.d/discord-bot

check process discord-bot matching "python main.py"
    start program = "/usr/bin/systemctl start discord-bot"
    stop program = "/usr/bin/systemctl stop discord-bot"
    if cpu > 80% for 5 cycles then alert
    if memory > 90% for 5 cycles then alert
    if does not exist then restart
```

---

## ⚠️ Viktiga Säkerhetstips

### 1. SSH Security

```bash
# Disable password auth (använd bara SSH keys)
sudo nano /etc/ssh/sshd_config

# Ändra:
PasswordAuthentication no
PermitRootLogin no

sudo systemctl restart sshd
```

### 2. Håll System Uppdaterat

```bash
# Setup auto-updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

### 3. Backup .env fil

```bash
# Ladda ner en kopia lokalt (innehåller känslig data)
# FÖRVARA SÄKERT!
```

---

## 💡 Tips & Tricks

### 1. Free Domain

- Använd **freenom.com** för gratis domain
- Eller **DuckDNS** för gratis subdomain
- Peka domain till din VM's public IP

### 2. Setup Reverse Proxy (Optional)

```bash
# Om du vill ha web dashboard
sudo apt install nginx
sudo nano /etc/nginx/sites-available/bot-dashboard

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

sudo ln -s /etc/nginx/sites-available/bot-dashboard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 3. SSL Certificate (Gratis)

```bash
# Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## 🚨 Troubleshooting

### Bot startar inte

```bash
# Kolla logs
sudo journalctl -u discord-bot -n 100

# Kolla om port används
sudo netstat -tlnp | grep python

# Test kör manuellt
cd ~/discord-bot
source venv/bin/activate
python main.py
```

### Out of Memory

```bash
# Kolla memory usage
free -h

# Setup swap (extra minne)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Permanent swap
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Database connection issues

```bash
# Kolla om PostgreSQL körs
sudo systemctl status postgresql

# Test connection
psql -U botuser -d tournament_bot -h localhost
```

---

## 📈 Skalning (om du växer)

### När du når gränserna (osannolikt):

1. **Upgrade till Pay-As-You-Go** (~$10-20/månad för mer power)
2. **Separera databas** till Oracle Autonomous DB
3. **Load balancing** med flera VMs
4. **CDN** för statiska filer (Cloudflare gratis)

---

## 📞 Support & Länkar

- **Oracle Docs:** docs.oracle.com
- **Discord.py Docs:** discordpy.readthedocs.io
- **Oracle Community:** community.oracle.com

---

## ✅ Checklist - Snabb översikt

```
□ Skapat Oracle Cloud konto
□ VM Instance skapad (ARM Ampere)
□ Firewall konfigurerad
□ SSH access fungerar
□ PostgreSQL installerad & konfigurerad
□ Bot kod uppsatt
□ .env konfigurerad
□ Systemd service skapad
□ Bot körs och startar automatiskt
□ Backup script uppsatt
□ Monitoring konfigurerat
```

---

## 🎉 Klart!

Din bot körs nu GRATIS 24/7 på Oracle Cloud med:

- ✅ 4 CPU cores
- ✅ 24 GB RAM
- ✅ 100 GB disk
- ✅ 10 TB bandbredd/månad
- ✅ 99.9%+ uptime
- ✅ $0/månad FOREVER

**Total setup tid: ~1-2 timmar**
