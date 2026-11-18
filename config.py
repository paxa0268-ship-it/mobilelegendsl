"""Sozlamalarni muhit o'zgaruvchilaridan (environment variables) o'qiydi.
Render'da bularni Dashboard -> Environment bo'limiga kiritasiz, hech qanday .env fayl kerak emas."""
import os
import sys


def _e(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


BOT_TOKEN = _e("BOT_TOKEN")
OWNER_ID_RAW = _e("OWNER_ID")
DATABASE_URL = _e("DATABASE_URL")  # bo'sh bo'lsa SQLite ishlatiladi (data/bot.db)
BASE_URL = (_e("BASE_URL") or _e("RENDER_EXTERNAL_URL")).rstrip("/")
PORT = int(_e("PORT", "10000"))
WEBHOOK_SECRET = _e("WEBHOOK_SECRET") or "ml-hero-bot-secret"

_missing = []
if not BOT_TOKEN:
    _missing.append("BOT_TOKEN")
if not OWNER_ID_RAW:
    _missing.append("OWNER_ID")

if _missing:
    print(f"XATO: quyidagi muhit o'zgaruvchilari kiritilmagan: {', '.join(_missing)}", file=sys.stderr)
    print("Render -> Settings -> Environment bo'limiga kiriting.", file=sys.stderr)
    sys.exit(1)

try:
    OWNER_ID = int(OWNER_ID_RAW)
except ValueError:
    print(f"XATO: OWNER_ID butun son bo'lishi kerak, hozir: {OWNER_ID_RAW!r}", file=sys.stderr)
    sys.exit(1)

ROLES = ["Tank", "Jangchi", "Suiqasdchi", "Sehrgar", "O'qchi", "Yordamchi"]
DIFFICULTIES = ["Oson", "O'rta", "Qiyin"]
