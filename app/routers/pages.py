import sqlite3
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from .. import repo
from ..db import get_db
from ..templating import templates

router = APIRouter()


@router.get("/campanhas")
def campanhas(request: Request, db: sqlite3.Connection = Depends(get_db)):
    ctx = {"request": request, "campanhas": repo.list_campanhas_ativas(db)}
    return templates.TemplateResponse(request, "campanhas.html", ctx)


@router.get("/quem-somos")
def quem_somos(request: Request):
    return templates.TemplateResponse(request, "quem_somos.html", {})


@router.get("/cada-gota-conta")
def cada_gota_conta(request: Request):
    return templates.TemplateResponse(request, "cada_gota_conta.html", {})


@router.get("/seja-doadora")
def seja_doadora_form(
    request: Request, enviado: Optional[int] = None, db: sqlite3.Connection = Depends(get_db)
):
    ctx = {
        "request": request,
        "estados": repo.distinct_estados(db),
        "enviado": bool(enviado),
    }
    return templates.TemplateResponse(request, "seja_doadora.html", ctx)


@router.post("/seja-doadora")
def seja_doadora_submit(
    nome: str = Form(...),
    email: str = Form(...),
    telefone: str = Form(...),
    cidade: str = Form(...),
    uf: str = Form(...),
    bebe_nascimento: Optional[str] = Form(None),
    ja_doou_antes: Optional[str] = Form(None),
    mensagem: Optional[str] = Form(None),
    db: sqlite3.Connection = Depends(get_db),
):
    data = {
        "nome": nome,
        "email": email,
        "telefone": telefone,
        "cidade": cidade,
        "uf": uf.upper(),
        "bebe_nascimento": bebe_nascimento or None,
        "ja_doou_antes": 1 if ja_doou_antes else 0,
        "mensagem": mensagem or None,
        "banco_leite_id": None,
    }
    repo.insert_doadora(db, data)
    return RedirectResponse(url="/seja-doadora?enviado=1", status_code=303)


@router.get("/localizador")
def localizador(request: Request, db: sqlite3.Connection = Depends(get_db)):
    ctx = {"request": request, "estados": repo.distinct_estados(db)}
    return templates.TemplateResponse(request, "localizador.html", ctx)
