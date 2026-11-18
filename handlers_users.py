"""Oddiy foydalanuvchilar uchun: qahramonlarni rol bo'yicha ko'rish, qidirish, tasodifiy qahramon."""
import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import config as cfg
import db
from utils import esc, hero_card_text, role_label, split_text

log = logging.getLogger("users")
router = Router(name="users")
router.message.filter(F.chat.type == "private")

WELCOME = """👋 Salom! Men Mobile Legends qahramonlarini qanday o'ynashni o'rgataman.

🎮 /qahramonlar — rol bo'yicha ko'rish
🔍 /qidir <ism> — qahramon qidirish
🎲 /tasodifiy — tasodifiy qahramon tavsiyasi
❓ /yordam — yordam"""

HELP = """<b>Buyruqlar</b>

• /qahramonlar — qahramonlarni rol bo'yicha ko'rish
• /qidir &lt;ism&gt; — ism bo'yicha qidirish (masalan: /qidir fanny)
• /tasodifiy — tasodifiy qahramon tavsiyasi"""


def _main_role_kb() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=role_label(r), callback_data=f"role:{r}")] for r in cfg.ROLES]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _hero_list_kb(heroes: list, back_cb: str) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=h["name"], callback_data=f"hero:{h['id']}:{back_cb}")] for h in heroes]
    rows.append([InlineKeyboardButton(text="⬅️ Rollarga qaytish", callback_data="roles")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _hero_detail_kb(back_cb: str) -> InlineKeyboardMarkup | None:
    rows = [[InlineKeyboardButton(text="⬅️ Ro'yxatga qaytish", callback_data=back_cb)]]
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _send_hero(target, hero: dict, kb=None):
    """target: Message yoki CallbackQuery.message — rasm/matn/videoni ketma-ket yuboradi.
    Rasmga faqat oddiy sarlavha beramiz, to'liq (HTML'li) matnni alohida xabar qilib yuboramiz —
    shunda uzun matn HTML teglarini noto'g'ri joydan kesib, xatoga olib kelmaydi."""
    text = hero_card_text(hero)
    if hero.get("photo_file_id"):
        await target.answer_photo(hero["photo_file_id"], caption=f"{role_label(hero['role'])} · {esc(hero['name'])}")
    parts = split_text(text, limit=3800)
    for i, part in enumerate(parts):
        await target.answer(part, reply_markup=kb if i == len(parts) - 1 else None)
    if hero.get("video_file_id"):
        await target.answer_video(hero["video_file_id"], caption="🎬 Gameplay")
    elif hero.get("video_url"):
        vkb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="▶️ Videoni ko'rish", url=hero["video_url"])]])
        await target.answer("🎬 Video qo'llanma:", reply_markup=vkb)


@router.message(Command("start"))
async def cmd_start(m: Message):
    await db.touch_user(m.from_user.id, m.from_user.username, m.from_user.first_name)
    await m.answer(WELCOME)


@router.message(Command("yordam"))
async def cmd_help(m: Message):
    await m.answer(HELP)


@router.message(Command("qahramonlar"))
async def cmd_heroes(m: Message):
    await m.answer("Qaysi rolni ko'rmoqchisiz?", reply_markup=_main_role_kb())


@router.callback_query(F.data == "roles")
async def cb_roles(cb: CallbackQuery):
    await cb.message.edit_text("Qaysi rolni ko'rmoqchisiz?", reply_markup=_main_role_kb())
    await cb.answer()


@router.callback_query(F.data.startswith("role:"))
async def cb_role(cb: CallbackQuery):
    role = cb.data.split(":", 1)[1]
    rows = await db.list_heroes_by_role(role)
    if not rows:
        return await cb.answer("Bu rolda hali qahramon qo'shilmagan.", show_alert=True)
    await cb.message.edit_text(f"{role_label(role)} — qahramonlar:", reply_markup=_hero_list_kb(rows, f"role:{role}"))
    await cb.answer()


@router.callback_query(F.data.startswith("hero:"))
async def cb_hero(cb: CallbackQuery):
    _, hero_id, back_cb = cb.data.split(":", 2)
    hero = await db.get_hero(int(hero_id))
    if not hero:
        return await cb.answer("Topilmadi (o'chirilgan bo'lishi mumkin).", show_alert=True)
    await cb.answer()
    await _send_hero(cb.message, hero, _hero_detail_kb(back_cb))


@router.message(Command("qidir"))
async def cmd_search(m: Message, command: CommandObject):
    q = (command.args or "").strip()
    if not q:
        return await m.answer("Misol: /qidir fanny")
    rows = await db.search_heroes(q)
    if not rows:
        return await m.answer(f"\"{esc(q)}\" bo'yicha hech narsa topilmadi.")
    if len(rows) == 1:
        return await _send_hero(m, rows[0])
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=h["name"], callback_data=f"hero:{h['id']}:roles")] for h in rows
    ])
    await m.answer("Topilganlar:", reply_markup=kb)


@router.message(Command("tasodifiy"))
async def cmd_random(m: Message):
    hero = await db.random_hero()
    if not hero:
        return await m.answer("Hali birorta qahramon qo'shilmagan.")
    await _send_hero(m, hero)


@router.message(F.chat.type == "private")
async def on_other_text(m: Message):
    await m.answer("Tushunmadim 🤔 /yordam buyrug'ini yuboring.")
