import requests
import logging
from collections import Counter
from flask import Blueprint, jsonify, request
from ...services_routs import CONTROL_URL, STRATEGIES_URL, USER_URL, DOMAIN_URL

agente_control_orch_bp = Blueprint('agente_control_orch_bp', __name__)


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

        exercise_context_by_id, _ = _build_exercise_context_for_session(session_id)
        exercise_context_by_id = exercise_context_by_id or {}

        perf_res = requests.get(f"{CONTROL_URL}/sessions/{session_id}/agent_summary", timeout=20)
        session_performance_summary = "Sem dados de performance da sessão."
        if perf_res.status_code == 200:
            session_performance_summary = (perf_res.json() or {}).get('summary', session_performance_summary)

        class_profile_res = requests.post(
            f"{USER_URL}/students/summarize_preferences",
            json={"student_ids": student_ids},
            timeout=25
        )
        class_profile_summary = "Perfil da turma não disponível."
        if class_profile_res.status_code == 200:
            class_summary_raw = (class_profile_res.json() or {}).get("summary", class_profile_summary)
            class_profile_summary = class_summary_raw if isinstance(class_summary_raw, str) else str(class_summary_raw)

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
            executed_indices = student_state.get("executed_indices", [])
            executed_tactics = []
            for idx in executed_indices:
                if isinstance(idx, int) and 0 <= idx < len(tactics):
                    tactic_id = tactics[idx].get("id")
                    if tactic_id is not None:
                        executed_tactics.append(int(tactic_id))

            student_profile_res = requests.post(
                f"{USER_URL}/agent/summarize_logged_user",
                json={"user_id": student_id},
                timeout=20
            )
            student_profile_summary = "Perfil individual não disponível."
            if student_profile_res.status_code == 200:
                student_profile_summary = (student_profile_res.json() or {}).get("summary", student_profile_summary)

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

            difficulty_res = requests.post(
                f"{CONTROL_URL}/agent/student_session_difficulty_summary",
                json={
                    "student_id": student_id,
                    "session_id": session_id,
                    "exercise_context_by_id": exercise_context_by_id
                },
                timeout=40
            )
            current_session_student_performance = "Sem desempenho individual na sessão atual."
            if difficulty_res.status_code == 200:
                diff_json = difficulty_res.json() or {}
                current_session_student_performance = diff_json.get(
                    "difficulty_summary",
                    current_session_student_performance
                )

            cache_key = (
                str(student_profile_summary).strip(),
                str(student_history_summary).strip(),
                str(current_session_student_performance).strip(),
                str(student_state.get("last_rating"))
            )

            cached_decision = decision_cache.get(cache_key)
            if cached_decision is None:
                ai_payload = {
                    "student_id": str(student_id),
                    "strategy_id": strategy_id,
                    "executed_tactics": executed_tactics,
                    "student_profile_summary": student_profile_summary,
                    "performance_summary": session_performance_summary,
                    "class_profile_summary": class_profile_summary,
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

            decision = cached_decision
            chosen_tactic_id = decision.get("chosen_tactic_id")
            idx = None
            if chosen_tactic_id is not None:
                try:
                    idx = tactic_idx_by_id.get(int(chosen_tactic_id))
                except (TypeError, ValueError):
                    idx = None
            if idx is None:
                idx = int(student_state.get("current_tactic_index", 0))
            idx = max(0, min(idx, len(tactics) - 1))
            recommended_indices.append(idx)

            requests.post(
                f"{CONTROL_URL}/sessions/{session_id}/students/{student_id}/set_tactic",
                json={"tactic_index": idx},
                timeout=15
            )

            individual_decisions.append({
                "student_id": str(student_id),
                "recommended_tactic_index": idx,
                "chosen_tactic_id": chosen_tactic_id,
                "reason": decision.get("reasoning", "")
            })

        if not individual_decisions:
            return None

        distribution = dict(Counter(recommended_indices))

        return jsonify({
            "success": True,
            "mode": "individual_per_student",
            "consensus_tactic_index": None,
            "tactic_distribution": distribution,
            "ai_calls_count": len(decision_cache),
            "student_decisions": individual_decisions
        }), 200
    except Exception as e:
        logging.error(f"Erro na orquestração do Agente por aluno: {e}")
        return None
