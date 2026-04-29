"""Normaliza respuestas JSON de la newapi Dooblo (CustomerProjects, etc.) a items estables."""

from __future__ import annotations

from typing import Any, Iterable

_ID_KEYS = (
    "ProjectId",
    "ProjectID",
    "CustomerProjectId",
    "StudioProjectId",
    "ID",
    "Id",
    "id",
)
_NAME_KEYS = (
    "ProjectName",
    "Name",
    "Title",
    "Subject",
    "Description",
)

_SURVEY_ID_KEYS = (
    "SurveyID",
    "SurveyId",
    "surveyID",
    "surveyId",
    "Sid",
    "SurveySid",
    "ID",
    "Id",
    "id",
)
_SURVEY_TITLE_KEYS = (
    "SurveyName",
    "Name",
    "Subject",
    "Title",
    "Description",
)

_CUSTOMER_ID_KEYS = (
    "CustomerID",
    "CustomerId",
    "customerID",
    "customerId",
    "ID",
    "Id",
    "id",
)
_CUSTOMER_NAME_KEYS = (
    "CustomerName",
    "Name",
    "CompanyName",
    "Title",
    "Subject",
    "Description",
)


def _pick_first_str(obj: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    lower_map = {str(k).lower(): k for k in obj}
    for k in keys:
        if k in obj and obj[k] not in (None, ""):
            return str(obj[k]).strip()
        lk = k.lower()
        if lk in lower_map:
            raw = obj.get(lower_map[lk])
            if raw not in (None, ""):
                return str(raw).strip()
    return None


def _row_to_item(row: Any) -> tuple[str, str] | None:
    if not isinstance(row, dict):
        return None
    rid = _pick_first_str(row, _ID_KEYS)
    name = _pick_first_str(row, _NAME_KEYS) or "(sin nombre)"
    if not rid:
        return None
    return rid, name


def _survey_row_to_item(row: Any) -> tuple[str, str] | None:
    if not isinstance(row, dict):
        return None
    rid = _pick_first_str(row, _SURVEY_ID_KEYS)
    name = _pick_first_str(row, _SURVEY_TITLE_KEYS) or "(sin nombre)"
    if not rid:
        return None
    return rid, name


def _customer_row_to_item(row: Any) -> tuple[str, str] | None:
    if not isinstance(row, dict):
        return None
    rid = _pick_first_str(row, _CUSTOMER_ID_KEYS)
    name = _pick_first_str(row, _CUSTOMER_NAME_KEYS) or "(sin nombre)"
    if not rid:
        return None
    return rid, name


def _iter_nested_lists(obj: Any, depth: int = 0, max_depth: int = 8) -> Iterable[list[Any]]:
    if depth > max_depth:
        return
    if isinstance(obj, list):
        yield obj
        for x in obj:
            yield from _iter_nested_lists(x, depth + 1, max_depth)
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _iter_nested_lists(v, depth + 1, max_depth)


def normalize_customer_projects_payload(data: Any) -> list[dict[str, str]]:
    """
    Intenta extraer pares (external_id, title) de la respuesta de CustomerProjects u homólogos.
    Si la forma del JSON cambia, ampliar heurísticas aquí (sin romper el contrato API Field).
    """
    seen: set[str] = set()
    out: list[dict[str, str]] = []

    candidates: list[list[Any]] = []
    if isinstance(data, list):
        candidates.append(data)
    elif isinstance(data, dict):
        for key in (
            "Projects",
            "ProjectList",
            "CustomerProjects",
            "Items",
            "Data",
            "Rows",
            "projects",
        ):
            inner = data.get(key)
            if isinstance(inner, list):
                candidates.append(inner)
        # algunos envoltorios devuelven un solo objeto
        single = _row_to_item(data)
        if single:
            eid, title = single
            if eid not in seen:
                seen.add(eid)
                out.append({"external_id": eid, "title": title})

    for lst in candidates:
        for row in lst:
            parsed = _row_to_item(row)
            if parsed:
                eid, title = parsed
                if eid not in seen:
                    seen.add(eid)
                    out.append({"external_id": eid, "title": title})

    # barrido profundo por si la lista útil está anidada (listas de listas)
    if not out and data is not None:
        for lst in _iter_nested_lists(data):
            for row in lst:
                parsed = _row_to_item(row)
                if parsed:
                    eid, title = parsed
                    if eid not in seen:
                        seen.add(eid)
                        out.append({"external_id": eid, "title": title})
                if len(out) > 5000:
                    break

    return out


def normalize_customers_payload(data: Any) -> list[dict[str, str]]:
    """
    Extrae (customer id, etiqueta) de Customers u homólogos en JSON heterogéneo.
    """
    seen: set[str] = set()
    out: list[dict[str, str]] = []

    candidates: list[list[Any]] = []
    if isinstance(data, list):
        candidates.append(data)
    elif isinstance(data, dict):
        for key in (
            "Customers",
            "CustomerList",
            "Items",
            "Data",
            "Rows",
            "customers",
        ):
            inner = data.get(key)
            if isinstance(inner, list):
                candidates.append(inner)
        single = _customer_row_to_item(data)
        if single:
            eid, title = single
            if eid not in seen:
                seen.add(eid)
                out.append({"external_id": eid, "title": title})

    for lst in candidates:
        for row in lst:
            parsed = _customer_row_to_item(row)
            if parsed:
                eid, title = parsed
                if eid not in seen:
                    seen.add(eid)
                    out.append({"external_id": eid, "title": title})

    if not out and data is not None:
        for lst in _iter_nested_lists(data):
            for row in lst:
                parsed = _customer_row_to_item(row)
                if parsed:
                    eid, title = parsed
                    if eid not in seen:
                        seen.add(eid)
                        out.append({"external_id": eid, "title": title})
                if len(out) > 5000:
                    break

    return out


def normalize_project_surveys_payload(data: Any) -> list[dict[str, str]]:
    """
    Extrae (survey id, título) de ProjectSurveys u homólogos en JSON heterogéneo.
    """
    seen: set[str] = set()
    out: list[dict[str, str]] = []

    candidates: list[list[Any]] = []
    if isinstance(data, list):
        candidates.append(data)
    elif isinstance(data, dict):
        for key in (
            "Surveys",
            "SurveyList",
            "ProjectSurveys",
            "Items",
            "Data",
            "Rows",
            "surveys",
        ):
            inner = data.get(key)
            if isinstance(inner, list):
                candidates.append(inner)
        single = _survey_row_to_item(data)
        if single:
            eid, title = single
            if eid not in seen:
                seen.add(eid)
                out.append({"external_id": eid, "title": title})

    for lst in candidates:
        for row in lst:
            parsed = _survey_row_to_item(row)
            if parsed:
                eid, title = parsed
                if eid not in seen:
                    seen.add(eid)
                    out.append({"external_id": eid, "title": title})

    if not out and data is not None:
        for lst in _iter_nested_lists(data):
            for row in lst:
                parsed = _survey_row_to_item(row)
                if parsed:
                    eid, title = parsed
                    if eid not in seen:
                        seen.add(eid)
                        out.append({"external_id": eid, "title": title})
                if len(out) > 5000:
                    break

    return out
