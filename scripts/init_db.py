import sqlite3
import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app.config import DB_PATH  # noqa: E402
from scripts.seed_content import seed_if_empty  # noqa: E402

SCHEMA_SQL = """
CREATE INDEX IF NOT EXISTS idx_bancos_uf     ON bancos_de_leite(uf);
CREATE INDEX IF NOT EXISTS idx_bancos_cidade ON bancos_de_leite(cidade);

CREATE TABLE IF NOT EXISTS campanhas (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  titulo      TEXT NOT NULL,
  resumo      TEXT NOT NULL,
  conteudo    TEXT,
  imagem_url  TEXT,
  data_inicio DATE,
  data_fim    DATE,
  ativa       INTEGER NOT NULL DEFAULT 1 CHECK (ativa IN (0,1)),
  ordem       INTEGER NOT NULL DEFAULT 0,
  criado_em   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS doadoras (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  nome             TEXT NOT NULL,
  email            TEXT NOT NULL,
  telefone         TEXT NOT NULL,
  cidade           TEXT NOT NULL,
  uf               TEXT NOT NULL CHECK (length(uf) = 2),
  bebe_nascimento  DATE,
  ja_doou_antes    INTEGER NOT NULL DEFAULT 0 CHECK (ja_doou_antes IN (0,1)),
  mensagem         TEXT,
  banco_leite_id   INTEGER REFERENCES bancos_de_leite(id),
  status           TEXT NOT NULL DEFAULT 'novo' CHECK (status IN ('novo','contatada','confirmada','inativa')),
  criado_em        TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS contatos (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  nome      TEXT NOT NULL,
  email     TEXT NOT NULL,
  assunto   TEXT,
  mensagem  TEXT NOT NULL,
  criado_em TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if "bancos_de_leite" not in tables:
            raise RuntimeError(
                f"Tabela 'bancos_de_leite' nao encontrada em {DB_PATH}. "
                "Rode parse_blhs.py antes de iniciar o app."
            )

        row_count = conn.execute("SELECT COUNT(*) FROM bancos_de_leite").fetchone()[0]
        if row_count == 0:
            raise RuntimeError("Tabela 'bancos_de_leite' esta vazia — verifique o banco.")

        conn.executescript(SCHEMA_SQL)
        conn.commit()

        seed_if_empty(conn)

        print(f"[init_db] OK — bancos_de_leite mantido com {row_count} registros.")
        campanhas_count = conn.execute("SELECT COUNT(*) FROM campanhas").fetchone()[0]
        print(f"[init_db] campanhas: {campanhas_count} registros.")
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
