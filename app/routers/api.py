import sqlite3
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from .. import repo
from ..db import get_db
from ..models import ChatIn, ContatoIn
from ..services import chat as chat_service

router = APIRouter(prefix="/api")


@router.get("/localizador")
def api_localizador(
    uf: Optional[str] = None,
    cidade: Optional[str] = None,
    categoria: Optional[str] = None,
    db: sqlite3.Connection = Depends(get_db),
):
    resultados = repo.list_bancos(db, uf=uf, cidade=cidade, categoria=categoria)
    return {"total": len(resultados), "resultados": resultados}


@router.get("/cidades")
def api_cidades(uf: Optional[str] = None, db: sqlite3.Connection = Depends(get_db)):
    return {"cidades": repo.distinct_cidades(db, uf=uf)}


@router.get("/estados")
def api_estados(db: sqlite3.Connection = Depends(get_db)):
    return {"estados": repo.distinct_estados(db)}


@router.get("/campanhas")
def api_campanhas(db: sqlite3.Connection = Depends(get_db)):
    return {"campanhas": repo.list_campanhas_ativas(db)}


@router.post("/contatos", status_code=201)
def api_contatos(payload: ContatoIn, db: sqlite3.Connection = Depends(get_db)):
    novo_id = repo.insert_contato(db, payload.model_dump())
    return JSONResponse(status_code=201, content={"ok": True, "id": novo_id})


@router.post("/chat")
def api_chat(payload: ChatIn):
    historico = [m.model_dump() for m in payload.historico]
    resposta = chat_service.ask(payload.mensagem, historico)
    return {"resposta": resposta}
