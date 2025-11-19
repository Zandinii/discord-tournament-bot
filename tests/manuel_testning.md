3. MANUAL TESTING CHECKLIST
   3.1 Initial Setup

Kör /cs2-setup med korrekta Pterodactyl credentials
Verifiera att config sparas i databas
Testa /cs2-toggle för att aktivera/avaktivera
Kör /cs2-status och verifiera att info visas korrekt

3.2 SteamID Linking

Låt spelare köra /steam-link med sitt SteamID64
Verifiera att SteamID sparas i databas
Testa med ogiltigt SteamID format (ska ge error)
Verifiera att länkat SteamID visas i /cs2-status

3.3 Match Creation Flow

Skapa en turnering med /tournament-create
Låt spelare anmäla sig med /signup
Starta turneringen med /tournament-start
Verifiera att match skapas automatiskt

3.4 Server Automation

Verifiera att server startar automatiskt när match skapas
Övervaka bot logs för server status polling
Verifiera att server når "running" state inom 3 minuter
Kolla att config commands skickas (se logs)
Verifiera att connect-info skickas till Discord voice channels

3.5 In-Game Testing

Anslut till servern med connect-strängen
Verifiera att server password fungerar
Testa att rätt karta laddas
Verifiera team names (Team A / Team B)
Testa match settings (roundtime, maxrounds, etc)
Verifiera warmup fungerar

3.6 Match Completion

Rapportera match-resultat med /report-win
Verifiera att match markeras som completed
Kolla att server shutdown schemalä ggs (5 min delay)
Verifiera att server faktiskt stoppas efter delay

3.7 Error Scenarios

Testa med fel Pterodactyl API key (ska ge error)
Testa när server inte startar (timeout)
Testa när Pterodactyl API är nere
Testa med spelare som saknar SteamID
Använd /cs2-force-start när automation är avstängd

5. ACCEPTANSKRITERIER
   ✅ Match Automation

Server startar automatiskt när match skapas
Server når "running" state inom 3 minuter
Alla config commands skickas korrekt
Connect-info skickas till rätt Discord channels

✅ SteamID Management

Spelare kan länka SteamID med /steam-link
SteamIDs valideras (17 siffror, SteamID64 format)
Whitelisting implementeras (via plugin eller native)

✅ Match Configuration

Rätt karta laddas
Team names sätts korrekt
Match settings (rounds, time, overtime) fungerar
Server password fungerar

✅ Error Handling

Timeout hanteras gracefully (efter 3 min)
API errors loggas och rapporteras
Rate limiting respekteras
Spelare utan SteamID får tydlig felmeddelande

✅ Cleanup

Server stängs automatiskt efter match
Delay före shutdown fungerar (5 min default)
Voice channels rensas korrekt
Database logs uppdateras

✅ Admin Controls

/cs2-setup fungerar korrekt
/cs2-toggle kan aktivera/avaktivera
/cs2-status visar korrekt info
/cs2-force-start och /cs2-force-stop fungerar

6. REGRESSION TESTS
   Efter varje uppdatering, kör:

Alla unit tests (pytest tests/)
Integration tests med mock server
Manual smoke test av hela flödet
Performance test (3-5 concurrent matches)

SAMMANFATTNING
Denna testplan täcker:

Unit tests för isolerade komponenter
Integration tests för hela systemet
Manual testing för användarflöden
Performance tests för concurrent matches
Acceptanskriterier för godkännande

Kör tester med:
pytest tests/ -v --asyncio-mode=auto
