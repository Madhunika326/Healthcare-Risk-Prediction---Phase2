"""
Report database model
"""

from datetime import datetime
from app import db


class Report(db.Model):
    """Generated PDF report metadata"""

    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    prediction_id = db.Column(db.Integer, db.ForeignKey('predictions.id'), nullable=False, unique=True, index=True)
    report_type = db.Column(db.String(50), nullable=False, default='assessment_pdf')
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    prediction = db.relationship('Prediction')

    def __repr__(self):
        return f'<Report {self.id}: {self.report_type}>'