"""Umumiy yordamchi funksiyalar."""
import asyncio
import html
import logging

log = logging.getLogger("utils")

ROLE_EMOJI = {
    "Tank": "🛡", "Jangchi": "⚔️", "Suiqasdchi": "🗡",
    "Sehrgar": "🔮", "O'qchi": "🏹", "Yordamchi": "💚",
}
DIFF_EMOJI = {"Oson": "🟢", "O'rta": "🟡", "Qiyin": "🔴"}


def esc(s) -> str:
    return html.escape(str(s or ""), quote=False)


def role_label(role: str) -> str:
    return f"{ROLE_EMOJI.get(role, '')} {role}".strip()


def diff_label(diff: str) -> str:
    return f"{DIFF_EMOJI.get(diff, '')} {diff}".strip()


def hero_card_text(h: dict) -> str:
    parts = [
        f"<b>{esc(h['name'])}</b>",
        f"{role_label(h['role'])} · Qiyinligi: {diff_label(h['difficulty'])}",
    ]
    if h.get("summary"):
        parts.append(f"\n{esc(h['summary'])}")
    if h.get("build"):
        parts.append(f"\n🛒 <b>Build:</b>\n{esc(h['build'])}")
    if h.get("combo"):
        parts.append(f"\n🎯 <b>Kombo:</b>\n{esc(h['combo'])}")
    if h.get("tips"):
        parts.append(f"\n💡 <b>Maslahatlar:</b>\n{esc(h['tips'])}")
    if h.get("counters"):
        parts.append(f"\n⚖️ <b>Kuchli/kuchsiz tomonlari:</b>\n{esc(h['counters'])}")
    return "\n".join(parts)


def split_text(text: str, limit: int = 3800) -> list[str]:
    text = text or ""
    out = []
    while len(text) > limit:
        cut = text.rfind("\n", 0, limit)
        if cut < limit // 2:
            cut = limit
        out.append(text[:cut])
        text = text[cut:].lstrip("\n")
    if text:
        out.append(text)
    return out


def spawn(coro):
    """Fon vazifasini ishga tushiradi va xatosini log qilib qo'yadi (jim o'lib qolmasligi uchun)."""
    task = asyncio.ensure_future(coro)

    def _done(t):
        exc = t.exception() if not t.cancelled() else None
        if exc:
            log.error("Fon vazifasida xato: %s", exc, exc_info=exc)

    task.add_done_callback(_done)
    return task
