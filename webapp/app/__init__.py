"""
Flask Application Factory
Creates and initializes the Flask app with all necessary extensions
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import get_config


# Initialize Flask extensions
db = SQLAlchemy()
login_manager = LoginManager()


def create_app(config_name=None):
    """
    Application factory function
    
    Args:
        config_name: Configuration name ('development', 'production', 'testing')
    
    Returns:
        Flask application instance
    """
    
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    config = get_config()
    app.config.from_object(config)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Create instance and logs directory
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.dirname(app.config['LOG_FILE']), exist_ok=True)
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.assessment import assessment_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.api import api_bp
    from app.routes.admin import admin_bp
    from app.routes.export import export_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(assessment_bp, url_prefix='/assessment')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(export_bp, url_prefix='/export')
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Setup logging
    setup_logging(app)
    
    # Register context processors
    register_context_processors(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    return app


def setup_logging(app):
    """Configure application logging"""
    
    if not app.debug:
        if not os.path.exists(os.path.dirname(app.config['LOG_FILE'])):
            os.makedirs(os.path.dirname(app.config['LOG_FILE']))
        
        file_handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=10240000,
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Healthcare Risk Prediction Web App Startup')


def register_context_processors(app):
    """Register template context processors"""
    
    @app.context_processor
    def inject_config():
        """Inject configuration variables to templates"""
        return {
            'risk_thresholds': app.config['RISK_THRESHOLDS'],
            'valid_ranges': app.config['VALID_RANGES'],
            'valid_categories': app.config['VALID_CATEGORIES']
        }


def register_error_handlers(app):
    """Register error handlers"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f'Internal error: {error}')
        return {'error': 'Internal server error'}, 500


def load_user_callback(user_id):
    """User loader callback for Flask-Login"""
    from app.models.user import User
    return User.query.get(int(user_id))


login_manager.user_loader(load_user_callback)
