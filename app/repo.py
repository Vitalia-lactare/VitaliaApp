import json
import re
import sqlite3
from collections import Counter
from datetime import date, timedelta
from typing import Optional


def _digits(value: Optional[str]) -> str:
    return re.sub(r"\D", "", value or "")


def phone_info(telefone: Optional[str]) -> dict:
    """Normaliza um telefone bruto do banco em texto formatado + links tel:/wa.me.

    Os dados de origem são heterogêneos (alguns com DDD antigo de 3 dígitos,
    outros com placeholders tipo '0000-00'), então links só são gerados quando
    o número de dígitos bate com um telefone brasileiro válido (10 ou 11).
    """
    if not telefone:
        return {"telefone_fmt": None, "tel_link": None, "whatsapp_link": None}

    digits = _digits(telefone)
    if len(digits) > 11:
        digits = digits[-11:]

    if len(digits) in (10, 11):
        ddd, resto = digits[:2], digits[2:]
        fmt = f"({ddd}) {resto[:-4]}-{resto[-4:]}"
        return {
            "telefone_fmt": fmt,
            "tel_link": f"tel:+55{digits}",
            "whatsapp_link": f"https://wa.me/55{digits}",
        }

    return {"telefone_fmt": telefone, "tel_link": None, "whatsapp_link": None}


def _row_to_banco(row: sqlite3.Row) -> dict:
    d = dict(row)
    d.update(phone_info(d.get("telefone")))
    return d


def list_bancos(
    conn: sqlite3.Connection,
    uf: Optional[str] = None,
    cidade: Optional[str] = None,
    categoria: Optional[str] = None,
    limit: int = 200,
) -> list[dict]:
    clauses = []
    params: list = []

    if uf:
        clauses.append("uf = ?")
        params.append(uf.strip().upper())
    if cidade:
        clauses.append("LOWER(cidade) LIKE LOWER(?)")
        params.append(f"%{cidade.strip()}%")
    if categoria:
        clauses.append("categoria = ?")
        params.append(categoria.strip())

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"""
        SELECT id, nome, categoria, endereco, cidade, uf, cep, estado, telefone, url_slug
        FROM bancos_de_leite
        {where}
        ORDER BY cidade, nome
        LIMIT ?
    """
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    return [_row_to_banco(r) for r in rows]


def distinct_estados(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT DISTINCT uf, estado
        FROM bancos_de_leite
        WHERE uf IS NOT NULL
        ORDER BY estado
        """
    ).fetchall()
    return [dict(r) for r in rows]


def distinct_cidades(conn: sqlite3.Connection, uf: Optional[str] = None) -> list[str]:
    if uf:
        rows = conn.execute(
            """
            SELECT DISTINCT cidade FROM bancos_de_leite
            WHERE uf = ? AND cidade IS NOT NULL
            ORDER BY cidade
            """,
            (uf.strip().upper(),),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT DISTINCT cidade FROM bancos_de_leite
            WHERE cidade IS NOT NULL
            ORDER BY cidade
            """
        ).fetchall()
    return [r["cidade"] for r in rows]


def count_bancos(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM bancos_de_leite").fetchone()[0]


def count_estados(conn: sqlite3.Connection) -> int:
    return conn.execute(
        "SELECT COUNT(DISTINCT uf) FROM bancos_de_leite WHERE uf IS NOT NULL"
    ).fetchone()[0]


def match_banco_leite_id(
    conn: sqlite3.Connection, uf: str, cidade: str, uf_fallback: bool = True
) -> Optional[int]:
    row = conn.execute(
        """
        SELECT id FROM bancos_de_leite
        WHERE uf = ? AND LOWER(cidade) = LOWER(?)
        LIMIT 1
        """,
        (uf.strip().upper(), cidade.strip()),
    ).fetchone()
    if row:
        return row["id"]

    if not uf_fallback:
        return None

    row = conn.execute(
        """
        SELECT id FROM bancos_de_leite
        WHERE uf = ?
        ORDER BY CASE categoria
                   WHEN 'Banco de Leite' THEN 0
                   WHEN 'Centro de Referência' THEN 1
                   ELSE 2
                 END, cidade
        LIMIT 1
        """,
        (uf.strip().upper(),),
    ).fetchone()
    return row["id"] if row else None


def get_banco_by_id(conn: sqlite3.Connection, banco_id: int) -> Optional[dict]:
    row = conn.execute(
        """
        SELECT id, nome, categoria, endereco, cidade, uf, cep, estado, telefone, url_slug
        FROM bancos_de_leite WHERE id = ?
        """,
        (banco_id,),
    ).fetchone()
    return _row_to_banco(row) if row else None


def buscar_banco_proximo(conn: sqlite3.Connection, uf: str, cidade: str) -> Optional[dict]:
    """Encontra o banco mais proximo: match exato de cidade, com fallback para
    qualquer banco no mesmo UF. Nao ha calculo geografico real (sem lat/long)."""
    exato_id = match_banco_leite_id(conn, uf, cidade, uf_fallback=False)
    if exato_id:
        banco = get_banco_by_id(conn, exato_id)
        banco["match_tipo"] = "cidade"
        return banco

    aprox_id = match_banco_leite_id(conn, uf, cidade, uf_fallback=True)
    if aprox_id:
        banco = get_banco_by_id(conn, aprox_id)
        banco["match_tipo"] = "uf"
        return banco

    return None


def list_campanhas_ativas(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT * FROM campanhas
        WHERE ativa = 1
        ORDER BY ordem, data_inicio DESC, id DESC
        """
    ).fetchall()
    return [dict(r) for r in rows]


def list_campanhas_all(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM campanhas ORDER BY ordem, id DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def insert_campanha(conn: sqlite3.Connection, data: dict) -> int:
    cur = conn.execute(
        """
        INSERT INTO campanhas (titulo, resumo, conteudo, imagem_url, data_inicio, data_fim)
        VALUES (:titulo, :resumo, :conteudo, :imagem_url, :data_inicio, :data_fim)
        """,
        data,
    )
    conn.commit()
    return cur.lastrowid


def toggle_campanha_ativa(conn: sqlite3.Connection, campanha_id: int) -> None:
    conn.execute(
        "UPDATE campanhas SET ativa = 1 - ativa WHERE id = ?", (campanha_id,)
    )
    conn.commit()


def insert_contato(conn: sqlite3.Connection, data: dict) -> int:
    cur = conn.execute(
        """
        INSERT INTO contatos (nome, email, assunto, mensagem)
        VALUES (:nome, :email, :assunto, :mensagem)
        """,
        data,
    )
    conn.commit()
    return cur.lastrowid


# ---- Portal do Doador: eventos de funil e triagem ----

def log_evento(
    conn: sqlite3.Connection,
    sessao_id: str,
    evento: str,
    etapa: Optional[str] = None,
    metadata: Optional[dict] = None,
    doadora_id: Optional[int] = None,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO eventos_funil (sessao_id, evento, etapa, metadata, doadora_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        (sessao_id, evento, etapa, json.dumps(metadata) if metadata else None, doadora_id),
    )
    conn.commit()
    return cur.lastrowid


def criar_triagem(conn: sqlite3.Connection, sessao_id: str, respostas: dict) -> dict:
    alertas = []
    if respostas["fumante"]:
        alertas.append("fumante")
    if respostas["usa_medicamento"]:
        alertas.append("uso_medicamento")
    if not respostas["exame_recente"]:
        alertas.append("sem_exame_recente")

    cur = conn.execute(
        """
        INSERT INTO triagens
            (sessao_id, amamentando, idade_bebe, usa_medicamento, fumante,
             exame_recente, ja_doou_antes, alertas)
        VALUES
            (:sessao_id, :amamentando, :idade_bebe, :usa_medicamento, :fumante,
             :exame_recente, :ja_doou_antes, :alertas)
        """,
        {
            "sessao_id": sessao_id,
            "amamentando": respostas["amamentando"],
            "idade_bebe": respostas["idade_bebe"],
            "usa_medicamento": int(respostas["usa_medicamento"]),
            "fumante": int(respostas["fumante"]),
            "exame_recente": int(respostas["exame_recente"]),
            "ja_doou_antes": int(respostas["ja_doou_antes"]),
            "alertas": json.dumps(alertas) if alertas else None,
        },
    )
    conn.commit()
    return {"id": cur.lastrowid, "alertas": alertas}


def buscar_triagem_por_sessao(conn: sqlite3.Connection, sessao_id: str) -> Optional[dict]:
    row = conn.execute(
        "SELECT * FROM triagens WHERE sessao_id = ? ORDER BY id DESC LIMIT 1",
        (sessao_id,),
    ).fetchone()
    return dict(row) if row else None


def vincular_triagem_doadora(conn: sqlite3.Connection, triagem_id: int, doadora_id: int) -> None:
    conn.execute("UPDATE triagens SET doadora_id = ? WHERE id = ?", (doadora_id, triagem_id))
    conn.commit()


def insert_doadora_portal(conn: sqlite3.Connection, data: dict) -> int:
    if not data.get("banco_leite_id"):
        data["banco_leite_id"] = match_banco_leite_id(conn, data["uf"], data["cidade"])

    cur = conn.execute(
        """
        INSERT INTO doadoras
            (nome, email, telefone, cidade, uf, bebe_nascimento, ja_doou_antes,
             mensagem, banco_leite_id, status, cep, sessao_id, triagem_id)
        VALUES
            (:nome, :email, :telefone, :cidade, :uf, :bebe_nascimento, :ja_doou_antes,
             :mensagem, :banco_leite_id, 'novo', :cep, :sessao_id, :triagem_id)
        """,
        data,
    )
    conn.commit()
    return cur.lastrowid


def atualizar_agendamento(conn: sqlite3.Connection, doadora_id: int, data: dict) -> None:
    conn.execute(
        """
        UPDATE doadoras
        SET agendamento_solicitado = 1,
            endereco_coleta = :endereco_coleta,
            agendamento_data_preferida = :data_preferida,
            agendamento_periodo = :periodo
        WHERE id = :doadora_id
        """,
        {**data, "doadora_id": doadora_id},
    )
    conn.commit()


def atualizar_feedback(
    conn: sqlite3.Connection, doadora_id: int, nota: int, comentario: Optional[str]
) -> None:
    conn.execute(
        "UPDATE doadoras SET feedback_nota = ?, feedback_comentario = ? WHERE id = ?",
        (nota, comentario, doadora_id),
    )
    conn.commit()


# ---- Dashboard de indicadores ----

def funil_contagem_por_evento(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT evento, COUNT(*) AS total, COUNT(DISTINCT sessao_id) AS sessoes
        FROM eventos_funil GROUP BY evento ORDER BY sessoes DESC
        """
    ).fetchall()
    return [dict(r) for r in rows]


def funil_dropoff_quiz(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT etapa, COUNT(DISTINCT sessao_id) AS sessoes
        FROM eventos_funil
        WHERE evento = 'quiz_step_view' AND etapa IS NOT NULL
        GROUP BY etapa ORDER BY etapa
        """
    ).fetchall()
    return [dict(r) for r in rows]


def taxa_conclusao_quiz(conn: sqlite3.Connection) -> dict:
    iniciaram = conn.execute(
        "SELECT COUNT(DISTINCT sessao_id) FROM eventos_funil WHERE evento='quiz_step_view' AND etapa='q1'"
    ).fetchone()[0]
    concluiram = conn.execute(
        "SELECT COUNT(DISTINCT sessao_id) FROM eventos_funil WHERE evento='quiz_completed'"
    ).fetchone()[0]
    return {
        "iniciaram": iniciaram,
        "concluiram": concluiram,
        "taxa_pct": round(100 * concluiram / iniciaram, 1) if iniciaram else 0.0,
    }


def taxa_conversao_cadastro(conn: sqlite3.Connection) -> dict:
    sessoes_totais = conn.execute(
        "SELECT COUNT(DISTINCT sessao_id) FROM eventos_funil"
    ).fetchone()[0]
    quiz_completo = conn.execute(
        "SELECT COUNT(DISTINCT sessao_id) FROM eventos_funil WHERE evento='quiz_completed'"
    ).fetchone()[0]
    cadastro_ok = conn.execute(
        "SELECT COUNT(DISTINCT sessao_id) FROM eventos_funil WHERE evento='cadastro_submitted'"
    ).fetchone()[0]
    return {
        "sessoes_totais": sessoes_totais,
        "quiz_completo": quiz_completo,
        "cadastro_ok": cadastro_ok,
        "taxa_geral_pct": round(100 * cadastro_ok / sessoes_totais, 1) if sessoes_totais else 0.0,
    }


def alertas_breakdown(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT alertas FROM triagens WHERE alertas IS NOT NULL").fetchall()
    counter = Counter()
    for r in rows:
        for alerta in json.loads(r["alertas"]):
            counter[alerta] += 1
    return [{"alerta": k, "total": v} for k, v in counter.most_common()]


def cadastros_por_uf(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT uf, COUNT(*) AS total FROM doadoras GROUP BY uf ORDER BY total DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def acessos_por_hora(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT CAST(strftime('%H', criado_em, '-3 hours') AS INTEGER) AS hora,
               COUNT(DISTINCT sessao_id) AS sessoes
        FROM eventos_funil GROUP BY hora ORDER BY hora
        """
    ).fetchall()
    por_hora = {r["hora"]: r["sessoes"] for r in rows}
    return [{"hora": h, "sessoes": por_hora.get(h, 0)} for h in range(24)]


def taxa_retorno(conn: sqlite3.Connection) -> dict:
    rows = conn.execute(
        "SELECT ja_doou_antes, COUNT(*) AS total FROM doadoras GROUP BY ja_doou_antes"
    ).fetchall()
    novas = next((r["total"] for r in rows if r["ja_doou_antes"] == 0), 0)
    recorrentes = next((r["total"] for r in rows if r["ja_doou_antes"] == 1), 0)
    geral = novas + recorrentes
    return {
        "novas": novas,
        "recorrentes": recorrentes,
        "taxa_retorno_pct": round(100 * recorrentes / geral, 1) if geral else 0.0,
    }


def count_sessoes_totais(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(DISTINCT sessao_id) FROM eventos_funil").fetchone()[0]


def count_doadoras_portal(conn: sqlite3.Connection) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM doadoras WHERE sessao_id IS NOT NULL"
    ).fetchone()[0]


def count_agendamentos_solicitados(conn: sqlite3.Connection) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM doadoras WHERE agendamento_solicitado = 1"
    ).fetchone()[0]


def cadastros_por_mes(conn: sqlite3.Connection) -> dict:
    row = conn.execute(
        """
        SELECT
          SUM(CASE WHEN strftime('%Y-%m', criado_em) = strftime('%Y-%m', 'now') THEN 1 ELSE 0 END) AS atual,
          SUM(CASE WHEN strftime('%Y-%m', criado_em) = strftime('%Y-%m', 'now', '-1 month') THEN 1 ELSE 0 END) AS anterior
        FROM doadoras WHERE sessao_id IS NOT NULL
        """
    ).fetchone()
    return {"atual": row["atual"] or 0, "anterior": row["anterior"] or 0}


def agendamentos_por_mes(conn: sqlite3.Connection) -> dict:
    """Mes do agendamento aproximado pelo criado_em do cadastro (nao ha
    timestamp proprio para o momento em que o agendamento foi solicitado)."""
    row = conn.execute(
        """
        SELECT
          SUM(CASE WHEN strftime('%Y-%m', criado_em) = strftime('%Y-%m', 'now') THEN 1 ELSE 0 END) AS atual,
          SUM(CASE WHEN strftime('%Y-%m', criado_em) = strftime('%Y-%m', 'now', '-1 month') THEN 1 ELSE 0 END) AS anterior
        FROM doadoras WHERE agendamento_solicitado = 1
        """
    ).fetchone()
    return {"atual": row["atual"] or 0, "anterior": row["anterior"] or 0}


def _conversao_do_mes(conn: sqlite3.Connection, offset: str) -> Optional[float]:
    row = conn.execute(
        """
        SELECT
          COUNT(DISTINCT sessao_id) AS sessoes,
          COUNT(DISTINCT CASE WHEN evento = 'cadastro_submitted' THEN sessao_id END) AS cadastros
        FROM eventos_funil
        WHERE strftime('%Y-%m', criado_em) = strftime('%Y-%m', 'now', ?)
        """,
        (offset,),
    ).fetchone()
    if not row["sessoes"]:
        return None
    return round(100 * row["cadastros"] / row["sessoes"], 1)


def conversao_por_mes(conn: sqlite3.Connection) -> dict:
    return {
        "atual": _conversao_do_mes(conn, "0 months"),
        "anterior": _conversao_do_mes(conn, "-1 months"),
    }


def _avaliacao_do_mes(conn: sqlite3.Connection, offset: str) -> Optional[float]:
    row = conn.execute(
        """
        SELECT AVG(feedback_nota) AS media
        FROM doadoras
        WHERE feedback_nota IS NOT NULL
          AND strftime('%Y-%m', criado_em) = strftime('%Y-%m', 'now', ?)
        """,
        (offset,),
    ).fetchone()
    return round(row["media"], 1) if row["media"] is not None else None


def avaliacao_por_mes(conn: sqlite3.Connection) -> dict:
    return {
        "atual": _avaliacao_do_mes(conn, "0 months"),
        "anterior": _avaliacao_do_mes(conn, "-1 months"),
    }


def avaliacoes_breakdown(conn: sqlite3.Connection) -> dict:
    rows = conn.execute(
        """
        SELECT feedback_nota AS nota, COUNT(*) AS total
        FROM doadoras
        WHERE feedback_nota IS NOT NULL
        GROUP BY feedback_nota
        """
    ).fetchall()
    por_nota = {r["nota"]: r["total"] for r in rows}
    total_respostas = sum(por_nota.values())
    media_row = conn.execute(
        "SELECT AVG(feedback_nota) AS media FROM doadoras WHERE feedback_nota IS NOT NULL"
    ).fetchone()
    breakdown = [
        {
            "nota": nota,
            "total": por_nota.get(nota, 0),
            "pct": round(100 * por_nota.get(nota, 0) / total_respostas, 0) if total_respostas else 0,
        }
        for nota in (5, 4, 3, 2, 1)
    ]
    return {
        "media": round(media_row["media"], 1) if media_row["media"] is not None else None,
        "total_respostas": total_respostas,
        "breakdown": breakdown,
    }


def cadastros_por_dia(conn: sqlite3.Connection, dias: int = 14) -> list[dict]:
    rows = conn.execute(
        """
        SELECT date(criado_em) AS dia, COUNT(*) AS total
        FROM doadoras
        WHERE sessao_id IS NOT NULL AND date(criado_em) >= date('now', ?)
        GROUP BY dia
        """,
        (f"-{dias - 1} days",),
    ).fetchall()
    por_dia = {r["dia"]: r["total"] for r in rows}
    hoje = date.today()
    return [
        {
            "dia": (hoje - timedelta(days=i)).isoformat(),
            "total": por_dia.get((hoje - timedelta(days=i)).isoformat(), 0),
        }
        for i in range(dias - 1, -1, -1)
    ]
