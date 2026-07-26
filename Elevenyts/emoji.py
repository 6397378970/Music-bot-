# ==========================================================
# Premium Custom Emoji IDs
# Yahan apne premium emoji IDs daalo
#
# Kaise use karein:
#   from Elevenyts.emoji import Emoji
#   text = f"{Emoji.MUSIC} Chal raha hai!"
#
# Telegram custom emoji format:
#   <emoji id="EMOJI_ID">🔥</emoji>  — HTML parse mode mein
#   ya seedha Emoji.NAME string use karo jo already formatted hai
# ==========================================================


def _e(emoji_id: str, fallback: str) -> str:
    """Custom premium emoji string banata hai HTML format mein."""
    return f'<emoji id="{emoji_id}">{fallback}</emoji>'


class Emoji:
    # ── Music & Playback ─────────────────────────────────
    MUSIC         = _e("4970133401857163956", "🎵")   # Yahan ID daalo
    PLAY          = _e("4970176665062736422", "▶️")
    PAUSE         = _e("", "⏸")
    STOP          = _e("", "⏹")
    SKIP          = _e("", "⏭")
    QUEUE         = _e("", "📋")
    LOOP          = _e("", "🔁")
    SHUFFLE       = _e("", "🔀")
    VOLUME        = _e("", "🔊")
    MUTE          = _e("", "🔇")

    # ── Status & UI ──────────────────────────────────────
    SUCCESS       = _e("", "✅")
    ERROR         = _e("", "❌")
    WARNING       = _e("", "⚠️")
    LOADING       = _e("", "⏳")
    FIRE          = _e("", "🔥")
    STAR          = _e("", "⭐")
    CROWN         = _e("", "👑")
    HEART         = _e("", "❤️")
    ROCKET        = _e("", "🚀")
    SPARKLE       = _e("", "✨")

    # ── Admin & Bot ──────────────────────────────────────
    ADMIN         = _e("", "🛡")
    BAN           = _e("", "🔨")
    SETTINGS      = _e("", "⚙️")
    BROADCAST     = _e("", "📢")
    STATS         = _e("", "📊")
    PING          = _e("", "📡")


# ── Seedhe string chahiye toh plain fallback ─────────────
# (premium emoji support na ho tab kaam aata hai)
class PlainEmoji:
    MUSIC     = "🎵"
    PLAY      = "▶️"
    PAUSE     = "⏸"
    STOP      = "⏹"
    SKIP      = "⏭"
    QUEUE     = "📋"
    LOOP      = "🔁"
    SHUFFLE   = "🔀"
    VOLUME    = "🔊"
    MUTE      = "🔇"
    SUCCESS   = "✅"
    ERROR     = "❌"
    WARNING   = "⚠️"
    LOADING   = "⏳"
    FIRE      = "🔥"
    STAR      = "⭐"
    CROWN     = "👑"
    HEART     = "❤️"
    ROCKET    = "🚀"
    SPARKLE   = "✨"
    ADMIN     = "🛡"
    BAN       = "🔨"
    SETTINGS  = "⚙️"
    BROADCAST = "📢"
    STATS     = "📊"
    PING      = "📡"
