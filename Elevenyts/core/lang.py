# ==========================================================
# Copyright (c) 2026 ArtistBots
# All Rights Reserved.
#
# Project      : ArtistBots API Telegram Music Bot
# Powered By   : Artist
# Type         : API Based Telegram Music Bot
#
# Bot          : @ArtistApibot
# Channel      : https://t.me/artistbots
# GitHub       : https://github.com/elevenyts
#
# Unauthorized copying, modification, or redistribution
# of this source code without permission is prohibited.
# ==========================================================
import json
from functools import wraps
from pathlib import Path

from Elevenyts import db, logger

# Supported language codes and their display names
lang_codes = {
    "en": "English 🇬🇧",
    "hi": "Hindi 🇮🇳",
    "te": "Telugu 🇮🇳",
    "ko": "Korean 🇰🇷",
    "my": "Myanmar 🇲🇲",
    "id": "Indonesian 🇮🇩",
    "pt": "Portuguese 🇧🇷",
    "ar": "Arabic 🇸🇦",
    "es": "Spanish 🇪🇸",
    "fr": "French 🇫🇷",
    "ru": "Russian 🇷🇺",
    "de": "German 🇩🇪",
    "tr": "Turkish 🇹🇷",
    "bn": "Bengali 🇧🇩",
    "th": "Thai 🇹🇭",
    "vi": "Vietnamese 🇻🇳",
    "ja": "Japanese 🇯🇵",
    "zh": "Chinese 🇨🇳",
    "ur": "Urdu 🇵🇰",
    "fa": "Persian 🇮🇷",
}


class Language:
    """
    Language class for managing multilingual support using JSON language files.
    """

    def __init__(self):
        """Initialize the language system and load all translation files."""
        self.lang_codes = lang_codes
        self.lang_dir = Path("Elevenyts/locales")
        self.languages = self.load_files()

    def load_files(self):
        """Load all language JSON files from the locales directory."""
        languages = {}
        for lang_code in self.lang_codes.keys():
            lang_file = self.lang_dir / f"{lang_code}.json"
            if lang_file.exists():
                with open(lang_file, "r", encoding="utf-8") as file:
                    languages[lang_code] = json.load(file)
        logger.info(f"🌐 Loaded languages: {', '.join(languages.keys())}")
        return languages

    def get_merged_lang(self, lang_code: str) -> dict:
        """Get language dict merged with English fallback for missing keys."""
        base = self.languages.get("en", {}).copy()
        if lang_code != "en" and lang_code in self.languages:
            base.update(self.languages[lang_code])
        return base

    async def get_lang(self, chat_id: int) -> dict:
        """Get the translation dictionary for a specific chat/user."""
        lang_code = await db.get_lang(chat_id)
        return self.get_merged_lang(lang_code)

    def language(self):
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                fallen = next(
                    (
                        arg
                        for arg in args
                        if hasattr(arg, "chat") or hasattr(arg, "message")
                    ),
                    None,
                )

                if hasattr(fallen, "chat"):
                    chat = fallen.chat
                elif hasattr(fallen, "message"):
                    chat = fallen.message.chat

                if chat.id in db.blacklisted:
                    try:
                        await chat.leave()
                    except Exception:
                        pass
                    return

                # Get user's preferred language (falls back to "en")
                lang_code = "en"
                user = getattr(fallen, "from_user", None)
                if user:
                    lang_code = await db.get_lang(user.id)

                lang_dict = self.get_merged_lang(lang_code)

                setattr(fallen, "lang", lang_dict)
                return await func(*args, **kwargs)

            return wrapper

        return decorator
