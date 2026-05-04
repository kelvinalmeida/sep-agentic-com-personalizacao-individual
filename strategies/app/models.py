from app import db
from datetime import datetime


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
