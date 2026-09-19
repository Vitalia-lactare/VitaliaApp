"""Geocodifica as cidades com banco de leite cadastrado (via Nominatim/OSM) e
salva um cache local em data/cidades_geo.json, usado pelo mapa da home.

Roda uma vez (ou quando a base de bancos_de_leite mudar) — nao e chamado em
tempo de requisicao. Respeita o limite de 1 req/s da politica de uso do
Nominatim.
"""
import json
import sqlite3
import time
from pathlib import Path

import httpx

APP_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = APP_ROOT / "data" / "blhs.db"
CACHE_PATH = APP_ROOT / "data" / "cidades_geo.json"

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "VitaliaApp/1.0 (contato: murilomercadante819@gmail.com)"}


def load_cache() -> dict:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return {}


def save_cache(cache: dict) -> None:
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def geocode_cidade(cidade: str, estado: str) -> dict | None:
    params = {
        "city": cidade,
        "state": estado,
        "country": "Brazil",
        "format": "json",
        "limit": 1,
    }
    try:
        resp = httpx.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        print(f"  [erro] {cidade}/{estado}: {exc}")
        return None

    if not data:
        return None

    return {"lat": float(data[0]["lat"]), "lng": float(data[0]["lon"])}


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT DISTINCT cidade, uf, estado FROM bancos_de_leite
        WHERE cidade IS NOT NULL AND uf IS NOT NULL
        ORDER BY estado, cidade
        """
    ).fetchall()
    conn.close()

    cache = load_cache()
    total = len(rows)
    novos = 0

    for i, row in enumerate(rows, 1):
        key = f"{row['cidade']}|{row['uf']}"
        if key in cache:
            continue

        resultado = geocode_cidade(row["cidade"], row["estado"])
        cache[key] = resultado
        novos += 1
        status = "ok" if resultado else "nao encontrado"
        print(f"[{i}/{total}] {row['cidade']}/{row['uf']}: {status}")

        save_cache(cache)
        time.sleep(1.1)

    resolvidos = sum(1 for v in cache.values() if v)
    print(f"\n[geocode_cidades] {resolvidos}/{len(cache)} cidades geocodificadas "
          f"({novos} novas nesta execucao). Cache em {CACHE_PATH}")


if __name__ == "__main__":
    main()
