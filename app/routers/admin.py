import sqlite3
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from .. import repo
from ..db import get_db
from ..templating import templates

router = APIRouter(prefix="/admin")


@router.get("/campanhas")
def admin_campanhas_list(request: Request, db: sqlite3.Connection = Depends(get_db)):
    ctx = {"request": request, "campanhas": repo.list_campanhas_all(db)}
    return templates.TemplateResponse(request, "admin_campanhas.html", ctx)


@router.post("/campanhas")
def admin_campanhas_create(
    titulo: str = Form(...),
    resumo: str = Form(...),
    conteudo: Optional[str] = Form(None),
    imagem_url: Optional[str] = Form(None),
    data_inicio: Optional[str] = Form(None),
    data_fim: Optional[str] = Form(None),
    db: sqlite3.Connection = Depends(get_db),
):
    repo.insert_campanha(
        db,
        {
            "titulo": titulo,
            "resumo": resumo,
            "conteudo": conteudo or None,
            "imagem_url": imagem_url or None,
            "data_inicio": data_inicio or None,
            "data_fim": data_fim or None,
        },
    )
    return RedirectResponse(url="/admin/campanhas", status_code=303)


@router.post("/campanhas/{campanha_id}/toggle")
def admin_campanhas_toggle(campanha_id: int, db: sqlite3.Connection = Depends(get_db)):
    repo.toggle_campanha_ativa(db, campanha_id)
    return RedirectResponse(url="/admin/campanhas", status_code=303)
