from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from run import app, db
from app.models.user import User
from werkzeug.security import check_password_hash

TARGET_USERNAME = 'Madhunika K J'
TARGET_EMAIL = 'madhunikakj@gmail.com'
TARGET_PASSWORD = 'mkj@123'

with app.app_context():
    users = User.query.order_by(User.id).all()
    print('ALL_USERS')
    for user in users:
        role = 'Admin' if user.is_admin else 'Advisor' if getattr(user, 'is_advisor', False) else 'User'
        print(f'{user.id}\t{user.username}\t{user.email}\tadmin={user.is_admin}\trole={role}')

    admin_user = User.query.filter((User.email == TARGET_EMAIL) | (User.username == TARGET_USERNAME)).first()
    created = False
    updated = False
    if admin_user is None:
        admin_user = User(username=TARGET_USERNAME, email=TARGET_EMAIL, is_admin=True)
        admin_user.set_password(TARGET_PASSWORD)
        db.session.add(admin_user)
        created = True
    else:
        admin_user.username = TARGET_USERNAME
        admin_user.email = TARGET_EMAIL
        admin_user.is_admin = True
        admin_user.is_active = True
        admin_user.set_password(TARGET_PASSWORD)
        updated = True

    db.session.commit()
    db.session.refresh(admin_user)

    print('ADMIN_RECORD')
    print(f'created={created} updated={updated}')
    print(f'username={admin_user.username}')
    print(f'email={admin_user.email}')
    print(f'is_admin={admin_user.is_admin}')
    print(f'password_hash={admin_user.password_hash}')
    print(f'hash_valid={check_password_hash(admin_user.password_hash, TARGET_PASSWORD)}')

    client = app.test_client()
    login_response = client.post('/login/admin', data={'username': TARGET_USERNAME, 'password': TARGET_PASSWORD}, follow_redirects=False)
    print('LOGIN_RESPONSE')
    print(f'status={login_response.status_code}')
    print(f'location={login_response.headers.get("Location")}')

    if login_response.status_code in (302, 303):
        dashboard_response = client.get('/admin/dashboard')
        print('DASHBOARD_RESPONSE')
        print(f'status={dashboard_response.status_code}')
        print(f'contains_dashboard={(b"Admin Dashboard" in dashboard_response.data) or (b"dashboard" in dashboard_response.data.lower())}')
    else:
        print('DASHBOARD_RESPONSE')
        print('status=SKIPPED')
