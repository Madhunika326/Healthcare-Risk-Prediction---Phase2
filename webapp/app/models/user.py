"""
User database model
"""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db
from sqlalchemy import func
from app.models.prediction import Prediction


class User(UserMixin, db.Model):
    """User model for authentication"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(120))
    last_name = db.Column(db.String(120))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    residence = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    is_advisor = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    predictions = db.relationship('Prediction', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f'{self.first_name} {self.last_name}'
        return self.username
    
    def get_prediction_count(self):
        """Get total predictions by user"""
        return self.predictions.count()
    
    def get_average_risk_score(self):
        """Get average risk score of user's predictions"""
        from app.models.prediction import Prediction
        avg = db.session.query(func.avg(Prediction.health_risk_score)).filter(Prediction.user_id == self.id).scalar()
        return round(avg, 2) if avg else None
    
    def get_risk_distribution(self):
        """Get distribution of risk categories"""
        predictions = self.predictions.all()
        distribution = {'Low': 0, 'Medium': 0, 'High': 0}
        
        for pred in predictions:
            distribution[pred.risk_category] += 1
        
        return distribution
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.get_full_name(),
            'age': self.age,
            'gender': self.gender,
            'residence': self.residence,
            'created_at': self.created_at.isoformat(),
            'is_admin': self.is_admin
        }
