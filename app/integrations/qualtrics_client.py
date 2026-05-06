"""Cliente mínimo Qualtrics Survey API v3 (HTTPS + ``X-API-TOKEN``)."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse

import httpx


@dataclass(frozen=True)
class QualtricsCreds:
    base_url: str
    api_token: str


def canonical_qualtrics_base_url(raw: str) -> str:
    """Normaliza origen del datacenter: HTTPS, sin path ni barra final."""
    s = (raw or "").strip().rstrip("/")
    if not s:
        raise ValueError("base_url vacío.")
    if not s.startswith(("http://", "https://")):
        s = "https://" + s
    parsed = urlparse(s)
    if parsed.scheme != "https":
        raise ValueError("Qualtrics API v3 requiere HTTPS.")
    host = (parsed.hostname or "").lower()
    if not host.endswith(".qualtrics.com") and host != "qualtrics.com":
        raise ValueError(
            "El host debe ser un datacenter Qualtrics (*.qualtrics.com). "
            "Revise la URL en Account Settings → Qualtrics IDs."
        )
    netloc = parsed.netloc.split("@")[-1]
    clean = urlunparse(("https", netloc, "", "", "", "")).rstrip("/")
    return clean


async def verify_qualtrics_credentials(
    creds: QualtricsCreds,
    *,
    timeout_s: float = 20.0,
) -> tuple[bool, int | None, str | None]:
    """
    Comprueba token contra la API (listado mínimo de encuestas).

    Returns:
        (ok, http_status, mensaje_error)
    """
    url = f"{creds.base_url}/API/v3/surveys?pageSize=1"
    headers = {"X-API-TOKEN": creds.api_token, "Accept": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            r = await client.get(url, headers=headers)
    except httpx.HTTPError as e:
        return False, None, str(e)
    if r.status_code == 200:
        return True, r.status_code, None
    detail: str | None
    try:
        body = r.json()
        err = body.get("meta", {}).get("error", {})
        detail = err.get("errorMessage") if isinstance(err, dict) else None
    except Exception:
        detail = (r.text or "")[:300] or None
    return False, r.status_code, detail or r.reason_phrase
