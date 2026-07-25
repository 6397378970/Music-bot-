# ==========================================================
# PREMIUM EMOJIS CONFIG
# Apna premium emoji ID yahan daalo.
# ID khali ("") rakhoge to normal emoji dikhega.
#
# ID kaise milega:
#   1. Koi bhi premium emoji apne Saved Messages mein bhejo
#   2. Us message ko @RawDataBot ko forward karo
#   3. "custom_emoji_id" copy karo
# ==========================================================

_EMOJIS = {
    # ── Music ─────────────────────────────────────────────
    "music":      ("🎵", ""),   # /play, now playing
    "headphone":  ("🎧", ""),   # now playing detail
    "mic":        ("🎙", ""),   # bot started
    "radio":      ("📻", ""),   # live/radio
    "notes":      ("🎶", ""),   # general music

    # ── Playback Controls ─────────────────────────────────
    "play":       ("▶",  ""),   # playing / resume
    "pause":      ("⏸",  ""),   # paused
    "stop":       ("⏹",  ""),   # stopped
    "skip":       ("⏭",  ""),   # skipped
    "seek":       ("⏩",  ""),   # seeked forward
    "seekback":   ("⏪",  ""),   # seeked backward
    "loop":       ("🔁",  ""),   # loop
    "shuffle":    ("🔀",  ""),   # shuffle
    "replay":     ("↻",   ""),   # replayed

    # ── Status ────────────────────────────────────────────
    "check":      ("✅",  ""),   # success
    "cross":      ("❌",  ""),   # error / not found
    "warn":       ("⚠️", ""),   # warning
    "ban":        ("🚫",  ""),   # banned
    "lock":       ("🔒",  ""),   # admin only / locked
    "auth":       ("🔐",  ""),   # authorized
    "key":        ("🔑",  ""),   # sudo / key
    "crown":      ("👑",  ""),   # owner / sudo
    "live":       ("🔴",  ""),   # live stream
    "expire":     ("⌛",  ""),   # expired
    "stopsign":   ("🛑",  ""),   # broadcast stopped

    # ── Info & System ─────────────────────────────────────
    "zap":        ("⚡",  ""),   # fast / powered by
    "ping":       ("📡",  ""),   # ping / satellite
    "cpu":        ("💻",  ""),   # cpu
    "ram":        ("🧠",  ""),   # ram
    "disk":       ("💾",  ""),   # storage
    "clock":      ("🕐",  ""),   # duration / uptime
    "wait":       ("⏳",  ""),   # processing / wait
    "refresh":    ("🔄",  ""),   # reloading
    "bot":        ("🤖",  ""),   # bot
    "pkg":        ("📦",  ""),   # modules
    "py":         ("🐍",  ""),   # python

    # ── Users & Chats ─────────────────────────────────────
    "user":       ("👤",  ""),   # single user
    "users":      ("👥",  ""),   # multiple users
    "chat":       ("💬",  ""),   # chat
    "id":         ("🆔",  ""),   # user/chat id
    "tag":        ("🔖",  ""),   # tag

    # ── Actions ───────────────────────────────────────────
    "dl":         ("⬇️", ""),   # downloading
    "send":       ("📤",  ""),   # broadcast send
    "broadcast":  ("📢",  ""),   # broadcast
    "mail":       ("📬",  ""),   # sent to
    "empty":      ("📭",  ""),   # empty / no data
    "folder":     ("📂",  ""),   # logs folder
    "doc":        ("📄",  ""),   # log file
    "link":       ("🔗",  ""),   # link / source
    "trash":      ("🗑",   ""),   # removed
    "add":        ("✚",   ""),   # add me
    "mute":       ("🔕",  ""),   # logger off

    # ── UI ────────────────────────────────────────────────
    "queue":      ("📋",  ""),   # queue list
    "stats":      ("📊",  ""),   # stats
    "lang":       ("🌍",  ""),   # language
    "back":       ("↩",   ""),   # back button
    "heart":      ("♥",   ""),   # powered by
    "star":       ("✦",   ""),   # now playing header
    "bullet":     ("▸",   ""),   # list bullet
}


def e(key: str) -> str:
    """
    Return premium emoji HTML if ID is set, else return plain emoji.

    Usage in Python files:
        from Elevenyts.emojis import e
        text = f"{e('music')} Now Playing"
    """
    fallback, eid = _EMOJIS.get(key, ("❓", ""))
    if eid:
        return f'<tg-emoji emoji-id="{eid}">{fallback}</tg-emoji>'
    return fallback


def build_map() -> dict:
    """
    Returns a dict {e_key: emoji_html} for use in string .format_map().
    Used by lang.py to substitute placeholders in locale strings.
    """
    return {f"e_{k}": e(k) for k in _EMOJIS}
