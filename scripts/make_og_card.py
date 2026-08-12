#!/usr/bin/env python3
"""Generate docs/og-card.png — the site's 1200x630 link-preview card.

Reads the mascot grid out of assets/mascot-mark.svg and draws the card as a
terminal window, mirroring assets/banner.svg. Standard library only (re, zlib,
struct): no image library, no SVG renderer, and — deliberately — no system
font. Every glyph comes from the 5x7 bitmap font embedded below, so the output
is byte-identical on any machine with python3.

Run from anywhere:  python3 scripts/make_og_card.py

docs/og-card.png is the single documented exception to the repo's .png ban;
see CLAUDE.md ("Never commit") and CONTRIBUTING.md ("Assets and the mascot").
"""
import re, struct, sys, zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets" / "mascot-mark.svg"
OUT = ROOT / "docs" / "og-card.png"

# The fixed palette (CONTRIBUTING.md, "Assets and the mascot") plus the three
# greys the site already uses. No other colour appears on the card.
SPORE = (0xC5, 0xF2, 0x4A)
LIVE = (0x35, 0xD9, 0x4F)
ROT = (0x1E, 0x9C, 0x39)
DEEP_ROT = (0x0D, 0x5A, 0x22)
VOID = (0x08, 0x0B, 0x09)
BAR = (0x10, 0x15, 0x12)  # terminal chrome
DOT = (0x33, 0x3B, 0x34)  # window dots
MUTED = (0x84, 0x95, 0x88)  # prompt + claim line
BODY = (0xC9, 0xD6, 0xCD)  # tagline

MASCOT_FILLS = {"#c5f24a": SPORE, "#35d94f": LIVE, "#1e9c39": ROT, "#080b09": VOID}

W, H = 1200, 630

# ── 5x7 bitmap font ─────────────────────────────────────────────────────────
# Seven rows per glyph, '#' = ink and '.' or ' ' = blank (normalised below, so
# the two read the same). Advance is 6*scale — 5 wide plus a 1-column gap.
FONT = {
    " ": ("     ", "     ", "     ", "     ", "     ", "     ", "     "),
    "a": ("     ", "     ", ".### ", "    #", ".####", "#   #", ".####"),
    "b": ("#    ", "#    ", "#### ", "#   #", "#   #", "#   #", "#### "),
    "c": ("     ", "     ", ".####", "#    ", "#    ", "#    ", ".####"),
    "d": ("    #", "    #", ".####", "#   #", "#   #", "#   #", ".####"),
    "e": ("     ", "     ", ".### ", "#   #", "#####", "#    ", ".### "),
    "f": ("  ## ", " #  #", " #   ", "#### ", " #   ", " #   ", " #   "),
    "g": ("     ", "     ", ".####", "#   #", ".####", "    #", ".### "),
    "h": ("#    ", "#    ", "#### ", "#   #", "#   #", "#   #", "#   #"),
    "i": ("  #  ", "     ", " ##  ", "  #  ", "  #  ", "  #  ", " ### "),
    "j": ("   # ", "     ", "  ## ", "   # ", "   # ", "#  # ", " ##  "),
    "k": ("#    ", "#    ", "#   #", "#  # ", "###  ", "#  # ", "#   #"),
    "l": (" ##  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "),
    "m": ("     ", "     ", "## ##", "# # #", "# # #", "# # #", "# # #"),
    "n": ("     ", "     ", "#### ", "#   #", "#   #", "#   #", "#   #"),
    "o": ("     ", "     ", ".### ", "#   #", "#   #", "#   #", ".### "),
    "p": ("     ", "     ", "#### ", "#   #", "#### ", "#    ", "#    "),
    "q": ("     ", "     ", ".####", "#   #", ".####", "    #", "    #"),
    "r": ("     ", "     ", "# ## ", "##   ", "#    ", "#    ", "#    "),
    "s": ("     ", "     ", ".####", "#    ", ".### ", "    #", "#### "),
    "t": (" #   ", " #   ", "#### ", " #   ", " #   ", " #  #", "  ## "),
    "u": ("     ", "     ", "#   #", "#   #", "#   #", "#  ##", " ## #"),
    "v": ("     ", "     ", "#   #", "#   #", "#   #", " # # ", "  #  "),
    "w": ("     ", "     ", "#   #", "#   #", "# # #", "# # #", " # # "),
    "x": ("     ", "     ", "#   #", " # # ", "  #  ", " # # ", "#   #"),
    "y": ("     ", "     ", "#   #", "#   #", ".####", "    #", ".### "),
    "z": ("     ", "     ", "#####", "   # ", "  #  ", " #   ", "#####"),
    "A": (".### ", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    "B": ("#### ", "#   #", "#   #", "#### ", "#   #", "#   #", "#### "),
    "C": (".### ", "#   #", "#    ", "#    ", "#    ", "#   #", ".### "),
    "D": ("#### ", "#   #", "#   #", "#   #", "#   #", "#   #", "#### "),
    "E": ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#####"),
    "F": ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#    "),
    "G": (".### ", "#   #", "#    ", "# ###", "#   #", "#   #", ".### "),
    "H": ("#   #", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    "I": (" ### ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "),
    "J": ("  ###", "   # ", "   # ", "   # ", "   # ", "#  # ", " ##  "),
    "K": ("#   #", "#  # ", "# #  ", "##   ", "# #  ", "#  # ", "#   #"),
    "L": ("#    ", "#    ", "#    ", "#    ", "#    ", "#    ", "#####"),
    "M": ("#   #", "## ##", "# # #", "# # #", "#   #", "#   #", "#   #"),
    "N": ("#   #", "##  #", "# # #", "# # #", "#  ##", "#   #", "#   #"),
    "O": (".### ", "#   #", "#   #", "#   #", "#   #", "#   #", ".### "),
    "P": ("#### ", "#   #", "#   #", "#### ", "#    ", "#    ", "#    "),
    "Q": (".### ", "#   #", "#   #", "#   #", "# # #", "#  # ", " ## #"),
    "R": ("#### ", "#   #", "#   #", "#### ", "# #  ", "#  # ", "#   #"),
    "S": (".####", "#    ", "#    ", ".### ", "    #", "    #", "#### "),
    "T": ("#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "),
    "U": ("#   #", "#   #", "#   #", "#   #", "#   #", "#   #", ".### "),
    "V": ("#   #", "#   #", "#   #", "#   #", "#   #", " # # ", "  #  "),
    "W": ("#   #", "#   #", "#   #", "# # #", "# # #", "## ##", "#   #"),
    "X": ("#   #", "#   #", " # # ", "  #  ", " # # ", "#   #", "#   #"),
    "Y": ("#   #", "#   #", " # # ", "  #  ", "  #  ", "  #  ", "  #  "),
    "Z": ("#####", "    #", "   # ", "  #  ", " #   ", "#    ", "#####"),
    "0": (".### ", "#   #", "#  ##", "# # #", "##  #", "#   #", ".### "),
    "1": ("  #  ", " ##  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "),
    "2": (".### ", "#   #", "    #", "   # ", "  #  ", " #   ", "#####"),
    "3": ("#####", "   # ", "  #  ", "   # ", "    #", "#   #", ".### "),
    "4": ("   # ", "  ## ", " # # ", "#  # ", "#####", "   # ", "   # "),
    "5": ("#####", "#    ", "#### ", "    #", "    #", "#   #", ".### "),
    "6": ("  ## ", " #   ", "#    ", "#### ", "#   #", "#   #", ".### "),
    "7": ("#####", "    #", "   # ", "  #  ", " #   ", " #   ", " #   "),
    "8": (".### ", "#   #", "#   #", ".### ", "#   #", "#   #", ".### "),
    "9": (".### ", "#   #", "#   #", ".####", "    #", "   # ", " ##  "),
    ".": ("     ", "     ", "     ", "     ", "     ", " ##  ", " ##  "),
    ":": ("     ", " ##  ", " ##  ", "     ", " ##  ", " ##  ", "     "),
    "-": ("     ", "     ", "     ", "#####", "     ", "     ", "     "),
    "/": ("    #", "    #", "   # ", "  #  ", " #   ", "#    ", "#    "),
    "$": ("  #  ", ".####", "# #  ", ".### ", "  # #", "#### ", "  #  "),
    "~": ("     ", "     ", " ## #", "#  # ", "     ", "     ", "     "),
}
FONT = {k: tuple(row.replace(".", " ") for row in rows) for k, rows in FONT.items()}
GLYPH_W, GLYPH_H, ADVANCE = 5, 7, 6


def text_width(s, scale):
    return (len(s) * ADVANCE - 1) * scale if s else 0


# ── canvas ──────────────────────────────────────────────────────────────────
canvas = bytearray(W * H * 3)


def fill(x, y, w, h, color):
    """Paint an axis-aligned rect, clipped to the canvas."""
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(color) * (x1 - x0)
    for yy in range(y0, y1):
        off = (yy * W + x0) * 3
        canvas[off : off + len(row)] = row


def border(x, y, w, h, t, color):
    fill(x, y, w, t, color)
    fill(x, y + h - t, w, t, color)
    fill(x, y, t, h, color)
    fill(x + w - t, y, t, h, color)


def text(s, x, y, scale, color):
    """Draw `s` with its top-left at (x, y). Unknown characters are fatal."""
    for i, ch in enumerate(s):
        glyph = FONT.get(ch)
        if glyph is None:
            sys.exit(f"make_og_card.py: unknown glyph {ch!r} — add it to FONT")
        gx = x + i * ADVANCE * scale
        for r in range(GLYPH_H):
            row = glyph[r]
            c = 0
            while c < GLYPH_W:
                if row[c] == "#":
                    run = 1
                    while c + run < GLYPH_W and row[c + run] == "#":
                        run += 1
                    fill(gx + c * scale, y + r * scale, run * scale, scale, color)
                    c += run
                else:
                    c += 1


# ── mascot ──────────────────────────────────────────────────────────────────
def load_mascot():
    """Parse the pixel grid out of mascot-mark.svg. Pure <rect>s, so this is
    an exact rasterisation — no renderer and no anti-aliasing involved."""
    svg = SRC.read_text()
    m = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg)
    if not m:
        sys.exit(f"make_og_card.py: no viewBox in {SRC}")
    vw, vh = int(m.group(1)), int(m.group(2))
    rects = re.findall(
        r'<rect x="(\d+)" y="(\d+)" width="(\d+)" height="(\d+)" fill="(#[0-9a-f]{6})"',
        svg,
    )
    if not rects:
        sys.exit(f"make_og_card.py: no <rect> elements in {SRC}")
    out = []
    for x, y, w, h, f in rects:
        if f not in MASCOT_FILLS:
            sys.exit(f"make_og_card.py: {SRC} uses off-palette fill {f}")
        out.append((int(x), int(y), int(w), int(h), MASCOT_FILLS[f]))
    return vw, vh, out


# ── PNG ─────────────────────────────────────────────────────────────────────
def chunk(tag, data):
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def write_png(path):
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter type 0 (None) on every scanline
        off = y * W * 3
        raw += canvas[off : off + W * 3]
    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )
    path.write_bytes(png)
    return len(png)


# ── the card ────────────────────────────────────────────────────────────────
def main():
    vw, vh, rects = load_mascot()

    PX, PY, PW, PH = 24, 24, 1152, 582  # panel
    BAR_H, RULE = 68, 2  # title bar
    SCALE = 3  # mascot: 136x128 -> 408x384
    MX, MY = 80, 158
    COL = 544  # right column
    PROMPT = "~/brainrot $ ./scripts/banner.sh"

    fill(0, 0, W, H, VOID)
    fill(PX + 10, PY + 10, PW, PH, DEEP_ROT)  # drop shadow
    fill(PX, PY, PW, PH, VOID)
    fill(PX, PY, PW, BAR_H, BAR)
    fill(PX, PY + BAR_H, PW, RULE, ROT)
    border(PX, PY, PW, PH, 3, ROT)

    for i in range(3):  # window dots, square to stay on-grid
        fill(PX + 28 + i * 26, PY + (BAR_H - 14) // 2, 14, 14, DOT)
    text(PROMPT, 138, PY + (BAR_H - GLYPH_H * 3) // 2, 3, MUTED)

    for x, y, w, h, color in rects:
        fill(MX + x * SCALE, MY + y * SCALE, w * SCALE, h * SCALE, color)

    y = 219
    text("brainrot", COL + 6, y + 6, 12, DEEP_ROT)  # matches the site h1 shadow
    text("brainrot", COL, y, 12, SPORE)
    y += GLYPH_H * 12 + 28
    fill(COL, y, text_width("brainrot", 12), 4, ROT)
    y += 4 + 30
    text("a self-audit toolkit", COL, y, 4, BODY)
    y += GLYPH_H * 4 + 12
    text("for Claude", COL, y, 4, BODY)
    y += GLYPH_H * 4 + 26
    text("10 skills . 2 commands", COL, y, 3, MUTED)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    size = write_png(OUT)
    print(f"OK {OUT.relative_to(ROOT)} {W}x{H} {size} bytes "
          f"({len(rects)} mascot rects from {SRC.name}, viewBox {vw}x{vh})")


if __name__ == "__main__":
    main()
