import re
import sqlite3
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


def match_banco_leite_id(conn: sqlite3.Connection, uf: str, cidade: str) -> Optional[int]:
    row = conn.execute(
        """
        SELECT id FROM bancos_de_leite
        WHERE uf = ? AND LOWER(cidade) = LOWER(?)
        LIMIT 1
        """,
        (uf.strip().upper(), cidade.strip()),
    ).fetchone()
    return row["id"] if row else None


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


def insert_doadora(conn: sqlite3.Connection, data: dict) -> int:
    if not data.get("banco_leite_id"):
        data["banco_leite_id"] = match_banco_leite_id(conn, data["uf"], data["cidade"])

    cur = conn.execute(
        """
        INSERT INTO doadoras
            (nome, email, telefone, cidade, uf, bebe_nascimento,
             ja_doou_antes, mensagem, banco_leite_id, status)
        VALUES
            (:nome, :email, :telefone, :cidade, :uf, :bebe_nascimento,
             :ja_doou_antes, :mensagem, :banco_leite_id, 'novo')
        """,
        data,
    )
    conn.commit()
    return cur.lastrowid


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
