import json
import logging
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

USER_URL = 'http://user:5002'
CONTROL_URL = 'http://agente_sessao:5001'


def _build_session_summary(sessions):
    if not sessions:
        return "Nenhuma sessão encontrada para este professor."
    lines = []
    for s in sessions:
        session_id = s.get('id')
        status = s.get('status', 'desconhecido')
        students = s.get('students', [])
        verified = s.get('verified_answers', [])
        rating_avg = s.get('rating_average', 0)
        if verified:
            scores = [v.get('score', 0) for v in verified]
            avg = sum(scores) / len(scores) if scores else 0
            lines.append(
                f"- Sessão {session_id} ({status}): {len(students)} aluno(s), "
                f"{len(verified)} resposta(s), média de acertos: {avg:.1f}, "
                f"avaliação média da sessão: {rating_avg:.1f}"
            )
        else:
            lines.append(
                f"- Sessão {session_id} ({status}): {len(students)} aluno(s), "
                f"sem respostas registradas, avaliação: {rating_avg:.1f}"
            )
    return "\n".join(lines)


def generate_reports_for_all_teachers(app):
    with app.app_context():
        from app.models import TeacherReport
        from app import db
        from config import Config
        from openai import OpenAI

        logging.info("[Scheduler] Iniciando geração de relatórios para professores")

        try:
            teachers_resp = requests.get(f"{USER_URL}/teachers", timeout=15)
            if teachers_resp.status_code != 200:
                logging.error("[Scheduler] Falha ao buscar professores: %s", teachers_resp.status_code)
                return
            teachers = teachers_resp.json()
        except Exception as e:
            logging.error("[Scheduler] Erro ao buscar professores: %s", e)
            return

        try:
            sessions_resp = requests.get(f"{CONTROL_URL}/sessions", timeout=30)
            all_sessions = sessions_resp.json() if sessions_resp.status_code == 200 else []
        except Exception as e:
            logging.warning("[Scheduler] Erro ao buscar sessões: %s", e)
            all_sessions = []

        if not Config.GROQ_API_KEY:
            logging.error("[Scheduler] GROQ_API_KEY não configurada")
            return

        client = OpenAI(api_key=Config.GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

        for teacher in teachers:
            teacher_id = teacher.get('id')
            teacher_name = teacher.get('name', 'Professor')

            try:
                teacher_sessions = [
                    s for s in all_sessions
                    if str(teacher_id) in [str(t) for t in s.get('teachers', [])]
                ]
                session_summary = _build_session_summary(teacher_sessions)

                prompt = f"""
Você é um agente educacional que analisa periodicamente o desempenho das sessões de aprendizagem.
Gere um relatório de desempenho para o professor {teacher_name}.

SESSÕES DO PROFESSOR:
{session_summary}

Responda APENAS em JSON exato:
{{
  "performance_summary": "<análise de 150-200 palavras sobre padrões observados, pontos fortes e áreas de atenção nas sessões>",
  "tips": "<2-3 dicas curtas, objetivas e acionáveis para melhorar o engajamento e a aprendizagem dos alunos>"
}}
"""
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "Você é especialista em análise pedagógica. Responda apenas JSON válido."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3
                )

                content = json.loads(response.choices[0].message.content or "{}")
                report = TeacherReport(
                    teacher_id=teacher_id,
                    teacher_name=teacher_name,
                    performance_summary=content.get('performance_summary', ''),
                    tips=content.get('tips', ''),
                    sessions_analyzed=len(teacher_sessions)
                )
                db.session.add(report)
                db.session.commit()
                logging.info("[Scheduler] Relatório gerado para teacher_id=%s", teacher_id)

            except Exception as e:
                logging.error("[Scheduler] Erro para teacher_id=%s: %s", teacher_id, e)
                db.session.rollback()


def start_scheduler(app):
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(
        func=lambda: generate_reports_for_all_teachers(app),
        trigger=IntervalTrigger(days=2),
        id='teacher_reports',
        replace_existing=True
    )
    scheduler.start()
    logging.info("[Scheduler] Iniciado — relatórios de professores a cada 2 dias")
    return scheduler
