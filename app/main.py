import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import APP_DIR, APP_NAME
from .routers import admin, api, pages, portal
from scripts.init_db import init_db

app = FastAPI(title=APP_NAME)

app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")

app.include_router(portal.router)
app.include_router(pages.router)
app.include_router(api.router)
app.include_router(admin.router)

SERVICE_WORKER_PATH = APP_ROOT / "service-worker.js"


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/service-worker.js")
def service_worker():
    return FileResponse(SERVICE_WORKER_PATH, media_type="application/javascript")
