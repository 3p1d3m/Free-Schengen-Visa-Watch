# 🛂 Schengen Visa Appointment Notifier

A free, open-source Telegram bot that scans **all 29 Schengen countries simultaneously** for open visa appointment slots and sends instant notifications ranked by the earliest available date.

> Built for applicants based in the **UK** — covers VFS Global, TLScontact & Embassy portals.

---

## 🚀 Use it instantly

Just open Telegram and start the bot — no setup required:

👉 **[t.me/YOUR_BOT_USERNAME](https://t.me/YOUR_BOT_USERNAME)**

---

## ✨ Features

- 🌍 Monitors all 29 Schengen countries at once
- ⚡ Scans every 2 minutes
- 📊 Results ranked by earliest available date
- 🏢 Covers VFS Global, TLScontact & Embassy Direct
- 🔔 Instant Telegram notifications
- ☀️ Daily morning status summary
- 100% free and open source

---

## 🛠️ Self-host in 5 minutes

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/schengen-visa-bot.git
cd schengen-visa-bot
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
```bash
npm i -g @railway/cli
railway login && railway init
railway add --env BOT_TOKEN=your_token
railway up
```

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
├── requirements.txt
├── Dockerfile
└── .env.example
```

---

## 🤝 Contributing

PRs welcome! If a portal URL has changed or HTML structure needs updating, open an issue or PR.

---

## ⚠️ Disclaimer

For personal use only. Respect the terms of service of visa portals. Do not set scan interval below 1 minute.

---

## 📄 License

MIT — free to use, modify, and share.
