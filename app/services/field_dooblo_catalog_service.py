"""Catálogo remoto Dooblo (Customers, CustomerProjects, ProjectSurveys): paginación y filtro q en servidor."""

from __future__ import annotations

import asyncio
import json
import logging

from typing import Any

import httpx
from fastapi import HTTPException

from app.integrations import dooblo_client as dooblo
from app.integrations.dooblo_catalog_normalize import (
    normalize_customer_projects_payload,
    normalize_customer_projects_xml,
    normalize_customers_payload,
    normalize_project_surveys_payload,
)
from app.models.dooblo_catalog_model import (
    FailedCustomerEntry,
    OrganizationStudioProjectsCatalogPage,
    RemoteFieldCatalogItem,
    RemoteFieldCatalogPage,
)

log = logging.getLogger(__name__)

_REASON_MAX_LEN = 3500

_JSON_ACCEPT = {"Accept": "application/json, text/xml;q=0.9, */*;q=0.8"}

_MAX_429_RETRIES = 6


async def _catalog_dooblo_get(
    operation: str,
    params: dict[str, Any] | None,
    *,
    creds: dooblo.DoobloCreds,
) -> httpx.Response:
    """GET catálogo con reintentos ante HTTP 429 (SurveyToGo ~2 req/s)."""
    backoff = 1.1
    last: httpx.Response | None = None
    for attempt in range(_MAX_429_RETRIES):
        last = await dooblo.dooblo_get(
            operation,
            params,
            creds=creds,
            extra_headers=_JSON_ACCEPT,
        )
        if last.status_code != 429:
            return last
        await asyncio.sleep(backoff)
        backoff = min(backoff * 1.65, 9.0)
    assert last is not None
    return last


def _truncate_reason(s: str, max_len: int = _REASON_MAX_LEN) -> str:
    t = (s or "").strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 3] + "..."


def _response_json_snippet(r: httpx.Response, limit: int = 800) -> str:
    t = (r.text or "").strip()
    return t[:limit] if t else "(cuerpo vacío)"


def _customers_raw_row_estimate(data: Any) -> int:
    """Cuenta filas obvias en payload Customers antes de normalizar (detectar mismatch)."""
    if isinstance(data, list):
        return len(data)
    if not isinstance(data, dict):
        return 0
    best = 0
    for key in ("Customers", "customers", "CustomerList", "d", "result"):
        v = data.get(key)
        if isinstance(v, list):
            best = max(best, len(v))
        elif isinstance(v, dict):
            for nk in ("Customer", "Customers", "Items", "Item", "Rows"):
                nested = v.get(nk)
                if isinstance(nested, list):
                    best = max(best, len(nested))
                elif isinstance(nested, dict):
                    best = max(best, 1)
    return best


def _parse_customer_projects_response(r: httpx.Response) -> list[dict[str, str]]:
    """Interpreta JSON y, si hace falta, XML (SurveyToGo puede devolver cualquiera)."""
    ct = (r.headers.get("content-type") or "").lower()
    body = r.text or ""
    rows: list[dict[str, str]] = []
    if "json" in ct and body.strip():
        try:
            data = json.loads(body)
            rows = normalize_customer_projects_payload(data)
        except (json.JSONDecodeError, TypeError, ValueError):
            rows = []
    if not rows and body.strip().startswith("{"):
        try:
            rows = normalize_customer_projects_payload(json.loads(body))
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    if not rows and body.strip().startswith("<"):
        rows = normalize_customer_projects_xml(body)
    return rows


async def _fetch_customer_projects_normalized(
    creds: dooblo.DoobloCreds,
    customer_surveytogo_id: str,
    *,
    customer_display_name: str | None = None,
) -> tuple[list[dict[str, str]], str | None]:
    """
    GET CustomerProjects con CustomerID y CustomerId.
    Devuelve ([], None) si la API respondió 200 pero sin proyectos (válido).
    Devuelve ([], mensaje) ante errores HTTP / parse / excepciones de red.
    """
    disp = customer_display_name or ""
    errors: list[str] = []
    saw_soft_empty = False
    endpoint = "CustomerProjects"

    for pname in ("CustomerID", "CustomerId"):
        try:
            r2 = await _catalog_dooblo_get(
                endpoint,
                {pname: customer_surveytogo_id},
                creds=creds,
            )
        except Exception as exc:
            log.warning(
                "dooblo_org_catalog %s exception customer_id=%s customer_name=%r "
                "query_param=%s error=%r",
                endpoint,
                customer_surveytogo_id,
                disp,
                pname,
                exc,
                exc_info=True,
            )
            errors.append(f"{pname}: request exception {exc!r}")
            continue

        ct2 = (r2.headers.get("content-type") or "").lower()
        body = r2.text or ""
        snip = body[:600].replace("\n", " ") if body else ""
        log.info(
            "dooblo_org_catalog %s customer_id=%s customer_name=%r query_param=%s "
            "http_status=%s content_type=%r body_prefix=%r",
            endpoint,
            customer_surveytogo_id,
            disp,
            pname,
            r2.status_code,
            ct2,
            snip,
        )

        if r2.status_code >= 400:
            errors.append(f"{pname}: HTTP {r2.status_code} {_response_json_snippet(r2)}")
            continue

        try:
            rows = _parse_customer_projects_response(r2)
        except Exception as exc:
            log.warning(
                "dooblo_org_catalog %s parse exception customer_id=%s query_param=%s error=%r",
                endpoint,
                customer_surveytogo_id,
                pname,
                exc,
                exc_info=True,
            )
            errors.append(f"{pname}: parse exception {exc!r}")
            continue

        if rows:
            return rows, None

        if r2.status_code == 200:
            if "json" in ct2 or body.strip().startswith("<") or body.strip().startswith("{"):
                saw_soft_empty = True
            else:
                errors.append(f"{pname}: respuesta 200 con tipo no reconocido ({ct2})")

    if saw_soft_empty:
        return [], None
    return [], "; ".join(errors) if errors else "CustomerProjects sin datos interpretables"



def _looks_like_standalone_email_not_customer_id(s: str) -> bool:
    """Errores típicos: pegar solo el correo del usuario Studio en lugar del Customer ID."""
    t = s.strip()
    if "/" in t:
        return False
    if "@" not in t:
        return False
    _, sep, after = t.partition("@")
    if sep != "@":
        return False
    return "." in after


def _looks_like_surveytogo_rest_api_username(s: str) -> bool:
    """Usuario API REST SurveyToGo = REST_API_KEY/usuario (suele incluir '@'); va en credenciales, no en Customer ID."""
    t = s.strip()
    if "/" not in t:
        return False
    left, _, right = t.partition("/")
    left = left.strip()
    right = right.strip()
    if not left or not right:
        return False
    return "-" in left and len(left) >= 12


def _paginate_filtered_rows(
    rows: list[dict[str, str]],
    *,
    page: int,
    page_size: int,
    q: str | None,
) -> tuple[list[dict[str, str]], int, int, int, bool]:
    qn = (q or "").strip().lower()
    if qn:
        rows = [
            x
            for x in rows
            if qn in x["title"].lower() or qn in x["external_id"].lower()
        ]
    total = len(rows)
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    start = (page - 1) * page_size
    chunk = rows[start : start + page_size]
    has_more = start + page_size < total
    return chunk, total, page, page_size, has_more


def _paginate_filtered_org_project_rows(
    rows: list[dict[str, str]],
    *,
    page: int,
    page_size: int,
    q: str | None,
) -> tuple[list[dict[str, str]], int, int, int, bool]:
    """Filtra por q sobre id, título y datos de cliente SurveyToGo."""
    qn = (q or "").strip().lower()
    if qn:
        filtered: list[dict[str, str]] = []
        for x in rows:
            blob = " ".join(
                [
                    x["external_id"],
                    x["title"],
                    x.get("studio_customer_id") or "",
                    x.get("studio_customer_name") or "",
                ]
            ).lower()
            if qn in blob:
                filtered.append(x)
        rows = filtered
    total = len(rows)
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    start = (page - 1) * page_size
    chunk = rows[start : start + page_size]
    has_more = start + page_size < total
    return chunk, total, page, page_size, has_more


async def list_dooblo_organization_studio_projects_catalog(
    creds: dooblo.DoobloCreds,
    *,
    page: int = 1,
    page_size: int = 25,
    q: str | None = None,
    max_customers: int = 120,
) -> OrganizationStudioProjectsCatalogPage:
    """
    Agrega proyectos Studio visibles para el usuario API: Customers → CustomerProjects por cliente.
    Respeta ~2 req/s de SurveyToGo con pausa entre llamadas.
    Un cliente fallido no aborta el barrido: se devuelve en `failed_customers`.
    """
    mc = min(max(1, max_customers), 200)

    r = await _catalog_dooblo_get("Customers", None, creds=creds)
    if r.status_code >= 400:
        snippet = (r.text or "")[:2000]
        raise HTTPException(
            status_code=502,
            detail=f"Dooblo Customers falló ({r.status_code}). {snippet}",
        )
    ct = (r.headers.get("content-type") or "").lower()
    if "json" not in ct:
        raise HTTPException(
            status_code=502,
            detail="Dooblo devolvió un cuerpo no JSON para Customers (¿formato XML?).",
        )
    try:
        data = r.json()
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Respuesta JSON inválida de Customers.",
        ) from exc

    customers = normalize_customers_payload(data)[:mc]
    raw_rows_hint = _customers_raw_row_estimate(data)
    if not customers and raw_rows_hint > 0:
        keys = list(data.keys())[:40] if isinstance(data, dict) else []
        raise HTTPException(
            status_code=424,
            detail=(
                "SurveyToGo devolvió datos en Customers pero no se pudieron interpretar las filas "
                f"(aprox. {raw_rows_hint} entrada(s) detectada(s)). "
                f"Claves JSON: {keys}. "
                "Copie la respuesta del REST API Testbed (operation Customers) para soporte."
            ),
        )

    merged: list[dict[str, str]] = []
    seen_project: set[str] = set()
    failed_customers: list[FailedCustomerEntry] = []

    for idx, cust in enumerate(customers):
        cid_cust = cust["external_id"].strip()
        cname = cust["title"].strip()
        if idx > 0:
            await asyncio.sleep(0.55)

        try:
            rows_cp, err_cp = await _fetch_customer_projects_normalized(
                creds,
                cid_cust,
                customer_display_name=cname,
            )
        except Exception as exc:
            log.exception(
                "dooblo_org_catalog iteration unexpected customer_id=%s customer_name=%r",
                cid_cust,
                cname,
            )
            failed_customers.append(
                FailedCustomerEntry(
                    customer_id=cid_cust,
                    customer_name=cname or None,
                    reason=_truncate_reason(f"unexpected: {exc!r}"),
                )
            )
            continue

        if err_cp:
            failed_customers.append(
                FailedCustomerEntry(
                    customer_id=cid_cust,
                    customer_name=cname or None,
                    reason=_truncate_reason(err_cp),
                )
            )

        for proj in rows_cp:
            eid = proj["external_id"].strip()
            if eid in seen_project:
                continue
            seen_project.add(eid)
            merged.append(
                {
                    "external_id": eid,
                    "title": proj["title"],
                    "studio_customer_id": cid_cust,
                    "studio_customer_name": cname,
                }
            )

    chunk, total, page, page_size, has_more = _paginate_filtered_org_project_rows(
        merged, page=page, page_size=page_size, q=q
    )

    items = [
        RemoteFieldCatalogItem(
            external_id=x["external_id"],
            title=x["title"],
            kind="studio_project",
            studio_customer_id=x.get("studio_customer_id"),
            studio_customer_name=x.get("studio_customer_name"),
        )
        for x in chunk
    ]

    return OrganizationStudioProjectsCatalogPage(
        provider="dooblo",
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more,
        query_applied=(q or "").strip() or None,
        failed_customers=failed_customers,
    )


async def list_dooblo_customers_catalog(
    creds: dooblo.DoobloCreds,
    *,
    page: int = 1,
    page_size: int = 25,
    q: str | None = None,
) -> RemoteFieldCatalogPage:
    """Operation `Customers`: clientes SurveyToGo visibles para el usuario API (Basic auth)."""
    r = await _catalog_dooblo_get("Customers", None, creds=creds)
    if r.status_code >= 400:
        snippet = (r.text or "")[:2000]
        raise HTTPException(
            status_code=502,
            detail=f"Dooblo Customers falló ({r.status_code}). {snippet}",
        )
    ct = (r.headers.get("content-type") or "").lower()
    if "json" not in ct:
        raise HTTPException(
            status_code=502,
            detail="Dooblo devolvió un cuerpo no JSON para Customers (¿formato XML?).",
        )
    try:
        data = r.json()
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Respuesta JSON inválida de Customers.",
        ) from exc

    rows = normalize_customers_payload(data)
    raw_rows_hint = _customers_raw_row_estimate(data)
    if not rows and raw_rows_hint > 0:
        keys = list(data.keys())[:40] if isinstance(data, dict) else []
        raise HTTPException(
            status_code=424,
            detail=(
                "SurveyToGo devolvió datos en Customers pero no se pudieron interpretar las filas "
                f"(aprox. {raw_rows_hint} entrada(s)). Claves JSON: {keys}."
            ),
        )
    chunk, total, page, page_size, has_more = _paginate_filtered_rows(
        rows, page=page, page_size=page_size, q=q
    )

    items = [
        RemoteFieldCatalogItem(
            external_id=x["external_id"],
            title=x["title"],
            kind="customer",
        )
        for x in chunk
    ]

    return RemoteFieldCatalogPage(
        provider="dooblo",
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more,
        query_applied=(q or "").strip() or None,
    )


async def list_dooblo_customer_projects_catalog(
    creds: dooblo.DoobloCreds,
    *,
    customer_id: str,
    page: int = 1,
    page_size: int = 25,
    q: str | None = None,
) -> RemoteFieldCatalogPage:
    """
    Operation `CustomerProjects`: proyectos Studio de **un** cliente SurveyToGo (requiere CustomerID).
    Ver documentación SurveyToGo REST API.
    """
    cid = customer_id.strip()
    if not cid:
        raise HTTPException(status_code=400, detail="customer_id es obligatorio.")
    if _looks_like_surveytogo_rest_api_username(cid):
        raise HTTPException(
            status_code=400,
            detail=(
                "customer_id parece el usuario API completo de SurveyToGo (REST_API_KEY/usuario). "
                "Eso debe guardarse solo en credenciales (usuario REST key). Aquí use el Customer ID "
                "del cliente devuelto por la operation Customers o Studio."
            ),
        )
    if _looks_like_standalone_email_not_customer_id(cid):
        raise HTTPException(
            status_code=400,
            detail=(
                "customer_id parece solo un correo. Use el identificador de cliente SurveyToGo "
                "(Customer ID), no el email del usuario API."
            ),
        )

    rows, err = await _fetch_customer_projects_normalized(creds, cid)
    if err:
        raise HTTPException(status_code=424, detail=err)

    chunk, total, page, page_size, has_more = _paginate_filtered_rows(
        rows, page=page, page_size=page_size, q=q
    )

    items = [
        RemoteFieldCatalogItem(
            external_id=x["external_id"],
            title=x["title"],
            kind="studio_project",
        )
        for x in chunk
    ]

    return RemoteFieldCatalogPage(
        provider="dooblo",
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more,
        query_applied=(q or "").strip() or None,
    )


async def list_dooblo_project_surveys_catalog(
    creds: dooblo.DoobloCreds,
    *,
    project_id: str,
    page: int = 1,
    page_size: int = 25,
    q: str | None = None,
) -> RemoteFieldCatalogPage:
    pid = project_id.strip()
    if not pid:
        raise HTTPException(status_code=400, detail="project_id es obligatorio.")

    r = await dooblo.dooblo_get(
        "ProjectSurveys",
        {"ProjectID": pid},
        creds=creds,
        extra_headers=_JSON_ACCEPT,
    )
    if r.status_code >= 400:
        snippet = (r.text or "")[:2000]
        raise HTTPException(
            status_code=502,
            detail=f"Dooblo ProjectSurveys falló ({r.status_code}). {snippet}",
        )
    ct = (r.headers.get("content-type") or "").lower()
    if "json" not in ct:
        raise HTTPException(
            status_code=502,
            detail="Dooblo devolvió un cuerpo no JSON para ProjectSurveys.",
        )
    try:
        data = r.json()
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Respuesta JSON inválida de ProjectSurveys.",
        ) from exc

    rows = normalize_project_surveys_payload(data)
    chunk, total, page, page_size, has_more = _paginate_filtered_rows(
        rows, page=page, page_size=page_size, q=q
    )

    items = [
        RemoteFieldCatalogItem(
            external_id=x["external_id"],
            title=x["title"],
            kind="survey",
        )
        for x in chunk
    ]

    return RemoteFieldCatalogPage(
        provider="dooblo",
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more,
        query_applied=(q or "").strip() or None,
    )
