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
import os
import re
import asyncio
import aiohttp
import base64

from PIL import (
    Image,
    ImageDraw,
    ImageEnhance,
    ImageFilter,
    ImageFont
)

from Elevenyts import config
from Elevenyts.helpers import Track


# ── Canvas dimensions ────────────────────────────────────────────────────────
W, H = 1280, 720

# Panel — centered, slight left-of-center for asymmetric layout
PANEL_W, PANEL_H = 1040, 622
PANEL_X = (W - PANEL_W) // 2
PANEL_Y = 49

# Thumbnail — inside panel, upper region
THUMB_W, THUMB_H = 940, 418
THUMB_X = PANEL_X + (PANEL_W - THUMB_W) // 2
THUMB_Y = PANEL_Y + 28

# Text rows
TITLE_X  = THUMB_X + 4
TITLE_Y  = THUMB_Y + THUMB_H + 22
META_Y   = TITLE_Y + 56

# Progress bar
BAR_X         = THUMB_X + 4
BAR_Y         = META_Y + 58
BAR_RED_LEN   = 340
BAR_TOTAL_LEN = 930
BAR_H         = 7   # half-height (bar drawn ±BAR_H from BAR_Y)

# Play icons strip
ICONS_W, ICONS_H = 420, 45
ICONS_X = PANEL_X + (PANEL_W - ICONS_W) // 2
ICONS_Y = BAR_Y + 68

MAX_TITLE_WIDTH = 830

# ── Palette ───────────────────────────────────────────────────────────────────
# Primary accent: electric violet-cyan
ACCENT_A   = (140,  80, 255)   # deep violet
ACCENT_B   = (  0, 220, 255)   # cyan
ACCENT_C   = (200, 100, 255)   # light violet
WHITE      = (255, 255, 255)
DIM_WHITE  = (210, 210, 230)
MID_GREY   = (160, 160, 185)
DARK_GREY  = ( 45,  45,  60)

_f = "QXJ0aXN0Ym90cw=="


def _decode_f() -> str:
    decoded = base64.b64decode(_f).decode("utf-8")
    return f"✦  {decoded.upper()}  ✦"


def trim_to_width(text: str, font, max_w: int) -> str:
    ellipsis = "…"
    if font.getlength(text) <= max_w:
        return text
    for i in range(len(text) - 1, 0, -1):
        if font.getlength(text[:i] + ellipsis) <= max_w:
            return text[:i] + ellipsis
    return ellipsis


def draw_glow_rect(draw, box, radius, color, spread=10, max_alpha=70):
    """Layered outer glow around a rounded rect."""
    x0, y0, x1, y1 = box
    for i in range(spread, 0, -1):
        alpha = int(max_alpha * (i / spread) ** 1.4)
        draw.rounded_rectangle(
            (x0 - i, y0 - i, x1 + i, y1 + i),
            radius=radius + i,
            outline=(*color[:3], alpha),
            width=1
        )


def gradient_line(draw, x0, y0, x1, y1, thickness,
                  color_a, color_b, steps=80):
    """Horizontal gradient bar drawn as thin vertical slices."""
    length = x1 - x0
    for i in range(steps):
        t  = i / (steps - 1)
        x  = int(x0 + length * i / steps)
        xn = int(x0 + length * (i + 1) / steps)
        r  = int(color_a[0] + (color_b[0] - color_a[0]) * t)
        g  = int(color_a[1] + (color_b[1] - color_a[1]) * t)
        b  = int(color_a[2] + (color_b[2] - color_a[2]) * t)
        draw.rectangle((x, y0, xn, y0 + thickness), fill=(r, g, b, 255))


def draw_watermark_badge(img: Image.Image, text: str, font,
                         top: int = 22, right: int = 28):
    """
    Draws a glowing pill badge in the top-right corner of `img`.
    Returns the modified image.
    """
    draw = ImageDraw.Draw(img, "RGBA")

    # Measure text
    bbox   = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 22, 10

    bw = tw + pad_x * 2
    bh = th + pad_y * 2

    x1 = img.width - right
    x0 = x1 - bw
    y0 = top
    y1 = y0 + bh
    r  = bh // 2   # full pill

    # Outer glow (violet)
    draw_glow_rect(draw, (x0, y0, x1, y1),
                   radius=r, color=ACCENT_A, spread=14, max_alpha=90)

    # Pill background — semi-transparent dark violet
    draw.rounded_rectangle(
        (x0, y0, x1, y1),
        radius=r,
        fill=(30, 10, 60, 200)
    )

    # Gradient-ish top highlight inside pill
    draw.rounded_rectangle(
        (x0 + 2, y0 + 2, x1 - 2, y0 + bh // 2),
        radius=r - 2,
        fill=(255, 255, 255, 20)
    )

    # Pill border — thin violet-cyan
    draw.rounded_rectangle(
        (x0, y0, x1, y1),
        radius=r,
        outline=(*ACCENT_C, 220),
        width=2
    )

    # Text shadow
    tx = x0 + pad_x
    ty = y0 + pad_y
    draw.text((tx + 1, ty + 1), text, fill=(0, 0, 0, 140), font=font)
    # Text — gradient-feel via layered semi-transparent draws
    draw.text((tx, ty), text, fill=(*ACCENT_B, 230), font=font)
    # Brighten center chars slightly
    draw.text((tx, ty), text, fill=(255, 255, 255, 60), font=font)

    return img


class Thumbnail:

    def __init__(self):
        try:
            self.title_font     = ImageFont.truetype(
                "Elevenyts/helpers/Raleway-Bold.ttf", 42)
            self.regular_font   = ImageFont.truetype(
                "Elevenyts/helpers/Inter-Light.ttf", 24)
            self.signature_font = ImageFont.truetype(
                "Elevenyts/helpers/Raleway-Bold.ttf", 22)
            self.small_font     = ImageFont.truetype(
                "Elevenyts/helpers/Inter-Light.ttf", 20)
            self.badge_font     = ImageFont.truetype(
                "Elevenyts/helpers/Raleway-Bold.ttf", 19)
        except OSError:
            fb = ImageFont.load_default()
            self.title_font = self.regular_font = self.signature_font = \
                self.small_font = self.badge_font = fb

    async def save_thumb(self, output_path: str, url: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                with open(output_path, "wb") as f:
                    f.write(await resp.read())
        return output_path

    async def generate(self, song: Track, size=(1280, 720)) -> str:
        try:
            temp   = f"cache/temp_{song.id}.jpg"
            output = f"cache/{song.id}_ultra.png"
            if os.path.exists(output):
                return output
            await self.save_thumb(temp, song.thumbnail)
            return await asyncio.get_event_loop().run_in_executor(
                None, self._generate_sync, temp, output, song, size)
        except Exception:
            return config.DEFAULT_THUMB

    def _generate_sync(self, temp, output, song, size=(1280, 720)):
        try:
            cW, cH = size  # 1280 × 720

            # ── 1. Background ─────────────────────────────────────────────────
            with Image.open(temp) as tmp:
                base = tmp.resize(size).convert("RGBA")

            bg = base.filter(ImageFilter.GaussianBlur(38))
            bg = ImageEnhance.Brightness(bg).enhance(0.18)
            bg = ImageEnhance.Contrast(bg).enhance(1.6)

            # Purple-blue color tint (premium feel)
            tint = Image.new("RGBA", size, (20, 5, 50, 120))
            bg   = Image.alpha_composite(bg, tint)

            # Radial vignette — stronger corners
            vignette = Image.new("RGBA", size, (0, 0, 0, 0))
            vd = ImageDraw.Draw(vignette)
            for i in range(70, 0, -1):
                alpha  = int(180 * (1 - i / 70) ** 1.3)
                spread = i * 7
                vd.ellipse(
                    (cW // 2 - spread, cH // 2 - spread * 9 // 16,
                     cW // 2 + spread, cH // 2 + spread * 9 // 16),
                    fill=(0, 0, 0, alpha)
                )
            bg = Image.alpha_composite(bg, vignette)

            # Subtle dark overlay
            dark = Image.new("RGBA", size, (0, 0, 0, 80))
            bg   = Image.alpha_composite(bg, dark)

            draw = ImageDraw.Draw(bg, "RGBA")

            # ── 2. Glass panel ────────────────────────────────────────────────
            panel = Image.new("RGBA", (PANEL_W, PANEL_H), (0, 0, 0, 0))
            pd    = ImageDraw.Draw(panel, "RGBA")

            # Multi-layer outer glow (violet → cyan)
            for gi in range(12, 0, -1):
                t   = gi / 12
                gr  = int(ACCENT_A[0] + (ACCENT_B[0] - ACCENT_A[0]) * (1 - t))
                gg  = int(ACCENT_A[1] + (ACCENT_B[1] - ACCENT_A[1]) * (1 - t))
                gb_ = int(ACCENT_A[2] + (ACCENT_B[2] - ACCENT_A[2]) * (1 - t))
                ga  = int(45 * (gi / 12) ** 1.2)
                pd.rounded_rectangle(
                    (-gi, -gi, PANEL_W - 1 + gi, PANEL_H - 1 + gi),
                    radius=44 + gi,
                    outline=(gr, gg, gb_, ga),
                    width=1
                )

            # Glass fill — very dark, slightly blue-tinted
            pd.rounded_rectangle(
                (0, 0, PANEL_W - 1, PANEL_H - 1),
                radius=44,
                fill=(6, 4, 20, 175)
            )

            # Thin top gradient strip — decorative accent line
            for xi in range(60, PANEL_W - 60):
                t   = (xi - 60) / (PANEL_W - 120)
                cr  = int(ACCENT_A[0] + (ACCENT_B[0] - ACCENT_A[0]) * t)
                cg  = int(ACCENT_A[1] + (ACCENT_B[1] - ACCENT_A[1]) * t)
                cb  = int(ACCENT_A[2] + (ACCENT_B[2] - ACCENT_A[2]) * t)
                ca  = 200
                pd.line([(xi, 0), (xi, 3)], fill=(cr, cg, cb, ca))

            # Inner highlight — frosted top third
            pd.rounded_rectangle(
                (3, 3, PANEL_W - 4, PANEL_H // 3),
                radius=42,
                fill=(255, 255, 255, 10)
            )
            # Outer border — violet-to-cyan
            pd.rounded_rectangle(
                (0, 0, PANEL_W - 1, PANEL_H - 1),
                radius=44,
                outline=(*ACCENT_B, 200),
                width=2
            )

            pmask = Image.new("L", (PANEL_W, PANEL_H), 0)
            ImageDraw.Draw(pmask).rounded_rectangle(
                (0, 0, PANEL_W, PANEL_H), radius=44, fill=255)
            bg.paste(panel, (PANEL_X, PANEL_Y), pmask)

            # ── 3. Thumbnail with glow frame ──────────────────────────────────
            thumb = base.resize((THUMB_W, THUMB_H))

            # Glow behind thumbnail — violet-ish
            glow_layer = Image.new("RGBA", size, (0, 0, 0, 0))
            gd = ImageDraw.Draw(glow_layer, "RGBA")
            for gi in range(14, 0, -1):
                t   = gi / 14
                gr  = int(ACCENT_A[0] * t + ACCENT_B[0] * (1 - t))
                gg  = int(ACCENT_A[1] * t + ACCENT_B[1] * (1 - t))
                gb_ = int(ACCENT_A[2] * t + ACCENT_B[2] * (1 - t))
                ga  = int(55 * (gi / 14) ** 1.3)
                gd.rounded_rectangle(
                    (THUMB_X - gi, THUMB_Y - gi,
                     THUMB_X + THUMB_W + gi, THUMB_Y + THUMB_H + gi),
                    radius=30 + gi,
                    fill=(gr, gg, gb_, ga)
                )
            bg = Image.alpha_composite(bg, glow_layer)
            draw = ImageDraw.Draw(bg, "RGBA")

            tmask = Image.new("L", thumb.size, 0)
            ImageDraw.Draw(tmask).rounded_rectangle(
                (0, 0, THUMB_W, THUMB_H), radius=26, fill=255)
            bg.paste(thumb, (THUMB_X, THUMB_Y), tmask)

            # Cyan border around thumbnail
            draw.rounded_rectangle(
                (THUMB_X, THUMB_Y, THUMB_X + THUMB_W, THUMB_Y + THUMB_H),
                radius=26, outline=(*ACCENT_B, 150), width=2
            )

            # ── 4. Vertical accent bar + Title ────────────────────────────────
            # Gradient vertical bar (violet → cyan, top → bottom)
            bar_top    = TITLE_Y + 2
            bar_bottom = TITLE_Y + 46
            for yi in range(bar_top, bar_bottom):
                t   = (yi - bar_top) / max(bar_bottom - bar_top, 1)
                br  = int(ACCENT_A[0] + (ACCENT_B[0] - ACCENT_A[0]) * t)
                bg_ = int(ACCENT_A[1] + (ACCENT_B[1] - ACCENT_A[1]) * t)
                bb  = int(ACCENT_A[2] + (ACCENT_B[2] - ACCENT_A[2]) * t)
                draw.rectangle(
                    (TITLE_X, yi, TITLE_X + 5, yi + 1),
                    fill=(br, bg_, bb, 255)
                )

            clean_title = re.sub(r"\W+", " ", song.title).title() + "  ·  Artistbots"
            final_title = trim_to_width(clean_title, self.title_font, MAX_TITLE_WIDTH)

            # Title glow (very subtle violet)
            for gi in range(4, 0, -1):
                draw.text(
                    (TITLE_X + 12 + gi, TITLE_Y + 1),
                    final_title,
                    fill=(*ACCENT_A, 30),
                    font=self.title_font
                )
            # Drop shadow
            draw.text((TITLE_X + 13, TITLE_Y + 3), final_title,
                      fill=(0, 0, 0, 150), font=self.title_font)
            # Main title — white
            draw.text((TITLE_X + 12, TITLE_Y + 1), final_title,
                      fill=(*WHITE, 255), font=self.title_font)

            # ── 5. Meta info ──────────────────────────────────────────────────
            dot   = "  ·  "
            meta  = f"▷  Now Playing{dot}YouTube{dot}{song.view_count or 'Unknown Views'}"
            draw.text((TITLE_X + 12, META_Y), meta,
                      fill=(*MID_GREY, 230), font=self.regular_font)

            # ── 6. Progress bar (gradient fill) ──────────────────────────────
            # Track background
            draw.rounded_rectangle(
                (BAR_X, BAR_Y - BAR_H, BAR_X + BAR_TOTAL_LEN, BAR_Y + BAR_H),
                radius=BAR_H + 4, fill=(*DARK_GREY, 220)
            )

            # Gradient fill — violet → cyan
            bar_layer = Image.new("RGBA", size, (0, 0, 0, 0))
            bl        = ImageDraw.Draw(bar_layer, "RGBA")
            gradient_line(
                bl,
                BAR_X, BAR_Y - BAR_H,
                BAR_X + BAR_RED_LEN, BAR_Y + BAR_H,
                BAR_H * 2,
                ACCENT_A, ACCENT_B
            )
            # Soft sheen on bar
            bl.rounded_rectangle(
                (BAR_X, BAR_Y - BAR_H,
                 BAR_X + BAR_RED_LEN, BAR_Y),
                radius=BAR_H,
                fill=(255, 255, 255, 30)
            )
            bg = Image.alpha_composite(bg, bar_layer)
            draw = ImageDraw.Draw(bg, "RGBA")

            # Knob
            kx = BAR_X + BAR_RED_LEN
            for gi in range(12, 0, -1):
                ga = int(65 * (gi / 12) ** 1.5)
                draw.ellipse(
                    (kx - 10 - gi, BAR_Y - 10 - gi,
                     kx + 10 + gi, BAR_Y + 10 + gi),
                    fill=(*ACCENT_B, ga)
                )
            draw.ellipse(
                (kx - 10, BAR_Y - 10, kx + 10, BAR_Y + 10),
                fill=(*ACCENT_B, 255)
            )
            draw.ellipse(
                (kx - 5, BAR_Y - 5, kx + 5, BAR_Y + 5),
                fill=(*WHITE, 255)
            )

            # Time stamps
            draw.text((BAR_X, BAR_Y + 14), "00:00",
                      fill=(*MID_GREY, 200), font=self.small_font)
            is_live  = getattr(song, "is_live", False)
            end_text = "🔴  LIVE" if is_live else song.duration
            tw       = self.small_font.getlength(end_text)
            draw.text(
                (BAR_X + BAR_TOTAL_LEN - tw, BAR_Y + 14),
                end_text,
                fill=(*ACCENT_B, 230) if is_live else (*MID_GREY, 200),
                font=self.small_font
            )

            # ── 7. Play icons ─────────────────────────────────────────────────
            icons_path = "Elevenyts/helpers/play_icons.png"
            if os.path.isfile(icons_path):
                with Image.open(icons_path) as icons_img:
                    ic = icons_img.resize((ICONS_W, ICONS_H)).convert("RGBA")
                    r_, g_, b_, a_ = ic.split()
                    # Tint icons with accent cyan
                    tinted_ic = Image.merge("RGBA", (
                        r_.point(lambda _: ACCENT_B[0]),
                        g_.point(lambda _: ACCENT_B[1]),
                        b_.point(lambda _: ACCENT_B[2]),
                        a_
                    ))
                    bg.paste(tinted_ic, (ICONS_X, ICONS_Y), tinted_ic)

            # ── 8. Watermark badge — top-right corner ─────────────────────────
            bg = draw_watermark_badge(
                bg,
                text=_decode_f(),
                font=self.badge_font,
                top=24,
                right=30
            )

            bg.save(output)
            try:
                os.remove(temp)
            except OSError:
                pass
            return output

        except Exception:
            return config.DEFAULT_THUMB
