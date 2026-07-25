# ==========================================================
# Copyright (c) 2026 ArtistBots — All Rights Reserved.
# ==========================================================
import time
import psutil

from pyrogram import filters, types
from Elevenyts import app, tune, boot, config, lang
from Elevenyts.helpers import buttons


@app.on_message(filters.command(["alive", "ping"]) & ~app.bl_users)
@lang.language()
async def _ping(_, m: types.Message):
    try:
        await m.delete()
    except Exception:
        pass

    start = time.time()
    sent = await m.reply_text(m.lang["pinging"])

    def get_time(s):
        parts = []
        for v, u in zip(
            [s // 86400, (s // 3600) % 24, (s // 60) % 60, s % 60],
            ["d", "h", "m", "s"]
        ):
            if v:
                parts.append(f"{v}{u}")
        return " ".join(parts) or "0s"

    uptime  = get_time(int(time.time() - boot))
    latency = round((time.time() - start) * 1000, 2)
    mem     = psutil.virtual_memory()
    ram     = f"{round(mem.used/(1024**3),1)}GB / {round(mem.total/(1024**3),1)}GB"
    cpu     = psutil.cpu_percent(interval=0.5)

    from Elevenyts import db
    active_chats = len(await db.get_chats())

    bot_name = getattr(app, "name", "Elevenyts")

    text = m.lang["ping_pong"].format(
        bot_name,
        latency,
        uptime,
        await tune.ping(),
        ram,
        cpu,
        active_chats,
    )

    try:
        await sent.edit_media(
            media=types.InputMediaPhoto(media=config.PING_IMG, caption=text),
            reply_markup=buttons.ping_markup(m.lang["support"]),
        )
    except Exception:
        await sent.edit_text(
            text=text,
            reply_markup=buttons.ping_markup(m.lang["support"]),
        )
