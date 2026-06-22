"""
Authentication Routes
User and admin login flows
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User
from app.models.audit_log import AuditLog

auth_bp = Blueprint('auth', __name__)


def _redirect_after_login(user):
    """Send users to the correct dashboard based on role."""
    if user.is_admin:
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('dashboard.user_dashboard'))


def _handle_login(expected_role):
    """Shared login flow for user and admin access."""
    if current_user.is_authenticated:
        return _redirect_after_login(current_user)

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Username and password required', 'danger')
            return render_template('auth/login.html' if expected_role == 'user' else 'auth/login_admin.html')

        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            flash('Invalid username or password', 'danger')
            return render_template('auth/login.html' if expected_role == 'user' else 'auth/login_admin.html')

        if not user.is_active:
            flash('Your account has been disabled', 'warning')
            return render_template('auth/login.html' if expected_role == 'user' else 'auth/login_admin.html')

        if expected_role == 'admin' and not user.is_admin:
            flash('Admin access required', 'danger')
            return render_template('auth/login_admin.html')

        if expected_role == 'user' and user.is_admin:
            flash('Please use the admin login for administrator access', 'warning')
            return render_template('auth/login.html')

        login_user(user, remember=bool(request.form.get('remember')))

        from datetime import datetime
        user.last_login = datetime.utcnow()
        db.session.commit()

        AuditLog.log_action(
            user_id=user.id,
            action=f'{expected_role.upper()}_LOGIN',
            resource_type='User',
            resource_id=user.id,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )

        return _redirect_after_login(user)

    return render_template('auth/login.html' if expected_role == 'user' else 'auth/login_admin.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return _redirect_after_login(current_user)
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate inputs
        if not all([username, email, password, confirm_password]):
            flash('All fields are required', 'danger')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('auth/register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'danger')
            return render_template('auth/register.html')
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return render_template('auth/register.html')
        
        # Create user
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Log action
        AuditLog.log_action(
            user_id=user.id,
            action='USER_REGISTERED',
            resource_type='User',
            resource_id=user.id,
            ip_address=request.remote_addr
        )
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.user_login'))
    
    return render_template('auth/register.html')


@auth_bp.route('/login')
def login():
    """Legacy login redirect"""
    return redirect(url_for('auth.user_login'))


@auth_bp.route('/login/user', methods=['GET', 'POST'])
def user_login():
    """User login"""
    return _handle_login('user')


@auth_bp.route('/login/admin', methods=['GET', 'POST'])
def admin_login():
    """Admin login"""
    return _handle_login('admin')


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    AuditLog.log_action(
        user_id=current_user.id,
        action='USER_LOGOUT',
        resource_type='User',
        resource_id=current_user.id,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string if request.user_agent else None
    )
    
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('auth/profile.html', user=current_user)


@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    if request.method == 'POST':
        current_user.first_name = request.form.get('first_name')
        current_user.last_name = request.form.get('last_name')
        current_user.age = request.form.get('age', type=int)
        current_user.gender = request.form.get('gender')
        current_user.residence = request.form.get('residence')
        
        db.session.commit()
        
        AuditLog.log_action(
            user_id=current_user.id,
            action='PROFILE_UPDATED',
            resource_type='User',
            resource_id=current_user.id,
            ip_address=request.remote_addr
        )
        
        flash('Profile updated successfully', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/edit_profile.html', user=current_user)
