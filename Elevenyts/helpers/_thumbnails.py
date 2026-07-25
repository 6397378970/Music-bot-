# ==========================================================
# Copyright (c) 2026 ArtistBots — All Rights Reserved.
# ==========================================================
import os
import re
import math
import asyncio
import aiohttp
import base64

from PIL import (
    Image,
    ImageDraw,
    ImageEnhance,
    ImageFilter,
    ImageFont,
)

from Elevenyts import config
from Elevenyts.helpers import Track


# ── Canvas ────────────────────────────────────────────────
W, H = 1280, 720

# ── Album art (left side) ─────────────────────────────────
ART_X, ART_Y     = 52, 52
ART_W, ART_H     = 546, 616
ART_RADIUS       = 36

# ── Info card (right side) ────────────────────────────────
CARD_X, CARD_Y   = 638, 52
CARD_W, CARD_H   = 590, 616
CARD_RADIUS      = 36

# ── Colors ────────────────────────────────────────────────
PURPLE  = (162,  89, 255)
PINK    = (255,  75, 155)
BLUE    = ( 75, 155, 255)
WHITE   = (255, 255, 255)
LIGHT   = (210, 190, 255)
DIM     = (140, 120, 180)
DARK    = ( 10,   8,  20)

# progress bar
BAR_FILL  = 0.33          # fraction already played
BAR_COLOR = (162,  89, 255)
BAR_BG    = ( 40,  35,  60)

# signature
_f = "QXJ0aXN0Ym90cw=="


def _sig():
    return f"✦ {base64.b64decode(_f).decode()} ✦"


# ── Font loader ──────────────────────────────────────────
def _fonts():
    try:
        bold   = "Elevenyts/helpers/Raleway-Bold.ttf"
        light  = "Elevenyts/helpers/Inter-Light.ttf"
        return {
            "title":  ImageFont.truetype(bold,  46),
            "title2": ImageFont.truetype(bold,  36),
            "badge":  ImageFont.truetype(bold,  18),
            "meta":   ImageFont.truetype(light, 22),
            "small":  ImageFont.truetype(light, 19),
            "sig":    ImageFont.truetype(bold,  20),
        }
    except OSError:
        d = ImageFont.load_default()
        return {k: d for k in ("title","title2","badge","meta","small","sig")}


# ── Helpers ───────────────────────────────────────────────
def _trim(text, font, max_w):
    if font.getlength(text) <= max_w:
        return text
    for i in range(len(text) - 1, 0, -1):
        if font.getlength(text[:i] + "…") <= max_w:
            return text[:i] + "…"
    return "…"


def _lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _gradient_rect(draw, x0, y0, x1, y1, c_left, c_right):
    """Horizontal gradient fill via scanline."""
    for x in range(x0, x1):
        t = (x - x0) / max(x1 - x0 - 1, 1)
        draw.line([(x, y0), (x, y1)], fill=(*_lerp_color(c_left, c_right, t), 255))


def _glow_ellipse(layer, cx, cy, rx, ry, color, steps=14, max_alpha=60):
    d = ImageDraw.Draw(layer)
    for i in range(steps, 0, -1):
        a = int(max_alpha * (i / steps) ** 2)
        sx = int(rx * i / steps * 2.2)
        sy = int(ry * i / steps * 2.2)
        d.ellipse((cx - sx, cy - sy, cx + sx, cy + sy),
                  fill=(*color[:3], a))


def _rounded_paste(base, img, xy, radius):
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, img.width, img.height), radius=radius, fill=255)
    base.paste(img, xy, mask)


def _draw_waveform(draw, x, y, w, h, color, bars=38, seed=7):
    """Decorative static waveform bars."""
    gap = 4
    bw  = (w - gap * (bars - 1)) // bars
    for i in range(bars):
        t  = i / (bars - 1)
        # smooth sine envelope
        env = 0.3 + 0.7 * abs(math.sin(math.pi * t * 2.5 + seed))
        bh  = int(h * env)
        bx  = x + i * (bw + gap)
        by  = y + (h - bh) // 2
        alpha = int(180 + 60 * env)
        c = (*_lerp_color(color, PINK, t), alpha)
        draw.rounded_rectangle(
            (bx, by, bx + bw, by + bh), radius=bw // 2, fill=c)


def _draw_progress(draw, x, y, length, height, fraction, color_l, color_r):
    """Gradient progress bar with glowing knob."""
    # Track background
    draw.rounded_rectangle(
        (x, y, x + length, y + height),
        radius=height // 2, fill=(*BAR_BG, 255))
    # Played gradient
    played = int(length * fraction)
    if played > height:
        tmp = Image.new("RGBA", (played, height), (0, 0, 0, 0))
        _gradient_rect(ImageDraw.Draw(tmp), 0, 0, played, height, color_l, color_r)
        rmask = Image.new("L", (played, height), 0)
        ImageDraw.Draw(rmask).rounded_rectangle(
            (0, 0, played, height), radius=height // 2, fill=255)
        base = Image.new("RGBA", (length, height), (0, 0, 0, 0))
        base.paste(tmp, (0, 0), rmask)
        draw._image.paste(base, (x, y), base)
    # Knob
    kx = x + played
    ky = y + height // 2
    kr = height
    for gi in range(10, 0, -1):
        ga = int(70 * (gi / 10) ** 2)
        draw.ellipse((kx - kr - gi, ky - kr - gi,
                      kx + kr + gi, ky + kr + gi),
                     fill=(*color_r, ga))
    draw.ellipse((kx - kr, ky - kr, kx + kr, ky + kr), fill=(*color_r, 255))
    draw.ellipse((kx - kr // 2, ky - kr // 2,
                  kx + kr // 2, ky + kr // 2), fill=WHITE)


# ── Main class ────────────────────────────────────────────
class Thumbnail:

    def __init__(self):
        self.fonts = _fonts()

    async def save_thumb(self, output_path, url):
        async with aiohttp.ClientSession() as s:
            async with s.get(url) as r:
                with open(output_path, "wb") as f:
                    f.write(await r.read())
        return output_path

    async def generate(self, song: Track, size=(W, H)) -> str:
        try:
            temp   = f"cache/temp_{song.id}.jpg"
            output = f"cache/{song.id}_ultra.png"
            if os.path.exists(output):
                return output
            await self.save_thumb(temp, song.thumbnail)
            return await asyncio.get_event_loop().run_in_executor(
                None, self._generate_sync, temp, output, song)
        except Exception:
            return config.DEFAULT_THUMB

    def _generate_sync(self, temp, output, song):
        try:
            fonts = self.fonts

            # ── 1. Background ──────────────────────────────────────────
            with Image.open(temp) as tmp:
                raw = tmp.resize((W, H)).convert("RGBA")

            bg = raw.filter(ImageFilter.GaussianBlur(40))
            bg = ImageEnhance.Brightness(bg).enhance(0.18)
            bg = ImageEnhance.Contrast(bg).enhance(1.6)
            bg = ImageEnhance.Color(bg).enhance(0.5)

            # Deep dark overlay
            bg = Image.alpha_composite(
                bg, Image.new("RGBA", (W, H), (*DARK, 130)))

            # ── 2. Ambient glow blobs ──────────────────────────────────
            glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            _glow_ellipse(glow, ART_X + ART_W // 2, ART_Y + ART_H // 2,
                          ART_W // 2, ART_H // 2, PURPLE, steps=18, max_alpha=55)
            _glow_ellipse(glow, CARD_X + CARD_W // 2, H // 2,
                          CARD_W // 2, CARD_H // 2, PINK, steps=14, max_alpha=35)
            bg = Image.alpha_composite(bg, glow)
            draw = ImageDraw.Draw(bg)

            # ── 3. Decorative corner dots (top-left) ──────────────────
            for di, (dx, dy) in enumerate([(20, 20), (36, 20), (20, 36)]):
                a = 200 - di * 50
                draw.ellipse((dx - 3, dy - 3, dx + 3, dy + 3),
                             fill=(*PURPLE, a))

            # ── 4. Album art ───────────────────────────────────────────
            with Image.open(temp) as tmp:
                art = tmp.resize((ART_W, ART_H)).convert("RGBA")

            # Glow behind art
            art_glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            _glow_ellipse(art_glow,
                          ART_X + ART_W // 2, ART_Y + ART_H // 2,
                          ART_W // 2 + 20, ART_H // 2 + 20,
                          PURPLE, steps=12, max_alpha=80)
            bg = Image.alpha_composite(bg, art_glow)
            draw = ImageDraw.Draw(bg)

            _rounded_paste(bg, art, (ART_X, ART_Y), ART_RADIUS)

            # Gradient border around art (purple → pink)
            border_size = 3
            art_border = Image.new("RGBA", (ART_W + border_size * 2,
                                            ART_H + border_size * 2), (0, 0, 0, 0))
            bd = ImageDraw.Draw(art_border)
            steps = ART_W + ART_H
            for si in range(steps):
                t   = si / steps
                col = _lerp_color(PURPLE, PINK, t)
                ang = 2 * math.pi * t
                bx  = int((ART_W // 2 + border_size) + (ART_W // 2 + border_size) * math.cos(ang))
                by  = int((ART_H // 2 + border_size) + (ART_H // 2 + border_size) * math.sin(ang))
                bx  = max(border_size, min(bx, ART_W + border_size - 1))
                by  = max(border_size, min(by, ART_H + border_size - 1))
            # Simpler: draw 4 gradient lines around the art rect
            for si in range(ART_W):
                t   = si / ART_W
                col = _lerp_color(PURPLE, PINK, t)
                # top edge
                draw.line([(ART_X + si, ART_Y - 2),
                           (ART_X + si, ART_Y - 1)], fill=(*col, 230))
                # bottom edge
                draw.line([(ART_X + si, ART_Y + ART_H + 1),
                           (ART_X + si, ART_Y + ART_H + 2)], fill=(*col, 230))
            for si in range(ART_H):
                t   = si / ART_H
                col = _lerp_color(PURPLE, PINK, t)
                draw.line([(ART_X - 2, ART_Y + si),
                           (ART_X - 1, ART_Y + si)], fill=(*col, 230))
                draw.line([(ART_X + ART_W + 1, ART_Y + si),
                           (ART_X + ART_W + 2, ART_Y + si)], fill=(*col, 230))

            # ── 5. Glass info card ─────────────────────────────────────
            card = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0))
            cd   = ImageDraw.Draw(card)

            # Glass fill
            cd.rounded_rectangle(
                (0, 0, CARD_W - 1, CARD_H - 1),
                radius=CARD_RADIUS,
                fill=(18, 12, 35, 185))

            # Gradient top highlight
            for yi in range(CARD_H // 4):
                a = int(28 * (1 - yi / (CARD_H // 4)))
                cd.rounded_rectangle(
                    (0, 0, CARD_W - 1, yi * 2),
                    radius=CARD_RADIUS,
                    outline=(255, 255, 255, a),
                    width=1)

            # Gradient border (purple top → pink bottom)
            for side_y in range(CARD_H):
                t   = side_y / CARD_H
                col = _lerp_color(PURPLE, PINK, t)
                card.putpixel((0, side_y),              (*col, 180))
                card.putpixel((CARD_W - 1, side_y),     (*col, 180))
            for side_x in range(CARD_W):
                t   = side_x / CARD_W
                col = _lerp_color(PURPLE, PINK, t)
                card.putpixel((side_x, 0),              (*col, 180))
                card.putpixel((side_x, CARD_H - 1),     (*col, 180))

            cmask = Image.new("L", (CARD_W, CARD_H), 0)
            ImageDraw.Draw(cmask).rounded_rectangle(
                (0, 0, CARD_W, CARD_H), radius=CARD_RADIUS, fill=255)
            bg.paste(card, (CARD_X, CARD_Y), cmask)
            draw = ImageDraw.Draw(bg)

            # ── 6. Inside card — content ───────────────────────────────
            CX = CARD_X + 38   # content left margin
            CY = CARD_Y + 38   # content top margin
            CW = CARD_W - 76   # content width

            # "NOW PLAYING" badge
            badge_txt = "  NOW PLAYING  "
            bw = int(fonts["badge"].getlength(badge_txt)) + 4
            bh = 30
            badge_bg = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
            _gradient_rect(ImageDraw.Draw(badge_bg),
                           0, 0, bw, bh, PURPLE, PINK)
            bmask = Image.new("L", (bw, bh), 0)
            ImageDraw.Draw(bmask).rounded_rectangle(
                (0, 0, bw, bh), radius=bh // 2, fill=255)
            bg.paste(badge_bg, (CX, CY), bmask)
            draw = ImageDraw.Draw(bg)
            draw.text((CX + 10, CY + 6), badge_txt.strip(),
                      fill=WHITE, font=fonts["badge"])

            # Title
            raw_title = re.sub(r"\W+", " ", song.title).strip().title()
            line1 = _trim(raw_title, fonts["title"], CW)
            TY = CY + bh + 22
            # Drop shadow
            draw.text((CX + 2, TY + 2), line1,
                      fill=(0, 0, 0, 120), font=fonts["title"])
            draw.text((CX, TY), line1, fill=WHITE, font=fonts["title"])

            # Gradient underline below title
            ul_y  = TY + 56
            ul_len = min(int(fonts["title"].getlength(line1)), CW)
            for xi in range(ul_len):
                t   = xi / ul_len
                col = _lerp_color(PURPLE, PINK, t)
                draw.line([(CX + xi, ul_y), (CX + xi, ul_y + 2)],
                          fill=(*col, 200))

            # Meta row
            MY = ul_y + 18
            is_live = getattr(song, "is_live", False)
            dur_txt = "🔴 LIVE" if is_live else (song.duration or "--:--")
            views   = song.view_count or ""
            meta    = f"▷  {dur_txt}    ·    {views}" if views else f"▷  {dur_txt}"
            draw.text((CX, MY), meta, fill=LIGHT, font=fonts["meta"])

            # ── 7. Waveform decoration ─────────────────────────────────
            WY = MY + 46
            _draw_waveform(draw, CX, WY, CW, 72, PURPLE, bars=40, seed=42)

            # ── 8. Progress bar ────────────────────────────────────────
            PY  = WY + 96
            PH  = 8
            PW  = CW
            _draw_progress(draw, CX, PY, PW, PH, BAR_FILL, PURPLE, PINK)

            # Time labels
            draw.text((CX, PY + PH + 10), "00:00",
                      fill=DIM, font=fonts["small"])
            end_txt = dur_txt
            ew = int(fonts["small"].getlength(end_txt))
            draw.text((CX + PW - ew, PY + PH + 10), end_txt,
                      fill=(0, 220, 255) if is_live else DIM,
                      font=fonts["small"])

            # ── 9. Control icons ───────────────────────────────────────
            icons_y  = PY + PH + 50
            controls = ["⏮", "⏪", "⏯", "⏩", "⏭"]
            icon_gap = CW // len(controls)
            for ci, ic in enumerate(controls):
                ix   = CX + ci * icon_gap + icon_gap // 2
                col  = (*_lerp_color(PURPLE, PINK, ci / (len(controls) - 1)), 220)
                size = 30 if ci == 2 else 22
                iw   = fonts["meta"].getlength(ic)
                draw.text((ix - iw // 2, icons_y), ic,
                          fill=col, font=fonts["meta"])

            # ── 10. Signature / branding ───────────────────────────────
            sig     = _sig()
            sig_y   = CARD_Y + CARD_H - 46
            sig_w   = fonts["sig"].getlength(sig)
            sig_x   = CARD_X + (CARD_W - sig_w) // 2
            draw.text((sig_x + 1, sig_y + 1), sig,
                      fill=(0, 0, 0, 100), font=fonts["sig"])
            draw.text((sig_x, sig_y), sig,
                      fill=(*_lerp_color(PURPLE, PINK, 0.5), 210),
                      font=fonts["sig"])

            # ── 11. Save ───────────────────────────────────────────────
            out = bg.convert("RGB")
            out.save(output, quality=96)
            try:
                os.remove(temp)
            except OSError:
                pass
            return output

        except Exception:
            return config.DEFAULT_THUMB
