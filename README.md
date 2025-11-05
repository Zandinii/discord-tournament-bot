# Discord Tournament Bot

Discord Tournament Bot är en asynkron Discord-bot skriven i Python som gör det enkelt att skapa och hantera turneringar i din server. Botten använder slash-kommandon och interaktiva `discord.ui`-Views för en modern användarupplevelse. Den är byggd för att vara modulär (cogs), asynkron och lätt att köra lokalt eller på en server med stöd för både SQLite och PostgreSQL.

Funktioner

- Skapa, redigera och ta bort turneringar via admin-kommandon.
- Anmälan och avanmälan för spelare med automatiska uppdateringar av announcement-embed.
- Automatisk bracket-hantering (single elimination, double elimination och round-robin bracket-logik).
- Matchrapportering med bekräftelse-UI och ELO-uppdateringar.
- Skapande och cleanup av voice channels per match.
- Persistens via async SQLAlchemy (stöd för SQLite och PostgreSQL).
- Administrativa verktyg: server-setup, lista/ta bort turneringar, manuella åtgärder vid tvister.

Krav

- Python 3.10+ (rekommenderat 3.11).
- Se `requirements.txt` för exakta dependencies.
- En Discord bot-applikation med rätt scopes/behörigheter (inkl. application commands).

Konfiguration

- `DISCORD_TOKEN` — (obligatoriskt) bot-token från Discord Developer Portal.
- `GUILD_ID` — (valfritt) sätter sync-mål för snabbare guild-kommando-propagation under utveckling.
- `DATABASE_URL` — (valfritt) anslutningssträng för PostgreSQL; om den saknas används SQLite som default.

Utvecklingstips

- För snabba iterationer: använd `GUILD_ID` för att synkronisera commands i en test-guild (guild-commands visas omedelbart). Globala commands kan ta upp till ~1 timme att propagera.
- Lägg till nya slash-kommandon i respektive cog under `cogs/` med `@app_commands.command`.
- Följ `bot.log` och terminalutskrift för detaljerade fel och synk-loggar.

Felsökning — vanliga problem

- "Inga kommandon synkade": Kontrollera att cogs laddas utan undantag och att slash-kommandon deklarerats korrekt. Se loggarna.
- Dubbletter av kommandon: Kan uppstå om samma kommando finns både globalt och som guild-kommando. Rensa gamla guild-kommandon eller håll en konsekvent sync-strategi.
- Behörighetsproblem: Säkerställ att botten är inbjuden med rätt scopes och att appen har behörighet att registrera application commands.

Projektstruktur

- `bot.py` — huvudfil / entrypoint
- `cogs/` — modulariserade kommando-cogs (admin, player, tournament, match, voice, team)
- `database/` — SQLAlchemy-modeller och DB-setup
- `utils/` — hjälpfunktioner (ELO, embeds, permissions)
- `requirements.txt` — Pythonberoenden

Rättigheter till användning

- Ingen användning av koden eller dess delar får ske i kommersiella syften utan uttryckligt tillstånd från upphovsmannen.
