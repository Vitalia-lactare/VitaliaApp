import sqlite3

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from .. import repo
from ..db import get_db
from ..models import AgendamentoIn, CadastroPortalIn, EventoIn, FeedbackIn, TriagemIn
from ..services import cep as cep_service
from ..templating import templates

router = APIRouter()

# Nomes de evento usados pelo portal.js — documentacao, nao e validado por CHECK
# no banco (eventos_funil.evento fica como TEXT livre de proposito).
EVENTOS_CONHECIDOS = [
    "boas_vindas_view", "video_view", "quiz_step_view", "quiz_completed",
    "cadastro_view", "cadastro_submitted", "cadastro_error",
    "confirmacao_view", "agendamento_view", "agendamento_submitted",
    "agendamento_skipped", "feedback_view", "feedback_submitted",
    "fechamento_view", "saiba_mais_click",
]


@router.get("/")
def portal_wizard(request: Request, db: sqlite3.Connection = Depends(get_db)):
    ctx = {
        "request": request,
        "total_bancos": repo.count_bancos(db),
        "total_estados": repo.count_estados(db),
        "estados": repo.distinct_estados(db),
    }
    return templates.TemplateResponse(request, "portal.html", ctx)


@router.get("/api/portal/cep")
def portal_cep(cep: str, db: sqlite3.Connection = Depends(get_db)):
    resolved = cep_service.lookup_cep(cep)
    if not resolved:
        return {"encontrado": False}

    banco = repo.buscar_banco_proximo(db, resolved["uf"], resolved["cidade"])
    return {
        "encontrado": True,
        "cidade": resolved["cidade"],
        "uf": resolved["uf"],
        "banco": banco,
    }


@router.post("/api/portal/eventos", status_code=201)
def portal_evento(payload: EventoIn, db: sqlite3.Connection = Depends(get_db)):
    novo_id = repo.log_evento(db, payload.sessao_id, payload.evento, payload.etapa, payload.metadata)
    return {"ok": True, "id": novo_id}


@router.post("/api/portal/triagem", status_code=201)
def portal_triagem(payload: TriagemIn, db: sqlite3.Connection = Depends(get_db)):
    respostas = {
        "amamentando": payload.amamentando,
        "idade_bebe": payload.idade_bebe,
        "usa_medicamento": payload.usa_medicamento,
        "fumante": payload.fumante,
        "exame_recente": payload.exame_recente,
        "ja_doou_antes": payload.ja_doou_antes,
    }
    resultado = repo.criar_triagem(db, payload.sessao_id, respostas)
    return {"ok": True, "triagem_id": resultado["id"], "alertas": resultado["alertas"]}


@router.post("/api/portal/cadastro", status_code=201)
def portal_cadastro(payload: CadastroPortalIn, db: sqlite3.Connection = Depends(get_db)):
    data = payload.model_dump()
    data["bebe_nascimento"] = data["bebe_nascimento"].isoformat() if data["bebe_nascimento"] else None
    data["ja_doou_antes"] = 1 if data["ja_doou_antes"] else 0
    data["uf"] = data["uf"].upper()

    triagem = repo.buscar_triagem_por_sessao(db, data["sessao_id"])
    data["triagem_id"] = triagem["id"] if triagem else None

    if not data.get("banco_leite_id"):
        data["banco_leite_id"] = repo.match_banco_leite_id(db, data["uf"], data["cidade"])

    novo_id = repo.insert_doadora_portal(db, data)
    if triagem:
        repo.vincular_triagem_doadora(db, triagem["id"], novo_id)

    banco = repo.get_banco_by_id(db, data["banco_leite_id"]) if data["banco_leite_id"] else None
    return JSONResponse(status_code=201, content={"ok": True, "id": novo_id, "banco": banco})


@router.post("/api/portal/agendamento")
def portal_agendamento(payload: AgendamentoIn, db: sqlite3.Connection = Depends(get_db)):
    data = payload.model_dump()
    data["data_preferida"] = data["data_preferida"].isoformat() if data["data_preferida"] else None
    repo.atualizar_agendamento(db, payload.doadora_id, data)
    repo.log_evento(db, payload.sessao_id, "agendamento_submitted", doadora_id=payload.doadora_id)
    return {"ok": True}


@router.post("/api/portal/feedback")
def portal_feedback(payload: FeedbackIn, db: sqlite3.Connection = Depends(get_db)):
    repo.atualizar_feedback(db, payload.doadora_id, payload.nota, payload.comentario)
    repo.log_evento(
        db, payload.sessao_id, "feedback_submitted",
        metadata={"nota": payload.nota}, doadora_id=payload.doadora_id,
    )
    return {"ok": True}
