"""Gera os icones do PWA (motivo original de gota/asas, sem arte copiada)."""
from pathlib import Path

from PIL import Image, ImageDraw

ICONS_DIR = Path(__file__).resolve().parent.parent / "app" / "static" / "icons"
BG_COLOR = (21, 101, 192, 255)  # #1565C0
FG_COLOR = (255, 255, 255, 255)


def _draw_teardrop(draw: ImageDraw.ImageDraw, cx: float, cy: float, r: float, fill) -> None:
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill)
    apex = (cx, cy - r * 2.1)
    left = (cx - r * 0.95, cy - r * 0.15)
    right = (cx + r * 0.95, cy - r * 0.15)
    draw.polygon([apex, left, right], fill=fill)


def _draw_wing_accent(draw: ImageDraw.ImageDraw, cx: float, cy: float, r: float, color, width: int) -> None:
    bbox = [cx - r * 0.55, cy - r * 0.05, cx + r * 0.55, cy + r * 0.95]
    draw.arc(bbox, start=200, end=340, fill=color, width=width)


def make_icon(size: int, maskable: bool = False) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if maskable:
        draw.rectangle([0, 0, size, size], fill=BG_COLOR)
        content_r = size * 0.26
        cx, cy = size / 2, size / 2 + size * 0.06
    else:
        radius = int(size * 0.22)
        draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=BG_COLOR)
        content_r = size * 0.20
        cx, cy = size / 2, size / 2 + size * 0.08

    _draw_teardrop(draw, cx, cy, content_r, FG_COLOR)
    _draw_wing_accent(draw, cx, cy, content_r, BG_COLOR, max(2, int(size * 0.02)))
    return img


def generate_all() -> None:
    ICONS_DIR.mkdir(parents=True, exist_ok=True)

    make_icon(192).save(ICONS_DIR / "icon-192.png")
    make_icon(512).save(ICONS_DIR / "icon-512.png")
    make_icon(512, maskable=True).save(ICONS_DIR / "icon-maskable-512.png")
    make_icon(180).save(ICONS_DIR / "apple-touch-icon-180.png")

    favicon_src = make_icon(256)
    favicon_src.save(
        ICONS_DIR / "favicon.ico",
        sizes=[(16, 16), (32, 32), (48, 48)],
    )

    print(f"[generate_icons] Icones gerados em {ICONS_DIR}")


if __name__ == "__main__":
    generate_all()
