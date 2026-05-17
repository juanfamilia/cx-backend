"""Contrato estático de platform-memory (sin DB)."""

from app.platform_intelligence.schemas import ProductFlags
from app.platform_intelligence.service import _static_cross_feed, _static_lenses, _static_shared_primitives


def test_five_domain_lenses():
    flags = ProductFlags(
        cx=True, ins=True, field=True, clever=True, perfil=True
    )
    lenses = _static_lenses(flags)
    domains = {x.domain for x in lenses}
    assert domains == {"field", "ins", "cx", "clever", "perfil"}
    assert all(x.enabled_for_tenant for x in lenses)


def test_cross_feed_ins_to_field_partial():
    ch = _static_cross_feed()
    ins_field = [c for c in ch if c.source == "ins" and c.sink == "field"]
    assert len(ins_field) == 1
    assert ins_field[0].status == "partial"


def test_shared_primitives_include_findings_and_embeddings():
    prim = _static_shared_primitives()
    codes = {p.code for p in prim}
    assert "findings" in codes
    assert "embeddings" in codes
    assert "study_intelligence_bundles" in codes
