"""
Advisor Routes
Advisor dashboard and patient management
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app.models.user import User
from app.models.prediction import Prediction
from sqlalchemy import func

advisor_bp = Blueprint('advisor', __name__)


def advisor_required(f):
    """Decorator to require advisor privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or (not current_user.is_advisor and not current_user.is_admin):
            return {'error': 'Advisor access required'}, 403
        return f(*args, **kwargs)
    return decorated_function


@advisor_bp.route('/dashboard')
@login_required
@advisor_required
def dashboard():
    """Advisor dashboard with patient assessment management"""
    # Get filter parameters
    age_min = request.args.get('age_min', 18, type=int)
    age_max = request.args.get('age_max', 60, type=int)
    risk_category = request.args.get('risk_category', '', type=str)
    symptom_min = request.args.get('symptom_min', 1, type=float)
    symptom_max = request.args.get('symptom_max', 5, type=float)
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Build query
    query = Prediction.query
    
    # Apply filters
    query = query.filter(Prediction.age >= age_min, Prediction.age <= age_max)
    
    if risk_category:
        query = query.filter_by(risk_category=risk_category)
    
    query = query.filter(
        Prediction.symptom_severity >= symptom_min,
        Prediction.symptom_severity <= symptom_max
    )
    
    # Get paginated results
    predictions = query.order_by(Prediction.created_at.desc()).paginate(
        page=page, per_page=per_page
    )
    
    # Statistics
    total_patients = User.query.count()
    high_risk_count = Prediction.query.filter_by(risk_category='High').count()
    avg_risk_score = Prediction.query.with_entities(
        func.avg(Prediction.health_risk_score)
    ).scalar() or 0
    
    return render_template(
        'advisor/dashboard.html',
        predictions=predictions,
        total_patients=total_patients,
        high_risk_count=high_risk_count,
        avg_risk_score=round(avg_risk_score, 2),
        age_min=age_min,
        age_max=age_max,
        risk_category=risk_category,
        symptom_min=symptom_min,
        symptom_max=symptom_max
    )


@advisor_bp.route('/patient/<int:prediction_id>')
@login_required
@advisor_required
def patient_detail(prediction_id):
    """View patient assessment details"""
    prediction = Prediction.query.get_or_404(prediction_id)
    user = User.query.get(prediction.user_id)
    
    # Get all predictions for this patient
    patient_predictions = Prediction.query.filter_by(user_id=prediction.user_id).order_by(
        Prediction.created_at.desc()
    ).all()
    
    return render_template(
        'advisor/patient_detail.html',
        prediction=prediction,
        user=user,
        patient_predictions=patient_predictions
    )


@advisor_bp.route('/patient/<int:prediction_id>/notes', methods=['POST'])
@login_required
@advisor_required
def update_patient_notes(prediction_id):
    """Update clinical notes for a patient"""
    prediction = Prediction.query.get_or_404(prediction_id)
    data = request.get_json()
    
    if 'notes' in data:
        prediction.notes = data['notes']
        from app import db
        db.session.commit()
        return jsonify({'success': True, 'message': 'Notes updated'}), 200
    
    return jsonify({'error': 'Notes field required'}), 400


@advisor_bp.route('/api/statistics')
@login_required
@advisor_required
def api_statistics():
    """Get advisor statistics"""
    return jsonify({
        'total_patients': User.query.count(),
        'total_assessments': Prediction.query.count(),
        'high_risk_count': Prediction.query.filter_by(risk_category='High').count(),
        'medium_risk_count': Prediction.query.filter_by(risk_category='Medium').count(),
        'low_risk_count': Prediction.query.filter_by(risk_category='Low').count(),
        'avg_risk_score': float(Prediction.query.with_entities(
            func.avg(Prediction.health_risk_score)
        ).scalar() or 0)
    }), 200
