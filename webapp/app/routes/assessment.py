"""
Assessment Routes
Healthcare risk assessment form and prediction
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.prediction import Prediction
from app.models.audit_log import AuditLog
from app.services.ml_service import get_ml_service

assessment_bp = Blueprint('assessment', __name__)


@assessment_bp.route('/form')
def form():
    """Assessment form page"""
    from config import get_config
    config = get_config()
    return render_template(
        'assessment/form.html',
        valid_ranges=config.VALID_RANGES,
        valid_categories=config.VALID_CATEGORIES
    )


@assessment_bp.route('/predict', methods=['POST'])
@login_required
def predict():
    """
    Make a prediction
    Can be called via form POST or API
    """
    try:
        # Prepare input data
        input_data = {
            'Age': int(request.form.get('Age')),
            'Health_Awareness_Score': float(request.form.get('Health_Awareness_Score')),
            'Symptom_Severity': float(request.form.get('Symptom_Severity')),
            'Distance_to_Healthcare_km': float(request.form.get('Distance_to_Healthcare_km')),
            'Fear_of_Cost': float(request.form.get('Fear_of_Cost')),
            'Fear_of_Hospital': float(request.form.get('Fear_of_Hospital')),
            'Delay_in_Seeking_Care_Days': float(request.form.get('Delay_in_Seeking_Care_Days')),
            'Gender': request.form.get('Gender'),
            'Residence': request.form.get('Residence'),
            'Education_Level': request.form.get('Education_Level'),
            'Income_Level': request.form.get('Income_Level'),
            'Insurance_Status': request.form.get('Insurance_Status'),
        }
        
        # Get ML service and make prediction
        ml_service = get_ml_service()
        result = ml_service.predict(input_data)
        
        if not result['success']:
            flash(f"Prediction error: {result['error']}", 'danger')
            return redirect(url_for('assessment.form'))
        
        # Save prediction to database
        prediction = Prediction(
            user_id=current_user.id,
            age=input_data['Age'],
            health_awareness_score=input_data['Health_Awareness_Score'],
            symptom_severity=input_data['Symptom_Severity'],
            distance_to_healthcare_km=input_data['Distance_to_Healthcare_km'],
            fear_of_cost=input_data['Fear_of_Cost'],
            fear_of_hospital=input_data['Fear_of_Hospital'],
            delay_in_seeking_care_days=input_data['Delay_in_Seeking_Care_Days'],
            gender=input_data['Gender'],
            residence=input_data['Residence'],
            education_level=input_data['Education_Level'],
            income_level=input_data['Income_Level'],
            insurance_status=input_data['Insurance_Status'],
            health_risk_score=result['health_risk_score'],
            risk_category=result['risk_category'],
            ip_address=request.remote_addr,
            input_features_json=str(input_data)
        )
        
        db.session.add(prediction)
        db.session.commit()
        
        # Log action
        AuditLog.log_action(
            user_id=current_user.id,
            action='PREDICTION_MADE',
            resource_type='Prediction',
            resource_id=prediction.id,
            details=f'Risk Score: {result["health_risk_score"]}, Category: {result["risk_category"]}',
            ip_address=request.remote_addr
        )
        
        # Return results page
        return render_template(
            'assessment/result.html',
            prediction=prediction,
            result=result
        )
    
    except Exception as e:
        flash(f"Error processing prediction: {str(e)}", 'danger')
        return redirect(url_for('assessment.form'))


@assessment_bp.route('/history')
@login_required
def history():
    """View prediction history"""
    page = request.args.get('page', 1, type=int)
    predictions = current_user.predictions.order_by(
        Prediction.created_at.desc()
    ).paginate(page=page, per_page=10)
    
    return render_template('assessment/history.html', predictions=predictions)
