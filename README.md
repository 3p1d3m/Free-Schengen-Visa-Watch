# 🛂 UK Schengen SlotWatcher

A free, open-source Telegram bot that scans **all 29 Schengen countries simultaneously** for open visa appointment slots and sends instant notifications ranked by the earliest available date.

> Built for applicants based in the **UK** — covers VFS Global, TLScontact & Embassy portals.

---

## 🚀 Use it instantly

Just open Telegram — no setup, no account, no app to install:

👉 **[t.me/Schenwatch_bot](https://t.me/Schenwatch_bot)**

Or visit the website:

👉 **[3p1d3m.github.io/Free-Schengen-Visa-Watch](https://3p1d3m.github.io/Free-Schengen-Visa-Watch)**

---

## ✨ Features

- 🌍 Monitors all 29 Schengen countries at once
- ⚡ Scans every 2 minutes
- 📊 Results ranked by earliest available date
- 🏢 Covers VFS Global, TLScontact & Embassy Direct
- 🔔 Instant Telegram notifications
- ☀️ Daily morning status summary at 08:00
- 100% free and open source

---

## 🤖 Bot Commands

| Command | Description |
|---|---|
| `/start` | Show the main menu |
| `/check` | Scan all countries right now |
| `/unsubscribe` | Stop all alerts |
| `/help` | Show help |

---

## 🛠️ Self-host in 5 minutes

### 1. Clone the repo
```bash
git clone https://github.com/3p1d3m/Free-Schengen-Visa-Watch.git
cd Free-Schengen-Visa-Watch
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Create your Telegram bot
Message **@BotFather** on Telegram → `/newbot` → copy the API token.

### 4. Configure
```bash
cp .env.example .env
# Edit .env and paste your BOT_TOKEN
```

### 5. Run
```bash
python bot.py
```

### Deploy free on Railway (24/7)
1. Go to [railway.app](https://railway.app) and sign in with GitHub
2. Click **New Project → Deploy from GitHub repo**
3. Select this repo
4. Add environment variable: `BOT_TOKEN` = your token
5. Click **Deploy** — runs 24/7 even when your laptop is off

---

## 🌍 Countries covered

| Provider | Countries |
|---|---|
| **VFS Global** | Austria, Belgium, Croatia, Czech Republic, Denmark, Estonia, Finland, Germany, Greece, Hungary, Italy, Latvia, Lithuania, Malta, Netherlands, Norway, Poland, Portugal, Slovakia, Slovenia, Spain, Sweden |
| **TLScontact** | France, Luxembourg, Switzerland |
| **Embassy Direct** | Bulgaria, Iceland, Liechtenstein, Romania |

---

## 📁 Project structure

```
├── bot.py           # Telegram bot, commands & scheduler
├── scraper.py       # Appointment scraper (VFS, TLS, Embassy)
├── config.py        # Environment config loader
├── index.html       # Website landing page
├── sitemap.xml      # Google sitemap
├── requirements.txt
└── .env.example
```

---

## 🤝 Contributing

PRs welcome! If a portal URL has changed or the HTML scraping needs updating for a specific country, open an issue or submit a PR.

---

## ⚠️ Disclaimer

For personal use only. Please respect the terms of service of the visa portals. Do not set the scan interval below 1 minute.

---

## 📄 License

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/3p1d3m/Free-Schengen-Visa-Watch/blob/main/LICENSE)
