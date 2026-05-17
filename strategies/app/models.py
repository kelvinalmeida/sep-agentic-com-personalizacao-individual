from app import db
from datetime import datetime


class SessionAlert(db.Model):
    __tablename__ = 'session_alerts'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, nullable=False, index=True)
    student_id = db.Column(db.Integer, nullable=True)
    student_name = db.Column(db.String(255), nullable=True)
    student_email = db.Column(db.String(255), nullable=True)
    alert_type = db.Column(db.String(50), nullable=False, default='mastery')  # 'mastery' | 'low_score'
    concept = db.Column(db.String(255), nullable=True)
    mastery_pct = db.Column(db.Float, nullable=True)
    score = db.Column(db.Integer, nullable=True)       # para alert_type='low_score'
    answer_id = db.Column(db.Integer, nullable=True)   # dedup de low_score
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class TeacherReport(db.Model):
    __tablename__ = 'teacher_reports'

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, nullable=False, index=True)
    teacher_name = db.Column(db.String(255))
    performance_summary = db.Column(db.Text, nullable=False)
    tips = db.Column(db.Text, nullable=False)
    sessions_analyzed = db.Column(db.Integer, default=0)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    feedback = db.Column(db.Text)
    feedback_rating = db.Column(db.Integer)
    feedback_at = db.Column(db.DateTime)
