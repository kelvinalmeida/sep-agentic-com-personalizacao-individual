import requests
import logging
import re
from flask import Blueprint, jsonify, request
from ...services_routs import CONTROL_URL, STRATEGIES_URL, USER_URL, DOMAIN_URL

agente_wrong_answers_bp = Blueprint('agente_wrong_answers_bp', __name__)


def _build_exercise_context(session_id):
    """Retorna dicionário {exercise_id: exercise_data} para os exercícios da sessão."""
    exercise_context_by_id = {}

    session_resp = requests.get(f"{CONTROL_URL}/sessions/{session_id}", timeout=10)
    if session_resp.status_code != 200:
        return exercise_context_by_id

    domain_ids = (session_resp.json() or {}).get('domains', [])

    for domain_id in domain_ids:
        try:
            ex_resp = requests.get(f"{DOMAIN_URL}/domains/{int(domain_id)}/exercises", timeout=10)
            if ex_resp.status_code == 200:
                for exercise in (ex_resp.json() or []):
                    if isinstance(exercise, dict) and exercise.get('id') is not None:
                        exercise_context_by_id[str(exercise['id'])] = exercise
        except Exception as e:
            logging.warning("Erro ao buscar exercícios domain_id=%s: %s", domain_id, e)

    if not exercise_context_by_id:
        try:
            all_resp = requests.get(f"{DOMAIN_URL}/domains", timeout=10)
            if all_resp.status_code == 200:
                for domain in (all_resp.json() or []):
                    for exercise in (domain.get('exercises', []) if isinstance(domain, dict) else []):
                        if isinstance(exercise, dict) and exercise.get('id') is not None:
                            exercise_context_by_id[str(exercise['id'])] = exercise
        except Exception as e:
            logging.warning("Fallback de exercícios falhou session_id=%s: %s", session_id, e)

    return exercise_context_by_id


def _strip_correct_answer(line: str) -> str:
    """Remove a parte '| correta: ...' de uma linha de questão para não revelar a resposta."""
    return re.sub(r'\|\s*correta:\s*[^|]+', '', line).strip()


@agente_wrong_answers_bp.route('/orchestrator/agent/generate_wrong_answers_text', methods=['POST'])
def generate_wrong_answers_text():
    """
    Orquestrador: busca as questões que o aluno errou na sessão atual,
    obtém o perfil dele e envia ao agente de estratégia para gerar um
    texto explicativo de ~5 minutos de leitura SEM revelar as respostas.
    """
    data = request.get_json() or {}
    student_id = data.get('student_id')
    session_id = data.get('session_id')
    attempt_number = int(data.get('attempt_number', 1))

    if student_id is None or session_id is None:
        return jsonify({"error": "student_id e session_id são obrigatórios"}), 400

    try:
        # 1. Contexto dos exercícios para enriquecer o resumo de dificuldade
        exercise_context_by_id = _build_exercise_context(session_id)

        # 2. Resumo de dificuldade com detalhe das questões erradas
        difficulty_resp = requests.post(
            f"{CONTROL_URL}/agent/student_session_difficulty_summary",
            json={
                "student_id": student_id,
                "session_id": session_id,
                "exercise_context_by_id": exercise_context_by_id
            },
            timeout=60
        )
        if difficulty_resp.status_code != 200:
            return jsonify({
                "error": "Falha ao obter resumo de dificuldades",
                "details": difficulty_resp.text
            }), difficulty_resp.status_code

        difficulty_data = difficulty_resp.json()
        wrong_count = difficulty_data.get('wrong_count', 0)

        if wrong_count == 0:
            return jsonify({
                "student_id": student_id,
                "session_id": session_id,
                "wrong_count": 0,
                "study_text": "Parabéns! O aluno não errou nenhuma questão nesta sessão."
            }), 200

        # 3. Filtrar questões erradas e remover a resposta correta das linhas
        wrong_questions = [
            _strip_correct_answer(line)
            for line in difficulty_data.get('questions_summary', [])
            if isinstance(line, str) and 'ERROU' in line
        ]

        # 4. Perfil individual do aluno (sem LLM — leitura direta do banco)
        profile_summary = ""
        try:
            user_resp = requests.get(
                f"{USER_URL}/students/{student_id}/preferences",
                timeout=10
            )
            if user_resp.status_code == 200:
                d = user_resp.json()
                email_txt = "aceita e-mail" if d.get('pref_receive_email') else "não aceita e-mail"
                profile_summary = (
                    f"Nome: {d.get('name') or 'N/A'}. "
                    f"Curso: {d.get('course') or 'N/A'}. "
                    f"Idade: {d.get('age') or 'N/A'}. "
                    f"Conteúdo preferido: {d.get('pref_content_type') or 'N/A'}. "
                    f"Comunicação preferida: {d.get('pref_communication') or 'N/A'}. "
                    f"{email_txt.capitalize()}."
                )
        except Exception as e:
            logging.warning("Erro ao buscar perfil student_id=%s: %s", student_id, e)

        # 5. Histórico de sessões anteriores (memória persistente)
        student_history = ""
        try:
            hist_resp = requests.get(
                f"{USER_URL}/students/{student_id}/learning_history",
                params={"limit": 3},
                timeout=10
            )
            if hist_resp.status_code == 200:
                history_entries = hist_resp.json().get('history', [])
                if history_entries:
                    lines = [f"- Sessão {h['session_id']}: {h['summary']}" for h in history_entries]
                    student_history = "\n".join(lines)
        except Exception as e:
            logging.warning("Erro ao buscar histórico student_id=%s: %s", student_id, e)

        # 6. Gerar texto educativo via agente de estratégia
        strategies_resp = requests.post(
            f"{STRATEGIES_URL}/agent/generate_wrong_answers_study_text",
            json={
                "wrong_questions": wrong_questions,
                "profile_summary": profile_summary,
                "student_history": student_history,
                "attempt_number": attempt_number
            },
            timeout=60
        )
        if strategies_resp.status_code != 200:
            return jsonify({
                "error": "Falha ao gerar texto educativo",
                "details": strategies_resp.text
            }), strategies_resp.status_code

        result = strategies_resp.json()

        # 7. Registrar dificuldade no histórico persistente (fire-and-forget)
        try:
            questions_summary = "; ".join(wrong_questions[:3]) if wrong_questions else "questões não identificadas"
            requests.post(
                f"{USER_URL}/students/{student_id}/difficulty_note",
                json={
                    "session_id": session_id,
                    "attempt_number": attempt_number,
                    "wrong_questions_summary": questions_summary
                },
                timeout=5
            )
        except Exception:
            pass

        return jsonify({
            "student_id": student_id,
            "session_id": session_id,
            "wrong_count": wrong_count,
            "wrong_questions": wrong_questions,
            "study_text": result.get('study_text', '')
        }), 200

    except Exception as e:
        logging.error("Erro em generate_wrong_answers_text: %s", str(e))
        return jsonify({"error": "Falha na orquestração"}), 500
