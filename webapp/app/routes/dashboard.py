"""
Dashboard Routes
User dashboard and analytics
"""

from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from app.models.prediction import Prediction
from app.models.report import Report
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)


def _build_dashboard_payload(user):
    total_predictions = user.predictions.count()
    avg_risk_score = user.get_average_risk_score()
    risk_distribution = user.get_risk_distribution()
    recent_predictions = user.predictions.order_by(
        Prediction.created_at.desc()
    ).limit(5).all()
    recent_reports = Report.query.filter_by(user_id=user.id).order_by(
        Report.generated_at.desc()
    ).limit(5).all()

    upcoming_reminders = []
    if total_predictions:
        upcoming_reminders = [
            'Retake your assessment in 30 days to monitor trend changes.',
            'Review your personalized recommendations with a healthcare professional.',
            'Download the latest PDF report for your records.'
        ]

    return {
        'total_predictions': total_predictions,
        'avg_risk_score': avg_risk_score,
        'risk_distribution': risk_distribution,
        'recent_predictions': recent_predictions,
        'recent_reports': recent_reports,
        'upcoming_reminders': upcoming_reminders,
    }


@dashboard_bp.route('/')
@login_required
def index():
    """Role-aware dashboard landing"""
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('dashboard.user_dashboard'))


@dashboard_bp.route('/user')
@login_required
def user_dashboard():
    """Main user dashboard"""
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    payload = _build_dashboard_payload(current_user)
    return render_template('dashboard/index.html', **payload)


@dashboard_bp.route('/admin')
@login_required
def admin_dashboard_redirect():
    """Convenience redirect for admin landing"""
    return redirect(url_for('admin.dashboard'))


@dashboard_bp.route('/analytics')
@login_required
def analytics():
    """Analytics and trends"""
    user = current_user
    if user.is_admin:
        return redirect(url_for('admin.dashboard'))
    predictions = user.predictions.order_by(Prediction.created_at.asc()).all()
    
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
    
    # Build chart-ready trend data from real predictions
    trend_labels = [p['date'] for p in risk_trends]
    trend_scores = [p['score'] for p in risk_trends]

    # Feature impact: average normalised feature values across all predictions (0-100 scale)
    if predictions:
        n = len(predictions)
        feature_impact = {
            'Health Awareness': round(sum(min(p.health_awareness_score / 5.0, 1.0) * 100 for p in predictions) / n, 1),
            'Symptom Severity': round(sum(min(p.symptom_severity / 5.0, 1.0) * 100 for p in predictions) / n, 1),
            'Delay in Care':    round(sum(min(p.delay_in_seeking_care_days / 180.0, 1.0) * 100 for p in predictions) / n, 1),
            'Distance':         round(sum(min(p.distance_to_healthcare_km / 100.0, 1.0) * 100 for p in predictions) / n, 1),
            'Fear of Cost':     round(sum(min(p.fear_of_cost, 1.0) * 100 for p in predictions) / n, 1),
        }
        latest = predictions[-1]
        user_age       = user.age or latest.age or '--'
        user_residence = user.residence or latest.residence or '--'
        user_education = latest.education_level or '--'
    else:
        feature_impact = {'Health Awareness': 0, 'Symptom Severity': 0, 'Delay in Care': 0, 'Distance': 0, 'Fear of Cost': 0}
        user_age = user.age or '--'
        user_residence = user.residence or '--'
        user_education = '--'

    return render_template(
        'dashboard/analytics.html',
        risk_trends=risk_trends,
        risk_factors_summary=risk_factors_summary,
        trend_labels=trend_labels,
        trend_scores=trend_scores,
        feature_impact=feature_impact,
        user_age=user_age,
        user_residence=user_residence,
        user_education=user_education,
    )


@dashboard_bp.route('/insights')
@login_required
def insights():
    """AI-generated health insights"""
    user = current_user
    if user.is_admin:
        return redirect(url_for('admin.dashboard'))
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
