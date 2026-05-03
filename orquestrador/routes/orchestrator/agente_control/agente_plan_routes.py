import json
import logging
import requests
from flask import Blueprint, jsonify, request
from ...services_routs import CONTROL_URL, STRATEGIES_URL, USER_URL

logging.basicConfig(level=logging.INFO)

agente_plan_bp = Blueprint('agente_plan_bp', __name__)


def _aggregate_student_context(student_id, session_id, session_data):
    """Agrega perfil, histórico, maestria, chat e notas do aluno para passar à IA."""
    strategy_ids = session_data.get('strategies', [])
    student_ids = session_data.get('students', [])
    strategy_id = strategy_ids[0] if strategy_ids else None

    # Táticas da estratégia
    strategy_tactics = []
    if strategy_id:
        try:
            strat_resp = requests.get(f"{STRATEGIES_URL}/strategies/{strategy_id}", timeout=10)
            if strat_resp.status_code == 200:
                strategy_tactics = strat_resp.json().get('tatics', [])
        except Exception as e:
            logging.warning("Erro ao buscar táticas strategy_id=%s: %s", strategy_id, e)

    # Perfil individual do aluno
    student_profile = "Perfil não disponível."
    try:
        user_resp = requests.get(f"{USER_URL}/students/{student_id}/preferences", timeout=10)
        if user_resp.status_code == 200:
            d = user_resp.json()
            email_txt = "aceita e-mail" if d.get('pref_receive_email') else "não aceita e-mail"
            student_profile = (
                f"Nome: {d.get('name') or 'N/A'}. "
                f"Curso: {d.get('course') or 'N/A'}. "
                f"Idade: {d.get('age') or 'N/A'}. "
                f"Conteúdo preferido: {d.get('pref_content_type') or 'N/A'}. "
                f"Comunicação preferida: {d.get('pref_communication') or 'N/A'}. "
                f"{email_txt.capitalize()}."
            )
    except Exception as e:
        logging.warning("Erro ao buscar perfil student_id=%s: %s", student_id, e)

    # Perfil da turma
    class_profile = "Perfil da turma desconhecido."
    try:
        class_resp = requests.post(
            f"{USER_URL}/students/batch_preferences",
            json={"student_ids": student_ids},
            timeout=10
        )
        if class_resp.status_code == 200:
            students_raw = class_resp.json().get('students', [])
            if students_raw:
                lines = []
                for s in students_raw:
                    s_email = "aceita e-mail" if s.get('pref_receive_email') else "não aceita e-mail"
                    lines.append(
                        f"- {s.get('name') or 'Aluno'}: "
                        f"conteúdo '{s.get('pref_content_type') or 'N/A'}', "
                        f"comunicação '{s.get('pref_communication') or 'N/A'}', "
                        f"{s_email}."
                    )
                class_profile = "\n".join(lines)
    except Exception as e:
        logging.warning("Erro ao buscar perfil da turma: %s", e)

    # Notas do aluno
    exercise_scores = "Sem registros de exercícios."
    verified = [
        v for v in session_data.get('verified_answers', [])
        if str(v.get('student_id', '')) == str(student_id)
    ]
    if verified:
        scores = [v.get('score', 0) for v in verified]
        latest = verified[-1]
        total_q = max(len(latest.get('answers', [])), 1)
        latest_pct = int((latest.get('score', 0) / total_q) * 100)
        exercise_scores = (
            f"{len(scores)} tentativa(s). Notas: {scores}. "
            f"Última: {latest.get('score', 0)}/{total_q} ({latest_pct}%)."
        )

    # Username para filtrar mensagens do chat
    student_username = str(student_id)
    try:
        student_resp = requests.get(f"{USER_URL}/students/{student_id}", timeout=10)
        if student_resp.status_code == 200:
            student_username = student_resp.json().get('username', str(student_id))
    except Exception as e:
        logging.warning("Erro ao buscar username student_id=%s: %s", student_id, e)

    # Últimas 5 mensagens no chat
    student_chat_messages = []
    for tactic in strategy_tactics:
        chat_id = tactic.get('chat_id')
        if not chat_id:
            continue
        try:
            chat_resp = requests.get(f"{STRATEGIES_URL}/chat/{chat_id}/general_messages", timeout=10)
            if chat_resp.status_code == 200:
                resp_json = chat_resp.json()
                msgs = resp_json.get('messages', []) if isinstance(resp_json, dict) else resp_json
                for msg in (msgs or []):
                    if isinstance(msg, dict) and msg.get('username') == student_username:
                        student_chat_messages.append(msg.get('content', ''))
        except Exception as e:
            logging.warning("Erro ao buscar mensagens chat_id=%s: %s", chat_id, e)
    last_5_messages = student_chat_messages[-5:]

    # Histórico de sessões anteriores (guardamos entries para reusar os session_ids abaixo)
    student_history = ""
    history_entries = []
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

    # Maestria por conceito — sessão atual + média das sessões anteriores
    student_mastery_text = ""
    try:
        # 1. Sessão atual (pode estar vazia se a sessão acabou de começar)
        current_mastery = []
        mastery_resp = requests.get(
            f"{USER_URL}/students/{student_id}/mastery",
            params={"session_id": session_id},
            timeout=10
        )
        if mastery_resp.status_code == 200:
            current_mastery = mastery_resp.json().get('mastery', [])

        # 2. Média das sessões anteriores usando os session_ids do histórico
        concept_totals: dict = {}
        concept_counts: dict = {}
        for entry in history_entries:
            past_sid = entry.get('session_id')
            if not past_sid or str(past_sid) == str(session_id):
                continue
            try:
                pm = requests.get(
                    f"{USER_URL}/students/{student_id}/mastery",
                    params={"session_id": past_sid},
                    timeout=5
                )
                if pm.status_code == 200:
                    for m in pm.json().get('mastery', []):
                        c = m['concept']
                        concept_totals[c] = concept_totals.get(c, 0) + m['mastery_pct']
                        concept_counts[c] = concept_counts.get(c, 0) + 1
            except Exception:
                pass

        parts = []
        if current_mastery:
            lines = [f"- {m['concept']}: {m['mastery_pct']}%" for m in current_mastery]
            parts.append("Sessão atual:\n" + "\n".join(lines))

        if concept_totals:
            lines = [
                f"- {c}: {round(concept_totals[c] / concept_counts[c])}%"
                f" (média de {concept_counts[c]} sessão(ões) anterior(es))"
                for c in concept_totals
            ]
            parts.append("Histórico de sessões anteriores:\n" + "\n".join(lines))

        student_mastery_text = (
            "\n\n".join(parts)
            if parts
            else "Primeira sessão — sem dados de maestria anteriores."
        )
    except Exception as e:
        logging.warning("Erro ao buscar maestria student_id=%s: %s", student_id, e)

    return {
        "strategy_tactics": strategy_tactics,
        "student_profile": student_profile,
        "class_profile": class_profile,
        "exercise_scores": exercise_scores,
        "chat_messages": last_5_messages,
        "student_history": student_history,
        "student_mastery": student_mastery_text,
    }


@agente_plan_bp.route('/orchestrator/agent/plan_session', methods=['POST'])
def plan_session():
    """
    Planejamento multi-passo: a IA cria a sequência completa de táticas para o aluno
    ANTES de iniciar a primeira tática. O plano é salvo no banco e usado nas transições.

    Substitui adaptive_next_tactic(is_first=True).
    """
    data = request.get_json() or {}
    student_id = data.get('student_id')
    session_id = data.get('session_id')

    if student_id is None or session_id is None:
        return jsonify({"error": "student_id e session_id são obrigatórios"}), 400

    try:
        session_resp = requests.get(f"{CONTROL_URL}/sessions/{session_id}", timeout=10)
        if session_resp.status_code != 200:
            return jsonify({"error": "Falha ao buscar sessão"}), 502
        session_data = session_resp.json()

        ctx = _aggregate_student_context(student_id, session_id, session_data)
        strategy_tactics = ctx['strategy_tactics']

        if not strategy_tactics:
            return jsonify({"error": "Sem táticas na estratégia"}), 400

        all_tactics = [
            {"index": i, "name": t.get('name', ''), "description": t.get('description', '')}
            for i, t in enumerate(strategy_tactics)
        ]

        ai_payload = {
            "student_profile": ctx['student_profile'],
            "class_profile": ctx['class_profile'],
            "exercise_scores": ctx['exercise_scores'],
            "all_tactics": all_tactics,
            "chat_messages": ctx['chat_messages'],
            "student_history": ctx['student_history'],
            "student_mastery": ctx['student_mastery'],
            "is_replan": False,
        }

        logging.info("Chamando IA para planejar sessão student_id=%s session_id=%s", student_id, session_id)

        ai_resp = requests.post(
            f"{STRATEGIES_URL}/agent/plan_session_tactics",
            json=ai_payload,
            timeout=60
        )

        if ai_resp.status_code != 200:
            # Fallback: ordem natural das táticas
            tactic_sequence = list(range(len(strategy_tactics)))
            overall_goal = "Completar todas as atividades da sessão."
            tactic_reasons = {}
        else:
            ai_data = ai_resp.json()
            tactic_sequence = ai_data.get('tactic_sequence', list(range(len(strategy_tactics))))
            overall_goal = ai_data.get('overall_goal', '')
            tactic_reasons = ai_data.get('tactic_reasons', {})

        # Primeiro índice do plano = primeira tática a executar
        next_tactic_index = tactic_sequence[0] if tactic_sequence else 0
        next_tactic_name = strategy_tactics[next_tactic_index].get('name', '') if next_tactic_index < len(strategy_tactics) else ''

        plan_json = json.dumps({
            "tactic_sequence": tactic_sequence,
            "overall_goal": overall_goal,
            "tactic_reasons": tactic_reasons,
        })

        # Persiste plano + tática inicial no banco
        set_resp = requests.post(
            f"{CONTROL_URL}/sessions/{session_id}/student/{student_id}/set_tactic",
            json={
                "tactic_index": next_tactic_index,
                "executed_tactic_indices": [],
                "session_plan": plan_json,
            },
            timeout=10
        )
        if set_resp.status_code != 200:
            return jsonify({"error": "Falha ao definir tática do aluno"}), 502

        logging.info("Plano salvo student_id=%s sequence=%s", student_id, tactic_sequence)

        return jsonify({
            "next_tactic_index": next_tactic_index,
            "next_tactic_name": next_tactic_name,
            "overall_goal": overall_goal,
            "tactic_sequence": tactic_sequence,
            "reasoning": tactic_reasons.get(str(next_tactic_index), overall_goal),
        }), 200

    except Exception as e:
        logging.error("Erro em plan_session student_id=%s: %s", student_id, str(e))
        return jsonify({"error": "Falha no planejamento da sessão"}), 500


@agente_plan_bp.route('/orchestrator/agent/replan_session', methods=['POST'])
def replan_session():
    """
    Planeja/replaneja as táticas RESTANTES e salva no banco sem alterar a tática atual.
    Usado em dois momentos:
      - is_replan=False: primeiro exercício concluído → planeja com maestria real disponível.
      - is_replan=True : 2ª falha no Reuso → reordena para reforçar pontos fracos.
    Busca executed_tactic_indices diretamente do banco (não precisa vir na request).
    """
    data = request.get_json() or {}
    student_id = data.get('student_id')
    session_id = data.get('session_id')
    is_replan = bool(data.get('is_replan', True))

    if student_id is None or session_id is None:
        return jsonify({"error": "student_id e session_id são obrigatórios"}), 400

    try:
        # Busca progresso do aluno para obter executed_tactic_indices do banco
        executed_tactic_indices = []
        try:
            progress_resp = requests.get(
                f"{CONTROL_URL}/sessions/{session_id}/student/{student_id}/tactic_index",
                timeout=10
            )
            if progress_resp.status_code == 200:
                prog = progress_resp.json()
                executed_tactic_indices = list(prog.get('executed_tactic_indices', []))
        except Exception as e:
            logging.warning("Erro ao buscar progresso para replan student_id=%s: %s", student_id, e)

        session_resp = requests.get(f"{CONTROL_URL}/sessions/{session_id}", timeout=10)
        if session_resp.status_code != 200:
            return jsonify({"error": "Falha ao buscar sessão"}), 502
        session_data = session_resp.json()

        ctx = _aggregate_student_context(student_id, session_id, session_data)
        strategy_tactics = ctx['strategy_tactics']

        if not strategy_tactics:
            return jsonify({"error": "Sem táticas na estratégia"}), 400

        # Táticas ainda não executadas
        remaining_indices = [i for i in range(len(strategy_tactics)) if i not in executed_tactic_indices]

        if not remaining_indices:
            return jsonify({"message": "Sem táticas restantes para replanejar"}), 200

        remaining_tactics = [
            {"index": i, "name": strategy_tactics[i].get('name', ''), "description": strategy_tactics[i].get('description', '')}
            for i in remaining_indices
        ]

        ai_payload = {
            "student_profile": ctx['student_profile'],
            "class_profile": ctx['class_profile'],
            "exercise_scores": ctx['exercise_scores'],
            "all_tactics": remaining_tactics,
            "chat_messages": ctx['chat_messages'],
            "student_history": ctx['student_history'],
            "student_mastery": ctx['student_mastery'],
            "is_replan": is_replan,
        }

        logging.info("Chamando IA para %s student_id=%s remaining=%s",
                     "replanejar" if is_replan else "planejar após exercício",
                     student_id, remaining_indices)

        ai_resp = requests.post(
            f"{STRATEGIES_URL}/agent/plan_session_tactics",
            json=ai_payload,
            timeout=60
        )

        if ai_resp.status_code != 200:
            new_sequence = remaining_indices
            overall_goal = "Continuar com as atividades restantes."
            tactic_reasons = {}
        else:
            ai_data = ai_resp.json()
            new_sequence = ai_data.get('tactic_sequence', remaining_indices)
            overall_goal = ai_data.get('overall_goal', '')
            tactic_reasons = ai_data.get('tactic_reasons', {})

        plan_json = json.dumps({
            "tactic_sequence": new_sequence,
            "overall_goal": overall_goal,
            "tactic_reasons": tactic_reasons,
        })

        # Atualiza apenas o plano, mantendo a tática atual
        requests.post(
            f"{CONTROL_URL}/sessions/{session_id}/student/{student_id}/update_session_plan",
            json={"session_plan": plan_json},
            timeout=10
        )

        logging.info("Plano salvo student_id=%s new_sequence=%s is_replan=%s",
                     student_id, new_sequence, is_replan)

        return jsonify({
            "new_sequence": new_sequence,
            "overall_goal": overall_goal,
            "message": "Plano atualizado com sucesso.",
        }), 200

    except Exception as e:
        logging.error("Erro em replan_session student_id=%s: %s", student_id, str(e))
        return jsonify({"error": "Falha no replanejamento"}), 500
