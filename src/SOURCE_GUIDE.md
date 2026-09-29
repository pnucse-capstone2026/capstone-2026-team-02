# 주요 구현 안내

최종보고서의 설계·처리에 해당하는 함수·메서드와 클래스·열거형 일부를 발췌하였다. 생략된 보조 함수와 객체 초기화의 전제는 각 항목에 설명한다. 독립 실행 패키지는 아니다.

| 파일 | 주요 기능 | 최종보고서 관련 항목 |
|---|---|---|
| [choice_binding.py](choice_binding.py) | 식별자 조회와 실행 정보 반환 | 자연어 선택과 실제 실행의 연결, 「파티 수락의 전체 처리 사례」 |
| [admission.py](admission.py) | 판정 응답 검사와 거절 시 처리 중단 | 「생성 검수와 상태 보호」, 「검수 결과와 최종 표시의 연결」 |
| [memory_promotion.py](memory_promotion.py) | 작업 기억의 일화 기억 승격 | 「4계층 기억의 저장과 활용」 |
| [shared_experience.py](shared_experience.py) | 다자 관계 표현과 공동 사건 조회 | 관계 하이퍼그래프와 공유 경험 공급 사례 |

## 선택 식별자와 실행 정보

`resolve_execution_binding`은 실행 목록과 선택의 `execution_binding_id`를 받는다. 식별자를 정리하고 목록을 검증한 다음, 식별자가 일치하는 항목을 정확히 하나 찾아 지정된 실행 필드만 깊은 복사하여 반환한다. 일치하는 항목이 하나가 아니면 `ValueError`를 발생시킨다.

호출하는 보조 함수는 다음 조건을 검사한다.

| 호출 | 입력에 적용하는 조건 | 결과 |
|---|---|---|
| `_compact_required_text` | 문자열인지 검사하고 공백을 정리한 뒤 빈 문자열을 거절 | 비교에 사용할 식별자 문자열 |
| `normalize_execution_binding_catalog` | 비어 있지 않은 목록, 항목별 필드와 값, 중복 식별자를 검사 | 식별자와 실행 필드를 갖춘 정규화된 항목 목록 |

정산과 최종 상태 반영은 반환 이후에 수행한다. 실행 식별자는 정산을 연결하는 용도이며, 자연어 선택의 의미를 행동 목록으로 제한하지 않는다.

## 검수 판정 검사와 거절 집행

`normalize_narrative_admission`은 검수 응답, 식별자·주장 본문을 가진 `evidence`, 근거 범위를 가진 `receipts`를 받는다. 증거 목록의 식별자는 호출 전에 유일하게 구성되어 있어야 한다. 응답에는 증거 식별자마다 `admit` 또는 `reject` 판정이 하나씩 있어야 한다.

판정 개수, 필드 구성, 식별자의 유효성과 중복, 판정 값 및 근거 범위를 검사한다. 예를 들어 증거가 두 개일 때 같은 식별자의 판정을 두 번 반환하면 판정 개수가 맞더라도 오류가 된다. 정상 형식의 응답에서는 `reject`인 항목만 해당 주장과 함께 반환한다. 빈 목록은 거절 판정이 없다는 뜻이며, 문장의 사실성을 보증하지 않는다.

형식 위반 시 `LLMResponseContractException`을 발생시킨다. 이 함수는 자연어의 진위를 판단하지 않고 판정 응답을 검사한다.

`require_narrative_admission`은 주장·장면 범위 판정의 거절 식별자를 모은다. 선택 이행 판정이 `fulfilled`가 아니면 해당 판정의 식별자를 거절 목록에 합치고, 최종 목록이 비어 있지 않으면 `NarrativeCandidateRejected`를 발생시킨다. 이 예외가 추출 처리를 중단시키는 경로는 아래 [호출 흐름](#검수와-상태-반영의-호출-흐름)에 제시한다.

장면 범위·선택 판정의 보조 검사 함수와 두 예외 클래스의 정의는 발췌에서 생략하였다. 상태 복구는 이 함수 밖에서 처리한다.

## 작업 기억에서 일화 기억으로의 승격

`MemoryPromoter.on_completed_scene`은 완료 장면의 번호와 양의 체크포인트 번호를 받는다. `self.working`에서 슬롯을 조회하고, 중요도 조건을 만족하면서 아직 승격하지 않은 슬롯을 `self.episodic`에 추가한다. 내용·중요도·출처 메타데이터를 전달하고 승격한 장면을 슬롯에 기록하여 반복 추가를 막는다.

새로 추가한 일화 기억 항목 목록을 반환한다. 중요도는 기억의 보존 기준이며 사실 정확도의 점수가 아니다.

## 공동 경험의 표현과 조회

`EdgeType`에는 공동 사건 조회에 쓰는 세 관계 유형을, `HyperEdge`에는 여러 노드를 역할과 함께 연결하는 필드를 담았다. `HyperGraph.add_edge`는 참조 노드의 존재를 확인하고 간선과 노드별 인접 인덱스를 등록한다. `get_shared_events`는 두 노드 중 인접 간선이 적은 쪽을 탐색하여, 두 노드가 모두 포함된 참여·목격·원인 관계를 가중치 내림차순으로 반환한다.

노드·간선 사전과 인접 인덱스는 호출 전에 초기화되어 있어야 한다. 반환된 간선 목록을 장면 맥락으로 구성하고 생성 모델에 전달하는 처리는 이후 단계에서 수행한다.

## 시스템 수치로 구성하는 응답

게임 상태의 수치와 생성 문장의 주장은 서로 다른 근거를 가진다. 아래는 서버의 실제 전후 상태에서 자원 변경량을 계산하고, 정산 결과가 있는 응답의 수치 필드에 그 값을 사용하는 구간이다. 기존 발췌와 같은 구현에서 가져왔으며 각 코드 블록은 연속된 원문이다.

### 실제 상태에서 자원 변경량 계산

`ResourceDelta.from_player`는 행동 전 스냅샷과 처리 후 캐릭터 상태를 비교한다. HP·MP·골드 변경량의 입력은 생성 문장이 아니라 두 시점의 값이다. 아래는 클래스 메서드 전체이며, 변경량과 스냅샷 유무를 보관하는 데이터 클래스의 필드 선언은 생략하였다.

```python
    @classmethod
    def from_player(cls, pre_action_stats: dict[str, Any] | None, player: Any) -> ResourceDelta:
        if not isinstance(pre_action_stats, dict):
            return cls()
        hp_before = int(pre_action_stats["hp"])
        mp_before = int(pre_action_stats["mp"])
        gold_before = int(pre_action_stats["gold"])
        exp_before = int(pre_action_stats.get("exp", 0))
        level_before = int(pre_action_stats.get("level", 0))
        return cls(
            hp=int(getattr(player, "current_hp", hp_before)) - hp_before,
            mp=int(getattr(player, "current_mp", mp_before)) - mp_before,
            gold=int(getattr(player, "gold", gold_before)) - gold_before,
            exp=int(getattr(player, "exp", exp_before)) - exp_before,
            level=int(getattr(player, "level", level_before)) - level_before,
            snapshot_available=True,
        )
```

정산 객체를 만드는 `SettlementResult.from_pipeline_state`는 이 메서드에 행동 전 상태와 현재 캐릭터를 전달한다. 다른 정산 필드의 구성과 객체 저장 처리는 이 발췌에 포함하지 않았다.

### 정산 결과로 응답 수치 구성

`settlement_response_player_updates`는 기존 응답 필드를 복사한 뒤, 정산의 HP·MP·골드 변경량으로 해당 수치 필드를 구성한다. 딕셔너리 경로에서는 스냅샷과 필수 필드의 존재를 검사하고 정수값을 대입한다. 다른 응답 필드는 유지한다.

```python
def settlement_response_player_updates(
    settlement: Mapping[str, Any] | SettlementResult | None,
    existing_updates: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build response player_updates from the settlement resource owner."""

    updates = _copy_player_updates(existing_updates)
    if settlement is None:
        return updates
    if isinstance(settlement, SettlementResult):
        resource_updates = settlement.resource_delta.to_player_updates()
        if not resource_updates:
            _reject_existing_resource_updates(updates)
            return updates
        updates.update(resource_updates)
        return updates
    if not isinstance(settlement, Mapping):
        raise ValueError("settlement response source must be a mapping")

    if "resource_delta" not in settlement:
        raise ValueError("settlement missing resource_delta")
    raw_resource_delta = settlement["resource_delta"]
    if not isinstance(raw_resource_delta, Mapping):
        raise ValueError("settlement resource_delta must be a mapping")
    if not raw_resource_delta.get("snapshot_available", False):
        _reject_existing_resource_updates(updates)
        return updates

    for source_key, target_key in (
        ("hp", "hp_change"),
        ("mp", "mp_change"),
        ("gold", "gold_change"),
    ):
        if source_key not in raw_resource_delta:
            raise ValueError(f"settlement resource_delta missing {source_key}")
        updates[target_key] = _response_player_update_int(
            raw_resource_delta[source_key],
            f"settlement resource_delta {source_key}",
        )
    return updates
```

보조 함수 `_copy_player_updates`는 매핑을 깊은 복사하고, `_response_player_update_int`는 불리언을 제외한 정수만 허용한다. `_reject_existing_resource_updates`는 스냅샷이 없는 정산에 기존 HP·MP·골드 변경 필드가 섞여 있으면 오류를 발생시킨다. `SettlementResult`의 객체 정의와 이 보조 함수들은 생략하였다. 정산 자체가 `None`이면 기존 필드를 반환하는 분기도 있으므로, 이 함수만으로 모든 호출의 정산 존재를 보장한다고 해석하지 않는다.

### 상태 응답에 연결

게임 루프는 세션의 정산 결과와 추출 결과를 위 함수에 전달한다. 아래는 호출 메서드 전체다.

```python
    @staticmethod
    def _settlement_player_updates_for_response(
        session: dict,
        result: dict,
    ) -> dict[str, object]:
        return settlement_response_player_updates(
            session.get("_last_settlement_result"),
            result.get("player_updates"),
        )
```

같은 게임 루프의 `process_action_stream`은 이 반환값을 `STATE_UPDATE`의 `player_updates`로 전달한다. 아래는 해당 이벤트 구성 전체이며, 앞선 캐릭터 상태·장면·알림 구성과 이후 처리는 생략하였다.

```python
                yield SSEEvent(event=SSEEventType.STATE_UPDATE, data={
                    "character": char_state,
                    "sequences": [s.model_dump() for s in pydantic_sequences],
                    "notices": [notice.model_dump() for notice in notices],
                    "speaker_metadata": speaker_metadata,
                    "encountered_players": result.get("encountered_players", []),
                    "player_updates": self._settlement_player_updates_for_response(
                        session,
                        result,
                    ),
                    "ai_reasoning": None,
                    "intent_feedback": intent_feedback,
                    "intent_success": intent_success,
                    **self._stream_scene_meta_payload_for_scene(session, final_stream_scene),
                })
```

이 구간은 정산 결과가 있는 응답에서 수치 변경량의 출처와 전달을 보여준다. 전투 계산식, 모든 상태 변경 경로, 영속 저장과 Flutter의 소비 구현 전체를 포함하지는 않는다. 최종보고서 제4.4절의 전투 결과와 제4.4.1절의 MP 불변 사례는 실제 관측 결과를 별도로 제시한다. 서술 오류가 수치 변경으로 이어지지 않은 것과, 그 오류 문장이 사용자에게 표시되지 않은 것은 서로 다른 성과다.

## 검수와 상태 반영의 호출 흐름

다음은 서버의 `extract_updates`, 응답 처리 래퍼, `process_action_stream`에서 발췌한 구간이다. 각 코드 블록은 해당 함수 안의 연속된 원문이며, 블록 사이의 생략 부분은 설명에 표시했다. 최종보고서 제3.8절의 판정 집행과 제3.15절의 통합 처리에 해당한다.

### 후보 문장과 상태 근거

`extract_updates`는 후보의 표시 단위에서 `narrative_evidence`를 만들고, 플레이어·세션과 실행 결과에서 `narrative_receipts`를 구성한다. `narrative_claim_sequences`는 앞선 장면 생성 단계에서 세션에 보관한 후보이며, `system_res`는 실행 결과다. 이 입력을 준비하는 부분과 두 구성 함수의 내부는 생략하였다.

```python
        narrative_evidence = build_narrative_evidence(
            narrative_claim_sequences
        )
        narrative_receipts = build_narrative_fact_receipts(
            player,
            session,
            system_resolution=system_res,
            scene_end_time=narrative_claim_scene_end_time,
            scene_scope=narrative_scene_scope,
        )
```

### 응답 검사와 추출 결과 반환

같은 함수의 `_project_extract_response`는 위 근거와 후보 식별자를 사용해 응답의 판정을 검사한다. `require_narrative_admission`이 예외를 발생시키면 이후의 필드 분리와 반환으로 진행하지 않는다. 검사를 통과한 응답은 판정 필드를 분리하고, 필요한 경우 인물 참조와 파티 제안을 정리하여 반환한다.

아래는 중첩 함수 전체와 이를 전달하는 호출부다. 앞선 요청 구성과 지역변수 준비, 반환 후 세션 임시값 정리는 생략하였다. `fresh_reference_catalog`와 관련 변수는 해당 요청의 인물 참조 자료이며, `party_offer_context`는 파티 제안 추출에 필요한 맥락이다.

```python
        def _project_extract_response(data: dict) -> dict[str, Any]:
            if not isinstance(data, Mapping):
                raise LLMResponseContractException(
                    "EXTRACT_UPDATES response must be an object"
                )
            require_narrative_admission(
                data,
                evidence=narrative_evidence,
                receipts=narrative_receipts,
                prompt_name="EXTRACT_UPDATES",
                scene_scope=narrative_scene_scope,
                selected_choice_contract=selected_choice_continuity,
            )
            provider_data = deepcopy(dict(data))
            provider_data.pop(NARRATIVE_ADMISSION_FIELD)
            provider_data.pop(NARRATIVE_SCENE_SCOPE_FIELD)
            if selected_choice_continuity is not None:
                provider_data.pop(NARRATIVE_SELECTED_CHOICE_FIELD)

            offers = None
            if party_offer_context is not None:
                try:
                    offers = project_party_offers(provider_data.pop("party_offers", None), party_offer_context)
                except (TypeError, ValueError) as exc:
                    raise LLMResponseContractException(f"EXTRACT_UPDATES party offer contract failed: {exc}") from exc

            if fresh_reference_catalog is None:
                return provider_data
            try:
                projected_updates = project_fresh_system_updates(
                    provider_data,
                    fresh_reference_catalog,
                    new_actors=fresh_new_actors,
                    player_name=player.name,
                    allowed_actor_refs=fresh_scene_actor_refs,
                )
                if offers is not None:
                    projected_updates["_party_offers"] = offers
                return projected_updates
            except (TypeError, ValueError) as exc:
                raise LLMResponseContractException(
                    f"EXTRACT_UPDATES fresh response contract failed: {exc}"
                ) from exc

        result = await self._generate_scene_response_with_structural_recovery(
            request,
            _project_extract_response,
        )
```

응답 처리 래퍼는 모델의 실제 응답을 전달받아 이 검사 함수를 호출한다. 아래는 래퍼의 `try` 내부이며, 주변의 형식 오류 처리와 재시도 분기는 생략하였다.

```python
                response = await self._router.generate(attempt_request)
                return projector(response.data)
```

### 추출 이후의 상태 반영

`process_action_stream`은 `extract_updates`의 결과를 받은 뒤 후속 상태 반영을 수행한다. 추출 중 발생한 예외는 다시 발생시키므로, 실패한 추출 결과로 아래 `_apply_post_resolution`을 실행하거나 마지막 장면을 대입하지 않는다.

아래는 일반 행동 처리 중의 연속 구간이다. 앞선 장면 생성과 정산, 이 구간을 감싸는 예외 처리, 뒤따르는 저장과 응답 전송은 생략하였다.

```python
                # Phase 2: Extract state updates
                pydantic_sequences = [NarrativeSequence(**s) for s in phase1_sequences]
                result = {}
                try:
                    result = await self._scene_engine.extract_updates(player, session, choice_dict)
                    self._scene_engine.apply_scene_pressure_to_phase1(
                        phase1_result,
                        result,
                    )
                    if phase1_result.get("_phase1_guardrail_rejections"):
                        result["_phase1_guardrail_rejections"] = phase1_result[
                            "_phase1_guardrail_rejections"
                        ]
                except Exception as extract_err:
                    logger.error("[SSE] Phase 2 extract failed for %s: %s",
                                 session_id, extract_err, exc_info=True)
                    raise

                # Post-resolution: NPC처리, 메모리 갱신, 씬 전진 등
                try:
                    pydantic_sequences, _ = self._apply_post_resolution(
                        player, session, result, choice_dict,
                        narration_resolution=phase1_result,
                        pydantic_sequences=pydantic_sequences,
                        narration_text=narration_text,
                        append_system_to_narration=False,
                    )
                except Exception as post_err:
                    logger.error("[SSE] Post-resolution failed for %s: %s",
                                 session_id, post_err, exc_info=True)
                    raise
                final_narration_text = "\n".join(s.content for s in pydantic_sequences)
                session["last_narration"] = final_narration_text
                session["last_sequences"] = [s.model_dump() for s in pydantic_sequences]
```

이 발췌는 판정 실패가 후속 상태 반영을 중단시키는 연결을 보여준다. 바깥 예외 처리의 복구와 저장·응답 순서는 아래에 이어서 제시한다. 의미 판정의 정확도와 상태 보존·최종 표시의 관측 결과는 [최종보고서](../docs/Hallucination_최종보고서.pdf) 제4.4절에서 구분하여 설명한다.

## 실패 복구와 저장 후 응답

앞의 검수 호출에서 발생한 예외는 `process_action_stream`의 바깥 예외 처리로 전달된다. 아래는 같은 구현의 행동 전 스냅샷, 복구, 저장 및 응답 전송 구간이다. 각 블록은 연속된 원문이며, 중간에 생략한 처리는 설명으로 구분한다.

### 행동 전 상태와 복구 대상

일반 행동을 준비하는 `prepare_active_phase`는 캐릭터의 상태 변경 전에 다음 스냅샷을 보관한다. 앞선 선택 검사와 뒤따르는 정산 준비는 생략하였다.

```python
        session[ACTIVE_TURN_PLAYER_SNAPSHOT_KEY] = player.snapshot()
```

게임 루프의 복구 메서드는 해당 스냅샷을 꺼내 같은 캐릭터 객체에 복원한다. 아래 두 블록은 각각 메서드 전체다. 기간 경계 복원과 런타임 캐시 해제 함수의 내부는 포함하지 않는다.

```python
    @staticmethod
    def _restore_active_turn_player(session: dict) -> bool:
        """Commit 전 실패 시 active turn의 Character 상태를 원상 복원한다."""
        snapshot = session.pop(ACTIVE_TURN_PLAYER_SNAPSHOT_KEY, None)
        player = session.get("player")
        if snapshot is None or player is None:
            return False
        player.restore(snapshot)
        return True
```

```python
    def _rollback_active_turn(self, session_id: str, session: dict) -> None:
        """Outer commit 전 상태를 복원하고 실패한 런타임 캐시를 폐기한다."""
        restore_period_boundary_rollback_token(session)
        self._restore_active_turn_player(session)
        from src.cache.custom_cache import release_game_cache
        release_game_cache(session_id)
```

`player.restore`는 저장 상태의 형식과 아이템 원장을 먼저 검증한다. 다음은 그 뒤 실제로 수치·소유물·위치를 대입하는 연속 구간이다. `restored_item_ledger`는 앞에서 스냅샷의 아이템 원장으로 생성한 객체다. 인물 정체성·관계 그래프·사회 관계 등의 다른 복원 부분은 생략하였다.

```python
        # Progression
        self.level = snap.get("level", self.level)
        self.exp = snap.get("exp", self.exp)
        self.job = snap.get("job", self.job)
        self.job_tier = snap.get("job_tier", self.job_tier)
        self.gold = snap.get("gold", self.gold)

        # Stats
        if "stats" in snap and isinstance(snap["stats"], dict):
            self.stats = snap["stats"]

        # HP/MP
        if "current_hp" in snap:
            self._current_hp = snap["current_hp"]
        if "current_mp" in snap:
            self._current_mp = snap["current_mp"]

        # Inventory & Equipment
        self.inventory = snap.get("inventory", self.inventory)
        self.item_ledger = restored_item_ledger
        self.equipment = snap.get("equipment", self.equipment)
        self.equipped_stats = snap.get("equipped_stats", self.equipped_stats)
        self.equipment_registry = snap.get("equipment_registry", self.equipment_registry)
        self.current_location = snap.get("current_location", self.current_location)
        self.location_hierarchy = snap.get("location_hierarchy", self.location_hierarchy)
```

### 저장 완료를 확인한 뒤 전송

`_commit_session_strict`는 저장 작업을 시작하고 완료 결과를 확인한다. 호출자가 취소되더라도 진행 중인 저장 작업을 기다리며, `save_task.result()`의 예외는 호출자에게 전달된다. `_save_session_strict`는 세션 저장 계층을 호출하며 그 내부와 DB 트랜잭션 구현은 발췌에서 생략하였다.

```python
    async def _commit_session_strict(self, session_id: str) -> bool:
        """Persist one turn without mistaking to_thread cancellation for rollback.

        Returns True when the caller was cancelled while persistence was in flight.
        The save task is still awaited to a definitive success/failure before return.
        """
        save_task = asyncio.create_task(self._save_session_strict(session_id))
        cancellation_requested = False
        while not save_task.done():
            try:
                await asyncio.shield(save_task)
            except asyncio.CancelledError:
                if save_task.cancelled():
                    raise
                cancellation_requested = True
        save_task.result()
        return cancellation_requested
```

`process_action_stream`은 아래 저장 호출이 끝난 뒤 `save_committed`를 설정한다. 이 구간은 [상태 응답에 연결](#상태-응답에-연결)의 `STATE_UPDATE` 전송보다 앞에 있다. 중간의 알림 구성과 서술 이벤트 전송은 생략하였다.

```python
                self._mark_turn_succeeded(session, active_turn)
                cancelled_during_save = await self._commit_session_strict(session_id)
                save_committed = True
                self._confirm_turn_commit(session, active_turn)
                self._discard_active_turn_player_snapshot(session)
                if cancelled_during_save:
                    raise asyncio.CancelledError
```

그 응답의 `character`는 앞서 실제 캐릭터 객체에서 구성한다. `player_updates`는 위에서 설명한 정산 기반 변경량이고, `sequences`는 검수를 통과한 장면이다. 이 세 항목이 함께 `STATE_UPDATE`로 전달되며, Flutter에서 처리하는 내부는 포함하지 않는다.

```python
                char_state = self._map_character_state(
                    player,
                    session=session,
                    session_id=session_id,
                ).model_dump()
```

### 저장 전 실패와 저장 후 실패의 구분

아래는 같은 `process_action_stream`의 일반 예외 처리 블록 전체다. 앞선 `try` 본문과 별도의 취소 예외 블록은 생략하였다. 저장 전 실패에서는 행동을 복구하고 세션 캐시를 해제한 뒤 오류 이벤트를 보낸다. 저장 후 오류에서는 이 복구 분기를 실행하지 않고 별도의 오류를 알린다. `is_conclusive_llm_generation_failure`의 분류와 턴 상태 기록 함수의 내부는 생략하였다.

```python
            except Exception as e:
                logger.error(f"[SSE] Active phase error for session {session_id} (committed={save_committed}): {e}", exc_info=True)
                if not save_committed:
                    self._rollback_active_turn(session_id, session)
                    conclusive_llm_failure = (
                        is_conclusive_llm_generation_failure(e)
                    )
                    if conclusive_llm_failure:
                        await self._mark_turn_rolled_back(
                            session_id,
                            session,
                            active_turn,
                            error_code=getattr(
                                e,
                                "error_code",
                                "SCENE_GENERATION_FAILED",
                            ),
                            error_message=_SCENE_ROLLBACK_PLAYER_MESSAGE,
                        )
                        log_event(
                            session_id,
                            "scene_candidate_contained",
                            player_action_id=active_turn["turn_id"],
                            source="active",
                            error_code=getattr(
                                e,
                                "error_code",
                                type(e).__name__,
                            ),
                            evidence_ids=list(
                                getattr(e, "evidence_ids", ())
                            ),
                            continuation="last_committed_scene",
                        )
                    else:
                        await self._safe_mark_turn_failed(
                            session_id,
                            session,
                            active_turn,
                            error_code=getattr(e, "error_code", "TURN_FAILED"),
                            error_message=_TURN_ROLLBACK_PLAYER_MESSAGE,
                        )
                    # commit 전 실패 → in-memory 폐기. 다음 요청은 DB의 마지막 commit 상태에서 재로드.
                    self._session_svc.evict_session(session_id)
                    yield SSEEvent(event=SSEEventType.ERROR, data={
                        "error_code": (
                            "SCENE_GENERATION_ROLLED_BACK"
                            if conclusive_llm_failure
                            else "TURN_ROLLBACK"
                        ),
                        "message": (
                            _SCENE_ROLLBACK_PLAYER_MESSAGE
                            if conclusive_llm_failure
                            else _TURN_ROLLBACK_PLAYER_MESSAGE
                        ),
                    })
                else:
                    # commit 후 부수 작업(usage stats 등) 실패. 데이터는 이미 commit됨.
                    yield SSEEvent(event=SSEEventType.ERROR, data={
                        "error_code": "POST_COMMIT_ERROR",
                        "message": str(e),
                    })
```

이 발췌는 거절 예외가 복구로 이어지는 조건, 일부 상태의 실제 복원, 저장 완료 확인과 상태 응답 전송의 순서를 보여준다. 모든 상태·DB·클라이언트의 완전한 복구나 재시도 성공률까지 입증하지는 않는다. 이미 결과를 별도로 확정하는 보스전 등의 경로도 이 일반 행동 구간과 구분한다. 관측된 상태 유지·표시 결과와 수집 한도에 따른 진행 종료는 최종보고서 제4.2.1절과 제4.4절에 제시되어 있다.
