"""Catálogo remoto Dooblo (Customers, CustomerProjects, ProjectSurveys): paginación y filtro q en servidor."""

from fastapi import HTTPException

from app.integrations import dooblo_client as dooblo
from app.integrations.dooblo_catalog_normalize import (
    normalize_customer_projects_payload,
    normalize_customers_payload,
    normalize_project_surveys_payload,
)
from app.models.dooblo_catalog_model import RemoteFieldCatalogItem, RemoteFieldCatalogPage

_JSON_ACCEPT = {"Accept": "application/json, text/xml;q=0.9, */*;q=0.8"}


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
