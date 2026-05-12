"""Evaluación pura de gates Readiness (testable sin DB)."""

from __future__ import annotations

from dataclasses import dataclass

READINESS_ROLE_RESEARCH = "READINESS_ROLE_RESEARCH"
READINESS_ROLE_QA = "READINESS_ROLE_QA"
READINESS_ROLE_ACCOUNT = "READINESS_ROLE_ACCOUNT"

READINESS_SIGNATURE_ROLES = frozenset(
    {
        READINESS_ROLE_RESEARCH,
        READINESS_ROLE_QA,
        READINESS_ROLE_ACCOUNT,
    }
)


@dataclass(frozen=True)
class ReadinessPolicyView:
    require_role_research: bool
    require_role_qa: bool
    require_role_account: bool
    block_on_schema_invalid: bool
    block_on_missing_schema_validation: bool
    block_on_qa_stop: bool
    block_on_qa_fix_now: bool
    require_qa_run: bool
    enforce_signatory_grants: bool
    require_brief_approved: bool


@dataclass(frozen=True)
class RevisionGateSnapshot:
    status: str
    content_hash: str
    last_validation_ok: bool | None
    last_validation_content_hash: str | None


@dataclass(frozen=True)
class QARunGateSnapshot:
    run_id: int | None
    stop_count: int
    fix_now_count: int


@dataclass(frozen=True)
class ReadinessEvaluation:
    blocking_codes: tuple[str, ...]
    required_roles: tuple[str, ...]
    missing_roles: tuple[str, ...]
    stale_roles: tuple[str, ...]

    @property
    def blocked(self) -> bool:
        return len(self.blocking_codes) > 0

    @property
    def ready(self) -> bool:
        return not self.blocked and len(self.missing_roles) == 0


def required_roles_for_policy(policy: ReadinessPolicyView) -> tuple[str, ...]:
    roles: list[str] = []
    if policy.require_role_research:
        roles.append(READINESS_ROLE_RESEARCH)
    if policy.require_role_qa:
        roles.append(READINESS_ROLE_QA)
    if policy.require_role_account:
        roles.append(READINESS_ROLE_ACCOUNT)
    return tuple(roles)


def evaluate_readiness_gates(
    *,
    policy: ReadinessPolicyView,
    revision: RevisionGateSnapshot,
    qa: QARunGateSnapshot,
    active_signatures: dict[str, tuple[str, int | None]],
    signatory_user_ids_by_role: dict[str, frozenset[int]] | None,
    brief_ready_for_readiness: bool = True,
) -> ReadinessEvaluation:
    """
    active_signatures: firma vigente por rol -> (snapshot_spec_hash, snapshot_qa_run_id).
    signatory_user_ids_by_role: si ``enforce_signatory_grants``, mapa rol -> usuarios autorizados.
    """
    blocking: list[str] = []

    if revision.status == "archived":
        blocking.append("revision_archived")

    if policy.require_brief_approved and not brief_ready_for_readiness:
        blocking.append("brief_not_approved")

    required = required_roles_for_policy(policy)

    if policy.enforce_signatory_grants:
        if signatory_user_ids_by_role is None:
            blocking.append("signatory_grants_not_loaded")
        else:
            for role in required:
                ids = signatory_user_ids_by_role.get(role, frozenset())
                if len(ids) == 0:
                    blocking.append(f"no_signatories_for_{role}")

    if policy.block_on_missing_schema_validation:
        if revision.last_validation_ok is None:
            blocking.append("schema_validation_missing")

    if policy.block_on_schema_invalid:
        if revision.last_validation_ok is False:
            blocking.append("schema_validation_failed")
        elif revision.last_validation_ok is True:
            if revision.last_validation_content_hash != revision.content_hash:
                blocking.append("schema_validation_stale")

    if policy.require_qa_run:
        if qa.run_id is None:
            blocking.append("qa_run_missing")

    if policy.block_on_qa_stop and qa.stop_count > 0:
        blocking.append("qa_stop_present")

    if policy.block_on_qa_fix_now and qa.fix_now_count > 0:
        blocking.append("qa_fix_now_present")

    stale: list[str] = []
    signed_valid: set[str] = set()
    for role in required:
        if role not in active_signatures:
            continue
        snap_hash, snap_qa_id = active_signatures[role]
        hash_ok = snap_hash == revision.content_hash
        qa_ok = qa.run_id is None or snap_qa_id == qa.run_id
        if hash_ok and qa_ok:
            signed_valid.add(role)
        else:
            stale.append(role)

    missing = tuple(r for r in required if r not in signed_valid)

    return ReadinessEvaluation(
        blocking_codes=tuple(blocking),
        required_roles=required,
        missing_roles=missing,
        stale_roles=tuple(sorted(set(stale))),
    )
