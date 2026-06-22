"""
Main Routes
Public pages and platform information
"""

from flask import Blueprint, render_template, jsonify
from app.services.ml_service import get_ml_service

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@main_bp.route('/index')
def index():
    """Home page"""
    ml_service = get_ml_service()
    population_stats = ml_service.get_population_statistics()
    return render_template('index.html', stats=population_stats)


@main_bp.route('/about')
def about():
    """About platform page"""
    return render_template('about.html')


@main_bp.route('/register')
def register_page():
    """Public registration page"""
    return render_template('auth/register.html')


@main_bp.route('/login/user')
def user_login_page():
    """Public user login page"""
    return render_template('auth/login.html')


@main_bp.route('/login/admin')
def admin_login_page():
    """Public admin login page"""
    return render_template('auth/login_admin.html')


@main_bp.route('/research-paper')
def research_paper():
    """Research paper summary page"""
    return render_template('research_paper.html')


@main_bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')


@main_bp.route('/help-center')
def help_center():
    """Help center page"""
    return render_template('help_center.html')


@main_bp.route('/how-it-works')
def how_it_works():
    """How the ML model works"""
    return render_template('how_it_works.html')


@main_bp.route('/health-info')
def health_info():
    """Health information and education"""
    return render_template('health_info.html')


@main_bp.route('/api/health-check')
def health_check():
    """API health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Healthcare Risk Prediction API'
    }), 200


@main_bp.route('/privacy')
def privacy():
    """Privacy policy"""
    return render_template('privacy.html')


@main_bp.route('/terms')
def terms():
    """Terms of service"""
    return render_template('terms.html')
