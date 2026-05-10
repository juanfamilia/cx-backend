"""Motor determinístico Auto QA bootstrap — QA_RULE_001 … QA_RULE_005.

Contrato de hallazgos: ``source="instrument_qa_runtime"`` (ver L — anexo estructural).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any

QA_RULESET_BOOTSTRAP_V1 = "QA_RULESET_BOOTSTRAP_V1"
QA_SOURCE = "instrument_qa_runtime"


@dataclass(frozen=True)
class InstrumentQAFinding:
    rule_id: str
    severity: str  # STOP | FIX_NOW | MONITOR
    item_id: str | None
    block_id: str | None
    message: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "source": QA_SOURCE,
            "ruleset_version": QA_RULESET_BOOTSTRAP_V1,
            "rule_id": self.rule_id,
            "severity": self.severity,
            "item_id": self.item_id,
            "block_id": self.block_id,
            "message": self.message,
        }


_TERMINAL_TARGETS = frozenset(
    {
        "END",
        "__END__",
        "TERM",
        "TERMINATE",
        "SCREEN_OUT",
        "COMPLETE",
    }
)


def _norm_text(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    return s.lower()


def _iter_blocks_items(spec: dict[str, Any]) -> list[tuple[str | None, dict[str, Any]]]:
    out: list[tuple[str | None, dict[str, Any]]] = []
    blocks = spec.get("blocks")
    if not isinstance(blocks, list):
        return out
    for block in blocks:
        if not isinstance(block, dict):
            continue
        bid = block.get("block_id")
        bid_str = str(bid) if bid is not None else None
        items = block.get("items")
        if not isinstance(items, list):
            continue
        for raw in items:
            if isinstance(raw, dict) and raw.get("item_id"):
                out.append((bid_str, raw))
    return out


def _collect_item_ids(spec: dict[str, Any]) -> list[str]:
    return [str(it["item_id"]) for _, it in _iter_blocks_items(spec) if it.get("item_id")]


def _rule_001_double_barrel(block_id: str | None, item: dict[str, Any]) -> InstrumentQAFinding | None:
    text = item.get("text")
    if not isinstance(text, str) or len(text.strip()) < 12:
        return None
    t = text.strip()
    # Coordinación " … y … " típica de doble varilla en español.
    if re.search(r"\s+y\s+", t, flags=re.IGNORECASE):
        return InstrumentQAFinding(
            rule_id="QA_RULE_001",
            severity="FIX_NOW",
            item_id=str(item.get("item_id")),
            block_id=block_id,
            message="Posible doble varilla (coordinación ' y '): separar constructos de medición en ítems distintos.",
        )
    if re.search(r"(?i)\band\b", t):
        return InstrumentQAFinding(
            rule_id="QA_RULE_001",
            severity="FIX_NOW",
            item_id=str(item.get("item_id")),
            block_id=block_id,
            message="Posible doble varilla (coordinación 'and'): separar en ítems distintos.",
        )
    if t.count("?") >= 2:
        return InstrumentQAFinding(
            rule_id="QA_RULE_001",
            severity="FIX_NOW",
            item_id=str(item.get("item_id")),
            block_id=block_id,
            message="Varias interrogaciones en un mismo ítem: revisar doble varilla o sobrecarga cognitiva.",
        )
    return None


# Lista controlada bilingüe — expansión versionada con el ruleset.
_LEADING_LEXICON_ES = (
    "obviamente",
    "sin duda",
    "indiscutiblemente",
    "la marca líder",
    "marca líder",
    "la mejor opción",
    "mejor opción para usted",
    "todos sabemos",
    "todo el mundo sabe",
    "number one",
    "número uno",
)
_LEADING_LEXICON_EN = (
    "obviously",
    "clearly the best",
    "everyone knows",
    "leading brand",
    "undisputed",
    "without a doubt",
    "best choice for you",
)


def _rule_002_leading(block_id: str | None, item: dict[str, Any]) -> InstrumentQAFinding | None:
    text = item.get("text")
    if not isinstance(text, str) or not text.strip():
        return None
    low = _norm_text(text)
    for phrase in _LEADING_LEXICON_ES + _LEADING_LEXICON_EN:
        if phrase in low:
            return InstrumentQAFinding(
                rule_id="QA_RULE_002",
                severity="STOP",
                item_id=str(item.get("item_id")),
                block_id=block_id,
                message=f"Posible redacción sesgada / leading detectada (patrón controlado: «{phrase}»).",
            )
    return None


def _rule_003_quotas(block_id: str | None, item: dict[str, Any]) -> InstrumentQAFinding | None:
    resp = item.get("response")
    if not isinstance(resp, dict) or resp.get("type") != "quotas":
        return None
    strata = resp.get("strata")
    if not isinstance(strata, list) or not strata:
        return InstrumentQAFinding(
            rule_id="QA_RULE_003",
            severity="STOP",
            item_id=str(item.get("item_id")),
            block_id=block_id,
            message="Cuotas declaradas sin estratos válidos.",
        )
    names: list[str] = []
    total = 0.0
    for row in strata:
        if not isinstance(row, dict):
            continue
        name = row.get("name")
        pct = row.get("target_pct")
        if isinstance(name, str) and name.strip():
            names.append(name.strip())
        if isinstance(pct, (int, float)):
            total += float(pct)
        else:
            return InstrumentQAFinding(
                rule_id="QA_RULE_003",
                severity="STOP",
                item_id=str(item.get("item_id")),
                block_id=block_id,
                message="Cuota con target_pct no numérico.",
            )
    if len(names) != len(set(names)):
        return InstrumentQAFinding(
            rule_id="QA_RULE_003",
            severity="STOP",
            item_id=str(item.get("item_id")),
            block_id=block_id,
            message="Nombres de estratos duplicados en cuotas.",
        )
    if abs(total - 100.0) > 0.02:
        return InstrumentQAFinding(
            rule_id="QA_RULE_003",
            severity="STOP",
            item_id=str(item.get("item_id")),
            block_id=block_id,
            message=f"Distribución muestral cerrada: suma de target_pct es {total:.2f}% (se espera 100%).",
        )
    return None


def _rule_004_scale(block_id: str | None, item: dict[str, Any]) -> InstrumentQAFinding | None:
    resp = item.get("response")
    if not isinstance(resp, dict):
        return None
    rtype = resp.get("type")
    labels = resp.get("labels")
    if not isinstance(labels, list) or len(labels) == 0:
        return None

    if rtype == "likert":
        sp = resp.get("scale_points")
        if isinstance(sp, int) and len(labels) != sp:
            return InstrumentQAFinding(
                rule_id="QA_RULE_004",
                severity="FIX_NOW",
                item_id=str(item.get("item_id")),
                block_id=block_id,
                message=f"Escala Likert: scale_points={sp} pero etiquetas={len(labels)}.",
            )
    elif rtype == "numeric":
        mn = resp.get("min")
        mx = resp.get("max")
        if isinstance(mn, (int, float)) and isinstance(mx, (int, float)):
            span_pts = int(mx) - int(mn) + 1
            if int(mn) != mn or int(mx) != mx:
                return InstrumentQAFinding(
                    rule_id="QA_RULE_004",
                    severity="FIX_NOW",
                    item_id=str(item.get("item_id")),
                    block_id=block_id,
                    message="Escala numérica no entera: revisar coherencia puntos vs etiquetas manualmente.",
                )
            if len(labels) != span_pts:
                return InstrumentQAFinding(
                    rule_id="QA_RULE_004",
                    severity="FIX_NOW",
                    item_id=str(item.get("item_id")),
                    block_id=block_id,
                    message=f"Escala numérica [{mn},{mx}] ⇒ {span_pts} puntos, pero hay {len(labels)} etiquetas.",
                )
    return None


def _detect_cycle(nodes: set[str], edges: list[tuple[str, str]]) -> bool:
    adj: dict[str, list[str]] = {n: [] for n in nodes}
    for u, v in edges:
        if u in nodes and v in nodes:
            adj.setdefault(u, []).append(v)

    visited: set[str] = set()
    rec_stack: set[str] = set()

    def dfs(u: str) -> bool:
        visited.add(u)
        rec_stack.add(u)
        for v in adj.get(u, []):
            if v not in visited:
                if dfs(v):
                    return True
            elif v in rec_stack:
                return True
        rec_stack.remove(u)
        return False

    for n in nodes:
        if n not in visited:
            if dfs(n):
                return True
    return False


def _rule_005_branching(spec: dict[str, Any], item_ids: list[str]) -> list[InstrumentQAFinding]:
    findings: list[InstrumentQAFinding] = []
    item_set = set(item_ids)
    branching = spec.get("branching")
    if not isinstance(branching, dict):
        return findings
    edges_raw = branching.get("edges")
    if not isinstance(edges_raw, list) or not edges_raw:
        return findings

    parsed: list[tuple[str, str]] = []
    for i, e in enumerate(edges_raw):
        if not isinstance(e, dict):
            findings.append(
                InstrumentQAFinding(
                    rule_id="QA_RULE_005",
                    severity="STOP",
                    item_id=None,
                    block_id=None,
                    message=f"Arista de routing #{i + 1} no es un objeto válido.",
                )
            )
            continue
        f = e.get("from")
        t = e.get("to")
        if not isinstance(f, str) or not isinstance(t, str):
            findings.append(
                InstrumentQAFinding(
                    rule_id="QA_RULE_005",
                    severity="STOP",
                    item_id=None,
                    block_id=None,
                    message=f"Arista #{i + 1}: falta `from` o `to` texto.",
                )
            )
            continue
        if f not in item_set:
            findings.append(
                InstrumentQAFinding(
                    rule_id="QA_RULE_005",
                    severity="STOP",
                    item_id=f,
                    block_id=None,
                    message=f"Origen de routing desconocido: `{f}`.",
                )
            )
            continue
        if t not in item_set and t not in _TERMINAL_TARGETS:
            findings.append(
                InstrumentQAFinding(
                    rule_id="QA_RULE_005",
                    severity="STOP",
                    item_id=f,
                    block_id=None,
                    message=f"Destino de routing desconocido: `{t}` (no es ítem ni terminal conocido).",
                )
            )
            continue
        parsed.append((f, t))

    internal = [(f, t) for f, t in parsed if f in item_set and t in item_set]
    nodes_in_graph = set()
    for f, t in internal:
        nodes_in_graph.add(f)
        nodes_in_graph.add(t)

    if nodes_in_graph and _detect_cycle(nodes_in_graph, internal):
        findings.append(
            InstrumentQAFinding(
                rule_id="QA_RULE_005",
                severity="STOP",
                item_id=None,
                block_id=None,
                message="Grafo de routing contiene un ciclo (saltos instrumentales).",
            )
        )

    indegree: dict[str, int] = {n: 0 for n in nodes_in_graph}
    adj: dict[str, list[str]] = {n: [] for n in nodes_in_graph}
    for f, t in internal:
        adj[f].append(t)
        indegree[t] = indegree.get(t, 0) + 1

    roots = [n for n in nodes_in_graph if indegree.get(n, 0) == 0]
    if not roots and nodes_in_graph:
        roots = [min(nodes_in_graph)]

    reachable: set[str] = set()

    def walk(u: str) -> None:
        reachable.add(u)
        for v in adj.get(u, []):
            if v not in reachable:
                walk(v)

    for r in roots:
        if r in nodes_in_graph:
            walk(r)

    unreachable = nodes_in_graph - reachable
    for u in sorted(unreachable):
        findings.append(
            InstrumentQAFinding(
                rule_id="QA_RULE_005",
                severity="STOP",
                item_id=u,
                block_id=None,
                message=f"Ítem `{u}` participa en routing pero no es alcanzable desde entradas del grafo.",
            )
        )

    return findings


def run_instrument_qa_rules_bootstrap(spec: dict[str, Any]) -> list[InstrumentQAFinding]:
    """Ejecuta QA_RULE_001–005 sobre un dict raíz `instrument_spec`."""
    findings: list[InstrumentQAFinding] = []

    for block_id, item in _iter_blocks_items(spec):
        for rule_fn in (_rule_001_double_barrel, _rule_002_leading, _rule_003_quotas, _rule_004_scale):
            hit = rule_fn(block_id, item)
            if hit is not None:
                findings.append(hit)

    ordered_ids = _collect_item_ids(spec)
    findings.extend(_rule_005_branching(spec, ordered_ids))

    findings.sort(key=lambda f: (f.severity != "STOP", f.rule_id, f.item_id or "", f.message))
    return findings


def summarize_qa_severities(findings: list[InstrumentQAFinding]) -> tuple[int, int, int]:
    stops = sum(1 for f in findings if f.severity == "STOP")
    fix_now = sum(1 for f in findings if f.severity == "FIX_NOW")
    monitor = sum(1 for f in findings if f.severity == "MONITOR")
    return stops, fix_now, monitor
