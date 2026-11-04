<div align="center">

# 🤖 Discord RSS Bot

### Forum RSS → beautiful embed posts in Discord + web admin panel in your browser

[![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![discord.py](https://img.shields.io/badge/discord.py-2.x-blurple?style=for-the-badge&logo=discord&logoColor=white)](https://discordpy.readthedocs.io/)
[![Flask](https://img.shields.io/badge/flask-admin-black?style=for-the-badge&logo=flask)](https://flask.palletsprojects.com/)
[![Version](https://img.shields.io/badge/version-1.0.0-blue?style=for-the-badge)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](LICENSE)

**Universal bot:** takes any forum RSS feed and posts new topics to Discord as a beautiful embed — with image, author, date and a «Read on forum» button. Everything is configured from the browser, no code editing required.

[🚀 Quick start](#-quick-start) • [📖 Full guide](docs/INSTALL.md) • [📰 RSS per forum](docs/FORUMS.md) • [⚙️ Feed settings](#️-feed-settings) • [❓ FAQ](#faq)

> 🇷🇺 Русская версия: [README.md](README.md)

</div>

---

## ✨ Features

| | Feature |
|---|---|
| 📡 | **Any number of feeds** — different forum sections → different Discord channels |
| 🎨 | **Beautiful embed** — color bar, image, author, date, footer, link button |
| 📝 | **Custom message template** — `{title} {link} {author} {summary} {date} {feed_name} {tags}` |
| 🔎 | **Keyword filters** — include only what you need / exclude spam |
| ⏱ | **Flexible interval** — global default + per-feed override (min. 60s) |
| 👁 | **Preview without spam** — check the feed before publishing |
| 📤 | **Test post** — send the latest item to Discord with one click |
| 🌐 | **Web admin panel** — dark theme, plain browser, zero frontend build |
| ⚡ | **Slash commands** — `/rss-list`, `/rss-check` right in Discord |
| 💾 | **No duplicates** — remembers posted items in `data/seen.json` |

## 🚀 Quick start

> Full step-by-step guide: [docs/INSTALL.md](docs/INSTALL.md).

**1. Install Python 3.10+** — https://www.python.org/downloads/ (check `Add to PATH`).

**2. Configure:**

```bat
cd discord-rss-bot
copy config.example.json config.json
pip install -r requirements.txt
```

Put into `config.json`:

- `discord_token` — from https://discord.com/developers/applications → Bot → Token
- `feeds[].rss_url` — your forum RSS URL
- `feeds[].channel_id` — target Discord channel ID

**3. Invite the bot:** Developer Portal → **OAuth2 → URL Generator** → scopes `bot` + `applications.commands`, permissions `Send Messages`, `Embed Links` → open the generated URL.

**4. Run:**

```bat
start.bat
```

or `python bot.py` (Linux: `python3 bot.py`).

**5. Open the admin panel:** http://127.0.0.1:8000 — password `admin123` (change it in `config.json → web.password`).

That's it. Add feeds with the **＋ Add feed** button — no restart needed.

## ⚙️ Feed settings

| Field | Meaning | Example |
|---|---|---|
| Name | Footer caption in the embed | `Forum news` |
| RSS URL | Section feed URL | `https://forum.com/forums/news/index.rss` |
| Channel | Discord channel ID (digits) | `123456789012345678` |
| Color | Left bar of the embed | `#5865F2` |
| Interval | Seconds between checks, `0` = global | `300` |
| Template | Message text | `📰 **{title}**\n{summary}\n🔗 {link}` |
| Mention | Who to ping | empty / `@everyone` / `<@&ROLE_ID>` |
| Keywords incl. | Only posts containing these words | `release, update` |
| Keywords excl. | Skip posts containing these words | `spam, offtop` |
| Max posts | How many new items per check | `3` |
| Embed / Image / Author | Display toggles | on |

Template variables: `{title} {link} {author} {summary} {date} {feed_name} {tags}`.

## 📰 Supported forums

Full table — [docs/FORUMS.md](docs/FORUMS.md).

| Forum | RSS URL pattern |
|---|---|
| XenForo | `https://forum/index.php?forums/name.12/.rss` |
| phpBB | `https://forum/feed.php` |
| SMF | `https://forum/index.php?action=.xml;type=rss` |
| MyBB | `https://forum/syndication.php` |
| Invision (IPS) | from the forum's admin panel → RSS channels |
| vBulletin | `https://forum/external.php?type=rss2` |
| WordPress / DLE | `https://site/feed` |

Open the URL in a browser — you must see XML (`<rss…>` / `<feed…>`), not an HTML page.

## ⚡ Slash commands

| Command | Who | What it does |
|---|---|---|
| `/rss-list` | everyone | List all feeds: ID, name, channel |
| `/rss-check feed_id:...` | Manage Server | Check a feed right now |

For instant command sync set `guild_id` in `config.json` and restart.

## 📁 Project structure

```
discord-rss-bot/
├── bot.py                    # Discord bot + feed polling (tasks.loop)
├── webadmin.py               # Flask admin + REST API (/api/*)
├── rss_core.py               # Config, RSS parsing, filters, templates, seen/logs
├── templates/dashboard.html  # Admin UI (single file, no build step)
├── config.example.json       # Copy to config.json
├── start.bat                 # One-click launch (Windows)
├── CHANGELOG.md              # What's new per version
├── README.md                 # Russian version
├── docs/
│   ├── INSTALL.md            # Full installation guide
│   ├── FORUMS.md             # RSS URLs per forum engine
│   ├── PROMO.md              # Release & promotion materials
│   └── banner.svg            # 1280×640 banner for Social preview
├── data/                     # Created automatically: seen.json, bot.log (git-ignored)
└── README.en.md
```

## ❓ FAQ

**Admin shows 🔴 Bot offline?** You launched `webadmin.py` without Discord. Run `python bot.py` — the admin starts together with the bot.

**«RSS failed to parse»?** Open the URL in a browser — you should see XML. Common causes: login-required section, Cloudflare, wrong URL. Use 👁 Preview for the exact error.

**Slashes not visible?** Wait up to an hour (global sync) or set `guild_id` and restart.

**Port 8000 busy?** Change `web.port` in admin settings and restart.

**Is the token safe in config.json?** `config.json` and `data/` are git-ignored — they never reach GitHub. Never share the token; change `admin123`.

## 🤝 Contributing

PRs and issues are welcome. Keep dependencies light (`discord.py`, `feedparser`, `Flask`, `beautifulsoup4`).

Ideas: multi-channel per feed, daily digest, reaction buttons, webhook mode, Docker image.

## 📄 License

MIT — see [LICENSE](LICENSE).
