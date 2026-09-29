# 주요 구현 안내

최종보고서의 설계·처리에 해당하는 함수·메서드와 클래스·열거형 일부를 발췌하였다. 생략된 보조 함수와 객체 초기화의 전제는 각 항목에 설명한다. 독립 실행 패키지는 아니다.

처리 흐름: [수치 적용](#수치-변경의-권한과-실제-적용) · [정산과 응답](#시스템-수치로-구성하는-응답) · [기억 입력](#기억과-공동-경험의-생성-요청-연결) · [검수](#검수와-상태-반영의-호출-흐름) · [복구와 저장](#실패-복구와-저장-후-응답)

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

판정 개수, 필드 구성, 식별자의 유효성과 중복, 판정 값 및 근거 범위를 검사한다. 예를 들어 증거가 두 개일 때 같은 식별자의 판정을 두 번 반환하면 판정 개수가 맞더라도 오류가 된다. 정상 형식의 응답에서는 `reject`인 항목만 해당 주장과 함께 반환한다. 빈 목록은 거절 판정이 없다는 뜻이다.

형식 위반 시 `LLMResponseContractException`을 발생시킨다. 이 함수는 자연어의 진위를 판단하지 않고 판정 응답을 검사한다.

`require_narrative_admission`은 주장·장면 범위 판정의 거절 식별자를 모은다. 선택 이행 판정이 `fulfilled`가 아니면 해당 판정의 식별자를 거절 목록에 합치고, 최종 목록이 비어 있지 않으면 `NarrativeCandidateRejected`를 발생시킨다. 이 예외가 추출 처리를 중단시키는 경로는 아래 [호출 흐름](#검수와-상태-반영의-호출-흐름)에 제시한다.

장면 범위·선택 판정의 보조 검사 함수와 두 예외 클래스의 정의는 발췌에서 생략하였다. 상태 복구는 이 함수 밖에서 처리한다.

## 작업 기억에서 일화 기억으로의 승격

`MemoryPromoter.on_completed_scene`은 완료 장면의 번호와 양의 체크포인트 번호를 받는다. `self.working`에서 슬롯을 조회하고, 중요도 조건을 만족하면서 아직 승격하지 않은 슬롯을 `self.episodic`에 추가한다. 내용·중요도·출처 메타데이터를 전달하고 승격한 장면을 슬롯에 기록하여 반복 추가를 막는다.

새로 추가한 일화 기억 항목 목록을 반환한다. 중요도는 기억의 보존 기준이며 사실 정확도의 점수가 아니다.

## 공동 경험의 표현과 조회

`EdgeType`에는 공동 사건 조회에 쓰는 세 관계 유형을, `HyperEdge`에는 여러 노드를 역할과 함께 연결하는 필드를 담았다. `HyperGraph.add_edge`는 참조 노드의 존재를 확인하고 간선과 노드별 인접 인덱스를 등록한다. `get_shared_events`는 두 노드 중 인접 간선이 적은 쪽을 탐색하여, 두 노드가 모두 포함된 참여·목격·원인 관계를 가중치 내림차순으로 반환한다.

노드·간선 사전과 인접 인덱스는 호출 전에 초기화되어 있어야 한다. 조회 결과를 맥락으로 구성하고 생성 요청에 전달하는 연결은 [기억과 공동 경험의 생성 요청 연결](#기억과-공동-경험의-생성-요청-연결)에 제시한다.

## 수치 변경의 권한과 실제 적용

상태에서 응답 수치를 계산하는 것과 상태 자체를 변경하는 것은 별개의 단계다. 아래는 생성 응답의 수치 필드를 거절하는 경계와 전투 시스템이 캐릭터 수치를 변경하는 구간이다. 각 블록은 기존 구현의 연속된 원문이다.

### 생성 응답의 필드 검사

[추출 응답 처리](#응답-검사와-추출-결과-반환)에서 호출하는 `project_fresh_system_updates`는 다음 필드 검사로 시작한다. 허용된 기본 필드와 선택적인 `public_speech_priors` 외의 필드가 있으면 오류를 발생시킨다. 따라서 이 경로에 `player_updates`, `hp_change`, `mp_change`, `gold_change`를 추가한 생성 응답은 그대로 적용되지 않는다. 뒤따르는 인물 참조 검사와 반환은 생략하였다.

```python
def project_fresh_system_updates(
    raw_response: Any,
    raw_catalog: Any,
    *,
    new_actors: Sequence[Mapping[str, Any]],
    player_name: str,
    allowed_actor_refs: Sequence[str],
) -> dict[str, Any]:
    """Project Phase2 actor references without asking it to re-author identity."""
    if not isinstance(raw_response, Mapping):
        raise ValueError("fresh SYSTEM_UPDATES response must be an object")
    expected_response_fields = {
        "actor_updates",
        "dialogue_observations",
        "memory_update",
        "memory_importance",
    }
    response_fields = set(raw_response)
    if response_fields not in (
        expected_response_fields,
        expected_response_fields | {PUBLIC_SPEECH_PRIORS_FIELD},
    ):
        raise ValueError(
            "fresh SYSTEM_UPDATES response must use the exact provider shape"
        )
```

`PUBLIC_SPEECH_PRIORS_FIELD`는 `public_speech_priors`를 가리킨다. 이 함수의 `ValueError`는 [응답 검사와 추출 결과 반환](#응답-검사와-추출-결과-반환)에 제시한 호출부에서 계약 오류로 전달되어 후속 처리를 중단한다. 이 필드 검사는 인물 참조 자료를 사용하는 응답 경로에 적용된다.

### 전투 결과의 HP·MP 반영

`prepare_active_phase`가 호출하는 `resolve_pending_states`에서 보류된 전투를 수락한 분기는 다음과 같이 전투 서비스를 호출한다. `enc`와 `floor`는 앞에서 읽은 전투 정보이고, `actor_outcome_kwargs`는 참여 인물의 결과 처리에 필요한 맥락이다. 선택 확인과 이 값들의 준비는 생략하였다.

```python
                    result = self._loop._combat.resolve_mob_combat(
                        player, floor, enc, allow_auto_flee=False,
                        **actor_outcome_kwargs,
                    )
```

전투 서비스는 같은 인자들을 내부의 `resolve_mob_combat`에 전달한다. 아래는 내부 메서드의 시뮬레이션 실행과 결과 적용이다. `sim`에는 캐릭터에서 만든 `player_combatant`와 상대 전투 개체가 앞서 등록되어 있다. 개체 구성과 전투 계산식은 생략하였다.

```python
        result = sim.simulate(max_turns=50)
        party_history_candidate = player.party_combat_history_update(
            party_combat_records,
            sim.party_coordination_outcomes(),
        )

        # 결과 적용
        player.current_hp = max(0, int(player_combatant.stats.hp))
        player.current_mp = max(0, int(player_combatant.stats.mp))
        hp_after = player.current_hp
```

여기서 실제 HP·MP에 대입되는 값은 시뮬레이터가 갱신한 전투 개체의 값이다. 생성 문장에서 수치를 추출하여 이 대입에 사용하는 구조가 아니다.

### 전투 보상의 골드 반영

같은 전투 메서드는 보상 지급이 가능한 승리일 때 시뮬레이터의 시드·사건과 상대 정보로 보상 입력을 만든다.

```python
        reward_context = None
        if award_rewards and result == "player_victory" and not is_pk:
            reward_context = build_combat_reward_context(
                combat_id=combat_id,
                seed=sim.seed,
                events=sim.events,
                monsters=defeated_info,
            )
```

그 뒤 실제 처치 대상이 있는지 확인하여 보상 계산을 호출한다. 두 블록 사이의 처치·도주 표시 정보 구성은 생략하였다.

```python
        if (
            award_rewards
            and result == "player_victory"
            and not is_pk
            and reward_context is not None
            and reward_context.targets
        ):
            rewards = self._svc.calculate_combat_rewards(
                player,
                reward_context,
                staged=True,
            )
```

`CombatService.calculate_combat_rewards`의 위임 메서드 전체는 다음과 같다.

```python
    def calculate_combat_rewards(self, player, reward_context, staged=False, party_size=1, is_first_clear=False):
        return self._rewards.calculate_combat_rewards(player, reward_context, staged=staged, party_size=party_size, is_first_clear=is_first_clear)
```

보상 계산기는 위에서 구성한 `CombatRewardContext`를 받는다. 다른 형식의 입력은 `TypeError`로 거절한다.

```python
        if not isinstance(reward_context, CombatRewardContext):
            raise TypeError(
                "combat rewards require a CombatRewardContext built from "
                "simulator seed and defeat events"
            )
```

보상 대상별 반복문 안에서는 시스템 계산값을 합산한다. 앞선 대상 선정·보상 제외 조건과 계산 함수 내부는 생략하였다.

```python
            exp = self.calculate_exp_reward(player_level, monster_level, monster_grade, hp_percent)
            gold = self.calculate_gold_reward(player_level, monster_level, monster_grade)

            # 레이드 인원 분배 (party_size > 1일 때만)
            if party_size > 1:
                exp = int(exp / party_size)
                gold = int(gold / party_size)

            total_exp += exp
            total_gold += gold
```

합산한 골드는 같은 메서드에서 실제 캐릭터에 반영한다. 사이의 아이템·경험치 처리와 뒤따르는 알림 구성은 생략하였다. `staged=True`는 이 경로에서 장비·재료 적용을 보류하는 옵션이며, 골드 적용을 보류하지 않는다.

```python
        if total_gold > 0:
            gold_result = player.adjust_gold(total_gold, "전투 보상")
```

`adjust_gold` 내부의 실제 대입은 다음과 같다. 메서드의 로그 기록과 반환값 구성은 생략하였다.

```python
        old_gold = self.gold
        self.gold = max(0, self.gold + amount)
        actual_change = self.gold - old_gold
```

전투 후의 캐릭터 상태는 아래 정산 생성의 입력이 된다. 이동·시설·아이템 사용 등 다른 상태 변경 경로는 이 발췌에 포함하지 않았다.

## 시스템 수치로 구성하는 응답

게임 상태의 수치와 생성 문장의 주장은 서로 다른 근거를 가진다. 아래는 서버의 실제 전후 상태에서 자원 변경량을 계산하고, 정산 결과가 있는 응답의 수치 필드에 그 값을 사용하는 구간이다. 기존 발췌와 같은 구현에서 가져왔으며 각 코드 블록은 연속된 원문이다.

### 행동 전 비교 기준의 갱신

`prepare_active_phase`는 해당 행동을 처리하기 전에 비교 기준을 다시 기록한다. 아래는 행동 전 수치 사전의 대입 전체다. 앞선 캐릭터 조회와 별도의 복구용 스냅샷 처리는 생략하였다.

```python
        session["_pre_action_stats"] = {
            "hp": player.current_hp,
            "mp": player.current_mp,
            "gold": player.gold,
            "exp": getattr(player, "exp", 0),
            "level": getattr(player, "level", 0),
            "location": getattr(player, "current_location", ""),
        }
```

정산 생성 시 `session.pop("_pre_action_stats", None)`으로 이 사전을 꺼낸다. `_last_settlement_result`는 행동 준비 단계에서 초기화하지 않고, 아래 정상 완료 경로에서 새 정산으로 덮어쓴다.

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

### 현재 행동의 정산 생성과 세션 기록

후속 상태 처리의 `apply_post_resolution_inner`는 아래 호출로 현재 행동의 정산을 구성한다. 앞선 상태 적용과 드롭 처리, 뒤따르는 처리는 생략하였다.

```python
        self._settlements.apply_post_resolution_settlement(
            session=session,
            player=player,
            result=result,
            transition_result=transition_result,
            scene_frame_contract=session.get("_last_scene_time_contract"),
            drop_settlement=drop_settlement,
        )
```

호출된 `apply_post_resolution_settlement`는 행동 전 스냅샷과 현재 캐릭터를 `SettlementResult.from_pipeline_state`에 전달한다. 이 구성 메서드는 위의 `ResourceDelta.from_player`로 자원 변경량을 만든다. 아래는 정산 객체 생성, 응답 변경량 반영, 세션 기록이 이어지는 원문이다. 앞에서 준비한 전투·드롭·시간 등의 지역변수와 구성 메서드의 다른 필드는 생략하였다.

```python
        pre_stats = session.pop("_pre_action_stats", None)
        existing_player_updates = result.get("player_updates")

        settlement_result = SettlementResult.from_pipeline_state(
            scene_frame_contract=scene_frame_contract,
            transition_result=transition_result,
            combat_result=combat_result,
            environmental_hazard=environmental_hazard,
            pre_action_stats=pre_stats,
            player=player,
            notices=snapshot_pending_game_notices(session),
            drop_settlement=drop_settlement,
            runtime_tick=runtime_tick,
            pre_llm_snapshot=pre_llm_snapshot,
            execution_outcome=session.get(EXECUTION_OUTCOME_KEY),
        )
        result["player_updates"] = settlement_result.response_player_updates(
            existing_player_updates
        )
        session["_last_settlement_result"] = settlement_result.to_dict()
```

일반 행동의 정상 완료 경로에서는 현재 정산을 `session["_last_settlement_result"]`에 기록한 뒤 후속 상태 처리가 반환된다. 게임 루프는 이후 저장 완료를 확인하고, 상태 응답을 구성할 때 이 키를 읽는다. 위 대입은 메모리상의 세션 기록이며 DB 저장은 [실패 복구와 저장 후 응답](#실패-복구와-저장-후-응답)에서 별도로 처리한다.

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

보조 함수 `_copy_player_updates`는 매핑을 깊은 복사하고, `_response_player_update_int`는 불리언을 제외한 정수만 허용한다. `_reject_existing_resource_updates`는 스냅샷이 없는 정산에 기존 HP·MP·골드 변경 필드가 섞여 있으면 오류를 발생시킨다. `SettlementResult`의 객체 정의와 이 보조 함수들은 생략하였다. 정산이 `None`이면 기존 응답 필드를 그대로 반환한다.

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

정산 결과가 있는 응답의 수치 변경량은 실제 상태의 전후 차이로 구성된다. 전투 계산식 전체와 Flutter의 응답 처리는 생략하였다. 최종보고서 제4.4절에 전투 관측 결과를, 제4.4.1절에 잘못된 마나 회복 서술이 표시되었지만 실제 MP는 유지된 사례를 제시하였다.

## 기억과 공동 경험의 생성 요청 연결

장기 기억은 일반 행동 서술의 입력으로, 공동 경험은 시작 장면의 맥락으로 전달된다. 아래에 두 경로의 조회·조립·요청 코드를 제시한다. 프롬프트 본문과 기억 선택 알고리즘 내부는 생략하였다.

### 장기 기억에서 일반 행동 서술로

캐릭터의 `get_memory_context`는 연결된 기억 시스템에 조회를 위임한다. 아래는 그 분기다. 뒤따르는 미연결 오류 처리는 생략하였다.

```python
        if self._memory_system:
            return self._memory_system.get_context(
                exclude_sensory=exclude_sensory,
                seen_contents=seen_contents,
                scene_start=scene_start,
                scene_end=scene_end,
            )
```

기억 시스템의 `get_context`는 입력 예산과 각 계층을 맥락 구성기에 전달한다. 아래는 반환 구간이며, 앞선 예산 결정과 구성기 내부의 선택·요약 처리는 생략하였다. 일화 기억에는 [기억 승격](#작업-기억에서-일화-기억으로의-승격)에서 추가한 항목이 보관되며, 입력에는 예산에 맞게 선택한 항목을 사용한다.

```python
        return self._budget.build_context(
            total_budget, self.sensory, self.working, self.episodic, self.semantic,
            exclude_sensory=exclude_sensory,
            seen_contents=seen_contents,
            scene_start=scene_start,
            scene_end=scene_end,
        )
```

일반 행동의 생성 요청을 만드는 구간은 이 기억을 조회하고 현재 정산과 충돌하는 기억 맥락을 검사한다. `seen_contents`는 이미 공급한 내용의 중복을 줄이기 위한 집합이다. 검사 함수 내부는 생략하였다.

```python
        _long_term_memory = self._guardrail.filter_llm_memory_context_for_mechanical_conflicts(
            player.get_memory_context(
                exclude_sensory=True,
                seen_contents=session.get("_prompt_seen_contents"),
            ),
            session,
        )
```

그 반환값은 `format_kwargs.update(...)`의 다음 인자로 전달된다. 아래 한 줄은 호출의 키워드 인자 발췌이며 독립 문장이 아니다.

```python
            long_term_memory=_long_term_memory,
```

템플릿의 `long_term_memory` 자리에 값을 넣은 뒤 요청의 `user_prompt`로 전달한다. 다음 두 블록 사이의 요청 부가 정보 구성과 조건부 서두 추가는 생략하였다.

```python
        prompt = prompt_template.format(**format_kwargs)
```

```python
        request = LLMRequest(
            cacheable_prefix=build_cacheable_block(_revealed, _awareness, _pioneer_arg),
            user_prompt=prompt,
            prompt_name=prompt_name, response_schema=schema,
            cache_type="narrative",
            deathgame_revealed=_revealed,
            max_output_tokens=16384,
            metadata=request_metadata,
        )
```

이 요청은 아래 호출로 응답 처리 래퍼에 전달된다. 사이의 `project_active_response` 정의는 생략하였다. 래퍼가 실제 모델 라우터의 `generate`를 호출하는 구간은 [응답 검사와 추출 결과 반환](#응답-검사와-추출-결과-반환)에 제시되어 있다.

```python
        projected = await self._generate_scene_response_with_structural_recovery(
            request,
            project_active_response,
        )
```

### 공동 사건 조회에서 시작 장면 요청으로

`build_encounter_history_context`는 앞서 공개한 `get_shared_events`의 결과에서 사건 요약을 선택한다. 아래는 목록 초기화부터 반환까지의 원문이다. 인자 선언은 생략하였으며, `npc_ids`는 조회할 인물 식별자 목록이고 `max_events_per_npc`는 인물별 최대 사건 수다. 기존 인자 이름에 `npc`가 쓰이지만 게임 속 다른 플레이어를 가리킨다.

```python
        lines: List[str] = []

        for npc_id in npc_ids[:5]:
            node = graph.get_node(npc_id)
            if not node:
                continue
            shared = get_shared_events(graph, player_id, npc_id)
            if not shared:
                continue
            for edge in shared[:max_events_per_npc]:
                content = edge.properties.get("summary", "")
                if not content:
                    continue
                if seen_contents is not None and content in seen_contents:
                    continue
                lines.append(f"- {node.label}과(와)의 경험: {content}")
                if seen_contents is not None:
                    seen_contents.add(content)
        return "\n".join(lines)
```

맥락 구성기는 현재 인물·파티에서 준비한 식별자 목록으로 위 함수를 호출하고 결과가 있을 때만 `[공유 경험]` 항목에 넣는다. 앞선 식별자 목록 구성과 이후 관계 정보 구성은 생략하였다. `episodic_memory` 인자는 이 조회 함수에서 사용하지 않으며, 공급되는 내용은 위 코드의 간선 `summary`다.

```python
                if encountered_nids:
                    _mem_sys = session.get("memory_system")
                    _episodic = _mem_sys.episodic if _mem_sys else None
                    _seen = session.get("_prompt_seen_contents")
                    history_ctx = GraphQueries.build_encounter_history_context(
                        session["graph"], player._graph_node_id, encountered_nids,
                        episodic_memory=_episodic,
                        seen_contents=_seen,
                    )
                    if history_ctx:
                        parts.append(f"[공유 경험]\n{history_ctx}")
```

이 항목은 `active_narration_projection`이 거짓일 때 `world_context`에 추가된다. 일반 행동 서술용 맥락에서는 이 값이 참이므로 해당 블록을 추가하지 않는다. 앞선 위치 정보 구성과 뒤따르는 파티·안내 정보 추가는 생략하였다.

```python
            if not active_narration_projection:
                wc_parts.extend(self._build_graph_and_arc_context(session, player))

            wc_parts = [
                self._filter_llm_context_conflicts(part, session, player)
                for part in wc_parts
                if part
            ]
            world_context = "\n\n".join(part for part in wc_parts if part)
```

시작 장면에서는 `get_world_context`가 `OPENING_SCENE`에 해당하는 맥락을 반환하고, 구간 처리의 호출자가 이를 생성 메서드에 전달한다. 게임 루프의 `_get_world_context`는 맥락 구성기의 동명 메서드에 위임한다.

```python
        _, world_context = self.build_classified_context(
            session,
            opening_location_scope=strategy_key == "OPENING_SCENE",
        )
        return world_context
```

```python
            new_scene = await self._loop._scene_engine.generate_opening_scene(
                player, session, self._loop._get_world_context("OPENING_SCENE", session)
            )
```

`generate_opening_scene`은 전달받은 값을 `format_kwargs.update(...)`의 아래 인자로 넣는다. 이 한 줄 역시 호출의 키워드 인자 발췌다. `_without_scene_route_catalog_blocks`는 장면 경로 목록 블록을 제외하는 함수이며 내부는 생략하였다.

```python
            world_context=_without_scene_route_catalog_blocks(world_context),
```

그 뒤 템플릿을 채우고 시작 장면 요청을 만든다. 사이의 응답 스키마·공통 입력 준비는 생략하였다.

```python
        prompt = user_template.format(**format_kwargs)
```

```python
        request = LLMRequest(
            cacheable_prefix=build_cacheable_block(_revealed, _awareness, _pioneer_arg),
            user_prompt=prompt,
            prompt_name="PROMPT_OPENING_SCENE", response_schema=schema,
            cache_type="narrative",
            deathgame_revealed=_revealed,
            max_output_tokens=16384,
            metadata=_llm_request_metadata_for_session(session),
        )
```

후보 생성 반복문에서는 이 요청의 식별자와 부가 정보만 갱신한 복사본을 만들고, 응답 처리 래퍼에 전달한다. 아래 두 블록 사이에는 `try`가 있으며 주변 반복문과 예외 처리는 생략하였다. `user_prompt`는 이 복사 과정에서 바꾸지 않는다.

```python
            candidate_request = request.model_copy(update={
                "operation_id": request.operation_id if candidate_attempt == 1 else str(uuid4()),
                "metadata": {
                    **request.metadata,
                    "opening_candidate_attempt": candidate_attempt,
                    "opening_candidate_limit": candidate_limit,
                },
            })
```

```python
                projected = await self._generate_scene_response_with_structural_recovery(
                    candidate_request,
                    project_opening_response,
                )
```

선택된 기억·사건 요약은 위 경로를 통해 요청 입력에 포함된다. 공유 경험의 관측 사례는 2026년 8월 1일의 별도 실행 결과다. 해당 사례와 기억 입력 비교의 실험 조건·결과는 [README](../README.md#실제-동작과-평가-결과)에 정리하였다.

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

위 코드는 일반 행동에서 저장 전 실패를 복구하고, 저장 완료 후 상태 응답을 전송하는 경로다. DB 트랜잭션, Flutter의 처리, 결과를 별도로 확정하는 보스전 경로는 생략하였다. 상태 유지·표시 결과와 수집 한도에 따른 진행 종료는 최종보고서 제4.2.1절과 제4.4절에 제시하였다.
