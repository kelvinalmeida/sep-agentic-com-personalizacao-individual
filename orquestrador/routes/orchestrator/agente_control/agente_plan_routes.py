import json
import logging
import os
import requests
from flask import Blueprint, jsonify, request
from openai import OpenAI
from ...services_routs import CONTROL_URL, STRATEGIES_URL, USER_URL

logging.basicConfig(level=logging.INFO)

agente_plan_bp = Blueprint('agente_plan_bp', __name__)

TACTIC_TYPE_DESCRIPTIONS = """TIPOS DE TÁTICAS:
- Reuso: Apresenta recursos didáticos (PDFs, vídeos, exercícios) por tempo determinado.
- Debate Síncrono: Chat em tempo real entre alunos e professor.
- Envio de Informação: Envia materiais por e-mail.
- Mudança de Estratégia: Troca a estratégia didática atual.
- Regra: Executa ações condicionalmente."""

PERSONALIZATION_GUIDE = """REGRAS DE PERSONALIZAÇÃO DA SEQUÊNCIA (aplique SEMPRE que os dados do aluno indicarem):

Por preferência de conteúdo (pref_content_type):
- 'video' → coloque táticas Reuso antes das táticas síncronas ou de envio.
- 'pdf' ou 'leitura' → coloque táticas Reuso com materiais escritos antes das síncronas.
- 'exercicio' ou 'prática' → coloque táticas Reuso com exercícios mais cedo na sequência.

Por preferência de comunicação (pref_communication):
- 'sincrona' ou 'chat' → coloque Debate Síncrono e Apresentação Síncrona antes de Envio de Informação.
- 'assincrona' ou 'email' → coloque Envio de Informação antes do Debate Síncrono.

Por pref_receive_email:
- true → coloque Envio de Informação antes das atividades práticas.
- false → mova Envio de Informação para o final ou evite colocá-lo em primeiro lugar.

Por maestria:
- maestria < 60% em algum conceito → Reuso deve aparecer cedo para reforçar antes de avançar.
- maestria > 80% em todos os conceitos → o aluno pode ir direto para atividades desafiadoras.
- SEM dados de maestria (primeiro acesso ou sessão nova) → use pref_content_type e pref_communication como critério PRINCIPAL de ordenação.

IMPORTANTE: A ordem das táticas DEVE refletir o perfil individual do aluno.
Dois alunos com preferências diferentes devem ter sequências diferentes.
Reproduzir a ordem padrão só é aceitável se os dados do aluno explicitamente não indicarem outra coisa."""

# ---------------------------------------------------------------------------
# GUARDRAILS — regras pedagógicas obrigatórias
# Cada regra tem: id, descrição legível, e função fix(sequence, tactics, ctx)
# que retorna a sequência corrigida (ou a original se não houver violação).
# ---------------------------------------------------------------------------

_TRANSITION_TACTICS = {"mudança de estratégia", "mudanca de estrategia", "regra", "regras"}
_REVIEW_TACTICS = {"reuso", "debate síncrono", "debate sincrono"}


def _tactic_name(idx, tactics):
    t = next((t for t in tactics if t['index'] == idx), None)
    return t['name'].strip().lower() if t else ""


def _guardrail_no_transition_first(sequence, tactics, ctx):
    """G1: Táticas de transição não podem abrir a sessão."""
    if not sequence:
        return sequence, None
    if _tactic_name(sequence[0], tactics) not in _TRANSITION_TACTICS:
        return sequence, None
    seq = list(sequence)
    for i in range(1, len(seq)):
        if _tactic_name(seq[i], tactics) not in _TRANSITION_TACTICS:
            seq[0], seq[i] = seq[i], seq[0]
            return seq, f"G1: tática de transição removida da 1ª posição (trocada com posição {i+1})"
    return sequence, "G1: violação detectada mas sem tática alternativa disponível"


def _guardrail_review_first_on_replan(sequence, tactics, ctx):
    """G2: No replanejamento após falha, tática de revisão deve ser a primeira."""
    if not ctx.get('is_replan') or not sequence:
        return sequence, None
    if _tactic_name(sequence[0], tactics) in _REVIEW_TACTICS:
        return sequence, None
    seq = list(sequence)
    for i in range(1, len(seq)):
        if _tactic_name(seq[i], tactics) in _REVIEW_TACTICS:
            seq[0], seq[i] = seq[i], seq[0]
            return seq, f"G2: replanejamento sem revisão primeiro — tática de revisão movida para posição 1 (era posição {i+1})"
    return sequence, None


def _guardrail_low_mastery_reuso_early(sequence, tactics, ctx):
    """G3: Se maestria < 40% em algum conceito, Reuso deve estar na primeira metade."""
    mastery = ctx.get('mastery', [])
    if not mastery or not sequence:
        return sequence, None
    has_low_mastery = any(m.get('mastery_pct', 100) < 40 for m in mastery)
    if not has_low_mastery:
        return sequence, None
    half = max(1, len(sequence) // 2)
    first_half = sequence[:half]
    reuso_in_first_half = any(_tactic_name(idx, tactics) == 'reuso' for idx in first_half)
    if reuso_in_first_half:
        return sequence, None
    seq = list(sequence)
    for i in range(half, len(seq)):
        if _tactic_name(seq[i], tactics) == 'reuso':
            target = half - 1
            seq[target], seq[i] = seq[i], seq[target]
            return seq, f"G3: maestria < 40% — Reuso movido para posição {target+1} (era posição {i+1})"
    return sequence, None


GUARDRAILS = [
    _guardrail_no_transition_first,
    _guardrail_review_first_on_replan,
    _guardrail_low_mastery_reuso_early,
]

GUARDRAIL_DESCRIPTIONS = """RESTRIÇÕES PEDAGÓGICAS OBRIGATÓRIAS (você DEVE respeitá-las):
G1: Táticas de transição ("Mudança de Estratégia", "Regra") não podem ser a primeira tática da sequência.
G2: Em replanejamento após falha, a primeira tática deve ser de revisão ("Reuso" ou "Debate Síncrono") se disponível.
G3: Se o aluno tem maestria < 40% em algum conceito, "Reuso" deve estar na primeira metade da sequência."""


def _apply_guardrails(plan, available_tactics, is_replan, mastery=None):
    """Aplica todas as regras de guardrails à sequência gerada pelo agente."""
    sequence = list(plan['tactic_sequence'])
    ctx = {'is_replan': is_replan, 'mastery': mastery or []}
    violations = []

    for rule_fn in GUARDRAILS:
        sequence, msg = rule_fn(sequence, available_tactics, ctx)
        if msg:
            violations.append(msg)
            logging.warning("Guardrail aplicado: %s", msg)

    if violations:
        logging.info("Total de guardrails aplicados: %d — %s", len(violations), violations)

    return {**plan, 'tactic_sequence': sequence}, violations


# ---------------------------------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_student_profile",
            "description": "Busca o perfil individual do aluno: curso, idade, tipo de conteúdo preferido, forma de comunicação preferida e se aceita e-mail.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_class_profile",
            "description": "Busca as preferências de todos os alunos matriculados na sessão.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_student_mastery",
            "description": "Busca a maestria do aluno por conceito: percentuais da sessão atual e médias de sessões anteriores. Percentuais menores indicam maior necessidade de reforço.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_student_history",
            "description": "Busca o histórico das últimas sessões do aluno com resumos de desempenho.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_exercise_scores",
            "description": "Busca as notas do aluno nos exercícios da sessão atual.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_chat_messages",
            "description": "Busca as últimas mensagens enviadas pelo aluno nos chats das táticas desta sessão.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_session_plan",
            "description": "Cria o plano final da sessão. Chame esta ferramenta quando tiver informações suficientes para criar um plano pedagógico personalizado.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tactic_sequence": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Lista ordenada com TODOS os índices de táticas disponíveis, cada um exatamente uma vez."
                    },
                    "overall_goal": {
                        "type": "string",
                        "description": "Objetivo pedagógico claro e motivador para esta sessão em 1-2 frases."
                    },
                    "tactic_reasons": {
                        "type": "object",
                        "additionalProperties": {"type": "string"},
                        "description": "Justificativa para cada tática, com o índice como chave string."
                    }
                },
                "required": ["tactic_sequence", "overall_goal", "tactic_reasons"]
            }
        }
    }
]


def _build_groq_client():
    return OpenAI(
        api_key=os.environ.get('GROQ_API_KEY'),
        base_url="https://api.groq.com/openai/v1"
    )


def _run_planner_agent(student_id, session_id, session_data, available_tactics, is_replan=False):
    """
    Loop agentico: o LLM decide quais ferramentas chamar para coletar dados
    sobre o aluno e então chama create_session_plan com o plano final.
    Retorna (plan_dict, mastery_data) onde mastery_data é usado pelos guardrails.
    """
    strategy_ids = session_data.get('strategies', [])
    student_ids = session_data.get('students', [])
    strategy_id = strategy_ids[0] if strategy_ids else None

    strategy_tactics = []
    if strategy_id:
        try:
            r = requests.get(f"{STRATEGIES_URL}/strategies/{strategy_id}", timeout=10)
            if r.status_code == 200:
                strategy_tactics = r.json().get('tatics', [])
        except Exception as e:
            logging.warning("Erro ao buscar táticas strategy_id=%s: %s", strategy_id, e)

    valid_indices = [t['index'] for t in available_tactics]
    tactics_text = "\n".join(
        f"- Índice {t['index']}: {t['name']} | {str(t.get('description', ''))[:120]}"
        for t in available_tactics
    )
    replan_note = (
        "\nATENÇÃO: Este é um REPLANEJAMENTO após dificuldades. "
        "Priorize táticas que reforcem os pontos fracos identificados.\n"
        if is_replan else ""
    )

    system_prompt = f"""Você é um especialista em aprendizagem adaptativa.
Sua tarefa é criar uma sequência personalizada de táticas para um aluno específico.
{replan_note}
{TACTIC_TYPE_DESCRIPTIONS}

{PERSONALIZATION_GUIDE}

{GUARDRAIL_DESCRIPTIONS}

TÁTICAS DISPONÍVEIS (todos os índices {valid_indices} devem aparecer no plano):
{tactics_text}

INSTRUÇÕES:
1. OBRIGATÓRIO: chame get_student_profile e get_student_mastery antes de criar o plano.
2. Use as demais ferramentas conforme relevante (histórico enriquece o contexto).
3. Respeite obrigatoriamente as RESTRIÇÕES PEDAGÓGICAS ao ordenar as táticas.
4. Somente após coletar dados do aluno, chame create_session_plan com o plano final.
5. O plano deve conter EXATAMENTE os índices {valid_indices}, cada um UMA única vez.
6. A ORDEM deve ser personalizada: use pref_content_type e pref_communication como critério principal quando não há dados de maestria; use maestria como critério principal quando disponível.
7. Em tactic_reasons, explique para cada tática POR QUE ela está naquela posição com base nos dados do aluno."""

    # Captura mastery durante execução para uso nos guardrails
    mastery_captured = []

    # --- Implementações das ferramentas ---

    def _exec_get_student_profile():
        try:
            r = requests.get(f"{USER_URL}/students/{student_id}/preferences", timeout=10)
            if r.status_code == 200:
                d = r.json()
                return {
                    "course": d.get('course') or 'N/A',
                    "age": d.get('age') or 'N/A',
                    "pref_content_type": d.get('pref_content_type') or 'N/A',
                    "pref_communication": d.get('pref_communication') or 'N/A',
                    "pref_receive_email": d.get('pref_receive_email', False),
                }
        except Exception as e:
            logging.warning("Erro get_student_profile student_id=%s: %s", student_id, e)
        return {"error": "Perfil não disponível."}

    def _exec_get_class_profile():
        try:
            r = requests.post(
                f"{USER_URL}/students/batch_preferences",
                json={"student_ids": student_ids},
                timeout=10
            )
            if r.status_code == 200:
                students = r.json().get('students', [])
                return [{k: v for k, v in s.items() if k != 'name'} for s in students]
        except Exception as e:
            logging.warning("Erro get_class_profile: %s", e)
        return []

    def _exec_get_student_mastery():
        nonlocal mastery_captured
        history_entries = []
        try:
            h = requests.get(
                f"{USER_URL}/students/{student_id}/learning_history",
                params={"limit": 3}, timeout=10
            )
            if h.status_code == 200:
                history_entries = h.json().get('history', [])
        except Exception:
            pass

        current_mastery = []
        try:
            m = requests.get(
                f"{USER_URL}/students/{student_id}/mastery",
                params={"session_id": session_id}, timeout=10
            )
            if m.status_code == 200:
                current_mastery = m.json().get('mastery', [])
        except Exception:
            pass

        concept_totals: dict = {}
        concept_counts: dict = {}
        for entry in history_entries:
            past_sid = entry.get('session_id')
            if not past_sid or str(past_sid) == str(session_id):
                continue
            try:
                pm = requests.get(
                    f"{USER_URL}/students/{student_id}/mastery",
                    params={"session_id": past_sid}, timeout=5
                )
                if pm.status_code == 200:
                    for m in pm.json().get('mastery', []):
                        c = m['concept']
                        concept_totals[c] = concept_totals.get(c, 0) + m['mastery_pct']
                        concept_counts[c] = concept_counts.get(c, 0) + 1
            except Exception:
                pass

        historical = [
            {
                "concept": c,
                "mastery_pct": round(concept_totals[c] / concept_counts[c]),
                "sessions_count": concept_counts[c],
            }
            for c in concept_totals
        ]

        # Captura para guardrail G3: usa maestria atual ou histórica
        mastery_captured = current_mastery if current_mastery else historical

        no_data = not current_mastery and not historical
        return {
            "current_session": current_mastery if current_mastery else "Nenhum exercício respondido ainda nesta sessão.",
            "historical_average": historical if historical else "Nenhum histórico de sessões anteriores.",
            "personalization_note": (
                "Sem dados de maestria disponíveis. Use pref_content_type e pref_communication "
                "do perfil do aluno como critério PRINCIPAL para ordenar as táticas."
            ) if no_data else None,
        }

    def _exec_get_student_history():
        try:
            r = requests.get(
                f"{USER_URL}/students/{student_id}/learning_history",
                params={"limit": 3}, timeout=10
            )
            if r.status_code == 200:
                return r.json().get('history', [])
        except Exception as e:
            logging.warning("Erro get_student_history student_id=%s: %s", student_id, e)
        return []

    def _exec_get_exercise_scores():
        verified = [
            v for v in session_data.get('verified_answers', [])
            if str(v.get('student_id', '')) == str(student_id)
        ]
        if not verified:
            return {"message": "Sem registros de exercícios nesta sessão."}
        scores = [v.get('score', 0) for v in verified]
        latest = verified[-1]
        total_q = max(len(latest.get('answers', [])), 1)
        return {
            "attempts": len(scores),
            "scores": scores,
            "latest_score": latest.get('score', 0),
            "latest_total": total_q,
            "latest_pct": int((latest.get('score', 0) / total_q) * 100),
        }

    def _exec_get_chat_messages():
        student_username = str(student_id)
        try:
            sr = requests.get(f"{USER_URL}/students/{student_id}", timeout=10)
            if sr.status_code == 200:
                student_username = sr.json().get('username', str(student_id))
        except Exception:
            pass

        messages = []
        for tactic in strategy_tactics:
            chat_id = tactic.get('chat_id')
            if not chat_id:
                continue
            try:
                cr = requests.get(f"{STRATEGIES_URL}/chat/{chat_id}/general_messages", timeout=10)
                if cr.status_code == 200:
                    resp = cr.json()
                    msgs = resp.get('messages', []) if isinstance(resp, dict) else resp
                    for msg in (msgs or []):
                        if isinstance(msg, dict) and msg.get('username') == student_username:
                            messages.append(msg.get('content', ''))
            except Exception:
                pass
        return {"messages": messages[-5:]}

    tool_executors = {
        "get_student_profile": _exec_get_student_profile,
        "get_class_profile": _exec_get_class_profile,
        "get_student_mastery": _exec_get_student_mastery,
        "get_student_history": _exec_get_student_history,
        "get_exercise_scores": _exec_get_exercise_scores,
        "get_chat_messages": _exec_get_chat_messages,
    }

    # On the first iteration, exclude create_session_plan so the agent is
    # forced to gather at least one piece of student-specific data before planning.
    _data_tools_only = [t for t in TOOLS if t['function']['name'] != 'create_session_plan']

    client = _build_groq_client()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Colete os dados do aluno e crie o plano de sessão personalizado para ele."}
    ]

    data_gathered = False
    max_iterations = 10
    for iteration in range(max_iterations):
        tools_for_call = _data_tools_only if not data_gathered else TOOLS
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            tools=tools_for_call,
            tool_choice="required",
            temperature=0.3
        )

        msg = response.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            break

        plan_result = None
        tool_results = []

        for tool_call in msg.tool_calls:
            fn_name = tool_call.function.name
            logging.info("Agente chamou: %s (iter=%d, student=%s)", fn_name, iteration, student_id)

            if fn_name == "create_session_plan":
                try:
                    plan_result = json.loads(tool_call.function.arguments)
                except Exception:
                    plan_result = {}
                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": "Plano registrado."
                })
            elif fn_name in tool_executors:
                result = tool_executors[fn_name]()
                data_gathered = True
                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False)
                })
            else:
                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": "Ferramenta não reconhecida."
                })

        messages.extend(tool_results)

        if plan_result is not None:
            raw_seq = plan_result.get('tactic_sequence', [])
            seen, seq = set(), []
            for i in raw_seq:
                try:
                    idx = int(i)
                    if idx in valid_indices and idx not in seen:
                        seq.append(idx)
                        seen.add(idx)
                except (ValueError, TypeError):
                    pass
            for idx in valid_indices:
                if idx not in seen:
                    seq.append(idx)

            logging.info("Plano gerado em %d iteração(ões): sequence=%s student=%s", iteration + 1, seq, student_id)
            raw_plan = {
                "tactic_sequence": seq,
                "overall_goal": plan_result.get('overall_goal', ''),
                "tactic_reasons": plan_result.get('tactic_reasons', {}),
            }
            return raw_plan, mastery_captured

    logging.warning("Agente não gerou plano em %d iterações, usando fallback. student=%s", max_iterations, student_id)
    return {
        "tactic_sequence": valid_indices,
        "overall_goal": "Completar todas as atividades da sessão.",
        "tactic_reasons": {},
    }, mastery_captured


@agente_plan_bp.route('/orchestrator/agent/plan_session', methods=['POST'])
def plan_session():
    """
    Planejamento inicial: agente decide quais dados coletar e cria a sequência
    completa de táticas antes de iniciar a primeira tática.
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

        strategy_ids = session_data.get('strategies', [])
        strategy_id = strategy_ids[0] if strategy_ids else None
        strategy_tactics = []
        if strategy_id:
            strat_resp = requests.get(f"{STRATEGIES_URL}/strategies/{strategy_id}", timeout=10)
            if strat_resp.status_code == 200:
                strategy_tactics = strat_resp.json().get('tatics', [])

        if not strategy_tactics:
            return jsonify({"error": "Sem táticas na estratégia"}), 400

        available_tactics = [
            {"index": i, "name": t.get('name', ''), "description": t.get('description', '')}
            for i, t in enumerate(strategy_tactics)
        ]

        logging.info("Iniciando agente planejador student_id=%s session_id=%s", student_id, session_id)
        plan, mastery = _run_planner_agent(student_id, session_id, session_data, available_tactics, is_replan=False)
        plan, violations = _apply_guardrails(plan, available_tactics, is_replan=False, mastery=mastery)

        tactic_sequence = plan['tactic_sequence']
        next_tactic_index = tactic_sequence[0] if tactic_sequence else 0
        next_tactic_name = (
            strategy_tactics[next_tactic_index].get('name', '')
            if next_tactic_index < len(strategy_tactics) else ''
        )

        plan_json = json.dumps({
            "tactic_sequence": tactic_sequence,
            "overall_goal": plan['overall_goal'],
            "tactic_reasons": plan['tactic_reasons'],
            "guardrail_violations": violations,
        })

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

        logging.info("Plano salvo student_id=%s sequence=%s guardrails=%s", student_id, tactic_sequence, violations)

        return jsonify({
            "next_tactic_index": next_tactic_index,
            "next_tactic_name": next_tactic_name,
            "overall_goal": plan['overall_goal'],
            "tactic_sequence": tactic_sequence,
            "reasoning": plan['tactic_reasons'].get(str(next_tactic_index), plan['overall_goal']),
            "guardrail_violations": violations,
        }), 200

    except Exception as e:
        logging.error("Erro em plan_session student_id=%s: %s", student_id, str(e))
        return jsonify({"error": "Falha no planejamento da sessão"}), 500


@agente_plan_bp.route('/orchestrator/agent/replan_session', methods=['POST'])
def replan_session():
    """
    Planeja/replaneja as táticas restantes.
    - is_replan=False: após primeiro exercício, planeja com maestria real.
    - is_replan=True: 2ª falha no Reuso, reordena para reforçar pontos fracos.
    """
    data = request.get_json() or {}
    student_id = data.get('student_id')
    session_id = data.get('session_id')
    is_replan = bool(data.get('is_replan', True))

    if student_id is None or session_id is None:
        return jsonify({"error": "student_id e session_id são obrigatórios"}), 400

    try:
        executed_tactic_indices = []
        try:
            progress_resp = requests.get(
                f"{CONTROL_URL}/sessions/{session_id}/student/{student_id}/tactic_index",
                timeout=10
            )
            if progress_resp.status_code == 200:
                executed_tactic_indices = list(progress_resp.json().get('executed_tactic_indices', []))
        except Exception as e:
            logging.warning("Erro ao buscar progresso student_id=%s: %s", student_id, e)

        session_resp = requests.get(f"{CONTROL_URL}/sessions/{session_id}", timeout=10)
        if session_resp.status_code != 200:
            return jsonify({"error": "Falha ao buscar sessão"}), 502
        session_data = session_resp.json()

        strategy_ids = session_data.get('strategies', [])
        strategy_id = strategy_ids[0] if strategy_ids else None
        strategy_tactics = []
        if strategy_id:
            strat_resp = requests.get(f"{STRATEGIES_URL}/strategies/{strategy_id}", timeout=10)
            if strat_resp.status_code == 200:
                strategy_tactics = strat_resp.json().get('tatics', [])

        if not strategy_tactics:
            return jsonify({"error": "Sem táticas na estratégia"}), 400

        remaining_indices = [i for i in range(len(strategy_tactics)) if i not in executed_tactic_indices]

        if not remaining_indices:
            return jsonify({"message": "Sem táticas restantes para replanejar"}), 200

        available_tactics = [
            {"index": i, "name": strategy_tactics[i].get('name', ''), "description": strategy_tactics[i].get('description', '')}
            for i in remaining_indices
        ]

        logging.info(
            "Iniciando agente %s student_id=%s remaining=%s",
            "replanejador" if is_replan else "planejador pós-exercício",
            student_id, remaining_indices
        )
        plan, mastery = _run_planner_agent(student_id, session_id, session_data, available_tactics, is_replan=is_replan)
        plan, violations = _apply_guardrails(plan, available_tactics, is_replan=is_replan, mastery=mastery)

        plan_json = json.dumps({
            "tactic_sequence": plan['tactic_sequence'],
            "overall_goal": plan['overall_goal'],
            "tactic_reasons": plan['tactic_reasons'],
            "guardrail_violations": violations,
        })

        requests.post(
            f"{CONTROL_URL}/sessions/{session_id}/student/{student_id}/update_session_plan",
            json={"session_plan": plan_json},
            timeout=10
        )

        logging.info("Plano atualizado student_id=%s new_sequence=%s is_replan=%s guardrails=%s",
                     student_id, plan['tactic_sequence'], is_replan, violations)

        return jsonify({
            "new_sequence": plan['tactic_sequence'],
            "overall_goal": plan['overall_goal'],
            "message": "Plano atualizado com sucesso.",
            "guardrail_violations": violations,
        }), 200

    except Exception as e:
        logging.error("Erro em replan_session student_id=%s: %s", student_id, str(e))
        return jsonify({"error": "Falha no replanejamento"}), 500


@agente_plan_bp.route('/orchestrator/teacher/student_plans', methods=['GET'])
def get_student_plans():
    """Retorna os planos personalizados de todos os alunos de uma sessão."""
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({"error": "session_id é obrigatório"}), 400

    try:
        sess_resp = requests.get(f"{CONTROL_URL}/sessions/{session_id}", timeout=10)
        if sess_resp.status_code != 200:
            return jsonify({"error": "Sessão não encontrada"}), 404
        session_data = sess_resp.json()

        student_ids = session_data.get('students', [])
        strategy_ids = session_data.get('strategies', [])

        tactics_map = {}
        if strategy_ids:
            try:
                sr = requests.get(f"{STRATEGIES_URL}/strategies/{strategy_ids[0]}", timeout=10)
                if sr.status_code == 200:
                    tactics = sr.json().get('tatics', [])
                    tactics_map = {i: t.get('name', f'Tática {i}') for i, t in enumerate(tactics)}
            except Exception:
                pass

        student_names = {}
        if student_ids:
            try:
                nr = requests.get(
                    f"{USER_URL}/students/ids_to_usernames",
                    params={'ids': student_ids},
                    timeout=10
                )
                if nr.status_code == 200:
                    for s in nr.json().get('ids_with_usernames', []):
                        student_names[str(s['id'])] = s['username']
            except Exception:
                pass

        plans = []
        for student_id in student_ids:
            try:
                pr = requests.get(
                    f"{CONTROL_URL}/sessions/{session_id}/student/{student_id}/tactic_index",
                    timeout=10
                )
                if pr.status_code != 200:
                    continue
                raw_plan = pr.json().get('session_plan')
                if not raw_plan:
                    continue

                plan_data = json.loads(raw_plan) if isinstance(raw_plan, str) else raw_plan
                tactic_sequence = plan_data.get('tactic_sequence', [])
                tactic_reasons = plan_data.get('tactic_reasons', {})

                plans.append({
                    'student_id': str(student_id),
                    'student_name': student_names.get(str(student_id), f'Aluno {student_id}'),
                    'overall_goal': plan_data.get('overall_goal', ''),
                    'tactic_sequence': [
                        {
                            'index': i,
                            'name': tactics_map.get(i, f'Tática {i}'),
                            'reason': tactic_reasons.get(str(i), ''),
                        }
                        for i in tactic_sequence
                    ],
                    'guardrail_violations': plan_data.get('guardrail_violations', []),
                })
            except Exception as e:
                logging.warning("Erro ao buscar plano student_id=%s: %s", student_id, e)

        return jsonify(plans), 200

    except Exception as e:
        logging.error("Erro em get_student_plans session_id=%s: %s", session_id, e)
        return jsonify({"error": "Falha ao buscar planos"}), 500
