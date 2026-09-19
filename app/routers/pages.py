import sqlite3

from fastapi import APIRouter, Depends, Request

from .. import repo
from ..db import get_db
from ..templating import templates

router = APIRouter()


@router.get("/")
def home(request: Request, db: sqlite3.Connection = Depends(get_db)):
    ctx = {
        "request": request,
        "total_bancos": repo.count_bancos(db),
        "total_estados": repo.count_estados(db),
    }
    return templates.TemplateResponse(request, "home.html", ctx)


@router.get("/campanhas")
def campanhas(request: Request, db: sqlite3.Connection = Depends(get_db)):
    ctx = {"request": request, "campanhas": repo.list_campanhas_ativas(db)}
    return templates.TemplateResponse(request, "campanhas.html", ctx)


@router.get("/cada-gota-conta")
def cada_gota_conta(request: Request):
    return templates.TemplateResponse(request, "cada_gota_conta.html", {})


@router.get("/localizador")
def localizador(request: Request, db: sqlite3.Connection = Depends(get_db)):
    ctx = {"request": request, "estados": repo.distinct_estados(db)}
    return templates.TemplateResponse(request, "localizador.html", ctx)
