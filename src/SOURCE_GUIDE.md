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

이 발췌는 판정 실패가 후속 상태 반영을 중단시키는 연결을 보여준다. `_apply_post_resolution`의 내부 적용·복구, 영속 저장과 Flutter 표시까지 포함하지는 않는다. 의미 판정의 정확도와 상태 보존·최종 표시의 관측 결과는 [최종보고서](../docs/Hallucination_최종보고서.pdf) 제4.4절에서 구분하여 설명한다.
