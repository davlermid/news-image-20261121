#!/usr/bin/env python3
"""Draw the 21 November 2026 world-news poster as a 1024x1024 PNG.

Layout: navy masthead with the date, one full-width lead story with fact
chips, two half-width cards, three compact cards, and a sources footer.
Each card carries a coloured accent bar on its left edge.

Deterministic by construction: fixed strings, fixed fonts, fixed geometry,
no clock, no randomness, no network. Running it twice writes identical bytes.
"""
import hashlib
import os
import sys

from PIL import Image, ImageDraw, ImageFont

CANVAS = 1024
EDGE = 36                      # left/right margin
INNER_W = CANVAS - 2 * EDGE    # usable width inside the margins

NAVY = (15, 42, 74)
GOLD = (232, 180, 74)
RED = (192, 57, 43)
PAPER = (253, 251, 247)
INK = (34, 34, 34)
BODY = (68, 68, 68)
FAINT = (102, 102, 102)
RULE = (216, 210, 200)
CARD_BG = (255, 255, 255)
CARD_LINE = (220, 214, 204)
CHIP_BG = (238, 234, 228)
WHITE = (255, 255, 255)

FONT_HOME = "/usr/share/fonts/truetype/dejavu"
SERIF_BOLD = os.path.join(FONT_HOME, "DejaVuSerif-Bold.ttf")
SANS_BOLD = os.path.join(FONT_HOME, "DejaVuSans-Bold.ttf")
SANS = os.path.join(FONT_HOME, "DejaVuSans.ttf")

# One accent colour per beat; the card tag and its left bar share it.
BEAT_COLOURS = {
    "DIPLOMACY": (108, 52, 131),
    "CONFLICT": (192, 57, 43),
    "TECHNOLOGY": (31, 78, 121),
    "CLIMATE": (17, 122, 101),
    "ENERGY": (185, 119, 14),
    "DEFENSE": (30, 122, 52),
}


def load_font(path, size):
    return ImageFont.truetype(path, int(size))


def wrap_lines(draw, text, fnt, max_width):
    """Greedy word wrap: pack words until the next would overflow."""
    lines = []
    current = ""
    for word in text.split():
        candidate = word if not current else current + " " + word
        if draw.textlength(candidate, font=fnt) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def fit(draw, text, path, start_size, max_width, max_lines, floor=12):
    """Step the font size down until the text fits the line budget."""
    size = int(start_size)
    while size > floor:
        fnt = load_font(path, size)
        lines = wrap_lines(draw, text, fnt, max_width)
        if len(lines) <= max_lines:
            return fnt, lines
        size -= 1
    fnt = load_font(path, floor)
    return fnt, wrap_lines(draw, text, fnt, max_width)


def centre_text(draw, y, text, fnt, fill):
    w = draw.textlength(text, font=fnt)
    draw.text(((CANVAS - w) / 2, y), text, font=fnt, fill=fill)


def draw_pill(draw, x, y, text, fnt, bg, fg, pad_x=14, height=32):
    """Rounded label; returns the x just past its right edge."""
    w = draw.textlength(text, font=fnt) + 2 * pad_x
    draw.rounded_rectangle([x, y, x + w, y + height], radius=height // 2, fill=bg)
    draw.text((x + pad_x, y + (height - fnt.size) / 2 - 2), text, font=fnt, fill=fg)
    return x + w


def draw_card(draw, box, tag, headline, summary, head_size, sum_size,
              head_budget, sum_budget, pad=18):
    """One story card: white panel, accent bar, tag, headline, summary."""
    x0, y0, x1, y1 = box
    draw.rectangle([x0, y0, x1, y1], fill=CARD_BG, outline=CARD_LINE, width=1)
    accent = BEAT_COLOURS[tag.split(" ")[0]]
    draw.rectangle([x0, y0, x0 + 6, y1], fill=accent)
    text_w = (x1 - x0) - 2 * pad - 6
    tx = x0 + 6 + pad
    ty = y0 + pad
    tag_font = load_font(SANS_BOLD, 17 if (x1 - x0) > 400 else 15)
    draw.text((tx, ty), tag, font=tag_font, fill=accent)
    ty += tag_font.size + 10
    hfnt, hlines = fit(draw, headline, SANS_BOLD, head_size, text_w, head_budget)
    for ln in hlines:
        draw.text((tx, ty), ln, font=hfnt, fill=INK)
        ty += int(hfnt.size * 1.22)
    ty += 6
    sfnt, slines = fit(draw, summary, SANS, sum_size, text_w, sum_budget)
    for ln in slines:
        draw.text((tx, ty), ln, font=sfnt, fill=BODY)
        ty += int(sfnt.size * 1.28)


def draw_lead(draw):
    """Full-width lead story under the masthead, with two fact chips."""
    tag = "DIPLOMACY \u2022 SHENZHEN SUMMIT"
    headline = "Trump calls Europe after Shenzhen summit"
    summary = ("Fresh from his first-ever summit with Xi Jinping and Vladimir "
               "Putin in Shenzhen, President Trump phoned European allies "
               "about Ukraine, sounding \u201cfairly optimistic\u201d about a "
               "deal. The three leaders\u2019 peace declaration promised "
               "nuclear-risk talks but set no arms limits.")
    draw_pill(draw, EDGE, 152, tag, load_font(SANS_BOLD, 19),
              BEAT_COLOURS["DIPLOMACY"], WHITE)
    hfnt, hlines = fit(draw, headline, SANS_BOLD, 42, INNER_W, 2)
    y = 196
    for ln in hlines:
        draw.text((EDGE, y), ln, font=hfnt, fill=INK)
        y += int(hfnt.size * 1.2)
    y += 8
    sfnt, slines = fit(draw, summary, SANS, 23, INNER_W, 3)
    for ln in slines:
        draw.text((EDGE, y), ln, font=sfnt, fill=BODY)
        y += int(sfnt.size * 1.3)
    y += 12
    chip_font = load_font(SANS, 17)
    cx = EDGE
    for chip in ("First US\u2013China\u2013Russia summit", "No arms deal agreed"):
        cx = draw_pill(draw, cx, y, chip, chip_font, CHIP_BG, INK, pad_x=12, height=28)
        cx += 12


def main():
    img = Image.new("RGB", (CANVAS, CANVAS), PAPER)
    d = ImageDraw.Draw(img)

    # Masthead: title, date, red rule.
    d.rectangle([0, 0, CANVAS, 132], fill=NAVY)
    centre_text(d, 20, "WORLD NEWS", load_font(SERIF_BOLD, 60), WHITE)
    centre_text(d, 90, "SATURDAY, 21 NOVEMBER 2026", load_font(SANS_BOLD, 27), GOLD)
    d.rectangle([0, 132, CANVAS, 136], fill=RED)

    draw_lead(d)

    d.line([(EDGE, 420), (CANVAS - EDGE, 420)], fill=RULE, width=2)

    # Tier 2: two half-width cards.
    gap = 20
    half_w = (INNER_W - gap) // 2
    draw_card(d, (EDGE, 436, EDGE + half_w, 648),
              "CONFLICT \u2022 NATO",
              "Russian missiles land on Polish soil",
              "Three Russian weapons, including a Kh-101 missile, came "
              "down in south-east Poland during a huge strike on "
              "Ukraine. Warsaw called it an \u201cintentional "
              "provocation\u201d; NATO scrambled jets. Nobody was hurt.",
              28, 19, 2, 4)
    draw_card(d, (EDGE + half_w + gap, 436, CANVAS - EDGE, 648),
              "TECHNOLOGY \u2022 AI CHIPS",
              "US approved 900,000 AI chips for China",
              "Washington signed off nearly 900,000 Nvidia and AMD "
              "AI-chip shipments to Chinese firms in six months, a "
              "House committee disclosed \u2014 some to Pentagon-listed "
              "military firms.",
              28, 19, 2, 4)

    d.line([(EDGE, 664), (CANVAS - EDGE, 664)], fill=RULE, width=2)

    # Tier 3: three compact cards.
    t3_gap = 16
    t3_w = (INNER_W - 2 * t3_gap) // 3
    x = EDGE
    for tag, head, summ in [
        ("CLIMATE \u2022 COP31",
         "Climate talks run into overtime",
         "COP31 in Antalya missed its Friday deadline with no deal. A "
         "new draft dropped every mention of fossil fuels; a third "
         "text is due Saturday morning."),
        ("ENERGY \u2022 IRAN WAR",
         "IEA: no going back on energy",
         "The International Energy Agency says the Iran war\u2019s "
         "energy shock is permanently reshaping global energy "
         "strategy: \u201cThere is no going back to the way it was "
         "before.\u201d"),
        ("DEFENSE \u2022 ASIA",
         "Japan, India deepen defence ties",
         "Japan and India agreed closer military and arms-industry "
         "cooperation, including Japanese live-fire missile training "
         "at Indian ranges in future joint drills."),
    ]:
        draw_card(d, (x, 680, x + t3_w, 952), tag, head, summ,
                  24, 18, 3, 7, pad=14)
        x += t3_w + t3_gap

    # Footer: where the facts came from.
    centre_text(d, 968, "Sources: Reuters \u2022 AP \u2022 WSJ \u2022 CNN \u2022 AFP",
                load_font(SANS, 18), FAINT)

    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "entry.png")
    img.save(out, "PNG")
    data = open(out, "rb").read()
    print(f"wrote {out}: {img.size[0]}x{img.size[1]}, {len(data)} bytes, "
          f"sha256 {hashlib.sha256(data).hexdigest()}")
    assert img.size == (1024, 1024), "poster must be 1024x1024"
    assert len(data) <= 1048576, "poster must be at most 1 MiB"


if __name__ == "__main__":
    main()
