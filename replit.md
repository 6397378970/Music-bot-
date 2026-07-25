# Elevenyts — Telegram Voice Chat Music Bot

## Project Overview

**Elevenyts** is an advanced Telegram Voice Chat Music Bot built with Python. It streams audio/video in Telegram group voice chats using Pyrogram + PyTgCalls + MongoDB.

### Active Plugins (kept)
| Plugin | Category | Purpose |
|--------|----------|---------|
| `broadcast.py` | Broadcast | Send messages to all groups/users |
| `mongo.py` (core) | Database | MongoDB connection & all DB operations |
| `play.py`, `pause.py`, `resume.py`, `stop.py`, `skip.py`, `loop.py`, `seek.py`, `shuffle.py`, `queue.py`, `callbacks.py`, `channelplay.py`, `link.py`, `iquery.py`, `misc.py` | Play | Full music playback system |
| `lang.py` + `locales/` | Language | Multi-language support (20+ languages) |
| `auth.py` | Feature | Authorize/unauthorize users per group |

### Stack
- **Python** 3.10+
- **Pyrogram / kurigram** — Telegram client
- **PyTgCalls** — Voice chat streaming
- **MongoDB (pymongo)** — Database
- **yt-dlp** — Audio/video download
- **FFmpeg** — Media processing

## How to Run

Requires the following environment secrets set before starting:

| Variable | Required | Description |
|----------|----------|-------------|
| `API_ID` | ✅ | From [my.telegram.org](https://my.telegram.org) |
| `API_HASH` | ✅ | From [my.telegram.org](https://my.telegram.org) |
| `BOT_TOKEN` | ✅ | From @BotFather |
| `MONGO_DB_URI` | ✅ | MongoDB connection string |
| `LOGGER_ID` | ✅ | Telegram chat ID for bot logs |
| `OWNER_ID` | ✅ | Your Telegram user ID |
| `STRING_SESSION` | ✅ | Pyrogram string session (assistant account) |
| `ARTISTBOTS_KEY` | Optional | ArtistBots streaming API key |
| `STRING_SESSION2/3` | Optional | Extra assistant sessions |

**Run command:** `python -m Elevenyts`

## User Preferences
- Keep only: broadcast, database, play, language, feature (auth) plugins. All others removed.
