import logging
import os
import requests
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from openai import OpenAI

CONTROL_URL = 'http://agente_sessao:5001'
DOMAIN_URL = 'http://domain:5004'

PROACTIVE_COOLDOWN_MINUTES = 5


def _ensure_tables(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tutor_chat_history (
                id SERIAL PRIMARY KEY,
                student_username VARCHAR(100) NOT NULL,
                sender VARCHAR(20) NOT NULL,
                message TEXT NOT NULL,
                session_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            ALTER TABLE tutor_chat_history
            ADD COLUMN IF NOT EXISTS session_id INTEGER
        """)
    conn.commit()


def _get_domain_info(domain_ids):
    """Returns (name, description) for the first domain in the list."""
    if not domain_ids:
        return '', ''
    try:
        resp = requests.get(
            f"{DOMAIN_URL}/domains/ids_to_names",
            params={'ids': domain_ids},
            timeout=8
        )
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and data:
                first = data[0]
                if isinstance(first, dict):
                    return first.get('name', ''), first.get('description', '')
                return str(first), ''
            if isinstance(data, dict):
                first = next(iter(data.values()), {})
                if isinstance(first, dict):
                    return first.get('name', ''), first.get('description', '')
    except Exception:
        pass
    return '', ''


def _generate_tip(client, domain_name, domain_desc, pref_content_type):
    """Generates a short pedagogical tip (≤ 100 words) via LLM."""
    topic = domain_name or 'conteúdo da sessão'

    pref_line = f"\nPreferência de conteúdo: {pref_content_type}." if pref_content_type else ''

    prompt = f"""Você é um tutor educacional proativo acompanhando ESTUDANTE em uma sessão sobre "{topic}".
{('Descrição: ' + domain_desc[:200]) if domain_desc else ''}{pref_line}

Gere UMA dica pedagógica curta (máximo 100 palavras) e motivadora para ajudar o estudante com o conteúdo da sessão.
Regras:
- NUNCA revele respostas de exercícios ou gabaritos
- Use sempre "você" (nunca o nome do aluno)
- Dê uma dica geral e encorajadora sobre o tema
- Sem markdown, sem JSON, apenas texto corrido"""

    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Você escreve dicas pedagógicas curtas e motivadoras. Nunca revela gabaritos."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=150
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        logging.warning("[ProactiveScheduler] Falha ao gerar dica LLM: %s", e)
        return f"Continue praticando! Cada exercício sobre {topic} fortalece seu aprendizado. Você consegue!"


def send_proactive_tips(app):
    with app.app_context():
        from config import Config

        try:
            from db import create_connection
        except ImportError:
            logging.error("[ProactiveScheduler] Não foi possível importar create_connection")
            return

        db_url = os.getenv('DATABASE_URL')

        # 1. Buscar sessões ativas
        try:
            resp = requests.get(f"{CONTROL_URL}/sessions", timeout=15)
            all_sessions = resp.json() if resp.status_code == 200 else []
        except Exception as e:
            logging.error("[ProactiveScheduler] Erro ao buscar sessões: %s", e)
            return

        active_sessions = [s for s in all_sessions if s.get('status') == 'in-progress']
        if not active_sessions:
            return

        if not getattr(Config, 'GROQ_API_KEY', None):
            logging.error("[ProactiveScheduler] GROQ_API_KEY não configurada")
            return

        client = OpenAI(api_key=Config.GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

        conn = create_connection(db_url)
        if not conn:
            logging.error("[ProactiveScheduler] Falha na conexão com o banco")
            return

        try:
            _ensure_tables(conn)

            for session in active_sessions:
                session_id = session.get('id')
                student_ids = session.get('students', [])
                domain_ids = session.get('domains', [])

                domain_name, domain_desc = _get_domain_info(domain_ids)

                for student_id in student_ids:
                    try:
                        with conn.cursor() as cur:
                            cur.execute("""
                                SELECT username, pref_content_type
                                FROM student WHERE student_id = %s
                            """, (int(student_id),))
                            student_row = cur.fetchone()

                        if not student_row:
                            continue

                        username = student_row['username']
                        pref = student_row.get('pref_content_type', '') or ''

                        # Dedup: pular se última dica foi há menos de COOLDOWN minutos
                        with conn.cursor() as cur:
                            cur.execute("""
                                SELECT created_at FROM tutor_chat_history
                                WHERE student_username = %s
                                  AND session_id = %s
                                  AND sender = 'proactive'
                                ORDER BY created_at DESC LIMIT 1
                            """, (username, session_id))
                            last_row = cur.fetchone()

                        if last_row:
                            last_time = last_row['created_at']
                            if datetime.utcnow() - last_time < timedelta(minutes=PROACTIVE_COOLDOWN_MINUTES):
                                continue

                        tip = _generate_tip(client, domain_name, domain_desc, pref)

                        with conn.cursor() as cur:
                            cur.execute("""
                                INSERT INTO tutor_chat_history
                                    (student_username, sender, message, session_id)
                                VALUES (%s, 'proactive', %s, %s)
                            """, (username, tip, session_id))
                        conn.commit()

                        logging.info(
                            "[ProactiveScheduler] Dica enviada — aluno=%s sessão=%s",
                            username, session_id
                        )

                    except Exception as e:
                        logging.error(
                            "[ProactiveScheduler] Erro — student_id=%s sessão=%s: %s",
                            student_id, session_id, e
                        )
                        try:
                            conn.rollback()
                        except Exception:
                            pass

        finally:
            conn.close()


def start_scheduler(app):
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(
        func=lambda: send_proactive_tips(app),
        trigger=IntervalTrigger(minutes=1),
        id='proactive_tips',
        replace_existing=True
    )
    scheduler.start()
    logging.info(
        "[ProactiveScheduler] Iniciado — verifica sessões a cada 1 min "
        "(cooldown de %d min por aluno)", PROACTIVE_COOLDOWN_MINUTES
    )
    return scheduler
