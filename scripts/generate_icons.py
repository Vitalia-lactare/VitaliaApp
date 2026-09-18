"""Gera os icones do PWA a partir da logo do projeto (app/static/img/logo.png)."""
from pathlib import Path

from PIL import Image

ICONS_DIR = Path(__file__).resolve().parent.parent / "app" / "static" / "icons"
LOGO = Path(__file__).resolve().parent.parent / "app" / "static" / "img" / "logo.png"


def make_icon(size: int) -> Image.Image:
    logo = Image.open(LOGO).convert("RGBA")
    scale = min(size / logo.width, size / logo.height)
    logo = logo.resize((max(1, round(logo.width * scale)), max(1, round(logo.height * scale))), Image.LANCZOS)

    img = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    px = round(size / 2 - logo.width / 2)
    py = round(size / 2 - logo.height / 2)
    img.alpha_composite(logo, (px, py))
    return img


def generate_all() -> None:
    ICONS_DIR.mkdir(parents=True, exist_ok=True)

    make_icon(192).save(ICONS_DIR / "icon-192.png")
    make_icon(512).save(ICONS_DIR / "icon-512.png")
    make_icon(512).save(ICONS_DIR / "icon-maskable-512.png")
    make_icon(180).save(ICONS_DIR / "apple-touch-icon-180.png")

    favicon_src = make_icon(256)
    favicon_src.save(
        ICONS_DIR / "favicon.ico",
        sizes=[(16, 16), (32, 32), (48, 48)],
    )

    print(f"[generate_icons] Icones gerados em {ICONS_DIR}")


if __name__ == "__main__":
    generate_all()
