from fastapi.templating import Jinja2Templates

from .config import APP_DIR, APP_NAME, APP_TAGLINE, THEME_COLOR

templates = Jinja2Templates(directory=str(APP_DIR / "templates"))
templates.env.globals.update(
    APP_NAME=APP_NAME,
    APP_TAGLINE=APP_TAGLINE,
    THEME_COLOR=THEME_COLOR,
)
