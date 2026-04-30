"""
Heurísticas GPS desde export tabular Dooblo (OperationData / SimpleExport).

Solo usa coordenadas presentes en columnas reconocibles; sin geocodificar ni
inventar puntos. Política típica en ``FieldPolicySet.config``::

    gps_quality_enabled: true
    gps_max_internal_distance_km: 75
    gps_flag_null_island: true
    gps_column_pairs:           # opcional: fuerza columnas por encuesta / export
      - [CUSTOM_LAT, CUSTOM_LON]
      - { lat: Y_VISITA, lon: X_VISITA }
    gps_invalid_coord_warn_ratio: 0.08
    gps_invalid_coord_error_ratio: 0.20
    gps_internal_span_warn_ratio: 0.08
    gps_internal_span_error_ratio: 0.18

Si ``gps_column_pairs`` está vacío o ausente, se usa la heurística de nombres.
"""

from __future__ import annotations

import math
import re
from typing import Any

from app.integrations.field_dooblo_response_quality import _cell_as_float


def _round_coord(lat: float, lon: float, ndp: int = 5) -> tuple[float, float]:
    return (round(lat, ndp), round(lon, ndp))


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia sobre esfera WGS84 (aprox. Earth radius)."""
    r_km = 6371.0088
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dl = math.radians(lat2 - lat1)
    dg = math.radians(lon2 - lon1)
    a = math.sin(dl / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dg / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
    return r_km * c


def _is_lat_column(lk: str) -> bool:
    if lk.startswith("_") or "longitude" in lk or lk.endswith("lng") or lk.endswith("_lon"):
        return False
    if lk in ("latitude", "lat", "gps_lat", "gpslatitude", "coord_lat"):
        return True
    if lk.endswith("latitude") or lk.endswith("_lat") or lk.startswith("lat_"):
        return True
    if re.search(r"(^|_)lat($|_)", lk):
        return True
    return False


def _is_lon_column(lk: str) -> bool:
    if lk.startswith("_"):
        return False
    if lk in ("longitude", "lon", "lng", "long", "gps_lon", "gpslongitude", "coord_lon", "coord_lng"):
        return True
    if lk.endswith("longitude") or lk.endswith("_lon") or lk.endswith("_lng"):
        return True
    if lk.startswith("lon_") or lk.startswith("lng_"):
        return True
    if re.search(r"(^|_)lon($|_)|(^|_)lng($|_)", lk):
        return True
    return False


def _lon_key_candidates_for_lat(lat_key: str) -> list[str]:
    lk = lat_key.lower()
    cand: list[str] = []
    for repl in (
        ("latitude", "longitude"),
        ("_latitude", "_longitude"),
        ("gpslatitude", "gpslongitude"),
        ("gps_lat", "gps_lon"),
        ("coord_lat", "coord_lon"),
        ("lat_", "lon_"),
        ("_lat", "_lon"),
    ):
        if repl[0] in lk:
            cand.append(lk.replace(repl[0], repl[1]))
    # orden estable y únicos
    out: list[str] = []
    for c in cand:
        if c and c != lk and c not in out:
            out.append(c)
    return out


def _lower_row_index(row: dict[str, Any]) -> dict[str, Any]:
    return {str(k).lower(): v for k, v in row.items()}


def parse_gps_column_pairs_from_policy(policy_config: dict[str, Any]) -> list[tuple[str, str]] | None:
    """
    Lista de (lat_col, lon_col) en minúsculas para lookup case-insensitive en filas.
    Acepta ``gps_column_pairs`` o alias ``gps_lat_lon_column_pairs``.
    """
    raw = policy_config.get("gps_column_pairs")
    if raw is None:
        raw = policy_config.get("gps_lat_lon_column_pairs")
    if not isinstance(raw, list) or not raw:
        return None
    out: list[tuple[str, str]] = []
    for item in raw:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            a, b = str(item[0]).strip(), str(item[1]).strip()
            if a and b:
                out.append((a.lower(), b.lower()))
        elif isinstance(item, dict):
            la = item.get("lat") or item.get("latitude")
            lo = item.get("lon") or item.get("longitude") or item.get("lng")
            if la and lo:
                out.append((str(la).strip().lower(), str(lo).strip().lower()))
    return out or None


def _extract_lat_lon_pairs_heuristic(lm: dict[str, Any]) -> list[tuple[float, float]]:
    lat_keys = [k for k in lm if _is_lat_column(k)]
    used_lon: set[str] = set()
    pairs: list[tuple[float, float]] = []

    for lat_k in sorted(lat_keys):
        lat_v = _cell_as_float(lm.get(lat_k))
        if lat_v is None:
            continue
        lon_k_hit: str | None = None
        lon_v: float | None = None
        for cand in _lon_key_candidates_for_lat(lat_k):
            if cand in lm and cand not in used_lon:
                lv = _cell_as_float(lm[cand])
                if lv is not None:
                    lon_k_hit = cand
                    lon_v = lv
                    break
        if lon_k_hit is not None and lon_v is not None:
            used_lon.add(lon_k_hit)
            pairs.append((lat_v, lon_v))
            continue
        # Sin pareja explícita: emparejar primer lon libre (orden estable)
        for lk in sorted(lm):
            if lk in used_lon or not _is_lon_column(lk):
                continue
            lv = _cell_as_float(lm[lk])
            if lv is not None:
                used_lon.add(lk)
                pairs.append((lat_v, lv))
                break

    return pairs


def extract_lat_lon_pairs(
    row: dict[str, Any],
    *,
    column_pairs: list[tuple[str, str]] | None = None,
) -> list[tuple[float, float]]:
    """Pares (lat, lon); si ``column_pairs`` viene de política, solo esos nombres."""
    lm = _lower_row_index(row)
    if column_pairs:
        out: list[tuple[float, float]] = []
        for lat_k, lon_k in column_pairs:
            lat_v = _cell_as_float(lm.get(lat_k))
            lon_v = _cell_as_float(lm.get(lon_k))
            if lat_v is not None and lon_v is not None:
                out.append((lat_v, lon_v))
        return out
    return _extract_lat_lon_pairs_heuristic(lm)


def _coord_valid(lat: float, lon: float, *, flag_null_island: bool) -> bool:
    if math.isnan(lat) or math.isnan(lon) or math.isinf(lat) or math.isinf(lon):
        return False
    if abs(lat) > 90.0 or abs(lon) > 180.0:
        return False
    if flag_null_island and abs(lat) < 1e-6 and abs(lon) < 1e-6:
        return False
    return True


def summarize_gps_rows(
    rows: list[dict[str, Any]],
    *,
    max_internal_distance_km: float,
    flag_null_island: bool,
    column_pairs: list[tuple[str, str]] | None = None,
) -> dict[str, Any]:
    n = len(rows)
    rows_with_coords = 0
    rows_invalid = 0
    rows_span_over = 0
    km_sample: list[float] = []

    for row in rows:
        pairs = extract_lat_lon_pairs(row, column_pairs=column_pairs)
        if not pairs:
            continue
        rows_with_coords += 1
        invalid_here = any(
            not _coord_valid(lat, lon, flag_null_island=flag_null_island) for lat, lon in pairs
        )
        if invalid_here:
            rows_invalid += 1

        valid_pts = [
            (lat, lon)
            for lat, lon in pairs
            if _coord_valid(lat, lon, flag_null_island=flag_null_island)
        ]
        uniq = {_round_coord(a, b) for a, b in valid_pts}
        if len(uniq) >= 2:
            pts_u = list(uniq)
            max_km = 0.0
            for i in range(len(pts_u)):
                for j in range(i + 1, len(pts_u)):
                    la, lo = pts_u[i]
                    lb, ob = pts_u[j]
                    d = haversine_km(la, lo, lb, ob)
                    max_km = max(max_km, d)
            if len(km_sample) < 8:
                km_sample.append(round(max_km, 3))
            if max_km > max_internal_distance_km:
                rows_span_over += 1

    return {
        "row_count": n,
        "rows_with_coords": rows_with_coords,
        "rows_invalid_coord": rows_invalid,
        "rows_internal_span_over_threshold": rows_span_over,
        "max_internal_distance_km_threshold": max_internal_distance_km,
        "internal_span_km_sample": km_sample,
        "gps_column_pairs": ([[a, b] for a, b in column_pairs] if column_pairs else None),
    }


def gps_params_from_policy(policy_config: dict[str, Any]) -> tuple[float, bool, list[tuple[str, str]] | None]:
    """(max_internal_distance_km, flag_null_island, explicit_column_pairs_or_none)."""
    try:
        d = float(policy_config.get("gps_max_internal_distance_km", 75.0))
    except (TypeError, ValueError):
        d = 75.0
    d = max(1.0, min(d, 20_000.0))
    flag = policy_config.get("gps_flag_null_island", True) is not False
    pairs = parse_gps_column_pairs_from_policy(policy_config)
    return d, flag, pairs
