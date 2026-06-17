"""
Prediction database model
"""

from datetime import datetime
from app import db
import json


class Prediction(db.Model):
    """Prediction model for storing user predictions"""
    
    __tablename__ = 'predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Input Features
    age = db.Column(db.Integer, nullable=False)
    health_awareness_score = db.Column(db.Float, nullable=False)
    symptom_severity = db.Column(db.Float, nullable=False)
    distance_to_healthcare_km = db.Column(db.Float, nullable=False)
    fear_of_cost = db.Column(db.Float, nullable=False)
    fear_of_hospital = db.Column(db.Float, nullable=False)
    delay_in_seeking_care_days = db.Column(db.Float, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    residence = db.Column(db.String(50), nullable=False)
    education_level = db.Column(db.String(50), nullable=False)
    income_level = db.Column(db.String(50), nullable=False)
    insurance_status = db.Column(db.String(50), nullable=False)
    
    # Prediction Output
    health_risk_score = db.Column(db.Float, nullable=False)
    risk_category = db.Column(db.String(20), nullable=False)  # Low, Medium, High
    
    # Additional Information
    input_features_json = db.Column(db.Text)  # Store raw input as JSON
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Audit
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(255))
    
    def __repr__(self):
        return f'<Prediction {self.id}: {self.risk_category} (Score: {self.health_risk_score})>'
    
    def to_dict(self):
        """Convert prediction to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'age': self.age,
            'health_awareness_score': self.health_awareness_score,
            'symptom_severity': self.symptom_severity,
            'distance_to_healthcare_km': self.distance_to_healthcare_km,
            'fear_of_cost': self.fear_of_cost,
            'fear_of_hospital': self.fear_of_hospital,
            'delay_in_seeking_care_days': self.delay_in_seeking_care_days,
            'gender': self.gender,
            'residence': self.residence,
            'education_level': self.education_level,
            'income_level': self.income_level,
            'insurance_status': self.insurance_status,
            'health_risk_score': self.health_risk_score,
            'risk_category': self.risk_category,
            'created_at': self.created_at.isoformat(),
            'notes': self.notes
        }
    
    def get_risk_factors(self):
        """Extract key risk factors from features"""
        factors = []
        
        if self.age > 50:
            factors.append({'factor': 'Age', 'value': self.age, 'severity': 'High', 'description': 'Age above 50 increases health risks'})
        
        if self.symptom_severity > 3:
            factors.append({'factor': 'Symptom Severity', 'value': self.symptom_severity, 'severity': 'High', 'description': 'High symptom severity detected'})
        
        if self.delay_in_seeking_care_days > 60:
            factors.append({'factor': 'Delay in Care', 'value': self.delay_in_seeking_care_days, 'severity': 'High', 'description': f'Significant delay of {int(self.delay_in_seeking_care_days)} days in seeking care'})
        
        if self.distance_to_healthcare_km > 30:
            factors.append({'factor': 'Distance to Healthcare', 'value': self.distance_to_healthcare_km, 'severity': 'Medium', 'description': f'Healthcare facility {self.distance_to_healthcare_km}km away'})
        
        if self.fear_of_cost > 0.7 or self.fear_of_hospital > 0.7:
            factors.append({'factor': 'Healthcare Barriers', 'value': max(self.fear_of_cost, self.fear_of_hospital), 'severity': 'Medium', 'description': 'Financial or psychological barriers to healthcare'})
        
        if self.health_awareness_score < 2:
            factors.append({'factor': 'Health Awareness', 'value': self.health_awareness_score, 'severity': 'Medium', 'description': 'Low health awareness may impact preventive care'})
        
        return factors
    
    def get_recommendations(self):
        """Generate personalized health recommendations"""
        recommendations = []
        
        if self.symptom_severity > 3:
            recommendations.append('Seek immediate medical consultation for symptom evaluation')
        
        if self.delay_in_seeking_care_days > 30:
            recommendations.append('Establish a regular healthcare monitoring schedule')
        
        if self.distance_to_healthcare_km > 25:
            recommendations.append('Consider telehealth services for remote consultations')
        
        if self.fear_of_cost > 0.5:
            recommendations.append('Explore healthcare insurance options and subsidized services')
        
        if self.health_awareness_score < 2:
            recommendations.append('Participate in health education programs and wellness initiatives')
        
        if self.risk_category == 'High':
            recommendations.append('Schedule comprehensive health assessment with healthcare provider')
            recommendations.append('Implement preventive care measures immediately')
        
        if self.risk_category == 'Medium':
            recommendations.append('Monitor health parameters regularly')
            recommendations.append('Maintain preventive healthcare appointments')
        
        return recommendations
