"""Catálogo remoto Dooblo (Customers, CustomerProjects, ProjectSurveys): paginación y filtro q en servidor."""

from __future__ import annotations

import asyncio

from fastapi import HTTPException

from app.integrations import dooblo_client as dooblo
from app.integrations.dooblo_catalog_normalize import (
    normalize_customer_projects_payload,
    normalize_customers_payload,
    normalize_project_surveys_payload,
)
from app.models.dooblo_catalog_model import RemoteFieldCatalogItem, RemoteFieldCatalogPage

_JSON_ACCEPT = {"Accept": "application/json, text/xml;q=0.9, */*;q=0.8"}


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
) -> RemoteFieldCatalogPage:
    """
    Agrega proyectos Studio visibles para el usuario API: Customers → CustomerProjects por cliente.
    Respeta ~2 req/s de SurveyToGo con pausa entre llamadas.
    """
    mc = min(max(1, max_customers), 200)

    r = await dooblo.dooblo_get(
        "Customers",
        None,
        creds=creds,
        extra_headers=_JSON_ACCEPT,
    )
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
    merged: list[dict[str, str]] = []
    seen_project: set[str] = set()

    for idx, cust in enumerate(customers):
        cid_cust = cust["external_id"].strip()
        cname = cust["title"].strip()
        if idx > 0:
            await asyncio.sleep(0.55)

        r2 = await dooblo.dooblo_get(
            "CustomerProjects",
            {"CustomerID": cid_cust},
            creds=creds,
            extra_headers=_JSON_ACCEPT,
        )
        if r2.status_code >= 400:
            continue
        ct2 = (r2.headers.get("content-type") or "").lower()
        if "json" not in ct2:
            continue
        try:
            pdata = r2.json()
        except Exception:
            continue

        for proj in normalize_customer_projects_payload(pdata):
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

    return RemoteFieldCatalogPage(
        provider="dooblo",
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more,
        query_applied=(q or "").strip() or None,
    )


async def list_dooblo_customers_catalog(
    creds: dooblo.DoobloCreds,
    *,
    page: int = 1,
    page_size: int = 25,
    q: str | None = None,
) -> RemoteFieldCatalogPage:
    """Operation `Customers`: clientes SurveyToGo visibles para el usuario API (Basic auth)."""
    r = await dooblo.dooblo_get(
        "Customers",
        None,
        creds=creds,
        extra_headers=_JSON_ACCEPT,
    )
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

    r = await dooblo.dooblo_get(
        "CustomerProjects",
        {"CustomerID": cid},
        creds=creds,
        extra_headers=_JSON_ACCEPT,
    )
    if r.status_code >= 400:
        snippet = (r.text or "")[:2000]
        raise HTTPException(
            status_code=502,
            detail=f"Dooblo CustomerProjects falló ({r.status_code}). {snippet}",
        )
    ct = (r.headers.get("content-type") or "").lower()
    if "json" not in ct:
        raise HTTPException(
            status_code=502,
            detail="Dooblo devolvió un cuerpo no JSON para CustomerProjects.",
        )
    try:
        data = r.json()
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Respuesta JSON inválida de CustomerProjects.",
        ) from exc

    rows = normalize_customer_projects_payload(data)
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
