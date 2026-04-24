import requests
import logging
import re
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

        strat_res = requests.get(f"{STRATEGIES_URL}/strategies/{strategy_id}")
        if strat_res.status_code != 200:
            logging.error("❌ Não foi possível carregar estratégia atual no Strategies.")
            return None

        tactics = (strat_res.json() or {}).get('tatics', [])
        if not tactics:
            return None

        individual_decisions = []
        recommended_indices = []

        for student_id in student_ids:
            rec_res = requests.get(
                f"{CONTROL_URL}/sessions/{session_id}/students/{student_id}/recommendation",
                timeout=15
            )
            if rec_res.status_code != 200:
                logging.warning(
                    "Falha ao obter recomendação individual. session_id=%s student_id=%s status=%s",
                    session_id, student_id, rec_res.status_code
                )
                continue

            rec_json = rec_res.json() or {}
            recommendation = rec_json.get("recommendation", {})
            idx = int(recommendation.get("recommended_tactic_index", 0))
            idx = max(0, min(idx, len(tactics) - 1))
            recommended_indices.append(idx)

            set_res = requests.post(
                f"{CONTROL_URL}/sessions/{session_id}/students/{student_id}/set_tactic",
                json={"tactic_index": idx},
                timeout=15
            )
            if set_res.status_code != 200:
                logging.warning(
                    "Falha ao aplicar tática individual. session_id=%s student_id=%s status=%s",
                    session_id, student_id, set_res.status_code
                )

            individual_decisions.append({
                "student_id": str(student_id),
                "recommended_tactic_index": idx,
                "recommendation_action": recommendation.get("action", "keep"),
                "reason": recommendation.get("reason", "")
            })

        if not individual_decisions:
            return None

        consensus_index = Counter(recommended_indices).most_common(1)[0][0]
        requests.post(
            f"{CONTROL_URL}/sessions/tactic/set/{session_id}",
            json={"tactic_index": consensus_index},
            timeout=15
        )

        current_tactic = tactics[consensus_index]
        tactic_name = current_tactic.get('name', '').strip().lower()
        valid_names = ["mudanca de estrategia", "mudança de estratégia", "mudança de estrategia", "mudanca de estratégia"]

        if tactic_name in valid_names:
            description = str(current_tactic.get('description', ''))
            match = re.search(r'\d+', description)
            if match:
                target_strategy_id = int(match.group())
                switch_res = requests.post(
                    f"{CONTROL_URL}/sessions/{session_id}/temp_switch_strategy",
                    json={'strategy_id': target_strategy_id}
                )
                if switch_res.status_code != 200:
                    logging.error(f"❌ Falha ao trocar estratégia (consenso): {switch_res.text}")

        return jsonify({
            "success": True,
            "mode": "individual_per_student",
            "consensus_tactic_index": consensus_index,
            "student_decisions": individual_decisions
        }), 200
    except Exception as e:
        logging.error(f"Erro na orquestração do Agente por aluno: {e}")
        return None
