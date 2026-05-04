import requests
import logging
from flask import Blueprint, jsonify, request
from ...services_routs import CONTROL_URL, STRATEGIES_URL, USER_URL, DOMAIN_URL

logging.basicConfig(level=logging.INFO)

agente_memory_bp = Blueprint('agente_memory_bp', __name__)


def _build_exercise_context(session_id):
    """Retorna {exercise_id: exercise_data} para todos os exercícios da sessão."""
    exercise_context = {}
    try:
        session_resp = requests.get(f"{CONTROL_URL}/sessions/{session_id}", timeout=10)
        if session_resp.status_code != 200:
            return exercise_context
        domain_ids = (session_resp.json() or {}).get('domains', [])
        for domain_id in domain_ids:
            try:
                ex_resp = requests.get(f"{DOMAIN_URL}/domains/{int(domain_id)}/exercises", timeout=10)
                if ex_resp.status_code == 200:
                    for ex in (ex_resp.json() or []):
                        if isinstance(ex, dict) and ex.get('id') is not None:
                            exercise_context[str(ex['id'])] = ex
            except Exception:
                pass
    except Exception as e:
        logging.warning("Erro ao construir contexto de exercícios session_id=%s: %s", session_id, e)
    return exercise_context


@agente_memory_bp.route('/orchestrator/agent/save_session_memory', methods=['POST'])
def save_session_memory():
    """
    Chamado ao fim da sessão de um aluno.
    Agrega dados de desempenho e delega ao serviço user a geração e persistência
    do resumo de memória para uso em sessões futuras.
    """
    data = request.get_json() or {}
    student_id = data.get('student_id')
    session_id = data.get('session_id')

    if student_id is None or session_id is None:
        return jsonify({"error": "student_id e session_id são obrigatórios"}), 400

    try:
        # 1. Dados da sessão
        session_resp = requests.get(f"{CONTROL_URL}/sessions/{session_id}", timeout=10)
        if session_resp.status_code != 200:
            return jsonify({"error": "Falha ao buscar sessão"}), 502
        session_data = session_resp.json()

        # 2. Notas do aluno nesta sessão
        verified = [
            v for v in session_data.get('verified_answers', [])
            if str(v.get('student_id', '')) == str(student_id)
        ]
        scores = [v.get('score', 0) for v in verified]

        # 3. Nomes de todas as táticas da estratégia
        strategy_ids = session_data.get('strategies', [])
        strategy_id = strategy_ids[0] if strategy_ids else None
        tactics_names = []
        if strategy_id:
            try:
                strat_resp = requests.get(f"{STRATEGIES_URL}/strategies/{strategy_id}", timeout=10)
                if strat_resp.status_code == 200:
                    all_tactics = strat_resp.json().get('tatics', [])
                    tactics_names = [t.get('name', '') for t in all_tactics]
            except Exception as e:
                logging.warning("Erro ao buscar táticas strategy_id=%s: %s", strategy_id, e)

        # 4. Salva memória via serviço user (que chama o LLM e persiste)
        save_resp = requests.post(
            f"{USER_URL}/agent/save_session_memory",
            json={
                "student_id": student_id,
                "session_id": session_id,
                "scores": scores,
                "tactics_names": tactics_names,
            },
            timeout=30
        )

        if save_resp.status_code != 200:
            logging.error("Falha ao salvar memória: %s", save_resp.text)
            return jsonify({"error": "Falha ao salvar memória"}), 502

        # 5. Extrair conceitos dos exercícios e atualizar maestria (fire-and-forget)
        try:
            exercise_context = _build_exercise_context(session_id)
            if exercise_context:
                exercise_performance = []
                for va in verified:
                    for ans in va.get('answers', []):
                        ex_id = str(ans.get('exercise_id', ''))
                        ex = exercise_context.get(ex_id, {})
                        if ex.get('question'):
                            exercise_performance.append({
                                "question": ex['question'],
                                "was_correct": bool(ans.get('correct', False))
                            })

                if exercise_performance:
                    concepts_resp = requests.post(
                        f"{STRATEGIES_URL}/agent/extract_exercise_concepts",
                        json={"exercises": exercise_performance},
                        timeout=30
                    )
                    if concepts_resp.status_code == 200:
                        concepts = concepts_resp.json().get('concepts', [])
                        if concepts:
                            requests.post(
                                f"{USER_URL}/students/{student_id}/mastery_update",
                                json={"concepts": concepts, "session_id": session_id},
                                timeout=10
                            )
        except Exception as e:
            logging.warning("Erro ao atualizar maestria student_id=%s: %s", student_id, e)

        return jsonify(save_resp.json()), 200

    except Exception as e:
        logging.error("Erro em save_session_memory orchestrator: %s", str(e))
        return jsonify({"error": str(e)}), 500


def _get_current_mastery(student_id, session_id=None):
    """Busca a maestria do aluno para a sessão especificada."""
    try:
        params = {}
        if session_id is not None:
            params['session_id'] = session_id
        r = requests.get(f"{USER_URL}/students/{student_id}/mastery", params=params, timeout=10)
        if r.status_code == 200:
            return jsonify(r.json()), 200
    except Exception:
        pass
    return jsonify({"mastery": []}), 200


@agente_memory_bp.route('/orchestrator/student/mastery', methods=['GET'])
def get_student_mastery():
    """Leitura simples da maestria sem recalcular (usado no restore ao recarregar página)."""
    student_id = request.args.get('student_id')
    session_id = request.args.get('session_id')
    if not student_id:
        return jsonify({"mastery": []}), 200
    return _get_current_mastery(student_id, session_id)


@agente_memory_bp.route('/orchestrator/agent/update_and_get_mastery', methods=['POST'])
def update_and_get_mastery():
    """
    Chamado imediatamente após o aluno responder exercícios na tática Reuso.
    Extrai conceitos da tentativa atual, atualiza a maestria da sessão e retorna o mapa
    atualizado para exibição em tempo real na UI.
    """
    data = request.get_json() or {}
    student_id = data.get('student_id')
    session_id = data.get('session_id')

    if student_id is None or session_id is None:
        return jsonify({"mastery": []}), 200

    try:
        # 1. Respostas verificadas do aluno nesta sessão
        session_resp = requests.get(f"{CONTROL_URL}/sessions/{session_id}", timeout=10)
        if session_resp.status_code != 200:
            return _get_current_mastery(student_id, session_id)

        verified = [
            v for v in (session_resp.json() or {}).get('verified_answers', [])
            if str(v.get('student_id', '')) == str(student_id)
        ]
        if not verified:
            return _get_current_mastery(student_id, session_id)

        # Usa apenas a tentativa mais recente (maior tactic_index)
        latest = max(verified, key=lambda v: v.get('tactic_index', 0))

        # 2. Texto dos exercícios
        exercise_context = _build_exercise_context(session_id)
        if not exercise_context:
            return _get_current_mastery(student_id, session_id)

        exercise_performance = []
        for ans in latest.get('answers', []):
            ex = exercise_context.get(str(ans.get('exercise_id', '')), {})
            if ex.get('question'):
                exercise_performance.append({
                    "question": ex['question'],
                    "was_correct": bool(ans.get('correct', False))
                })

        if not exercise_performance:
            return _get_current_mastery(student_id, session_id)

        # 3. Extrai conceitos via LLM e atualiza maestria da sessão
        concepts_resp = requests.post(
            f"{STRATEGIES_URL}/agent/extract_exercise_concepts",
            json={"exercises": exercise_performance},
            timeout=30
        )
        if concepts_resp.status_code == 200:
            concepts = concepts_resp.json().get('concepts', [])
            if concepts:
                requests.post(
                    f"{USER_URL}/students/{student_id}/mastery_update",
                    json={"concepts": concepts, "session_id": session_id},
                    timeout=10
                )

        # 4. Retorna maestria atualizada da sessão
        return _get_current_mastery(student_id, session_id)

    except Exception as e:
        logging.error("Erro em update_and_get_mastery student_id=%s: %s", student_id, e)
        return _get_current_mastery(student_id, session_id)
