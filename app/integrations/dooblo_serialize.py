"""Serializa respuestas de Dooblo newapi a JSON safe para nuestro proxy Field."""

from __future__ import annotations

import json

import httpx


def httpx_response_to_proxy_dict(
    r: httpx.Response,
    *,
    max_raw_chars: int = 1_000_000,
) -> dict:
    """
    Devuelve upstream_status, content_type, y `data` (JSON parseado) o `raw` (texto).
    Trunca cuerpos enormes (no adecuado para lotes masivos; usar jobs en el futuro).
    """
    ct = (r.headers.get("content-type") or "").lower()
    out: dict = {
        "upstream_status": r.status_code,
        "content_type": r.headers.get("content-type"),
    }
    if "json" in ct:
        try:
            out["data"] = r.json()
        except (json.JSONDecodeError, ValueError):
            out["raw"] = r.text
        return out
    text = r.text
    if len(text) > max_raw_chars:
        out["raw"] = text[:max_raw_chars]
        out["raw_truncated"] = True
    else:
        out["raw"] = text
    return out
