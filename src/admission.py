"""Hallucination 주요 구현 발췌. SOURCE_GUIDE.md와 함께 읽는다."""
from __future__ import annotations
from collections.abc import Mapping, Sequence
from typing import Any

NARRATIVE_ADMISSION_FIELD = "narrative_admission_decisions"

NARRATIVE_ADMISSION_DECISIONS = ("admit", "reject")

NARRATIVE_ADMISSION_RECEIPT_SUPPORT_SCOPES = (
    "current_state",
    "completed_event",
)

_DECISION_FIELDS = {"evidence_id", "decision"}

def normalize_narrative_admission(
    data: Mapping[str, Any],
    *,
    evidence: Sequence[Mapping[str, str]],
    receipts: Sequence[Mapping[str, str]],
    prompt_name: str,
) -> list[dict[str, Any]]:
    """Validate one decision per evidence and return every rejected row."""
    if not isinstance(data, Mapping) or NARRATIVE_ADMISSION_FIELD not in data:
        raise LLMResponseContractException(
            f"{prompt_name} missing {NARRATIVE_ADMISSION_FIELD}"
        )
    decisions = data[NARRATIVE_ADMISSION_FIELD]
    if not isinstance(decisions, list):
        raise LLMResponseContractException(
            f"{prompt_name} {NARRATIVE_ADMISSION_FIELD} must be a list"
        )

    evidence_by_id = {
        str(row["evidence_id"]): str(row["content"])
        for row in evidence
    }
    evidence_ids = set(evidence_by_id)
    if len(decisions) != len(evidence_ids):
        raise LLMResponseContractException(
            f"{prompt_name} narrative admission must decide every evidence ID"
        )
    receipt_support_scopes = {
        str(row["receipt_id"]): str(row.get("support_scope") or "")
        for row in receipts
    }
    if any(
        value not in NARRATIVE_ADMISSION_RECEIPT_SUPPORT_SCOPES
        for value in receipt_support_scopes.values()
    ):
        raise LLMResponseContractException(
            f"{prompt_name} narrative admission receipt support scope is invalid"
        )
    normalized: list[dict[str, Any]] = []
    seen_evidence_ids: set[str] = set()
    for raw in decisions:
        if not isinstance(raw, Mapping) or set(raw) != _DECISION_FIELDS:
            raise LLMResponseContractException(
                f"{prompt_name} narrative admission decision fields are invalid"
            )
        evidence_id = str(raw.get("evidence_id") or "").strip()
        decision = str(raw.get("decision") or "").strip()
        if evidence_id not in evidence_ids or evidence_id in seen_evidence_ids:
            raise LLMResponseContractException(
                f"{prompt_name} narrative admission references invalid evidence"
            )
        seen_evidence_ids.add(evidence_id)
        if decision not in NARRATIVE_ADMISSION_DECISIONS:
            raise LLMResponseContractException(
                f"{prompt_name} narrative admission decision is invalid"
            )
        if decision == "reject":
            normalized.append({
                "evidence_id": evidence_id,
                "claim": evidence_by_id[evidence_id],
                "decision": decision,
            })

    if seen_evidence_ids != evidence_ids:
        raise LLMResponseContractException(
            f"{prompt_name} narrative admission must decide every evidence ID"
        )

    return normalized


def require_narrative_admission(
    data: Mapping[str, Any],
    *,
    evidence: Sequence[Mapping[str, str]],
    receipts: Sequence[Mapping[str, str]],
    prompt_name: str,
    scene_scope: Mapping[str, Any] | None = None,
    selected_choice_contract: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Reject every reported claim, visible-scope, or Choice violation."""
    normalized = normalize_narrative_admission(
        data,
        evidence=evidence,
        receipts=receipts,
        prompt_name=prompt_name,
    )
    scope_rejections = normalize_narrative_scene_scope_admission(
        data,
        evidence=evidence,
        scene_scope=scene_scope,
        prompt_name=prompt_name,
    )
    choice_decision = normalize_selected_choice_continuity(
        data,
        evidence=evidence,
        selected_choice_contract=selected_choice_contract,
        prompt_name=prompt_name,
    )
    rejected_ids = [
        row["evidence_id"]
        for row in [*normalized, *scope_rejections]
    ]
    if choice_decision is not None and choice_decision["status"] != "fulfilled":
        rejected_ids.extend(choice_decision["evidence_ids"])
    if rejected_ids:
        raise NarrativeCandidateRejected(
            list(dict.fromkeys(rejected_ids))
        )
    return []
