import logging
from flask import Blueprint, request, jsonify
from config import Config
from openai import OpenAI

agente_video_bp = Blueprint('agente_video_bp', __name__)


@agente_video_bp.route('/agent/recommend_youtube_video', methods=['POST'])
def recommend_youtube_video():
    """
    Recebe dificuldade + preferências do aluno e retorna um link de vídeo do YouTube
    sugerido pela IA para sanar a principal dificuldade.
    """
    data = request.get_json() or {}
    difficulty_summary = data.get('difficulty_summary', '')
    questions_summary = data.get('questions_summary', [])
    profile_summary = data.get('profile_summary', '')

    if not difficulty_summary and not questions_summary:
        return jsonify({"error": "difficulty_summary ou questions_summary é obrigatório"}), 400

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

        client = OpenAI(
            api_key=Config.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1"
        )

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Responda apenas JSON válido."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )

        import json
        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)

        return jsonify({
            "youtube_url": parsed.get("youtube_url", ""),
            "justification": parsed.get("justification", "")
        }), 200

    except Exception as e:
        logging.error(f"Erro em recommend_youtube_video: {str(e)}")
        return jsonify({"error": str(e)}), 500
