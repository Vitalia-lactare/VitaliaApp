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

CREATE TABLE IF NOT EXISTS triagens (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  sessao_id       TEXT NOT NULL,
  doadora_id      INTEGER REFERENCES doadoras(id),
  amamentando     TEXT NOT NULL CHECK (amamentando IN ('sim_atualmente','ainda_nao','nao_mais')),
  idade_bebe      TEXT NOT NULL CHECK (idade_bebe IN ('menos_1_mes','1_a_3_meses','3_a_6_meses','6_a_12_meses','mais_12_meses','nao_se_aplica')),
  usa_medicamento INTEGER NOT NULL CHECK (usa_medicamento IN (0,1)),
  fumante         INTEGER NOT NULL CHECK (fumante IN (0,1)),
  exame_recente   INTEGER NOT NULL CHECK (exame_recente IN (0,1)),
  ja_doou_antes   INTEGER NOT NULL CHECK (ja_doou_antes IN (0,1)),
  alertas         TEXT,
  criado_em       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_triagens_sessao  ON triagens(sessao_id);
CREATE INDEX IF NOT EXISTS idx_triagens_doadora ON triagens(doadora_id);

CREATE TABLE IF NOT EXISTS eventos_funil (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  sessao_id   TEXT NOT NULL,
  evento      TEXT NOT NULL,
  etapa       TEXT,
  metadata    TEXT,
  doadora_id  INTEGER REFERENCES doadoras(id),
  criado_em   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_eventos_sessao    ON eventos_funil(sessao_id);
CREATE INDEX IF NOT EXISTS idx_eventos_evento    ON eventos_funil(evento);
CREATE INDEX IF NOT EXISTS idx_eventos_criado_em ON eventos_funil(criado_em);
"""

DOADORA_NEW_COLUMNS = {
    "cep": "TEXT",
    "sessao_id": "TEXT",
    "triagem_id": "INTEGER REFERENCES triagens(id)",
    "endereco_coleta": "TEXT",
    "agendamento_solicitado": "INTEGER NOT NULL DEFAULT 0",
    "agendamento_data_preferida": "TEXT",
    "agendamento_periodo": "TEXT",
    "feedback_nota": "INTEGER",
    "feedback_comentario": "TEXT",
}


def _ensure_doadora_columns(conn: sqlite3.Connection) -> None:
    existing = {row[1] for row in conn.execute("PRAGMA table_info(doadoras)").fetchall()}
    for col, coldef in DOADORA_NEW_COLUMNS.items():
        if col not in existing:
            conn.execute(f"ALTER TABLE doadoras ADD COLUMN {col} {coldef}")
    conn.commit()


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

        _ensure_doadora_columns(conn)

        seed_if_empty(conn)

        print(f"[init_db] OK — bancos_de_leite mantido com {row_count} registros.")
        campanhas_count = conn.execute("SELECT COUNT(*) FROM campanhas").fetchone()[0]
        print(f"[init_db] campanhas: {campanhas_count} registros.")
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
