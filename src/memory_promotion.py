"""Hallucination 주요 구현 발췌. SOURCE_GUIDE.md와 함께 읽는다."""
from __future__ import annotations

class MemoryPromoter:
    PROMOTE_TO_EPISODIC_MIN_SCORE = 0.25  # 일상(0.0~0.2)만 제외

    def on_completed_scene(
        self,
        compatibility_period_id: int,
        scene_index: int,
        base_checkpoint_index: int,
    ) -> list:
        """
        Promote from working -> episodic.
        Called after a continuous scene has completed.
        Returns list of newly created EpisodicEntry objects.

        Working memory는 clear하지 않는다 — 7슬롯 용량 제한 + scene_index 기반
        오래된 경험 퇴출로 정리한다. 중요도는 이곳의 장기 기억 승격을 결정한다.
        last_promoted_scene으로 동일 슬롯의 중복 에피소딕 승격을 방지한다.
        """
        if (
            not isinstance(base_checkpoint_index, int)
            or isinstance(base_checkpoint_index, bool)
            or base_checkpoint_index <= 0
        ):
            raise ValueError("base_checkpoint_index must be positive")
        slots = self.working.get_all_slots()
        new_entries = []
        for slot in slots:
            if slot.priority >= self.PROMOTE_TO_EPISODIC_MIN_SCORE:
                # 이미 에피소딕에 승격된 슬롯은 재승격하지 않음 (초기값 -1)
                if slot.last_promoted_scene >= 0:
                    continue
                metadata = dict(slot.metadata or {})
                metadata["from_working_key"] = slot.key
                metadata.setdefault("base_importance_score", slot.priority)
                metadata.setdefault(
                    "base_checkpoint_index",
                    base_checkpoint_index,
                )
                entry = self.episodic.add_scene_entry(
                    content=slot.content,
                    importance_score=slot.priority,
                    compatibility_period_id=compatibility_period_id,
                    scene_index=scene_index,
                    metadata=metadata,
                )
                new_entries.append(entry)
                slot.last_promoted_scene = scene_index

        return new_entries
