"""
Dashboard Routes
User dashboard and analytics
"""

from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from app.models.prediction import Prediction
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard"""
    user = current_user
    
    # Statistics
    total_predictions = user.predictions.count()
    avg_risk_score = user.get_average_risk_score()
    risk_distribution = user.get_risk_distribution()
    
    # Recent predictions
    recent_predictions = user.predictions.order_by(
        Prediction.created_at.desc()
    ).limit(5).all()
    
    return render_template(
        'dashboard/index.html',
        total_predictions=total_predictions,
        avg_risk_score=avg_risk_score,
        risk_distribution=risk_distribution,
        recent_predictions=recent_predictions
    )


@dashboard_bp.route('/analytics')
@login_required
def analytics():
    """Analytics and trends"""
    user = current_user
    predictions = user.predictions.all()
    
    # Calculate trends
    risk_trends = []
    for pred in predictions:
        risk_trends.append({
            'date': pred.created_at.strftime('%Y-%m-%d'),
            'score': pred.health_risk_score,
            'category': pred.risk_category
        })
    
    # Risk factor analysis
    risk_factors_summary = {}
    for pred in predictions:
        for factor in pred.get_risk_factors():
            factor_name = factor['factor']
            if factor_name not in risk_factors_summary:
                risk_factors_summary[factor_name] = 0
            risk_factors_summary[factor_name] += 1
    
    return render_template(
        'dashboard/analytics.html',
        risk_trends=risk_trends,
        risk_factors_summary=risk_factors_summary
    )


@dashboard_bp.route('/insights')
@login_required
def insights():
    """AI-generated health insights"""
    user = current_user
    predictions = user.predictions.order_by(
        Prediction.created_at.desc()
    ).all()
    
    insights_list = []
    
    if predictions:
        # Average risk trend
        avg_score = sum(p.health_risk_score for p in predictions) / len(predictions)
        insights_list.append({
            'title': 'Average Health Risk Score',
            'value': f"{avg_score:.2f}",
            'insight': generate_insight_message(avg_score),
            'icon': 'chart-line'
        })
        
        # Risk distribution
        high_count = sum(1 for p in predictions if p.risk_category == 'High')
        if high_count > 0:
            insights_list.append({
                'title': 'High Risk Predictions',
                'value': high_count,
                'insight': f'You have {high_count} predictions in the High risk category',
                'icon': 'exclamation-triangle'
            })
    
    return render_template(
        'dashboard/insights.html',
        insights=insights_list
    )


def generate_insight_message(score):
    """Generate insight message based on risk score"""
    if score < 35:
        return 'Your average health risk is LOW. Continue maintaining preventive care.'
    elif score < 65:
        return 'Your average health risk is MEDIUM. Monitor your health parameters regularly.'
    else:
        return 'Your average health risk is HIGH. Consult with healthcare provider soon.'
