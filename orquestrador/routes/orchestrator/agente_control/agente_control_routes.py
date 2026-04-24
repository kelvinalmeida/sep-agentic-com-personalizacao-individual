import requests
import logging
import re
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


@agente_control_orch_bp.route('/orchestrator/agent/student_session_difficulty_summary', methods=['POST'])
def orchestrate_student_session_difficulty_summary():
    """
    Orquestra a coleta de exercícios no Domain e envia o contexto enriquecido
    para o endpoint do Control responsável pelo resumo de dificuldade.
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
        control_resp = requests.post(
            f"{CONTROL_URL}/agent/student_session_difficulty_summary",
            json=control_payload,
            timeout=60
        )

        response_json = {}
        try:
            response_json = control_resp.json()
        except Exception:
            response_json = {"raw": control_resp.text}

        return jsonify(response_json), control_resp.status_code

    except Exception as e:
        logging.error(f"Erro no orquestrador de student_session_difficulty_summary: {str(e)}")
        return jsonify({"error": "Falha na orquestração do resumo de dificuldade"}), 500


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
        # === FLUXO DE AGENTE DE IA ===
        logging.info("🤖 Agente de Estratégia ATIVADO. Iniciando ciclo de decisão...")

        # 1. Dados da Sessão (Control)
        strategy_id = session_json.get('strategies', [None])[0]

        # Inferir táticas executadas (usando histórico real do Control)
        executed_ids = []
        tactics = []
        if strategy_id:
            strat_res = requests.get(f"{STRATEGIES_URL}/strategies/{strategy_id}")
            if strat_res.status_code == 200:
                strat_data = strat_res.json()
                tactics = strat_data.get('tatics', [])

                # NOVO: Usar executed_indices do Control
                executed_indices = session_json.get('executed_indices', [])
                current_idx = session_json.get('current_tactic_index', 0)

                # Mapeia índices para IDs
                for idx in executed_indices:
                    if 0 <= idx < len(tactics):
                        executed_ids.append(tactics[idx]['id'])

                # Adiciona a atual também, pois ela acabou de ser "feita" no momento da decisão
                # Evita duplicidade se já estiver no histórico (embora Control adicione no next, aqui estamos decidindo O PRÓXIMO)
                if 0 <= current_idx < len(tactics):
                    current_id = tactics[current_idx]['id']
                    if current_id not in executed_ids:
                        executed_ids.append(current_id)

                # --- NEW CHECK: Se todas as táticas foram executadas, encerra a sessão ---
                # Apenas se a estratégia atual NÃO for vazia
                if tactics:
                    all_tactic_ids = {t['id'] for t in tactics}
                    executed_ids_set = set(executed_ids)

                    # Se já cobrimos todas as táticas da estratégia atual
                    if all_tactic_ids.issubset(executed_ids_set):
                        logging.info("🏁 Todas as táticas da estratégia atual foram executadas. Encerrando sessão.")

                        # Chama endpoint de fim de sessão no Control
                        end_res = requests.post(f"{CONTROL_URL}/sessions/end/{session_id}")

                        if end_res.status_code == 200:
                            return jsonify({
                                "success": True,
                                "session_status": "finished",
                                "message": "All tactics executed."
                            }), 200
                        else:
                            logging.error(f"Erro ao encerrar sessão: {end_res.text}")

        performance_res = requests.get(f"{CONTROL_URL}/sessions/{session_id}/agent_summary")
        performance_summary = performance_res.json().get('summary', 'Sem dados de performance.') if performance_res.status_code == 200 else 'Erro ao buscar performance.'

        # 2. Dados do Aluno/Turma (User)
        student_ids = session_json.get('students', [])
        student_profile_summary = "Sem alunos."
        if student_ids:
             user_res = requests.post(f"{USER_URL}/students/summarize_preferences", json={"student_ids": student_ids})
             if user_res.status_code == 200:
                 student_profile_summary = user_res.json().get('summary', 'Perfil não informado.')

        # 3. Conteúdo do Domínio (Domain)
        domain_id = session_json.get('domains', [None])[0]
        domain_name = "Domínio Desconhecido"
        domain_description = ""

        if domain_id:
             dom_res = requests.get(f"{DOMAIN_URL}/domains/{domain_id}")
             if dom_res.status_code == 200:
                 d_data = dom_res.json()
                 domain_name = d_data.get('name', '')
                 domain_description = d_data.get('description', '')

        content_res = requests.get(f"{DOMAIN_URL}/get_content/2") # MVP
        article_text = content_res.json().get('content', '') if content_res.status_code == 200 else ''

        # 4. Chamada ao Agente (Strategies)
        agent_payload = {
            "strategy_id": strategy_id,
            "executed_tactics": executed_ids,
            "student_profile_summary": student_profile_summary,
            "performance_summary": performance_summary,
            "domain_name": domain_name,
            "domain_description": domain_description,
            "article_text": article_text
        }

        logging.info(f"📤 Enviando payload para Agente: {agent_payload.keys()}")
        agent_res = requests.post(f"{STRATEGIES_URL}/agent/decide_next_tactic", json=agent_payload)

        if agent_res.status_code == 200:
            decision = agent_res.json().get('decision', {})
            chosen_tactic_id = decision.get('chosen_tactic_id')

            logging.info(f"📥 Decisão do Agente: Tática ID {chosen_tactic_id}")

            # 5. Aplicar Decisão (Encontrar índice e setar)
            if chosen_tactic_id and strategy_id:
                 # Reusar tactics já buscadas acima
                 target_index = -1
                 for idx, t in enumerate(tactics):
                     if t['id'] == chosen_tactic_id:
                         target_index = idx
                         break

                 if target_index != -1:
                     # Seta o índice no Control
                     requests.post(f"{CONTROL_URL}/sessions/tactic/set/{session_id}", json={'tactic_index': target_index})
                     logging.info(f"✅ Índice da tática atualizado para {target_index}")

                     # --- VERIFICAÇÃO DE MUDANÇA DE ESTRATÉGIA ---
                     current_tactic = tactics[target_index]
                     tactic_name = current_tactic.get('name', '').strip().lower()
                     valid_names = ["mudanca de estrategia", "mudança de estratégia", "mudança de estrategia", "mudanca de estratégia"]

                     if tactic_name in valid_names:
                         description = str(current_tactic.get('description', ''))
                         match = re.search(r'\d+', description)

                         if match:
                             target_strategy_id = int(match.group())
                             logging.info(f"🔄 Agente escolheu MUDANÇA DE ESTRATÉGIA para ID: {target_strategy_id}")

                             # Aciona a troca temporária
                             switch_res = requests.post(
                                 f"{CONTROL_URL}/sessions/{session_id}/temp_switch_strategy",
                                 json={'strategy_id': target_strategy_id}
                             )

                             if switch_res.status_code != 200:
                                 logging.error(f"❌ Falha ao trocar estratégia (Agente): {switch_res.text}")
                             else:
                                 logging.info("✅ Estratégia trocada com sucesso pelo Agente.")
                         else:
                             logging.warning(f"⚠️ Tática de mudança escolhida, mas sem ID na descrição: {description}")

                     return jsonify({"success": True, "agent_decision": decision}), 200
                 else:
                     logging.error("❌ Tática escolhida pelo agente não encontrada na estratégia atual.")
        else:
             logging.error(f"❌ Falha no Agente Strategies: {agent_res.text}")

    except Exception as e:
        logging.error(f"Erro na orquestração do Agente: {e}")

    # Se falhar ou não decidir, retorna None para indicar fallback
    return None
