import logging
import threading
from datetime import datetime
from flask import Blueprint, jsonify, request, current_app
from app.models import TeacherReport
from app import db

agente_teacher_report_bp = Blueprint('agente_teacher_report_bp', __name__)


@agente_teacher_report_bp.route('/agent/teacher_report/<int:teacher_id>', methods=['GET'])
def get_teacher_report(teacher_id):
    report = (
        TeacherReport.query
        .filter_by(teacher_id=teacher_id)
        .order_by(TeacherReport.generated_at.desc())
        .first()
    )
    if not report:
        return jsonify({"error": "Nenhum relatório gerado ainda"}), 404

    return jsonify({
        "id": report.id,
        "teacher_id": report.teacher_id,
        "teacher_name": report.teacher_name,
        "performance_summary": report.performance_summary,
        "tips": report.tips,
        "sessions_analyzed": report.sessions_analyzed,
        "generated_at": report.generated_at.isoformat() if report.generated_at else None,
        "feedback": report.feedback,
        "feedback_rating": report.feedback_rating,
        "feedback_at": report.feedback_at.isoformat() if report.feedback_at else None,
    }), 200


@agente_teacher_report_bp.route('/agent/teacher_report/<int:report_id>/feedback', methods=['POST'])
def save_feedback(report_id):
    data = request.get_json() or {}
    feedback = data.get('feedback', '').strip()
    rating = data.get('rating')

    if not feedback:
        return jsonify({"error": "feedback é obrigatório"}), 400

    report = TeacherReport.query.get(report_id)
    if not report:
        return jsonify({"error": "Relatório não encontrado"}), 404

    report.feedback = feedback
    if rating is not None:
        try:
            r = int(rating)
            if 1 <= r <= 5:
                report.feedback_rating = r
        except (ValueError, TypeError):
            pass
    report.feedback_at = datetime.utcnow()

    db.session.commit()
    return jsonify({"message": "Feedback salvo com sucesso"}), 200


@agente_teacher_report_bp.route('/agent/trigger_teacher_reports', methods=['POST'])
def trigger_reports():
    """Dispara geração imediata dos relatórios (útil para testes)."""
    from app.scheduler import generate_reports_for_all_teachers
    app = current_app._get_current_object()
    t = threading.Thread(target=generate_reports_for_all_teachers, args=(app,), daemon=True)
    t.start()
    return jsonify({"message": "Geração de relatórios iniciada em background"}), 202
