# 🔄 Uppdatera Discord Bot på Oracle Cloud

## ❌ Det sker INTE automatiskt!

När du gör ändringar lokalt på din dator påverkar det **INTE** botten på Oracle Cloud automatiskt. Du måste manuellt uppdatera servern.

---

## 🎯 Tre olika metoder (från enkel till avancerad)

---

## 📌 METOD 1: Git + Manual Pull (REKOMMENDERAD)

### **Setup (gör EN gång):**

#### 1. Skapa GitHub Repository (om du inte redan har ett)

```bash
# Lokalt på din dator:
cd ditt-bot-projekt
git init
git add .
git commit -m "Initial commit"

# Skapa nytt repo på github.com, sedan:
git remote add origin https://github.com/ditt-användarnamn/tournament-bot.git
git branch -M main
git push -u origin main
```

#### 2. Clona på Oracle Cloud

```bash
# SSH in till Oracle VM:
ssh -i ~/key.pem ubuntu@<oracle-vm-ip>

# Clona ditt repo:
cd ~
git clone https://github.com/ditt-användarnamn/tournament-bot.git discord-bot
cd discord-bot

# Installera dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Kopiera .env fil (gör manuellt, pusha ALDRIG .env till git!)
nano .env
# Klistra in din .env content
```

---

### **När du gör ändringar (VARJE GÅNG):**

#### Steg 1: Lokalt (din dator)

```bash
# Gör dina ändringar i koden
# Testa lokalt att allt fungerar

# Pusha till GitHub:
git add .
git commit -m "Fix: beskrivning av vad du fixade"
git push origin main
```

#### Steg 2: På Oracle Cloud

```bash
# SSH in till Oracle VM:
ssh -i ~/key.pem ubuntu@<oracle-vm-ip>

# Gå till bot directory:
cd ~/discord-bot

# Dra ner senaste ändringarna:
git pull origin main

# Om du lade till nya dependencies:
source venv/bin/activate
pip install -r requirements.txt

# Starta om botten:
sudo systemctl restart discord-bot

# Kolla att allt fungerar:
sudo systemctl status discord-bot
sudo journalctl -u discord-bot -f
```

**⏱️ Total tid: 1-2 minuter**

---

### **🚀 Snabb-kommando (spara detta):**

Skapa ett update-script på Oracle VM:

```bash
# Skapa script:
nano ~/update-bot.sh

# Lägg till:
#!/bin/bash
echo "🔄 Uppdaterar bot..."
cd ~/discord-bot
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --quiet
sudo systemctl restart discord-bot
echo "✅ Bot uppdaterad!"
sudo systemctl status discord-bot

# Gör körbar:
chmod +x ~/update-bot.sh
```

**Nu kan du uppdatera med:**

```bash
ssh -i ~/key.pem ubuntu@<oracle-vm-ip> '~/update-bot.sh'
```

Eller ännu enklare, SSH in och kör:

```bash
~/update-bot.sh
```

---

## 📌 METOD 2: SFTP/SCP Upload (Enklare men sämre)

### **När du gör ändringar:**

#### Windows (WinSCP eller FileZilla):

```
1. Öppna WinSCP/FileZilla
2. Anslut till Oracle VM (SSH)
3. Navigera till ~/discord-bot
4. Dra och släpp ändrade filer
5. SSH in och restart bot:
   sudo systemctl restart discord-bot
```

#### Mac/Linux (SCP):

```bash
# Ladda upp enskild fil:
scp -i ~/key.pem din-fil.py ubuntu@<oracle-vm-ip>:~/discord-bot/din-fil.py

# Ladda upp hel mapp:
scp -i ~/key.pem -r ./cogs ubuntu@<oracle-vm-ip>:~/discord-bot/

# SSH in och restart:
ssh -i ~/key.pem ubuntu@<oracle-vm-ip>
sudo systemctl restart discord-bot
```

**❌ Nackdelar:**

- Måste hålla koll på vilka filer som ändrats
- Risk att missa filer
- Ingen versionshantering
- Svårare att rulla tillbaka

---

## 📌 METOD 3: GitHub Actions (AVANCERAD - Auto-deploy)

### **Setup CI/CD för automatisk deployment:**

Detta gör att botten uppdateras AUTOMATISKT när du pushar till GitHub!

#### 1. Skapa GitHub Action

```bash
# Lokalt i ditt projekt:
mkdir -p .github/workflows
nano .github/workflows/deploy.yml
```

```yaml
name: Deploy to Oracle Cloud

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Oracle VM
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.ORACLE_VM_IP }}
          username: ubuntu
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd ~/discord-bot
            git pull origin main
            source venv/bin/activate
            pip install -r requirements.txt --quiet
            sudo systemctl restart discord-bot
            echo "✅ Deployment complete!"
```

#### 2. Lägg till Secrets i GitHub:

```
1. Gå till GitHub repo → Settings → Secrets and variables → Actions
2. Lägg till:
   - ORACLE_VM_IP: <din-vm-ip>
   - SSH_PRIVATE_KEY: <innehållet i din private key>
```

#### 3. Setup SSH key för GitHub på Oracle VM:

```bash
# På Oracle VM:
nano ~/.ssh/authorized_keys
# Lägg till din SSH public key från GitHub Actions
```

**🎉 Nu:**

```bash
# Lokalt:
git add .
git commit -m "Fix något"
git push origin main

# GitHub Actions deployer AUTOMATISKT! ✨
# Tar ~30 sekunder
```

---

## 🔧 Hot Reload (BONUS - för utveckling)

Om du vill testa ändringar SNABBT utan full restart:

### **Setup Watchdog (Auto-reload vid filändringar):**

```bash
# På Oracle VM:
pip install watchdog

# Skapa reload script:
nano ~/discord-bot/auto_reload.py
```

```python
import sys
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess

class BotReloader(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            print(f"🔄 Detected change in {event.src_path}")
            subprocess.run(['sudo', 'systemctl', 'restart', 'discord-bot'])

if __name__ == "__main__":
    event_handler = BotReloader()
    observer = Observer()
    observer.schedule(event_handler, path='~/discord-bot', recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
```

**⚠️ Använd bara för utveckling, inte production!**

---

## 📋 Workflow Comparison

| Metod              | Svårighet    | Tid per update | Versionshantering | Rollback möjligt |
| ------------------ | ------------ | -------------- | ----------------- | ---------------- |
| **Git + Manual**   | ⭐⭐ Lätt    | 1-2 min        | ✅ Ja             | ✅ Ja            |
| **SFTP/SCP**       | ⭐ Lättast   | 2-5 min        | ❌ Nej            | ❌ Nej           |
| **GitHub Actions** | ⭐⭐⭐ Medel | 30 sek (auto)  | ✅ Ja             | ✅ Ja            |

---

## 🎯 Min Rekommendation

### **För dig (börjar med Oracle Cloud):**

**Använd Git + Manual Pull (Metod 1)**

**Varför?**

- ✅ Enkel att lära sig
- ✅ Full kontroll
- ✅ Versionshantering
- ✅ Kan rulla tillbaka
- ✅ Professionell workflow
- ✅ Tar bara 1-2 minuter

**När du blir mer van:**

- Uppgradera till GitHub Actions (Metod 3)
- Då blir det automatiskt! 🚀

---

## 🚨 Viktiga Tips

### 1. **Testa ALLTID lokalt först!**

```bash
# Lokalt:
python main.py
# Se att allt fungerar

# Sedan pusha:
git push origin main
```

### 2. **Backup .env fil**

```bash
# .env finns BARA på Oracle VM
# Pusha ALDRIG .env till GitHub!

# Ta backup:
scp -i ~/key.pem ubuntu@<oracle-vm-ip>:~/discord-bot/.env ~/backup/.env
```

### 3. **Kolla logs efter update**

```bash
# Efter restart, kolla alltid logs:
sudo journalctl -u discord-bot -f
# Ctrl+C för att avsluta
```

### 4. **Rollback om något går fel**

```bash
# På Oracle VM:
cd ~/discord-bot
git log --oneline  # Se commit history
git checkout <commit-hash>  # Gå tillbaka till tidigare version
sudo systemctl restart discord-bot
```

---

## 📝 Quick Reference Cheat Sheet

### **Standard Update Workflow:**

```bash
# 1. LOKALT (din dator):
git add .
git commit -m "Beskrivning av ändring"
git push origin main

# 2. ORACLE VM:
ssh -i ~/key.pem ubuntu@<oracle-vm-ip>
cd ~/discord-bot
git pull origin main
sudo systemctl restart discord-bot
sudo systemctl status discord-bot
exit
```

### **Troubleshooting efter update:**

```bash
# Kolla status:
sudo systemctl status discord-bot

# Kolla logs:
sudo journalctl -u discord-bot -n 50

# Kolla real-time logs:
sudo journalctl -u discord-bot -f

# Manual test:
cd ~/discord-bot
source venv/bin/activate
python main.py

# Rollback:
git log --oneline
git checkout <previous-commit>
sudo systemctl restart discord-bot
```

---

## 🔐 Security Best Practices

### **.gitignore (VIKTIGT!):**

```bash
# Skapa/uppdatera .gitignore lokalt:
nano .gitignore

# Lägg till:
.env
*.log
__pycache__/
*.pyc
venv/
.DS_Store
*.pem
*.key

# Commit gitignore:
git add .gitignore
git commit -m "Add gitignore"
git push origin main
```

### **Känslig data:**

❌ Pusha ALDRIG:

- `.env` filer
- API keys
- Passwords
- SSH keys
- Database credentials

✅ Förvara istället:

- Lokalt på säker plats
- Password manager (1Password, Bitwarden)
- Manuellt på Oracle VM

---

## 💡 Pro Tips

### **1. Branch strategy för större ändringar:**

```bash
# Skapa dev branch för testing:
git checkout -b dev
# Gör ändringar
git push origin dev

# På Oracle VM, testa dev branch:
git fetch origin
git checkout dev
sudo systemctl restart discord-bot
# Testa...

# Om allt fungerar, merge till main:
git checkout main
git merge dev
git push origin main
```

### **2. Automated daily backups:**

```bash
# På Oracle VM:
nano ~/backup-bot.sh

#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf ~/backups/bot_backup_$DATE.tar.gz ~/discord-bot
# Behåll bara senaste 7 backups
ls -t ~/backups/bot_backup_* | tail -n +8 | xargs rm -f

# Cron job (daglig backup kl 03:00):
crontab -e
0 3 * * * ~/backup-bot.sh
```

### **3. Monitoring efter updates:**

```bash
# Installera monitoring:
sudo apt install htop

# Watch bot status:
watch -n 5 'systemctl status discord-bot'

# CPU/RAM usage:
htop
```

---

## 🎓 Learning Path

### **Vecka 1-2: Manual Git**

```bash
- Lär dig: git add, commit, push, pull
- Workflow: Manual updates via SSH
- Fokus: Förstå processen
```

### **Vecka 3-4: Automatisera**

```bash
- Skapa update script (~/update-bot.sh)
- Lägg till aliases i ~/.bashrc
- Workflow: One-command updates
```

### **Månad 2+: CI/CD**

```bash
- Setup GitHub Actions
- Automatic deployments
- Workflow: Push = Auto-update
```

---

## ❓ FAQ

**Q: Kan jag koda direkt på Oracle VM?**
A: Ja, men rekommenderas INTE. Använd lokalt + Git istället.

**Q: Vad händer om git pull får merge conflicts?**
A: Lös lokalt först, eller:

```bash
git fetch origin
git reset --hard origin/main
```

**Q: Kan jag testa ändringar utan att påverka live bot?**
A: Ja! Använd dev branch eller kör två bots (en för testing).

**Q: Hur ofta ska jag uppdatera?**
A:

- Bugfixes: Direkt
- Features: När testat lokalt
- Dependencies: Veckovis

---

## ✅ Sammanfattning

### **Det du behöver komma ihåg:**

1. ❌ Ändringar lokalt uppdaterar INTE automatiskt Oracle Cloud
2. ✅ Använd Git för versionshantering
3. ✅ Workflow: Ändra lokalt → Push GitHub → Pull på Oracle → Restart bot
4. ⚠️ Pusha ALDRIG .env eller känslig data till GitHub
5. 📋 Testa alltid lokalt innan deploy

### **Quick Update (efter setup):**

```bash
# Lokalt:
git push

# Oracle VM:
ssh <oracle> "cd ~/discord-bot && git pull && sudo systemctl restart discord-bot"
```

**Det är allt!** 🎉
