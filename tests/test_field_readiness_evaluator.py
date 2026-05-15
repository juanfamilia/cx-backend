"""Tests unitarios evaluador Readiness (sin DB)."""

from app.services.field_readiness_evaluator import (
    READINESS_ROLE_ACCOUNT,
    READINESS_ROLE_QA,
    READINESS_ROLE_RESEARCH,
    QARunGateSnapshot,
    ReadinessPolicyView,
    RevisionGateSnapshot,
    evaluate_readiness_gates,
)


def _base_policy(**kwargs: bool | None) -> ReadinessPolicyView:
    defaults = dict(
        require_role_research=True,
        require_role_qa=True,
        require_role_account=False,
        block_on_schema_invalid=True,
        block_on_missing_schema_validation=True,
        block_on_qa_stop=True,
        block_on_qa_fix_now=False,
        require_qa_run=True,
        enforce_signatory_grants=False,
        require_brief_approved=False,
    )
    defaults.update({k: v for k, v in kwargs.items() if v is not None})
    return ReadinessPolicyView(**defaults)  # type: ignore[arg-type]


def test_blocked_when_qa_stop_and_policy_enforces():
    pol = _base_policy()
    rev = RevisionGateSnapshot(
        status="draft",
        content_hash="abc",
        last_validation_ok=True,
        last_validation_content_hash="abc",
    )
    qa = QARunGateSnapshot(run_id=1, stop_count=2, fix_now_count=0)
    ev = evaluate_readiness_gates(
        policy=pol,
        revision=rev,
        qa=qa,
        active_signatures={},
        signatory_user_ids_by_role=None,
    )
    assert "qa_stop_present" in ev.blocking_codes
    assert READINESS_ROLE_RESEARCH in ev.missing_roles


def test_ready_when_all_signed_and_green():
    pol = _base_policy(require_role_account=False)
    rev = RevisionGateSnapshot(
        status="draft",
        content_hash="h1",
        last_validation_ok=True,
        last_validation_content_hash="h1",
    )
    qa = QARunGateSnapshot(run_id=99, stop_count=0, fix_now_count=0)
    sig = {
        READINESS_ROLE_RESEARCH: ("h1", 99),
        READINESS_ROLE_QA: ("h1", 99),
    }
    ev = evaluate_readiness_gates(
        policy=pol,
        revision=rev,
        qa=qa,
        active_signatures=sig,
        signatory_user_ids_by_role=None,
    )
    assert ev.ready
    assert ev.blocking_codes == ()


def test_stale_signature_requires_resign_and_does_not_hard_block_others():
    pol = _base_policy()
    rev = RevisionGateSnapshot(
        status="draft",
        content_hash="newhash",
        last_validation_ok=True,
        last_validation_content_hash="newhash",
    )
    qa = QARunGateSnapshot(run_id=1, stop_count=0, fix_now_count=0)
    sig = {READINESS_ROLE_RESEARCH: ("oldhash", 1), READINESS_ROLE_QA: ("newhash", 1)}
    ev = evaluate_readiness_gates(
        policy=pol,
        revision=rev,
        qa=qa,
        active_signatures=sig,
        signatory_user_ids_by_role=None,
    )
    assert "signatures_stale" not in ev.blocking_codes
    assert READINESS_ROLE_RESEARCH in ev.stale_roles
    assert READINESS_ROLE_RESEARCH in ev.missing_roles
    assert READINESS_ROLE_QA not in ev.missing_roles


def test_enforce_grants_requires_matrix():
    pol = _base_policy(enforce_signatory_grants=True)
    rev = RevisionGateSnapshot(
        status="draft",
        content_hash="x",
        last_validation_ok=True,
        last_validation_content_hash="x",
    )
    qa = QARunGateSnapshot(run_id=1, stop_count=0, fix_now_count=0)
    ev = evaluate_readiness_gates(
        policy=pol,
        revision=rev,
        qa=qa,
        active_signatures={
            READINESS_ROLE_RESEARCH: ("x", 1),
            READINESS_ROLE_QA: ("x", 1),
        },
        signatory_user_ids_by_role=None,
    )
    assert "signatory_grants_not_loaded" in ev.blocking_codes


def test_brief_gate_blocks_when_policy_requires_approval():
    pol = _base_policy(require_brief_approved=True)
    rev = RevisionGateSnapshot(
        status="draft",
        content_hash="x",
        last_validation_ok=True,
        last_validation_content_hash="x",
    )
    qa = QARunGateSnapshot(run_id=1, stop_count=0, fix_now_count=0)
    ev = evaluate_readiness_gates(
        policy=pol,
        revision=rev,
        qa=qa,
        active_signatures={},
        signatory_user_ids_by_role=None,
        brief_ready_for_readiness=False,
    )
    assert "brief_not_approved" in ev.blocking_codes


def test_brief_gate_passes_when_ready_or_policy_off():
    pol = _base_policy(require_brief_approved=True)
    rev = RevisionGateSnapshot(
        status="draft",
        content_hash="x",
        last_validation_ok=True,
        last_validation_content_hash="x",
    )
    qa = QARunGateSnapshot(run_id=1, stop_count=0, fix_now_count=0)
    ev_ok = evaluate_readiness_gates(
        policy=pol,
        revision=rev,
        qa=qa,
        active_signatures={},
        signatory_user_ids_by_role=None,
        brief_ready_for_readiness=True,
    )
    assert "brief_not_approved" not in ev_ok.blocking_codes

    pol_off = _base_policy(require_brief_approved=False)
    ev_off = evaluate_readiness_gates(
        policy=pol_off,
        revision=rev,
        qa=qa,
        active_signatures={},
        signatory_user_ids_by_role=None,
        brief_ready_for_readiness=False,
    )
    assert "brief_not_approved" not in ev_off.blocking_codes


def test_account_role_required_when_policy_says_so():
    pol = _base_policy(require_role_account=True)
    rev = RevisionGateSnapshot(
        status="draft",
        content_hash="x",
        last_validation_ok=True,
        last_validation_content_hash="x",
    )
    qa = QARunGateSnapshot(run_id=1, stop_count=0, fix_now_count=0)
    sig = {READINESS_ROLE_RESEARCH: ("x", 1), READINESS_ROLE_QA: ("x", 1)}
    ev = evaluate_readiness_gates(
        policy=pol,
        revision=rev,
        qa=qa,
        active_signatures=sig,
        signatory_user_ids_by_role=None,
    )
    assert READINESS_ROLE_ACCOUNT in ev.missing_roles
