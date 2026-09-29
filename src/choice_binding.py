"""Hallucination 주요 구현 발췌. SOURCE_GUIDE.md와 함께 읽는다."""
from __future__ import annotations
from copy import deepcopy
from typing import Any

EXECUTION_BINDING_PAYLOAD_FIELDS = (
    "floor_target",
    "zone_target",
    "encounter_request",
    "pvp_target",
    "rest_intent",
    "boss_room_entry",
    "party_join_target",
    "party_recruitment",
)

def resolve_execution_binding(
    raw_catalog: Any,
    execution_binding_id: Any,
) -> dict[str, Any]:
    binding_id = _compact_required_text(
        execution_binding_id,
        owner="choice execution_binding_id",
    )
    catalog = normalize_execution_binding_catalog(raw_catalog)
    matches = [
        entry for entry in catalog
        if entry["execution_binding_id"] == binding_id
    ]
    if len(matches) != 1:
        raise ValueError(
            "choice execution_binding_id must resolve to exactly one catalog entry"
        )
    return {
        field: deepcopy(matches[0][field])
        for field in EXECUTION_BINDING_PAYLOAD_FIELDS
        if field in matches[0]
    }
