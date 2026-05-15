"""
Schengen Visa Appointment Notifier Bot
Scans ALL 29 Schengen countries simultaneously and alerts you
ranked by the earliest available appointment date.
"""

import asyncio
import json
import logging
import re
from datetime import datetime, date
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from scraper import SchengenScraper, ALL_COUNTRIES
from config import Config

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(), logging.FileHandler("bot.log")],
)
logger = logging.getLogger(__name__)

# ── Persistent state ──────────────────────────────────────────────────────────
DB_FILE = Path("subscribers.json")


def load_db() -> dict:
    if DB_FILE.exists():
        return json.loads(DB_FILE.read_text())
    return {"subscribers": {}}


def save_db(db: dict):
    DB_FILE.write_text(json.dumps(db, indent=2, default=str))


def get_subscribers() -> dict:
    return load_db().get("subscribers", {})


def add_subscriber(chat_id: str):
    db = load_db()
    db["subscribers"][chat_id] = {"added": datetime.now().isoformat()}
    save_db(db)


def remove_subscriber(chat_id: str):
    db = load_db()
    db["subscribers"].pop(chat_id, None)
    save_db(db)


# ── Keyboards ─────────────────────────────────────────────────────────────────
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔔 Subscribe — all countries", callback_data="subscribe")],
        [InlineKeyboardButton("🔕 Unsubscribe",               callback_data="unsubscribe")],
        [InlineKeyboardButton("🔍 Check now",                 callback_data="check_now")],
        [InlineKeyboardButton("📋 My status",                 callback_data="my_settings")],
    ])


# ── Scan all countries in parallel ────────────────────────────────────────────
async def scan_all_countries() -> list[dict]:
    """
    Checks all 29 Schengen countries concurrently.
    Returns a flat list of slot dicts, each tagged with country info,
    sorted by the earliest parsed date.
    """
    scraper = SchengenScraper()

    async def fetch(code: str, cfg: dict):
        slots = await scraper.check(code, cfg["provider"])
        for s in slots:
            s["country_code"] = code
            s["country_name"] = cfg["name"]
            s["provider"]     = cfg["provider"]
        return slots

    results = await asyncio.gather(
        *[fetch(code, cfg) for code, cfg in ALL_COUNTRIES.items()],
        return_exceptions=True,
    )

    all_slots = []
    for r in results:
        if isinstance(r, list):
            all_slots.extend(r)

    # Sort by parsed date, unknowns go to the end
    def parse_date(slot):
        raw = slot.get("date", "")
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%B %d, %Y", "%d %B %Y"):
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                pass
        return date.max   # unknowns sort last

    all_slots.sort(key=parse_date)
    return all_slots


# ── Message formatting ────────────────────────────────────────────────────────
PROVIDER_LABELS = {"VFS": "VFS Global", "TLS": "TLScontact", "EMB": "Embassy"}

COUNTRY_FLAGS = {
    "AT": "🇦🇹", "BE": "🇧🇪", "BG": "🇧🇬", "HR": "🇭🇷", "CZ": "🇨🇿",
    "DK": "🇩🇰", "EE": "🇪🇪", "FI": "🇫🇮", "FR": "🇫🇷", "DE": "🇩🇪",
    "GR": "🇬🇷", "HU": "🇭🇺", "IS": "🇮🇸", "IT": "🇮🇹", "LV": "🇱🇻",
    "LI": "🇱🇮", "LT": "🇱🇹", "LU": "🇱🇺", "MT": "🇲🇹", "NL": "🇳🇱",
    "NO": "🇳🇴", "PL": "🇵🇱", "PT": "🇵🇹", "RO": "🇷🇴", "SK": "🇸🇰",
    "SI": "🇸🇮", "ES": "🇪🇸", "SE": "🇸🇪", "CH": "🇨🇭",
}


def format_all_slots(slots: list[dict]) -> str:
    if not slots:
        return (
            "😔 *No open slots found across all 29 Schengen countries.*\n\n"
            "I'll keep scanning every 2 minutes and alert you the instant one appears."
        )

    lines = [
        "🚨 *OPEN SCHENGEN APPOINTMENT SLOTS*",
        f"📊 Ranked by earliest date — {len(slots)} slot(s) found\n",
    ]

    # Group by country for a cleaner layout
    seen_countries = {}
    for s in slots:
        cc = s.get("country_code", "??")
        seen_countries.setdefault(cc, []).append(s)

    rank = 1
    for cc, country_slots in seen_countries.items():
        flag = COUNTRY_FLAGS.get(cc, "🌍")
        name = country_slots[0].get("country_name", cc)
        prov = PROVIDER_LABELS.get(country_slots[0].get("provider", ""), "")
        url  = country_slots[0].get("url", "#")

        lines.append(f"{rank}. {flag} *{name}* — {prov}")
        for s in country_slots[:3]:   # max 3 dates per country
            lines.append(f"   📅 {s.get('date','?')}  🕐 {s.get('time','?')}")
        lines.append(f"   🔗 [Book now]({url})\n")
        rank += 1
        if rank > 10:
            remaining = len(slots) - sum(len(v) for v in list(seen_countries.values())[:10])
            if remaining > 0:
                lines.append(f"…and slots in {len(seen_countries) - 10} more countries.")
            break

    lines.append("⚡ _Act fast — slots fill up quickly!_")
    return "\n".join(lines)


def format_no_slots_found(checked: int) -> str:
    return (
        f"✅ *Scan complete — {checked} countries checked.*\n\n"
        "😔 No open slots right now.\n"
        "I'll keep scanning every 2 minutes and ping you the moment one appears."
    )


# ── Command handlers ──────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Welcome to the Schengen Visa Appointment Notifier!*\n\n"
        "I scan *all 29 Schengen countries simultaneously* every 2 minutes "
        "and send you the earliest available slots ranked by date — "
        "so you grab the first opening anywhere in the Schengen area.\n\n"
        "One subscription covers every country and provider (VFS Global, TLScontact, Embassy).",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*Commands:*\n\n"
        "/start — Main menu\n"
        "/check — Scan all countries right now\n"
        "/unsubscribe — Stop alerts\n"
        "/help — This message\n\n"
        "*How it works:*\n"
        "• Scans all 29 Schengen countries every 2 minutes\n"
        "• Results ranked by earliest available date\n"
        "• Covers VFS Global, TLScontact & Embassy portals\n"
        "• One tap to subscribe, one tap to stop",
        parse_mode="Markdown",
    )


# ── Callback query handlers ───────────────────────────────────────────────────
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data  = query.data
    chat_id = str(query.from_user.id)

    if data == "back_main":
        await query.edit_message_text(
            "🏠 *Main Menu*",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(),
        )

    elif data == "subscribe":
        add_subscriber(chat_id)
        await query.edit_message_text(
            "✅ *Subscribed!*\n\n"
            "🌍 Monitoring: *all 29 Schengen countries*\n"
            "🏢 Providers: VFS Global · TLScontact · Embassy Direct\n"
            "⏱️ Scan interval: every *2 minutes*\n\n"
            "You'll receive a ranked list of the earliest available slots "
            "the moment any country opens up.\n\n"
            "Use /check to run a scan right now.",
            parse_mode="Markdown",
        )
        logger.info("New subscriber: %s", chat_id)

    elif data == "unsubscribe":
        if chat_id in get_subscribers():
            remove_subscriber(chat_id)
            await query.edit_message_text(
                "🔕 *Unsubscribed.* No more alerts.\n\nUse /start to subscribe again.",
                parse_mode="Markdown",
            )
        else:
            await query.edit_message_text(
                "ℹ️ You are not subscribed.\n\nUse /start to set up alerts.",
                parse_mode="Markdown",
            )

    elif data == "check_now":
        if chat_id not in get_subscribers():
            await query.edit_message_text(
                "⚠️ Subscribe first — use /start.",
            )
            return
        await query.edit_message_text(
            f"🔍 Scanning all 29 Schengen countries… this takes ~15 seconds."
        )
        slots = await scan_all_countries()
        if slots:
            msg = format_all_slots(slots)
        else:
            msg = format_no_slots_found(len(ALL_COUNTRIES))
        await query.edit_message_text(
            msg, parse_mode="Markdown", disable_web_page_preview=True
        )

    elif data == "my_settings":
        subs = get_subscribers()
        if chat_id in subs:
            since = subs[chat_id].get("added", "—")[:10]
            await query.edit_message_text(
                f"📋 *Your subscription:*\n\n"
                f"🌍 Watching: all 29 Schengen countries\n"
                f"🏢 Providers: VFS Global · TLScontact · Embassy\n"
                f"📅 Active since: `{since}`\n"
                f"⏱️ Scan interval: every 2 minutes",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Back", callback_data="back_main")]
                ]),
            )
        else:
            await query.edit_message_text(
                "You are not subscribed.",
                reply_markup=main_menu_keyboard(),
            )


# ── Scheduled job ─────────────────────────────────────────────────────────────
async def scheduled_check(app: Application):
    subs = get_subscribers()
    if not subs:
        return

    logger.info("Scheduled scan — %d subscriber(s), %d countries", len(subs), len(ALL_COUNTRIES))
    slots = await scan_all_countries()

    if not slots:
        logger.info("No slots found this round.")
        return

    msg = format_all_slots(slots)
    for chat_id in subs:
        try:
            await app.bot.send_message(
                chat_id=int(chat_id),
                text=msg,
                parse_mode="Markdown",
                disable_web_page_preview=True,
            )
            logger.info("Notified %s — %d slot(s)", chat_id, len(slots))
        except Exception as exc:
            logger.error("Failed to notify %s: %s", chat_id, exc)


async def daily_summary(app: Application):
    subs = get_subscribers()
    now  = datetime.now().strftime("%H:%M")
    for chat_id in subs:
        try:
            await app.bot.send_message(
                chat_id=int(chat_id),
                text=(
                    f"☀️ *Good morning!*\n\n"
                    f"Still watching all 29 Schengen countries.\n"
                    f"Last scan: {now} · Use /check to scan right now."
                ),
                parse_mode="Markdown",
            )
        except Exception as exc:
            logger.error("Daily summary error for %s: %s", chat_id, exc)


# ── Manual /check command ─────────────────────────────────────────────────────
async def manual_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_user.id)
    if chat_id not in get_subscribers():
        await update.message.reply_text(
            "⚠️ You are not subscribed. Use /start first."
        )
        return
    msg = await update.message.reply_text(
        "🔍 Scanning all 29 Schengen countries… (~15 seconds)"
    )
    slots = await scan_all_countries()
    text  = format_all_slots(slots) if slots else format_no_slots_found(len(ALL_COUNTRIES))
    await msg.edit_text(text, parse_mode="Markdown", disable_web_page_preview=True)


async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_user.id)
    remove_subscriber(chat_id)
    await update.message.reply_text("🔕 Unsubscribed. Use /start to subscribe again.")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    cfg = Config()
    if not cfg.BOT_TOKEN:
        raise ValueError("BOT_TOKEN is not set in your .env file.")

    app = Application.builder().token(cfg.BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",       start))
    app.add_handler(CommandHandler("help",        help_command))
    app.add_handler(CommandHandler("check",       manual_check))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe_command))
    app.add_handler(CallbackQueryHandler(button_handler))

    scheduler = AsyncIOScheduler(timezone="Europe/London")
    scheduler.add_job(
        scheduled_check, "interval",
        minutes=cfg.CHECK_INTERVAL_MINUTES,
        args=[app], id="slot_check",
    )
    scheduler.add_job(
        daily_summary, "cron",
        hour=8, minute=0,
        args=[app], id="daily_summary",
    )
    scheduler.start()
    logger.info("Scheduler started — scanning every %d min", cfg.CHECK_INTERVAL_MINUTES)
    logger.info("Bot is running. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
