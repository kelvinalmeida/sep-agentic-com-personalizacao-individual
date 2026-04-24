import logging
import json
import re
import requests
from flask import Blueprint, request, jsonify
from config import Config

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
        if not Config.GEMINI_API_KEY:
            return jsonify({"error": "GEMINI_API_KEY não configurada"}), 500

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

        gemini_url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            "gemini-2.5-flash:generateContent"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json"
            }
        }
        response = requests.post(
            f"{gemini_url}?key={Config.GEMINI_API_KEY}",
            json=payload,
            timeout=60
        )
        if response.status_code != 200:
            return jsonify({
                "error": "Falha ao consultar Gemini",
                "details": response.text
            }), response.status_code

        resp_json = response.json()
        candidates = resp_json.get("candidates", [])
        text_content = ""
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts and isinstance(parts[0], dict):
                text_content = parts[0].get("text", "")

        clean_content = text_content.strip()
        if clean_content.startswith("```"):
            clean_content = re.sub(r"^```(?:json)?\s*|\s*```$", "", clean_content, flags=re.DOTALL).strip()

        parsed = json.loads(clean_content or "{}")

        return jsonify({
            "youtube_url": parsed.get("youtube_url", ""),
            "justification": parsed.get("justification", "")
        }), 200

    except Exception as e:
        logging.error(f"Erro em recommend_youtube_video: {str(e)}")
        return jsonify({"error": str(e)}), 500
