import asyncio
import logging

import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

import config as cfg
import db
import handlers_admin
import handlers_users
from utils import spawn

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("main")

bot = Bot(token=cfg.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(handlers_admin.router)   # avval egasi (admin buyruqlari)
dp.include_router(handlers_users.router)   # keyin oddiy foydalanuvchilar

COMMANDS = [
    ("start", "Boshlash"), ("qahramonlar", "Qahramonlar ro'yxati"),
    ("qidir", "Qahramon qidirish"), ("tasodifiy", "Tasodifiy qahramon"),
    ("yordam", "Yordam"),
]

KEEPALIVE_SECONDS = 600  # 10 daqiqa: Render bepul server uxlab qolmasin


@dp.errors()
async def on_error(event):
    log.error("Handlerda xato: %s", event.exception, exc_info=event.exception)
    return True


async def _setup_telegram(bot: Bot):
    """Telegram sozlamalari fonda bajariladi: server portni darhol ochadi (Render shuni kutadi)."""
    try:
        await bot.set_my_commands([BotCommand(command=c, description=d) for c, d in COMMANDS])
    except Exception as e:  # noqa: BLE001
        log.error("Buyruqlar menyusini o'rnatib bo'lmadi: %s", e)
    if not cfg.BASE_URL:
        return
    for attempt in range(1, 6):
        try:
            await bot.set_webhook(
                f"{cfg.BASE_URL}/webhook",
                secret_token=cfg.WEBHOOK_SECRET,
                allowed_updates=dp.resolve_used_update_types(),
            )
            log.info("Webhook o'rnatildi: %s/webhook", cfg.BASE_URL)
            return
        except Exception as e:  # noqa: BLE001
            log.error("set_webhook %s-urinish xato: %s (BOT_TOKEN to'g'rimi?)", attempt, e)
            await asyncio.sleep(5)


async def _keepalive():
    """Render bepul servisi uzoq jim tursa uxlaydi; shu sabab o'zini-o'zi davriy 'uyg'otib' turadi."""
    if not cfg.BASE_URL:
        return
    await asyncio.sleep(120)
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
        while True:
            try:
                async with session.get(f"{cfg.BASE_URL}/health") as r:
                    log.info("Keepalive ping: %s", r.status)
            except Exception as e:  # noqa: BLE001
                log.warning("Keepalive ping xato: %s", e)
            await asyncio.sleep(KEEPALIVE_SECONDS)


async def on_startup(bot: Bot):
    await db.init()
    spawn(_setup_telegram(bot))
    spawn(_keepalive())


async def on_shutdown(bot: Bot):
    await db.close()
    await bot.session.close()


async def health(request):
    return web.Response(text="ok")


def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    if cfg.BASE_URL:
        app = web.Application()
        app["bot"] = bot
        app.router.add_get("/health", health)
        SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=cfg.WEBHOOK_SECRET).register(app, path="/webhook")
        setup_application(app, dp, bot=bot)
        log.info("Webhook rejimida ishga tushmoqda, port=%s", cfg.PORT)
        web.run_app(app, host="0.0.0.0", port=cfg.PORT)
    else:
        log.info("BASE_URL yo'q - polling rejimida ishga tushmoqda (lokal test uchun mos)")
        asyncio.run(dp.start_polling(bot))


if __name__ == "__main__":
    main()
