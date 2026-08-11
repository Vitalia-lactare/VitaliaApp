import sqlite3

CAMPANHAS_SEED = [
    {
        "titulo": "Cada Gota Salva Vidas",
        "resumo": "Campanha permanente de captação de doadoras em todo o Brasil, com foco nos 27 estados atendidos pela nossa rede de bancos de leite.",
        "conteudo": (
            "O leite humano doado é destinado a recém-nascidos prematuros ou de baixo peso "
            "internados em UTIs neonatais da rede pública. Qualquer mãe lactante saudável pode "
            "se tornar doadora — o excedente que seria descartado pode salvar vidas."
        ),
        "imagem_url": None,
        "data_inicio": None,
        "data_fim": None,
        "ordem": 0,
    },
    {
        "titulo": "Agosto Dourado",
        "resumo": "Mês de incentivo ao aleitamento materno: doe leite e ajude bebês prematuros internados em UTIs neonatais da sua região.",
        "conteudo": (
            "Durante todo o mês de agosto reforçamos a campanha de conscientização sobre a "
            "importância do aleitamento materno e da doação de leite humano excedente."
        ),
        "imagem_url": None,
        "data_inicio": "2026-08-01",
        "data_fim": "2026-08-31",
        "ordem": 1,
    },
    {
        "titulo": "Cada Gota Conta em Todo o País",
        "resumo": "Ação nacional conectando doadoras a bancos de leite humano em todos os estados brasileiros.",
        "conteudo": (
            "Ampliamos o alcance da campanha para conectar doadoras de qualquer cidade do Brasil "
            "ao banco de leite mais próximo, usando nossa rede de localização nacional."
        ),
        "imagem_url": None,
        "data_inicio": "2026-10-01",
        "data_fim": "2026-10-31",
        "ordem": 2,
    },
]


def seed_if_empty(conn: sqlite3.Connection) -> None:
    count = conn.execute("SELECT COUNT(*) FROM campanhas").fetchone()[0]
    if count > 0:
        return

    conn.executemany(
        """
        INSERT INTO campanhas (titulo, resumo, conteudo, imagem_url, data_inicio, data_fim, ordem)
        VALUES (:titulo, :resumo, :conteudo, :imagem_url, :data_inicio, :data_fim, :ordem)
        """,
        CAMPANHAS_SEED,
    )
    conn.commit()
