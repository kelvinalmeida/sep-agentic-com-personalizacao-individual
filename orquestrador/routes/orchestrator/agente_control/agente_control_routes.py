import os
import requests
import logging
import unicodedata
from datetime import datetime
from collections import Counter
from flask import Blueprint, jsonify, request
from ...services_routs import CONTROL_URL, STRATEGIES_URL, USER_URL, DOMAIN_URL

agente_control_orch_bp = Blueprint('agente_control_orch_bp', __name__)

try:
    TACTIC_DECISION_TTL_SECONDS = max(
        0,
        int(os.environ.get("TACTIC_DECISION_TTL_SECONDS", "45"))
    )
except Exception:
    TACTIC_DECISION_TTL_SECONDS = 45


def _safe_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_text(value):
    return " ".join(str(value or "").split())


def _normalize_label(value):
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return _normalize_text(text).lower()


def _parse_datetime(value):
    if isinstance(value, datetime):
        return value
    if not value:
        return None

    raw = str(value).strip()
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        pass

    for fmt in (
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue

    return None


def _get_tactic_kind(tactic):
    normalized_name = _normalize_label(tactic.get("name", ""))
    normalized_description = _normalize_label(tactic.get("description", ""))
    text = f"{normalized_name} {normalized_description}".strip()

    if "mudanca de estrategia" in normalized_name or "mudanca de estrategia" in text:
        return "strategy_change"
    if "reuso" in text:
        return "reuse"
    if "debate" in text or "sincrono" in text:
        return "debate"
    if "envio de informacao" in text:
        return "information"
    if "regra" in text:
        return "rules"
    return "other"


def _find_review_tactic_index(current_index, tactics):
    review_priority = {
        "reuse": 0,
        "information": 1,
        "debate": 2,
        "other": 3,
    }
    candidates = []
    for idx, tactic in enumerate(tactics):
        kind = _get_tactic_kind(tactic)
        if kind == "strategy_change":
            continue
        distance = abs(idx - current_index)
        candidates.append((distance, review_priority.get(kind, 4), idx, idx))

    if not candidates:
        return current_index

    candidates.sort()
    return candidates[0][3]


def _find_advancement_tactic_index(current_index, executed_indices, tactics):
    executed_set = {
        idx for idx in executed_indices
        if isinstance(idx, int) and 0 <= idx < len(tactics)
    }

    for idx in range(current_index + 1, len(tactics)):
        if idx in executed_set:
            continue
        if _get_tactic_kind(tactics[idx]) == "strategy_change":
            continue
        return idx

    for idx in range(current_index + 1, len(tactics)):
        if _get_tactic_kind(tactics[idx]) != "strategy_change":
            return idx

    return current_index


def _select_display_tactic_index(recommended_indices, fallback_index=0):
    if not recommended_indices:
        return fallback_index

    distribution = Counter(recommended_indices)
    return max(distribution.items(), key=lambda item: (item[1], item[0]))[0]


def _build_rule_decision(student_state, tactics, difficulty_data=None):
    if not tactics:
        return None

    current_index = _safe_int(student_state.get("current_tactic_index"), 0)
    current_index = max(0, min(current_index, len(tactics) - 1))
    executed_indices = student_state.get("executed_indices", [])
    if not isinstance(executed_indices, list):
        executed_indices = []

    started_at = _parse_datetime(student_state.get("current_tactic_started_at"))
    if started_at and TACTIC_DECISION_TTL_SECONDS > 0:
        elapsed_seconds = (datetime.utcnow() - started_at).total_seconds()
        if 0 <= elapsed_seconds < TACTIC_DECISION_TTL_SECONDS:
            return {
                "tactic_index": current_index,
                "source": "ttl_keep",
                "reason": (
                    f"Aluno ainda está dentro da janela mínima de {TACTIC_DECISION_TTL_SECONDS}s "
                    f"na tática atual; mantido sem nova consulta à IA."
                ),
                "force_apply": False,
                "chosen_tactic_id": tactics[current_index].get("id")
            }

    last_rating = _safe_int(student_state.get("last_rating"))
    if last_rating is not None:
        if last_rating <= 2:
            review_index = _find_review_tactic_index(current_index, tactics)
            return {
                "tactic_index": review_index,
                "source": "rule_rating_review",
                "reason": (
                    "Avaliação recente baixa; o fluxo aplicou reforço local antes de consultar a IA."
                ),
                "force_apply": True,
                "chosen_tactic_id": tactics[review_index].get("id")
            }

        if last_rating >= 4:
            next_index = _find_advancement_tactic_index(current_index, executed_indices, tactics)
            if next_index != current_index:
                return {
                    "tactic_index": next_index,
                    "source": "rule_rating_advance",
                    "reason": (
                        "Avaliação recente alta; o fluxo avançou localmente para a próxima tática adequada."
                    ),
                    "force_apply": True,
                    "chosen_tactic_id": tactics[next_index].get("id")
                }

    if not isinstance(difficulty_data, dict):
        return None

    total_questions = _safe_int(difficulty_data.get("total_questions"), 0) or 0
    wrong_count = _safe_int(difficulty_data.get("wrong_count"), 0) or 0
    correct_count = _safe_int(difficulty_data.get("correct_count"), 0) or 0

    if total_questions <= 0:
        return None

    if wrong_count == 0 and correct_count > 0:
        next_index = _find_advancement_tactic_index(current_index, executed_indices, tactics)
        if next_index != current_index:
            return {
                "tactic_index": next_index,
                "source": "rule_difficulty_advance",
                "reason": (
                    "Sem erros na sessão atual; o fluxo avançou localmente sem sobrecarregar a IA."
                ),
                "force_apply": True,
                "chosen_tactic_id": tactics[next_index].get("id")
            }

    if wrong_count >= max(2, (total_questions + 1) // 2):
        review_index = _find_review_tactic_index(current_index, tactics)
        return {
            "tactic_index": review_index,
            "source": "rule_difficulty_review",
            "reason": (
                "Erros relevantes na sessão atual; o fluxo escolheu reforço local antes de consultar a IA."
            ),
            "force_apply": True,
            "chosen_tactic_id": tactics[review_index].get("id")
        }

    return None


def _build_exercise_context_for_session(session_id):
    exercise_context_by_id = {}
    session_resp = requests.get(f"{CONTROL_URL}/sessions/{session_id}", timeout=10)
    if session_resp.status_code != 200:
        return None, (
            jsonify({
                "error": "Não foi possível obter metadados da sessão no Control",
                "details": session_resp.text
            }),
            session_resp.status_code
        )

    session_data = session_resp.json() or {}
    domain_ids = session_data.get('domains', [])

    for domain_id in domain_ids:
        try:
            ex_resp = requests.get(f"{DOMAIN_URL}/domains/{int(domain_id)}/exercises", timeout=10)
            if ex_resp.status_code != 200:
                logging.warning(
                    "Falha ao buscar exercícios no Domain. session_id=%s domain_id=%s status=%s",
                    session_id, domain_id, ex_resp.status_code
                )
                continue

            exercises = ex_resp.json()
            if isinstance(exercises, list):
                for exercise in exercises:
                    if not isinstance(exercise, dict):
                        continue
                    ex_id = exercise.get('id')
                    if ex_id is not None:
                        exercise_context_by_id[str(ex_id)] = exercise
        except Exception as ex_err:
            logging.warning(
                "Erro ao buscar exercícios no Domain. session_id=%s domain_id=%s error=%s",
                session_id, domain_id, str(ex_err)
            )

    # Fallback: quando a sessão não tem domains mapeados (ou falharam),
    # tenta buscar todos os domínios para localizar os exercícios por ID.
    if not exercise_context_by_id:
        try:
            all_domains_resp = requests.get(f"{DOMAIN_URL}/domains", timeout=10)
            if all_domains_resp.status_code == 200:
                all_domains = all_domains_resp.json()
                if isinstance(all_domains, list):
                    for domain in all_domains:
                        exercises = domain.get('exercises', []) if isinstance(domain, dict) else []
                        if not isinstance(exercises, list):
                            continue
                        for exercise in exercises:
                            if not isinstance(exercise, dict):
                                continue
                            ex_id = exercise.get('id')
                            if ex_id is not None:
                                exercise_context_by_id[str(ex_id)] = exercise
        except Exception as fallback_err:
            logging.warning(
                "Fallback de exercícios via /domains falhou. session_id=%s erro=%s",
                session_id, str(fallback_err)
            )

    return exercise_context_by_id, None



@agente_control_orch_bp.route('/orchestrator/agent/tudent_session_difficulty_summary', methods=['POST'])
@agente_control_orch_bp.route('/orchestrator/agent/student_session_learning_support', methods=['POST'])
def orchestrate_student_learning_support():
    """
    Junta:
      1) dificuldades da sessão (Control /agent/student_session_difficulty_summary),
      2) preferências do aluno (User /agent/summarize_logged_user),
    e envia para o agente de estratégia recomendar vídeo do YouTube.
    """
    data = request.get_json() or {}
    student_id = data.get('student_id')
    session_id = data.get('session_id')

    if student_id is None or session_id is None:
        return jsonify({"error": "student_id e session_id são obrigatórios"}), 400

    try:
        exercise_context_by_id, err_resp = _build_exercise_context_for_session(session_id)
        if err_resp:
            return err_resp

        control_payload = {
            "student_id": student_id,
            "session_id": session_id,
            "exercise_context_by_id": exercise_context_by_id
        }
        difficulty_resp = requests.post(
            f"{CONTROL_URL}/agent/student_session_difficulty_summary",
            json=control_payload,
            timeout=60
        )
        if difficulty_resp.status_code != 200:
            return jsonify({
                "error": "Falha ao obter resumo de dificuldade no Control",
                "details": difficulty_resp.text
            }), difficulty_resp.status_code

        user_resp = requests.post(
            f"{USER_URL}/agent/summarize_logged_user",
            json={"user_id": student_id},
            timeout=30
        )
        if user_resp.status_code != 200:
            return jsonify({
                "error": "Falha ao obter preferências no User",
                "details": user_resp.text
            }), user_resp.status_code

        difficulty_data = difficulty_resp.json()
        user_data = user_resp.json()

        strategy_payload = {
            "student_id": student_id,
            "session_id": session_id,
            "difficulty_summary": difficulty_data.get("difficulty_summary", ""),
            "questions_summary": difficulty_data.get("questions_summary", []),
            "wrong_count": difficulty_data.get("wrong_count", 0),
            "profile_summary": user_data.get("summary", "")
        }
        strategy_resp = requests.post(
            f"{STRATEGIES_URL}/agent/recommend_youtube_video",
            json=strategy_payload,
            timeout=60
        )
        study_text_resp = requests.post(
            f"{STRATEGIES_URL}/agent/generate_personalized_study_text",
            json=strategy_payload,
            timeout=60
        )

        strategy_json = {}
        try:
            strategy_json = strategy_resp.json()
        except Exception:
            strategy_json = {"raw": strategy_resp.text}

        study_text_json = {}
        try:
            study_text_json = study_text_resp.json()
        except Exception:
            study_text_json = {"raw": study_text_resp.text}

        return jsonify({
            "student_id": student_id,
            "session_id": session_id,
            "difficulty_data": difficulty_data,
            "profile_data": user_data,
            "video_recommendation": strategy_json,
            "personalized_study_text": study_text_json
        }), 200

    except Exception as e:
        logging.error(f"Erro no orquestrador de learning support: {str(e)}")
        return jsonify({"error": "Falha na orquestração de suporte de aprendizagem"}), 500


def execute_agent_logic(session_id, session_json):
    """
    Executa a lógica do Agente de Estratégia:
    1. Agrega dados (Contexto, Perfil, Performance).
    2. Consulta o Agente.
    3. Aplica a decisão.
    """
    try:
        logging.info("🤖 Agente de Estratégia por aluno ATIVADO. Iniciando ciclo de decisão individual...")

        strategy_id = session_json.get('strategies', [None])[0]
        student_ids = session_json.get('students', [])
        if not strategy_id or not student_ids:
            return None

        strat_res = requests.get(f"{STRATEGIES_URL}/strategies/{strategy_id}")
        if strat_res.status_code != 200:
            logging.error("❌ Não foi possível carregar estratégia atual no Strategies.")
            return None

        tactics = (strat_res.json() or {}).get('tatics', [])
        if not tactics:
            return None

        tactic_idx_by_id = {int(t.get("id")): idx for idx, t in enumerate(tactics) if t.get("id") is not None}
        individual_decisions = []
        recommended_indices = []
        decision_cache = {}
        exercise_context_by_id = None
        session_performance_summary = None
        class_profile_summary = None
        ai_calls_count = 0
        ai_cache_hit_count = 0
        local_rule_count = 0
        ttl_rule_count = 0
        difficulty_fetch_count = 0

        def get_exercise_context_by_id():
            nonlocal exercise_context_by_id
            if exercise_context_by_id is None:
                context, _ = _build_exercise_context_for_session(session_id)
                exercise_context_by_id = context or {}
            return exercise_context_by_id

        def get_session_performance_summary():
            nonlocal session_performance_summary
            if session_performance_summary is None:
                session_performance_summary = "Sem dados de performance da sessão."
                perf_res = requests.get(f"{CONTROL_URL}/sessions/{session_id}/agent_summary", timeout=20)
                if perf_res.status_code == 200:
                    session_performance_summary = (
                        (perf_res.json() or {}).get("summary", session_performance_summary)
                    )
            return session_performance_summary

        def get_class_profile_summary():
            nonlocal class_profile_summary
            if class_profile_summary is None:
                class_profile_summary = "Perfil da turma não disponível."
                class_profile_res = requests.post(
                    f"{USER_URL}/students/summarize_preferences",
                    json={"student_ids": student_ids},
                    timeout=25
                )
                if class_profile_res.status_code == 200:
                    class_summary_raw = (
                        (class_profile_res.json() or {}).get("summary", class_profile_summary)
                    )
                    class_profile_summary = (
                        class_summary_raw
                        if isinstance(class_summary_raw, str)
                        else str(class_summary_raw)
                    )
            return class_profile_summary

        for student_id in student_ids:
            student_state_res = requests.get(
                f"{CONTROL_URL}/sessions/{session_id}/students/{student_id}/current_tactic",
                timeout=15
            )
            if student_state_res.status_code != 200:
                logging.warning(
                    "Falha ao obter estado individual. session_id=%s student_id=%s status=%s",
                    session_id, student_id, student_state_res.status_code
                )
                continue

            student_state = student_state_res.json() or {}
            current_index = _safe_int(student_state.get("current_tactic_index"), 0) or 0
            current_index = max(0, min(current_index, len(tactics) - 1))
            executed_indices = student_state.get("executed_indices", [])
            if not isinstance(executed_indices, list):
                executed_indices = []
            executed_tactics = []
            for idx in executed_indices:
                if isinstance(idx, int) and 0 <= idx < len(tactics):
                    tactic_id = tactics[idx].get("id")
                    if tactic_id is not None:
                        executed_tactics.append(int(tactic_id))

            current_session_student_performance = "Sem desempenho individual na sessão atual."
            difficulty_data = None
            decision = _build_rule_decision(student_state, tactics)
            if decision:
                if decision["source"] == "ttl_keep":
                    ttl_rule_count += 1
                else:
                    local_rule_count += 1

            if decision is None:
                difficulty_fetch_count += 1
                difficulty_res = requests.post(
                    f"{CONTROL_URL}/agent/student_session_difficulty_summary",
                    json={
                        "student_id": student_id,
                        "session_id": session_id,
                        "exercise_context_by_id": get_exercise_context_by_id()
                    },
                    timeout=40
                )
                if difficulty_res.status_code == 200:
                    difficulty_data = difficulty_res.json() or {}
                    current_session_student_performance = difficulty_data.get(
                        "difficulty_summary",
                        current_session_student_performance
                    )
                    decision = _build_rule_decision(student_state, tactics, difficulty_data=difficulty_data)
                    if decision:
                        local_rule_count += 1
                elif difficulty_res.status_code not in (404, 422):
                    logging.warning(
                        "Falha ao obter resumo de dificuldade. session_id=%s student_id=%s status=%s",
                        session_id, student_id, difficulty_res.status_code
                    )

            if decision is None:
                student_profile_res = requests.post(
                    f"{USER_URL}/agent/summarize_logged_user",
                    json={"user_id": student_id},
                    timeout=20
                )
                student_profile_summary = "Perfil individual não disponível."
                if student_profile_res.status_code == 200:
                    student_profile_summary = (
                        (student_profile_res.json() or {}).get("summary", student_profile_summary)
                    )

                history_res = requests.get(
                    f"{CONTROL_URL}/students/{student_id}/grades_history",
                    timeout=20
                )
                student_history_summary = "Histórico do aluno não disponível."
                if history_res.status_code == 200:
                    student_history_summary = (history_res.json() or {}).get(
                        "student_performance_summary",
                        student_history_summary
                    )

                cache_key = (
                    _normalize_text(student_profile_summary),
                    _normalize_text(student_history_summary),
                    _normalize_text(current_session_student_performance),
                    str(student_state.get("last_rating"))
                )

                cached_decision = decision_cache.get(cache_key)
                decision_source = "ai_cache"
                if cached_decision is None:
                    ai_payload = {
                        "student_id": str(student_id),
                        "strategy_id": strategy_id,
                        "executed_tactics": executed_tactics,
                        "student_profile_summary": student_profile_summary,
                        "performance_summary": get_session_performance_summary(),
                        "class_profile_summary": get_class_profile_summary(),
                        "student_history_summary": student_history_summary,
                        "current_session_student_performance": current_session_student_performance,
                        "last_session_rating": student_state.get("last_rating"),
                        "personalization_rules": [
                            "Considere perfil individual, perfil da turma, histórico do aluno e desempenho atual da sessão.",
                            "Evite repetir táticas já executadas, exceto quando o reforço for necessário.",
                            "Se houver tática de mudança de estratégia, só use quando houver justificativa forte."
                        ]
                    }

                    ai_res = requests.post(
                        f"{STRATEGIES_URL}/agent/decide_next_tactic",
                        json=ai_payload,
                        timeout=45
                    )
                    if ai_res.status_code != 200:
                        logging.warning(
                            "Falha ao obter decisão da IA no Strategies. session_id=%s student_id=%s status=%s",
                            session_id, student_id, ai_res.status_code
                        )
                        continue

                    cached_decision = (ai_res.json() or {}).get("decision", {})
                    decision_cache[cache_key] = cached_decision
                    decision_source = "ai"
                    ai_calls_count += 1
                else:
                    ai_cache_hit_count += 1

                chosen_tactic_id = cached_decision.get("chosen_tactic_id")
                idx = None
                if chosen_tactic_id is not None:
                    try:
                        idx = tactic_idx_by_id.get(int(chosen_tactic_id))
                    except (TypeError, ValueError):
                        idx = None
                if idx is None:
                    idx = current_index

                decision = {
                    "tactic_index": idx,
                    "source": decision_source,
                    "reason": cached_decision.get("reasoning", ""),
                    "force_apply": False,
                    "chosen_tactic_id": chosen_tactic_id
                }

            chosen_tactic_id = decision.get("chosen_tactic_id")
            idx = _safe_int(decision.get("tactic_index"), current_index)
            idx = max(0, min(idx, len(tactics) - 1))
            recommended_indices.append(idx)

            should_apply = bool(decision.get("force_apply")) or idx != current_index
            applied = True
            if should_apply:
                set_res = requests.post(
                    f"{CONTROL_URL}/sessions/{session_id}/students/{student_id}/set_tactic",
                    json={"tactic_index": idx},
                    timeout=15
                )
                applied = set_res.status_code == 200
                if not applied:
                    logging.warning(
                        "Falha ao aplicar tática individual. session_id=%s student_id=%s tactic_index=%s status=%s",
                        session_id, student_id, idx, set_res.status_code
                    )

            individual_decisions.append({
                "student_id": str(student_id),
                "recommended_tactic_index": idx,
                "chosen_tactic_id": chosen_tactic_id,
                "decision_source": decision.get("source"),
                "applied": applied,
                "state_changed": should_apply,
                "reason": decision.get("reason", "")
            })

        if not individual_decisions:
            return None

        distribution = dict(Counter(recommended_indices))
        display_tactic_index = _select_display_tactic_index(
            recommended_indices,
            fallback_index=_safe_int(session_json.get("current_tactic_index"), 0) or 0
        )
        display_sync_applied = False

        display_set_res = requests.post(
            f"{CONTROL_URL}/sessions/tactic/set/{session_id}",
            json={"tactic_index": display_tactic_index},
            timeout=15
        )
        if display_set_res.status_code == 200:
            display_sync_applied = True
        else:
            logging.warning(
                "Falha ao sincronizar tática global de exibição. session_id=%s tactic_index=%s status=%s",
                session_id, display_tactic_index, display_set_res.status_code
            )

        return jsonify({
            "success": True,
            "mode": "individual_per_student",
            "consensus_tactic_index": None,
            "display_tactic_index": display_tactic_index,
            "display_sync_applied": display_sync_applied,
            "tactic_distribution": distribution,
            "ai_calls_count": ai_calls_count,
            "ai_cache_hit_count": ai_cache_hit_count,
            "local_rule_count": local_rule_count,
            "ttl_rule_count": ttl_rule_count,
            "difficulty_fetch_count": difficulty_fetch_count,
            "student_decisions": individual_decisions
        }), 200
    except Exception as e:
        logging.error(f"Erro na orquestração do Agente por aluno: {e}")
        return None
