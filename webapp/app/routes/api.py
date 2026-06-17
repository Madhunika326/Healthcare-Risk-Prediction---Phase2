"""
API Routes
REST API endpoints
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.prediction import Prediction
from app.services.ml_service import get_ml_service
from app.models.audit_log import AuditLog

api_bp = Blueprint('api', __name__)


@api_bp.route('/predict', methods=['POST'])
@login_required
def api_predict():
    """
    API endpoint for making predictions
    
    POST /api/predict
    {
        "Age": 45,
        "Health_Awareness_Score": 3,
        "Symptom_Severity": 3,
        ...
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        ml_service = get_ml_service()
        result = ml_service.predict(data)
        
        if result['success']:
            # Save to database
            prediction = Prediction(
                user_id=current_user.id,
                age=data.get('Age'),
                health_awareness_score=data.get('Health_Awareness_Score'),
                symptom_severity=data.get('Symptom_Severity'),
                distance_to_healthcare_km=data.get('Distance_to_Healthcare_km'),
                fear_of_cost=data.get('Fear_of_Cost'),
                fear_of_hospital=data.get('Fear_of_Hospital'),
                delay_in_seeking_care_days=data.get('Delay_in_Seeking_Care_Days'),
                gender=data.get('Gender'),
                residence=data.get('Residence'),
                education_level=data.get('Education_Level'),
                income_level=data.get('Income_Level'),
                insurance_status=data.get('Insurance_Status'),
                health_risk_score=result['health_risk_score'],
                risk_category=result['risk_category'],
                ip_address=request.remote_addr,
                input_features_json=str(data)
            )
            
            db.session.add(prediction)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'prediction_id': prediction.id,
                'health_risk_score': result['health_risk_score'],
                'risk_category': result['risk_category'],
                'risk_factors': result.get('risk_factors', []),
                'recommendations': result.get('recommendations', []),
                'confidence': result.get('confidence', 'Medium')
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Prediction failed')
            }), 400
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"API error: {str(e)}"
        }), 500


@api_bp.route('/predictions', methods=['GET'])
@login_required
def api_get_predictions():
    """Get user's predictions"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    predictions = current_user.predictions.order_by(
        Prediction.created_at.desc()
    ).paginate(page=page, per_page=per_page)
    
    return jsonify({
        'total': predictions.total,
        'pages': predictions.pages,
        'current_page': page,
        'predictions': [p.to_dict() for p in predictions.items]
    }), 200


@api_bp.route('/predictions/<int:prediction_id>', methods=['GET'])
@login_required
def api_get_prediction(prediction_id):
    """Get specific prediction"""
    prediction = Prediction.query.filter_by(
        id=prediction_id,
        user_id=current_user.id
    ).first()
    
    if not prediction:
        return jsonify({'error': 'Prediction not found'}), 404
    
    return jsonify(prediction.to_dict()), 200


@api_bp.route('/statistics', methods=['GET'])
@login_required
def api_statistics():
    """Get user statistics"""
    total_predictions = current_user.predictions.count()
    avg_score = current_user.get_average_risk_score()
    risk_dist = current_user.get_risk_distribution()
    
    return jsonify({
        'total_predictions': total_predictions,
        'average_risk_score': avg_score,
        'risk_distribution': risk_dist
    }), 200


@api_bp.route('/health', methods=['GET'])
def api_health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'Healthcare Risk Prediction API v1'
    }), 200
