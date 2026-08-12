import re
from typing import Optional

import httpx

VIACEP_URL = "https://viacep.com.br/ws/{cep}/json/"
TIMEOUT_SECONDS = 4.0


def _only_digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def lookup_cep(cep: str) -> Optional[dict]:
    """Resolve um CEP brasileiro para {'cep','cidade','uf'} via ViaCEP.

    Retorna None em qualquer cenario de falha (CEP mal formado, inexistente,
    timeout, erro de rede) — nunca lanca excecao. O chamador trata None como
    'sem correspondencia automatica' e revela campos manuais de cidade/UF.
    """
    digits = _only_digits(cep)
    if len(digits) != 8:
        return None

    try:
        resp = httpx.get(VIACEP_URL.format(cep=digits), timeout=TIMEOUT_SECONDS)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return None

    if not isinstance(data, dict) or data.get("erro"):
        return None

    cidade, uf = data.get("localidade"), data.get("uf")
    if not cidade or not uf:
        return None

    return {"cep": digits, "cidade": cidade, "uf": uf}
