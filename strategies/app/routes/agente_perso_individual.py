import logging
import json
from flask import Blueprint, request, jsonify
from config import Config
from openai import OpenAI

agente_perso_individual_bp = Blueprint('agente_perso_individual_bp', __name__)


def _build_groq_client():
    return OpenAI(
        api_key=Config.GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1"
    )


@agente_perso_individual_bp.route('/agent/recommend_youtube_video', methods=['POST'])
def recommend_youtube_video():
    """
    Recebe dificuldade + preferências do aluno e retorna um link de vídeo do YouTube
    sugerido pela IA (Groq) para sanar a principal dificuldade.
    """
    data = request.get_json() or {}
    difficulty_summary = data.get('difficulty_summary', '')
    questions_summary = data.get('questions_summary', [])
    profile_summary = data.get('profile_summary', '')

    if not difficulty_summary and not questions_summary:
        return jsonify({"error": "difficulty_summary ou questions_summary é obrigatório"}), 400

    if not Config.GROQ_API_KEY:
        return jsonify({"error": "GROQ_API_KEY não configurada"}), 500

    try:
        prompt = f"""
        Você é um tutor pedagógico especializado em recomendar vídeo-aulas.
        Analise o diagnóstico abaixo e indique UM vídeo do YouTube para ajudar o aluno.

        PERFIL DO ALUNO:
        {profile_summary}

        RESUMO DE DIFICULDADES:
        {difficulty_summary}

        QUESTÕES (DIAGNÓSTICO):
        {questions_summary}

        Responda APENAS em JSON neste formato:
        {{
          "youtube_url": "https://www.youtube.com/watch?v=...",
          "justification": "explicação curta"
        }}
        """

        client = _build_groq_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Responda apenas JSON válido."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )

        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)

        return jsonify({
            "youtube_url": parsed.get("youtube_url", ""),
            "justification": parsed.get("justification", "")
        }), 200

    except Exception as e:
        logging.error(f"Erro em recommend_youtube_video: {str(e)}")
        return jsonify({"error": str(e)}), 500


@agente_perso_individual_bp.route('/agent/generate_personalized_study_text', methods=['POST'])
def generate_personalized_study_text():
    """
    Gera um texto personalizado (~5 minutos de leitura) para sanar dificuldades do aluno.
    """
    data = request.get_json() or {}
    difficulty_summary = data.get('difficulty_summary', '')
    questions_summary = data.get('questions_summary', [])
    profile_summary = data.get('profile_summary', '')

    if not difficulty_summary and not questions_summary:
        return jsonify({"error": "difficulty_summary ou questions_summary é obrigatório"}), 400

    if not Config.GROQ_API_KEY:
        return jsonify({"error": "GROQ_API_KEY não configurada"}), 500

    try:
        prompt = f"""
        Você é um tutor especializado em personalização individual do aprendizado.
        Com base no diagnóstico, gere um texto didático em português para cerca de 5 minutos de leitura
        (aproximadamente 650 a 800 palavras), adaptado ao perfil do aluno.

        PERFIL DO ALUNO:
        {profile_summary}

        RESUMO DE DIFICULDADES:
        {difficulty_summary}

        QUESTÕES (DIAGNÓSTICO):
        {questions_summary}

        Requisitos do texto:
        - Linguagem simples e objetiva.
        - Explique os conceitos com exemplos práticos.
        - Destaque erros comuns que o aluno está cometendo.
        - Inclua uma mini seção final com 5 passos de revisão.
        - Não use markdown e não use JSON.
        """

        client = _build_groq_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Você escreve materiais pedagógicos personalizados com clareza."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )

        study_text = (response.choices[0].message.content or "").strip()

        return jsonify({
            "study_text": study_text
        }), 200

    except Exception as e:
        logging.error(f"Erro em generate_personalized_study_text: {str(e)}")
        return jsonify({"error": str(e)}), 500
