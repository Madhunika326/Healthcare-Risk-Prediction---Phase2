"""
Admin Routes
Admin dashboard and management
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from functools import wraps
from app.models.user import User
from app.models.prediction import Prediction
from app.models.audit_log import AuditLog
from app.models.report import Report
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard"""
    # Statistics
    total_users = User.query.count()
    total_predictions = Prediction.query.count()
    total_admin_actions = AuditLog.query.count()
    total_reports = Report.query.count()
    
    # Recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    # Recent audit logs
    recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(10).all()
    recent_reports = Report.query.order_by(Report.generated_at.desc()).limit(10).all()
    
    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        total_predictions=total_predictions,
        total_admin_actions=total_admin_actions,
        total_reports=total_reports,
        recent_users=recent_users,
        recent_logs=recent_logs,
        recent_reports=recent_reports
    )


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """Manage users"""
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(page=page, per_page=20)
    return render_template('admin/users.html', users=users)


@admin_bp.route('/users/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    """User detail page"""
    user = User.query.get_or_404(user_id)
    predictions = user.predictions.all()
    
    return render_template(
        'admin/user_detail.html',
        user=user,
        predictions=predictions
    )


@admin_bp.route('/api/statistics')
@login_required
@admin_required
def api_statistics():
    """Get admin statistics"""
    return jsonify({
        'total_users': User.query.count(),
        'total_predictions': Prediction.query.count(),
        'total_audit_logs': AuditLog.query.count(),
        'total_reports': Report.query.count(),
        'active_users': User.query.filter_by(is_active=True).count(),
        'admin_users': User.query.filter_by(is_admin=True).count()
    }), 200


@admin_bp.route('/api/user/<int:user_id>/promote', methods=['POST'])
@login_required
@admin_required
def api_promote_user(user_id):
    """Promote user to admin"""
    user = User.query.get_or_404(user_id)
    user.is_admin = True
    user.save()
    
    AuditLog.log_action(
        user_id=current_user.id,
        action='USER_PROMOTED',
        resource_type='User',
        resource_id=user_id
    )
    
    return jsonify({'success': True}), 200


@admin_bp.route('/audit-logs')
@login_required
@admin_required
def audit_logs():
    """View audit logs"""
    page = request.args.get('page', 1, type=int)
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).paginate(page=page, per_page=50)
    return render_template('admin/audit_logs.html', logs=logs)
