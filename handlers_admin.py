"""Faqat bot egasi (OWNER_ID) uchun: qahramon qo'llanmalarini qo'shish/tahrirlash/o'chirish."""
import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import config as cfg
import db
from utils import esc, hero_card_text, role_label, split_text

log = logging.getLogger("admin")
router = Router(name="admin")
router.message.filter(F.chat.type == "private", F.from_user.id == cfg.OWNER_ID)
router.callback_query.filter(F.from_user.id == cfg.OWNER_ID)

SKIP = "/otkazib_yuborish"
CANCEL = "/bekor_qilish"

HELP = f"""<b>Admin buyruqlari</b>

• /qahramon_qosh &lt;Ism&gt; — yangi qahramon qo'shish (bosqichma-bosqich so'rayman)
• /qahramonlarim — barcha qahramonlar ro'yxati (ID bilan)
• /qahramon_ochir &lt;Ism&gt; — qahramonni butunlay o'chirish
• /statistika — foydalanuvchilar va qahramonlar soni

Qo'shish jarayonida istalgan payt {CANCEL} yozib bekor qilishingiz mumkin.
Ixtiyoriy maydonlarda {SKIP} yozib o'tkazib yuborish mumkin."""


class AddHero(StatesGroup):
    role = State()
    difficulty = State()
    summary = State()
    build = State()
    combo = State()
    tips = State()
    counters = State()
    photo = State()
    video = State()


def _role_kb() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=r, callback_data=f"arole:{r}")] for r in cfg.ROLES]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _diff_kb() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=d, callback_data=f"adiff:{d}")] for d in cfg.DIFFICULTIES]
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(Command("yordam", "start"))
async def cmd_admin_help(m: Message):
    await m.answer(HELP)


@router.message(Command("statistika"))
async def cmd_stats(m: Message):
    await m.answer(
        f"📊 Qahramonlar: {await db.count_heroes()}\n👥 Foydalanuvchilar: {await db.count_users()}"
    )


@router.message(Command("qahramonlarim"))
async def cmd_list_mine(m: Message):
    rows = await db.list_all_heroes()
    if not rows:
        return await m.answer("Hali birorta qahramon qo'shilmagan. /qahramon_qosh <Ism>")
    lines = [f"#{r['id']} · {r['name']} · {r['role']}" for r in rows]
    for part in split_text("\n".join(lines)):
        await m.answer(part)


@router.message(Command("bekor_qilish"))
async def cmd_cancel(m: Message, state: FSMContext):
    if await state.get_state() is None:
        return await m.answer("Hozir hech qanday jarayon ketayotgani yo'q.")
    await state.clear()
    await m.answer("❌ Bekor qilindi.")


# ---------- qo'shish ----------
@router.message(Command("qahramon_qosh"))
async def cmd_add_start(m: Message, command: CommandObject, state: FSMContext):
    name = (command.args or "").strip()
    if not name:
        return await m.answer("Misol: /qahramon_qosh Fanny")
    if await db.get_hero_by_name(name):
        return await m.answer(
            f"\"{esc(name)}\" allaqachon mavjud. Avval /qahramon_ochir {esc(name)} bilan o'chiring, so'ng qayta qo'shing.")
    await state.update_data(name=name)
    await state.set_state(AddHero.role)
    await m.answer(f"\"{esc(name)}\" qo'shilmoqda.\n\nQaysi rolda?", reply_markup=_role_kb())


@router.callback_query(StateFilter(AddHero.role), F.data.startswith("arole:"))
async def add_role(cb: CallbackQuery, state: FSMContext):
    role = cb.data.split(":", 1)[1]
    await state.update_data(role=role)
    await state.set_state(AddHero.difficulty)
    await cb.message.edit_text(f"Rol: {role}\n\nQiyinligi qanday?", reply_markup=_diff_kb())
    await cb.answer()


@router.callback_query(StateFilter(AddHero.difficulty), F.data.startswith("adiff:"))
async def add_diff(cb: CallbackQuery, state: FSMContext):
    diff = cb.data.split(":", 1)[1]
    await state.update_data(difficulty=diff)
    await state.set_state(AddHero.summary)
    await cb.message.edit_text(f"Qiyinligi: {diff}\n\nEndi qisqacha tavsif yozing (1-2 gap):")
    await cb.answer()


@router.message(StateFilter(AddHero.summary))
async def add_summary(m: Message, state: FSMContext):
    if m.text == CANCEL:
        await state.clear()
        return await m.answer("❌ Bekor qilindi.")
    await state.update_data(summary=(m.text or "").strip())
    await state.set_state(AddHero.build)
    await m.answer("🛒 Build (item'larni yozing, har birini yangi qatorga yozsangiz chiroyli chiqadi):")


@router.message(StateFilter(AddHero.build))
async def add_build(m: Message, state: FSMContext):
    if m.text == CANCEL:
        await state.clear()
        return await m.answer("❌ Bekor qilindi.")
    await state.update_data(build=(m.text or "").strip())
    await state.set_state(AddHero.combo)
    await m.answer("🎯 Skill kombosi (masalan: 2-1-Asosiy zarba-Ultimate):")


@router.message(StateFilter(AddHero.combo))
async def add_combo(m: Message, state: FSMContext):
    if m.text == CANCEL:
        await state.clear()
        return await m.answer("❌ Bekor qilindi.")
    await state.update_data(combo=(m.text or "").strip())
    await state.set_state(AddHero.tips)
    await m.answer("💡 Umumiy maslahatlar (qanday o'ynash kerak, qachon hujum qilish kerak va h.k.):")


@router.message(StateFilter(AddHero.tips))
async def add_tips(m: Message, state: FSMContext):
    if m.text == CANCEL:
        await state.clear()
        return await m.answer("❌ Bekor qilindi.")
    await state.update_data(tips=(m.text or "").strip())
    await state.set_state(AddHero.counters)
    await m.answer(f"⚖️ Kimlarga qarshi kuchli/kuchsiz? (Ixtiyoriy — {SKIP} yozib o'tkazib yuboring)")


@router.message(StateFilter(AddHero.counters))
async def add_counters(m: Message, state: FSMContext):
    if m.text == CANCEL:
        await state.clear()
        return await m.answer("❌ Bekor qilindi.")
    counters = "" if m.text == SKIP else (m.text or "").strip()
    await state.update_data(counters=counters)
    await state.set_state(AddHero.photo)
    await m.answer(f"🖼 Endi shu qahramonning skrinshotini/rasmini yuboring (yoki {SKIP}).")


@router.message(StateFilter(AddHero.photo), F.photo)
async def add_photo(m: Message, state: FSMContext):
    await state.update_data(photo_file_id=m.photo[-1].file_id)
    await state.set_state(AddHero.video)
    await m.answer(f"🎬 Endi gameplay video yuboring YOKI YouTube havolasini yozing (yoki {SKIP}).")


@router.message(StateFilter(AddHero.photo))
async def add_photo_skip(m: Message, state: FSMContext):
    if m.text == CANCEL:
        await state.clear()
        return await m.answer("❌ Bekor qilindi.")
    if m.text != SKIP:
        return await m.answer(f"Rasm yuboring yoki {SKIP} deb yozing.")
    await state.update_data(photo_file_id=None)
    await state.set_state(AddHero.video)
    await m.answer(f"🎬 Endi gameplay video yuboring YOKI YouTube havolasini yozing (yoki {SKIP}).")


@router.message(StateFilter(AddHero.video), F.video)
async def add_video_file(m: Message, state: FSMContext):
    await state.update_data(video_file_id=m.video.file_id, video_url=None)
    await _finish_add(m, state)


@router.message(StateFilter(AddHero.video))
async def add_video_text(m: Message, state: FSMContext):
    if m.text == CANCEL:
        await state.clear()
        return await m.answer("❌ Bekor qilindi.")
    text = (m.text or "").strip()
    if text == SKIP:
        await state.update_data(video_file_id=None, video_url=None)
    elif text.startswith("http://") or text.startswith("https://"):
        await state.update_data(video_file_id=None, video_url=text)
    else:
        return await m.answer(f"Video fayl yuboring, havola yozing yoki {SKIP} deb yozing.")
    await _finish_add(m, state)


async def _finish_add(m: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    hero_id = await db.add_hero({
        "name": data["name"], "role": data["role"], "difficulty": data["difficulty"],
        "summary": data.get("summary", ""), "build": data.get("build", ""),
        "combo": data.get("combo", ""), "tips": data.get("tips", ""),
        "counters": data.get("counters", ""),
        "photo_file_id": data.get("photo_file_id"),
        "video_file_id": data.get("video_file_id"),
        "video_url": data.get("video_url"),
    })
    hero = await db.get_hero(hero_id)
    await m.answer(f"✅ #{hero_id} \"{esc(hero['name'])}\" qo'shildi!")
    if hero.get("photo_file_id"):
        await m.answer_photo(hero["photo_file_id"], caption=f"{role_label(hero['role'])} · {esc(hero['name'])}")
    for part in split_text(hero_card_text(hero), limit=3800):
        await m.answer(part)


# ---------- o'chirish ----------
@router.message(Command("qahramon_ochir"))
async def cmd_delete(m: Message, command: CommandObject):
    name = (command.args or "").strip()
    if not name:
        return await m.answer("Misol: /qahramon_ochir Fanny")
    hero = await db.get_hero_by_name(name)
    if not hero:
        return await m.answer(f"\"{esc(name)}\" topilmadi.")
    await db.delete_hero(hero["id"])
    await m.answer(f"🗑 \"{esc(hero['name'])}\" o'chirildi.")


# ---------- bitta maydonni tahrirlash ----------
FIELD_MAP = {
    "tavsif": "summary", "build": "build", "kombo": "combo",
    "maslahat": "tips", "qarshi": "counters",
}


@router.message(Command("qahramon_tahrir"))
async def cmd_edit(m: Message, command: CommandObject):
    args = (command.args or "").split(maxsplit=2)
    if len(args) < 3 or args[1] not in FIELD_MAP:
        fields = ", ".join(FIELD_MAP)
        return await m.answer(
            f"Misol: /qahramon_tahrir Fanny build Qalqon+Qilich+...\n\nMumkin bo'lgan maydonlar: {fields}")
    name, field, value = args
    hero = await db.get_hero_by_name(name)
    if not hero:
        return await m.answer(f"\"{esc(name)}\" topilmadi.")
    await db.update_hero(hero["id"], **{FIELD_MAP[field]: value.strip()})
    await m.answer(f"✏️ \"{esc(hero['name'])}\" ning \"{field}\" maydoni yangilandi.")


@router.message(Command("qahramon_rasm"), F.reply_to_message, F.reply_to_message.photo)
async def cmd_set_photo(m: Message, command: CommandObject):
    name = (command.args or "").strip()
    if not name:
        return await m.answer("Rasmga javob qaytarib shu buyruqni yozing: /qahramon_rasm <Ism>")
    hero = await db.get_hero_by_name(name)
    if not hero:
        return await m.answer(f"\"{esc(name)}\" topilmadi.")
    await db.update_hero(hero["id"], photo_file_id=m.reply_to_message.photo[-1].file_id)
    await m.answer(f"🖼 \"{esc(hero['name'])}\" ning rasmi yangilandi.")


@router.message(Command("qahramon_video"), F.reply_to_message, F.reply_to_message.video)
async def cmd_set_video(m: Message, command: CommandObject):
    name = (command.args or "").strip()
    if not name:
        return await m.answer("Videoga javob qaytarib shu buyruqni yozing: /qahramon_video <Ism>")
    hero = await db.get_hero_by_name(name)
    if not hero:
        return await m.answer(f"\"{esc(name)}\" topilmadi.")
    await db.update_hero(hero["id"], video_file_id=m.reply_to_message.video.file_id, video_url=None)
    await m.answer(f"🎬 \"{esc(hero['name'])}\" ning videosi yangilandi.")
