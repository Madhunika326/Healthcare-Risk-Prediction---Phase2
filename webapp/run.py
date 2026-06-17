"""
Healthcare Risk Prediction Web Application
Main entry point for running the Flask app

Usage:
    python run.py              # Development
    FLASK_ENV=production python run.py  # Production
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app import create_app, db

# Create Flask app
app = create_app()


@app.shell_context_processor
def make_shell_context():
    """Create shell context for Flask CLI"""
    return {
        'db': db,
        'User': __import__('app.models.user', fromlist=['User']).User,
        'Prediction': __import__('app.models.prediction', fromlist=['Prediction']).Prediction,
        'AuditLog': __import__('app.models.audit_log', fromlist=['AuditLog']).AuditLog
    }


@app.cli.command()
def init_db():
    """Initialize the database"""
    db.create_all()
    print('Database initialized')


@app.cli.command()
def create_admin():
    """Create an admin user"""
    from app.models.user import User
    
    username = input('Admin username: ')
    email = input('Admin email: ')
    password = input('Admin password: ')
    
    if User.query.filter_by(username=username).first():
        print('Username already exists')
        return
    
    admin = User(username=username, email=email, is_admin=True)
    admin.set_password(password)
    
    db.session.add(admin)
    db.session.commit()
    
    print(f'Admin user {username} created successfully')


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_ENV', 'development') == 'development'
    )
