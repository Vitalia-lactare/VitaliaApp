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


@router.get("/dashboard")
def admin_dashboard(request: Request, db: sqlite3.Connection = Depends(get_db)):
    funil = repo.funil_contagem_por_evento(db)
    quiz_dropoff = repo.funil_dropoff_quiz(db)
    alertas = repo.alertas_breakdown(db)
    cadastros_uf = repo.cadastros_por_uf(db)
    acessos_hora = repo.acessos_por_hora(db)

    ctx = {
        "request": request,
        "funil": funil,
        "funil_max": max((r["sessoes"] for r in funil), default=0),
        "quiz_dropoff": quiz_dropoff,
        "quiz_dropoff_max": max((r["sessoes"] for r in quiz_dropoff), default=0),
        "quiz_conclusao": repo.taxa_conclusao_quiz(db),
        "conversao": repo.taxa_conversao_cadastro(db),
        "alertas": alertas,
        "alertas_max": max((r["total"] for r in alertas), default=0),
        "cadastros_uf": cadastros_uf,
        "cadastros_uf_max": max((r["total"] for r in cadastros_uf), default=0),
        "acessos_hora": acessos_hora,
        "acessos_hora_max": max((r["sessoes"] for r in acessos_hora), default=0),
        "retorno": repo.taxa_retorno(db),
        "total_sessoes": repo.count_sessoes_totais(db),
        "total_doadoras_portal": repo.count_doadoras_portal(db),
    }
    return templates.TemplateResponse(request, "admin_dashboard.html", ctx)
