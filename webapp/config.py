"""
Flask Configuration Settings
Handles environment-based configuration for the Healthcare Risk Prediction Web App
"""

import os
from datetime import timedelta
from pathlib import Path

# Get the base directory
basedir = Path(__file__).parent.absolute()


class Config:
    """Base configuration"""
    
    # Flask Settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = False
    TESTING = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{basedir}/instance/healthcare_risk.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # File Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'csv', 'xlsx'}
    
    # ML Models Path
    MODELS_PATH = os.path.join(basedir, '..', 'models')
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = os.path.join(basedir, 'logs', 'app.log')
    
    # Pagination
    ITEMS_PER_PAGE = 20
    
    # Feature Validation
    VALID_FEATURES = {
        'numerical': [
            'Age', 'Health_Awareness_Score', 'Symptom_Severity',
            'Distance_to_Healthcare_km', 'Fear_of_Cost', 
            'Fear_of_Hospital', 'Delay_in_Seeking_Care_Days'
        ],
        'categorical': [
            'Gender', 'Residence', 'Education_Level',
            'Income_Level', 'Insurance_Status'
        ]
    }
    
    # Risk Thresholds
    RISK_THRESHOLDS = {
        'low': {'max': 35, 'color': '#28a745'},
        'medium': {'min': 35, 'max': 65, 'color': '#ffc107'},
        'high': {'min': 65, 'color': '#dc3545'}
    }
    
    # Valid Categories
    VALID_CATEGORIES = {
        'Gender': ['Male', 'Female'],
        'Residence': ['Urban', 'Rural'],
        'Education_Level': ['High', 'Low', 'Medium'],
        'Income_Level': ['Low', 'Middle', 'High'],
        'Insurance_Status': ['Insured', 'Uninsured']
    }
    
    # Valid Ranges (Raw Dataset Values)
    VALID_RANGES = {
        'Age': (18, 60),
        'Health_Awareness_Score': (1, 5),
        'Symptom_Severity': (1, 5),
        'Distance_to_Healthcare_km': (1, 49),
        'Fear_of_Cost': (0, 1),
        'Fear_of_Hospital': (0, 1),
        'Delay_in_Seeking_Care_Days': (0, 119)
    }


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
