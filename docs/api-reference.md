# API Reference - Tournament Bot

## Innehåll

- [Admin Commands](#admin-commands)
- [Player Commands](#player-commands)
- [Team Commands](#team-commands)
- [Match Commands](#match-commands)
- [Tournament Commands](#tournament-commands)
- [Season Commands](#season-commands)
- [Achievement Commands](#achievement-commands)
- [Template Commands](#template-commands)
- [Voice Commands](#voice-commands)
- [Help Commands](#help-commands)

---

## Admin Commands

### `/setup`

Initiera bot-inställningar för servern.

**Permissions:** Administrator

**Response:**

- Success embed med nästa steg
- Guild skapas i database

---

### `/tournament-create`

Skapa en ny turnering med wizard.

**Parameters:**

- `name` (string, required): Turneringens namn
- `game_mode` (choice, required): 1v1, 2v2, eller 5v5
- `tournament_type` (choice, required): single_elim, double_elim, round_robin
- `max_players` (integer, optional): Max deltagare (default: 32)

**Modal Fields:**

- `prize`: Prisbeskrivning
- `description`: Turnerings-beskrivning
- `start_time`: YYYY-MM-DD HH:MM format
- `game_name`: T.ex. CS2, Valorant
- `map_pool`: Komma-separerade kartor
- `bo_format`: 1 eller 3

**Permissions:** Administrator

**Response:**

- Tournament announcement embed med signup buttons
- Tournament sparas i database

**Errors:**

- Invalid date format
- Past date selected

---

### `/tournament-start [tournament_id]`

Starta en turnering och generera bracket.

**Parameters:**

- `tournament_id` (integer, required): Turnerings-ID

**Permissions:** Administrator

**Requirements:**

- Minst 2 deltagare
- Status måste vara SIGNUP

**Response:**

- Bracket generation
- Voice channels skapas
- Map ban phase startar
- Status → ONGOING

**Errors:**

- Tournament not found
- Not enough participants
- Already started

---

### `/tournament-list [status]`

Lista turneringar.

**Parameters:**

- `status` (choice, optional): signup, ongoing, completed, cancelled

**Permissions:** Administrator

**Response:**

- Embed med turneringar (max 10)
- Status, mode, start time

---

### `/tournament-delete [tournament_id]`

Ta bort en turnering permanent.

**Parameters:**

- `tournament_id` (integer, required)

**Permissions:** Administrator

**Response:**

- Confirmation message
- All related data deleted

**Cascade Deletes:**

- Participants
- Matches
- Map bans
- Notifications

---

### `/tournament-cancel [tournament_id]`

Avbryt en pågående turnering.

**Parameters:**

- `tournament_id` (integer, required)

**Permissions:** Administrator

**Response:**

- Status → CANCELLED
- Voice channels cleanup

---

### `/set-lobby [channel]`

Sätt lobby voice channel.

**Parameters:**

- `channel` (voice_channel, required)

**Permissions:** Administrator

**Response:**

- Confirmation message
- Guild config uppdaterad

---

### `/setup-match [match_id]`

Manuellt sätta upp voice channels för match.

**Parameters:**

- `match_id` (integer, required)

**Permissions:** Administrator

**Response:**

- 2 voice channels skapade
- 2 text channels skapade
- Spelare flyttade
- Map ban started

---

### `/cleanup-match [match_id]`

Ta bort voice channels för match.

**Parameters:**

- `match_id` (integer, required)

**Permissions:** Administrator

**Response:**

- Channels deleted
- Players moved to lobby

---

### `/cleanup-all`

Emergency cleanup av alla match-channels.

**Permissions:** Administrator

**Response:**

- All match channels deleted
- Category cleanup

---

### `/resolve-dispute [match_id] [winner_id] [score_p1] [score_p2]`

Lös en tvistad match.

**Parameters:**

- `match_id` (integer, required)
- `winner_id` (integer, required): User ID
- `score_p1` (integer, required)
- `score_p2` (integer, required)

**Permissions:** Administrator

**Response:**

- Match resolved
- ELO updated
- Progression continued

---

## Player Commands

### `/signup [tournament_id]`

Anmäl dig till turnering.

**Parameters:**

- `tournament_id` (integer, required)

**Response:**

- Confirmation message
- Participant count updated

**Errors:**

- Already signed up
- Tournament full
- Tournament not open
- Must have team (for 5v5)

---

### `/withdraw [tournament_id]`

Dra dig ur turnering.

**Parameters:**

- `tournament_id` (integer, required)

**Response:**

- Confirmation message
- Participant removed

**Errors:**

- Not signed up
- Tournament already started

---

### `/my-tournaments`

Visa dina pågående turneringar.

**Response:**

- Embed med aktiva turneringar
- Status, start time, mode

---

### `/my-matches`

Visa dina aktiva matcher.

**Response:**

- Embed med pågående matcher
- Opponent info
- Match IDs

---

### `/my-stats`

Visa din statistik.

**Response:**

- ELO rating
- Total matches
- Wins/losses
- Win rate
- Tournaments participated/won
- Win streak

---

### `/profile [@user]`

Visa spelarprofil.

**Parameters:**

- `user` (user, optional): Default: yourself

**Response:**

- Player stats embed
- Match history (last 5)
- Achievements count

---

### `/leaderboard [category]`

Visa top 10 spelare.

**Parameters:**

- `category` (string, optional): elo, wins, tournaments

**Response:**

- Top 10 players
- Medals för top 3
- Sorterad efter vald kategori

---

### `/match-history [@user]`

Visa match-historik.

**Parameters:**

- `user` (user, optional): Default: yourself

**Response:**

- Senaste 10 matcher
- Win/loss
- ELO change
- Opponent
- Timestamp

---

## Team Commands

### `/team-create [name] [tag]`

Skapa ett lag.

**Parameters:**

- `name` (string, required): Max 100 tecken
- `tag` (string, optional): Max 10 tecken

**Response:**

- Team created
- You are captain
- Team ID

**Errors:**

- Already captain of team
- Already member of team

---

### `/team-invite [@user]`

Bjud in till lag.

**Parameters:**

- `user` (user, required)

**Requirements:**

- Must be captain

**Response:**

- Invite sent
- Accept/Deny buttons (5 min timeout)

**Errors:**

- Not captain
- User already in team
- Can't invite bots/yourself

---

### `/team-leave`

Lämna ditt lag.

**Response:**

- Confirmation
- Removed from team

**Errors:**

- Not in team
- Captain must use /team-delete

---

### `/team-info [team_name]`

Visa lag-information.

**Parameters:**

- `team_name` (string, optional): Default: your team

**Response:**

- Team name, tag
- Captain
- Members
- Stats (ELO, W/L)

---

### `/team-list`

Lista alla lag.

**Response:**

- Alla lag (max 15)
- Sorted by ELO
- Member count
- Captain

---

### `/team-delete`

Ta bort ditt lag.

**Requirements:**

- Must be captain

**Response:**

- Team deleted
- All members removed

---

## Match Commands

### `/report-win [match_id] [score_winner] [score_loser]`

Rapportera vinst.

**Parameters:**

- `match_id` (integer, required)
- `score_winner` (integer, optional): Default 1
- `score_loser` (integer, optional): Default 0

**Requirements:**

- Must be participant

**Response:**

- Confirmation request sent to opponent
- Opponent must confirm/deny

**On Confirmation:**

- ELO updated
- Stats updated
- Match history saved
- Achievements checked
- Next match setup
- Voice cleanup

**Errors:**

- Not participant
- Match already completed
- Match disputed

---

### `/match-info [match_id]`

Visa match-detaljer.

**Parameters:**

- `match_id` (integer, required)

**Response:**

- Participants
- Status
- Score (if completed)
- Tournament
- Timestamps

---

## Tournament Commands

### `/bracket [tournament_id] [round_number]`

Visa turnerings-bracket.

**Parameters:**

- `tournament_id` (integer, required)
- `round_number` (integer, optional): Default: current round

**Response:**

- Bracket embed för specifikt round
- Match status
- Participants
- Winners

**Errors:**

- Tournament not started
- No matches found

---

## Season Commands

### `/season-create [name] [duration_days]`

Skapa ny säsong.

**Parameters:**

- `name` (string, required)
- `duration_days` (integer, optional): Default 90

**Permissions:** Administrator

**Response:**

- Season created
- All players get season stats
- Start/end dates

**Errors:**

- Active season already exists

---

### `/season-end`

Avsluta aktiv säsong.

**Permissions:** Administrator

**Response:**

- Season ended
- Top 3 announcement
- Stats preserved

---

### `/season-info`

Visa säsongs-information.

**Response:**

- Season name
- Start/end dates
- Time remaining
- Players/tournaments count

---

### `/season-leaderboard [season_name]`

Visa säsongens leaderboard.

**Parameters:**

- `season_name` (string, optional): Default: current season

**Response:**

- Top 10 players för season
- Season-specific stats

---

### `/season-list`

Lista alla säsonger.

**Response:**

- All seasons
- Active/completed status
- Dates

---

## Achievement Commands

### `/achievement-init`

Initiera achievements.

**Permissions:** Administrator

**Response:**

- 12 default achievements created

---

### `/achievements [@user]`

Visa achievements.

**Parameters:**

- `user` (user, optional): Default: yourself

**Response:**

- Unlocked achievements
- Progress (X/12)
- Timestamps

---

### `/achievements-list`

Lista alla achievements.

**Response:**

- All 12 achievements
- Grouped by type
- Descriptions
- Requirements

---

## Template Commands

### `/template-create`

Skapa turnerings-template.

**Parameters:**

- `name` (string, required)
- `game_mode` (choice, required)
- `tournament_type` (choice, required)
- `recurring` (boolean, optional): Default True
- `day_of_week` (integer, optional): 0=Monday, 6=Sunday
- `time` (string, optional): HH:MM format
- `recurrence` (choice, optional): weekly, biweekly, monthly

**Modal Fields:** (Same as tournament-create)

**Permissions:** Administrator

**Response:**

- Template created
- Schedule info

---

### `/template-list`

Lista templates.

**Permissions:** Administrator

**Response:**

- All templates
- Active/paused status
- Schedule
- Last created

---

### `/template-toggle [template_id]`

Aktivera/pausera template.

**Parameters:**

- `template_id` (integer, required)

**Permissions:** Administrator

**Response:**

- Status toggled

---

### `/template-delete [template_id]`

Ta bort template.

**Parameters:**

- `template_id` (integer, required)

**Permissions:** Administrator

**Response:**

- Template deleted

---

## Voice Commands

_Mostly automatic, but includes admin commands listed above_

---

## Help Commands

### `/help [category]`

Visa hjälp.

**Parameters:**

- `category` (string, optional): admin, player, team, match, tournament

**Response:**

- Overview (if no category)
- Detailed commands (if category specified)

---

### `/quickstart`

Snabbguide.

**Response:**

- Different guides for admin vs players
- Step-by-step instructions

---

## Database Models Reference

### Tournament

```
id, guild_id, name, game_mode, game_type, max_participants,
start_time, status, prize_description, description, created_by,
created_at, announcement_message_id, game_name, bo_format_groupstage,
bo_format_playoffs, map_pool, season_id
```

### Player

```
user_id, guild_id, username, elo_rating, total_matches,
total_wins, total_losses, tournaments_won, tournaments_participated,
created_at, current_season_id, highest_elo, win_streak, best_win_streak
```

### Match

```
id, tournament_id, round_number, match_number, participant1_id,
participant2_id, winner_id, score_p1, score_p2, status,
voice_channel_1_id, voice_channel_2_id, started_at, completed_at,
maps_to_play, ban_phase_complete, ban_message_id_team1, ban_message_id_team2
```

### Team

```
id, guild_id, name, tag, captain_id, created_at,
total_wins, total_losses, elo_rating
```

---

## Event Listeners

### `on_voice_state_update`

Auto-moves players to match channels when joining lobby.

### `check_notifications` (Background Task)

Runs every 1 minute, checks for scheduled notifications.

### `check_scheduled_tournaments` (Background Task)

Runs every 1 hour, auto-creates tournaments from templates.

---

## Utility Functions

### ELO Calculation

```python
calculate_elo(winner_elo: int, loser_elo: int, winner_matches: int) -> tuple[int, int]
```

K-factors:

- < 10 matches: K=40
- < 100 matches: K=32
- > = 100 matches: K=24

### Bracket Generation

```python
generate_single_elimination(tournament_id, participants) -> List[Match]
generate_round_robin(tournament_id, participants) -> List[Match]
```

---

## Rate Limits

Discord API limits:

- 50 requests per second
- Bot handles internally with exponential backoff

Bot-specific limits:

- 1 tournament creation per minute per user
- 5 signups per minute per user

---

## Error Codes

Standard errors return embeds with:

- Red color
- ❌ title
- Descriptive message
- Ephemeral (only visible to user)

Common errors:

- `404`: Resource not found
- `403`: Permission denied
- `400`: Invalid input
- `500`: Internal error (logged)

---

_Last Updated: 2025_
