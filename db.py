"""Ma'lumotlar bazasi: qahramon (hero) qo'llanmalari va foydalanuvchilar ro'yxati.
DATABASE_URL berilmasa, avtomatik lokal SQLite fayl ishlatiladi (data/bot.db)."""
import logging
import os
from datetime import datetime, timezone
from urllib.parse import urlparse

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine

import config as cfg

log = logging.getLogger("db")
md = sa.MetaData()


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


heroes = sa.Table(
    "heroes", md,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("name", sa.String(80), nullable=False, unique=True),
    sa.Column("role", sa.String(40), nullable=False),
    sa.Column("difficulty", sa.String(20), nullable=False),
    sa.Column("summary", sa.Text, default=""),
    sa.Column("build", sa.Text, default=""),
    sa.Column("combo", sa.Text, default=""),
    sa.Column("tips", sa.Text, default=""),
    sa.Column("counters", sa.Text, default=""),
    sa.Column("photo_file_id", sa.String(300), nullable=True),
    sa.Column("video_file_id", sa.String(300), nullable=True),
    sa.Column("video_url", sa.String(500), nullable=True),
    sa.Column("created_at", sa.DateTime, default=utcnow),
    sa.Column("updated_at", sa.DateTime, default=utcnow, onupdate=utcnow),
)

users = sa.Table(
    "users", md,
    sa.Column("id", sa.BigInteger, primary_key=True),
    sa.Column("username", sa.String(80), nullable=True),
    sa.Column("first_name", sa.String(200), nullable=True),
    sa.Column("joined_at", sa.DateTime, default=utcnow),
)


def _make_engine():
    url = cfg.DATABASE_URL
    if not url:
        os.makedirs("data", exist_ok=True)
        log.info("DATABASE_URL berilmagan - lokal SQLite ishlatiladi (data/bot.db)")
        return create_async_engine("sqlite+aiosqlite:///data/bot.db")

    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]

    parts = urlparse(url)
    local = (parts.hostname or "") in ("localhost", "127.0.0.1")
    base = url.split("?")[0]
    args = {}
    if "+asyncpg" in url:
        if not local and "sslmode=disable" not in url:
            args["ssl"] = True
        args["statement_cache_size"] = 0  # pgbouncer (Neon pooler) bilan mos ishlashi uchun
        base = base + "?prepared_statement_cache_size=0"

    return create_async_engine(base, connect_args=args, pool_size=3, max_overflow=2, pool_pre_ping=True)


engine = _make_engine()


async def init():
    async with engine.begin() as c:
        await c.run_sync(md.create_all)
    log.info("Baza tayyor.")


async def close():
    await engine.dispose()


def _d(row):
    return dict(row._mapping) if row is not None else None


# ---------- qahramonlar ----------
async def add_hero(data: dict) -> int:
    async with engine.begin() as c:
        res = await c.execute(sa.insert(heroes).values(**data))
    return res.inserted_primary_key[0]


async def get_hero(hero_id: int):
    async with engine.connect() as c:
        row = (await c.execute(sa.select(heroes).where(heroes.c.id == hero_id))).first()
    return _d(row)


async def get_hero_by_name(name: str):
    async with engine.connect() as c:
        row = (await c.execute(
            sa.select(heroes).where(sa.func.lower(heroes.c.name) == name.strip().lower())
        )).first()
    return _d(row)


async def update_hero(hero_id: int, **fields):
    if not fields:
        return
    async with engine.begin() as c:
        await c.execute(sa.update(heroes).where(heroes.c.id == hero_id).values(**fields))


async def delete_hero(hero_id: int) -> bool:
    async with engine.begin() as c:
        res = await c.execute(sa.delete(heroes).where(heroes.c.id == hero_id))
    return res.rowcount > 0


async def list_heroes_by_role(role: str):
    async with engine.connect() as c:
        rows = (await c.execute(
            sa.select(heroes).where(heroes.c.role == role).order_by(heroes.c.name)
        )).all()
    return [_d(r) for r in rows]


async def list_all_heroes():
    async with engine.connect() as c:
        rows = (await c.execute(sa.select(heroes).order_by(heroes.c.role, heroes.c.name))).all()
    return [_d(r) for r in rows]


async def search_heroes(query: str, limit: int = 15):
    q = f"%{query.strip().lower()}%"
    async with engine.connect() as c:
        rows = (await c.execute(
            sa.select(heroes).where(sa.func.lower(heroes.c.name).like(q)).order_by(heroes.c.name).limit(limit)
        )).all()
    return [_d(r) for r in rows]


async def random_hero():
    async with engine.connect() as c:
        row = (await c.execute(sa.select(heroes).order_by(sa.func.random()).limit(1))).first()
    return _d(row)


async def count_heroes() -> int:
    async with engine.connect() as c:
        return (await c.execute(sa.select(sa.func.count()).select_from(heroes))).scalar_one()


# ---------- foydalanuvchilar ----------
async def touch_user(user_id: int, username: str | None, first_name: str | None):
    async with engine.begin() as c:
        exists = (await c.execute(sa.select(users.c.id).where(users.c.id == user_id))).first()
        if exists:
            await c.execute(sa.update(users).where(users.c.id == user_id)
                             .values(username=username, first_name=first_name))
        else:
            await c.execute(sa.insert(users).values(id=user_id, username=username, first_name=first_name))


async def count_users() -> int:
    async with engine.connect() as c:
        return (await c.execute(sa.select(sa.func.count()).select_from(users))).scalar_one()


async def all_user_ids():
    async with engine.connect() as c:
        rows = (await c.execute(sa.select(users.c.id))).all()
    return [r[0] for r in rows]
