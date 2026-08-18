import sqlite3
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from .. import repo
from ..db import get_db
from ..templating import templates
from .auth import require_admin

router = APIRouter(prefix="/admin", dependencies=[Depends(require_admin)])

EVENTO_LABELS = {
    "boas_vindas_view": "Boas-vindas",
    "video_view": "Vídeo",
    "quiz_step_view": "Etapa do quiz",
    "quiz_completed": "Quiz concluído",
    "cadastro_view": "Visualizou cadastro",
    "cadastro_submitted": "Cadastro enviado",
    "cadastro_error": "Erro no cadastro",
    "confirmacao_view": "Confirmação",
    "agendamento_view": "Visualizou agendamento",
    "agendamento_submitted": "Agendamento enviado",
    "agendamento_skipped": "Agendamento pulado",
    "feedback_view": "Visualizou feedback",
    "feedback_submitted": "Feedback enviado",
    "fechamento_view": "Fechamento",
    "saiba_mais_click": "Clique em saiba mais",
}

ALERTA_LABELS = {
    "fumante": "Fumante",
    "uso_medicamento": "Uso de medicamento",
    "sem_exame_recente": "Sem exame recente",
}

QUIZ_LABELS = {
    "q1": "Amamentando atualmente?",
    "q2": "Idade aproximada do bebê",
    "q3": "Toma algum medicamento?",
    "q4": "Fuma?",
    "q5": "Fez exames de sangue recentes?",
    "q6": "Já doou leite antes?",
}


def _humanize(code: str) -> str:
    return code.replace("_", " ").capitalize()


def _relabel(rows: list[dict], key: str, labels: dict[str, str]) -> list[dict]:
    for row in rows:
        row[key] = labels.get(row[key], _humanize(row[key]))
    return rows


def _delta_relativo(atual: int, anterior: int) -> Optional[dict]:
    """Variação percentual vs mês anterior. None quando não há base de comparação."""
    if not anterior:
        return None
    variacao = round(100 * (atual - anterior) / anterior)
    sinal = "+" if variacao >= 0 else ""
    return {"texto": f"{sinal}{variacao}% vs mês anterior", "positivo": variacao >= 0}


def _delta_pontos(atual: Optional[float], anterior: Optional[float], sufixo: str = "") -> Optional[dict]:
    """Diferença em pontos (percentuais ou de nota) vs mês anterior."""
    if atual is None or anterior is None:
        return None
    diff = round(atual - anterior, 1)
    sinal = "+" if diff >= 0 else ""
    return {"texto": f"{sinal}{diff}{sufixo} vs mês anterior", "positivo": diff >= 0}


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
    funil = _relabel(repo.funil_contagem_por_evento(db), "evento", EVENTO_LABELS)
    quiz_dropoff = _relabel(repo.funil_dropoff_quiz(db), "etapa", QUIZ_LABELS)
    alertas = _relabel(repo.alertas_breakdown(db), "alerta", ALERTA_LABELS)
    cadastros_uf = repo.cadastros_por_uf(db)
    acessos_hora = repo.acessos_por_hora(db)
    conversao = repo.taxa_conversao_cadastro(db)

    cadastros_mes = repo.cadastros_por_mes(db)
    agendamentos_mes = repo.agendamentos_por_mes(db)
    conversao_mes = repo.conversao_por_mes(db)
    avaliacao_mes = repo.avaliacao_por_mes(db)
    avaliacoes = repo.avaliacoes_breakdown(db)
    cadastros_dia = repo.cadastros_por_dia(db)

    funil_principal = [
        {"label": "Sessões iniciadas", "valor": conversao["sessoes_totais"], "cor": "stage-1"},
        {"label": "Quiz concluído", "valor": conversao["quiz_completo"], "cor": "stage-2"},
        {"label": "Cadastro enviado", "valor": conversao["cadastro_ok"], "cor": "stage-3"},
    ]
    funil_principal_max = funil_principal[0]["valor"] or 1

    ctx = {
        "request": request,
        "funil": funil,
        "funil_max": max((r["sessoes"] for r in funil), default=0),
        "quiz_dropoff": quiz_dropoff,
        "quiz_dropoff_max": max((r["sessoes"] for r in quiz_dropoff), default=0),
        "quiz_conclusao": repo.taxa_conclusao_quiz(db),
        "conversao": conversao,
        "alertas": alertas,
        "alertas_max": max((r["total"] for r in alertas), default=0),
        "cadastros_uf": cadastros_uf,
        "cadastros_uf_max": max((r["total"] for r in cadastros_uf), default=0),
        "acessos_hora": acessos_hora,
        "acessos_hora_max": max((r["sessoes"] for r in acessos_hora), default=0),
        "retorno": repo.taxa_retorno(db),
        "total_sessoes": repo.count_sessoes_totais(db),
        "total_doadoras_portal": repo.count_doadoras_portal(db),
        "total_agendamentos": repo.count_agendamentos_solicitados(db),
        "cadastros_mes": cadastros_mes,
        "cadastros_delta": _delta_relativo(cadastros_mes["atual"], cadastros_mes["anterior"]),
        "agendamentos_mes": agendamentos_mes,
        "agendamentos_delta": _delta_relativo(agendamentos_mes["atual"], agendamentos_mes["anterior"]),
        "conversao_delta": _delta_pontos(conversao_mes["atual"], conversao_mes["anterior"], " pts"),
        "avaliacao_delta": _delta_pontos(avaliacao_mes["atual"], avaliacao_mes["anterior"]),
        "avaliacoes": avaliacoes,
        "cadastros_dia": cadastros_dia,
        "cadastros_dia_max": max((r["total"] for r in cadastros_dia), default=0),
        "funil_principal": funil_principal,
        "funil_principal_max": funil_principal_max,
    }
    return templates.TemplateResponse(request, "admin_dashboard.html", ctx)
