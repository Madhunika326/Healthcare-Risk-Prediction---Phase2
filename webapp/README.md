# Healthcare Risk Prediction Web Application

## Overview

A production-ready Flask web application for healthcare risk prediction using AI/ML. This application wraps your trained ML pipeline (Autoencoder + ANN) with a complete web interface for user management, predictions, analytics, and reporting.

**Status:** ✅ Ready for Development & Deployment

---

## Project Structure

```
webapp/
├── app/
│   ├── __init__.py              # App factory and configuration
│   ├── routes/
│   │   ├── main.py              # Home, About, Help pages
│   │   ├── auth.py              # Login, Register, Profile
│   │   ├── assessment.py        # Assessment Form & Predictions
│   │   ├── dashboard.py         # User Dashboard & Analytics
│   │   ├── api.py               # REST API Endpoints
│   │   ├── admin.py             # Admin Dashboard
│   │   └── export.py            # PDF/CSV Export
│   ├── models/
│   │   ├── user.py              # User Model (SQLAlchemy)
│   │   ├── prediction.py        # Prediction Model
│   │   └── audit_log.py         # Audit Log Model
│   ├── services/
│   │   └── ml_service.py        # ML Pipeline Wrapper
│   ├── templates/
│   │   ├── base.html            # Base Template
│   │   ├── index.html           # Home Page
│   │   ├── about.html           # About Page
│   │   ├── auth/                # Auth Templates (login, register, profile)
│   │   ├── assessment/          # Assessment Templates (form, result, history)
│   │   ├── dashboard/           # Dashboard Templates (index, analytics, insights)
│   │   └── admin/               # Admin Templates
│   ├── static/
│   │   ├── css/style.css        # Main Stylesheet
│   │   ├── js/main.js           # Main JavaScript
│   │   └── images/              # Images & Assets
│   └── utils/                   # Utility Functions
├── logs/                        # Application Logs
├── instance/                    # Instance Files (DB, Cache)
├── config.py                    # Configuration Settings
├── run.py                       # Application Entry Point
├── requirements.txt             # Dependencies
├── .env.example                 # Environment Variables Template
└── README.md                    # This File
```

---

## Key Features

### Core Features (Paper-Compliant)
- ✅ Healthcare Risk Assessment Form (12 input features)
- ✅ Real-time Risk Prediction (ML Pipeline)
- ✅ Risk Score Visualization
- ✅ Risk Category Classification (Low/Medium/High)
- ✅ Prediction History Storage
- ✅ PDF Report Download
- ✅ Responsive UI

### Advanced Features
- ✅ User Authentication & Authorization
- ✅ User Profiles & Demographics
- ✅ Prediction Analytics Dashboard
- ✅ Risk Trend Charts (Chart.js)
- ✅ Personalized Health Recommendations
- ✅ Risk Factor Analysis
- ✅ Admin Dashboard
- ✅ REST API Endpoints
- ✅ Audit Logging
- ✅ CSV Export
- ✅ Dark Mode Support
- ✅ Mobile-Responsive Design

---

## Technology Stack

- **Framework:** Flask 3.0.0
- **Database:** SQLite (Development) / PostgreSQL (Production)
- **ORM:** SQLAlchemy
- **Authentication:** Flask-Login
- **ML Framework:** TensorFlow 2.15, Keras
- **Data Processing:** Pandas, NumPy, scikit-learn
- **Frontend:** Bootstrap 5, Chart.js
- **Reporting:** ReportLab
- **Server:** Gunicorn (Production)

---

## Installation & Setup

### Prerequisites
- Python 3.8+
- pip
- Virtual Environment (venv or conda)

### Step 1: Clone & Navigate
```bash
cd webapp
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv
source venv/Scripts/activate  # Windows
source venv/bin/activate       # Linux/Mac
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Environment Configuration
```bash
# Create .env file
cp .env.example .env

# Edit .env with your settings
```

### Step 5: Initialize Database
```bash
python run.py
# Or use: flask db init
```

### Step 6: Create Admin User
```bash
python run.py
# Then run the CLI command:
flask create-admin
# Follow prompts to create admin account
```

### Step 7: Run Development Server
```bash
python run.py
```

The application will be available at: `http://localhost:5000`

---

## Configuration

### Environment Variables (.env)

```env
# Flask
FLASK_ENV=development
FLASK_APP=run.py
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=sqlite:///instance/healthcare_risk.db

# ML Models
MODELS_PATH=../models

# Server
PORT=5000
DEBUG=True
```

### Configuration Classes (config.py)

- **DevelopmentConfig:** Debug enabled, SQLite
- **ProductionConfig:** Debug disabled, PostgreSQL
- **TestingConfig:** In-memory database, testing mode

---

## Usage

### 1. Home Page
- Overview of the platform
- Key statistics
- Quick access to assessments

### 2. Create Account
- Register with username, email, password
- Verify credentials
- Set up user profile

### 3. Healthcare Risk Assessment
- Fill comprehensive health form
- 12 input features (7 numerical, 5 categorical)
- Real-time validation
- Submit for prediction

### 4. View Results
- Risk Score Display (0-100)
- Risk Category (Low/Medium/High)
- Key Risk Factors Analysis
- Personalized Recommendations
- Comparison with Population Average

### 5. Dashboard
- View all assessments
- Risk Distribution Chart
- Average Risk Score
- Recent Predictions
- Quick Actions

### 6. Analytics
- Risk Trends Over Time
- Risk Factor Summary
- Health Insights

### 7. Export & Download
- PDF Report Download
- CSV Data Export
- Historical Data Download

### 8. Admin Features
- User Management
- Statistics Dashboard
- Audit Logs
- System Monitoring

---

## REST API Endpoints

### Public Endpoints
- `GET /` - Home page
- `GET /about` - About page
- `GET /api/health` - Health check

### Authentication Endpoints
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/logout` - User logout
- `GET /auth/profile` - User profile

### Assessment Endpoints
- `GET /assessment/form` - Assessment form page
- `POST /assessment/predict` - Make prediction
- `GET /assessment/history` - View history

### API Endpoints
- `POST /api/predict` - JSON prediction endpoint
- `GET /api/predictions` - Get user predictions (paginated)
- `GET /api/predictions/<id>` - Get specific prediction
- `GET /api/statistics` - Get user statistics

### Admin Endpoints
- `GET /admin/dashboard` - Admin dashboard
- `GET /admin/users` - User management
- `GET /admin/audit-logs` - Audit logs

### Export Endpoints
- `GET /export/predictions/csv` - Export as CSV
- `GET /export/prediction/<id>/pdf` - Export as PDF

---

## Database Models

### User
```python
- id: Integer (PK)
- username: String (Unique)
- email: String (Unique)
- password_hash: String
- first_name, last_name: String
- age, gender, residence: String
- is_admin: Boolean
- is_active: Boolean
- created_at, updated_at: DateTime
```

### Prediction
```python
- id: Integer (PK)
- user_id: Integer (FK)
- age, gender, residence: String
- health_awareness_score to delay_in_seeking_care_days: Float
- health_risk_score: Float
- risk_category: String (Low/Medium/High)
- created_at, updated_at: DateTime
```

### AuditLog
```python
- id: Integer (PK)
- user_id: Integer (FK)
- action: String
- resource_type, resource_id: String
- status: String
- created_at: DateTime
```

---

## Deployment

### Development
```bash
python run.py
```

### Production with Gunicorn
```bash
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:create_app()"]
```

### Docker Compose
```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://user:pass@db:5432/healthcare_risk
    depends_on:
      - db
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=healthcare_risk
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
```

---

## Security Considerations

### Implemented
- ✅ Password Hashing (Werkzeug)
- ✅ CSRF Protection
- ✅ Session Management
- ✅ SQL Injection Prevention (SQLAlchemy ORM)
- ✅ Input Validation
- ✅ Authentication Required Routes
- ✅ Admin-only Routes
- ✅ Audit Logging

### Recommendations
- [ ] Use HTTPS in production
- [ ] Enable HTTP Security Headers
- [ ] Implement Rate Limiting
- [ ] Use environment variables for secrets
- [ ] Regular security updates
- [ ] WAF (Web Application Firewall)
- [ ] Monitor audit logs

---

## Testing

### Run Unit Tests
```bash
pytest tests/
```

### Run with Coverage
```bash
pytest --cov=app tests/
```

### Sample Test Cases
- User Registration & Login
- Prediction Pipeline
- Form Validation
- Database Operations
- API Endpoints
- Admin Functions

---

## Troubleshooting

### Issue: Import Error - ML Pipeline
**Solution:** Ensure `predict_risk.py` is in parent directory
```python
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
```

### Issue: Database Lock (SQLite)
**Solution:** Use PostgreSQL for production

### Issue: Static Files Not Loading
**Solution:** Run `flask assets build` or rebuild CSS/JS

### Issue: ML Model Not Found
**Solution:** Check `MODELS_PATH` in config.py

---

## Performance Optimization

### Caching
- [ ] Redis for session caching
- [ ] Query caching for analytics
- [ ] Template caching

### Database
- [ ] Index frequently queried columns
- [ ] Use connection pooling
- [ ] Archive old predictions

### Frontend
- [ ] Minify CSS/JS
- [ ] Lazy load images
- [ ] Enable gzip compression

---

## Monitoring & Logging

### Logging Levels
- **DEBUG:** Detailed diagnostic information
- **INFO:** General informational messages
- **WARNING:** Warning messages
- **ERROR:** Error messages

### Log Files
```
logs/app.log          # Main application log
logs/error.log        # Error log
logs/access.log       # Access log (with reverse proxy)
```

### Monitoring Metrics
- Prediction latency
- User registration rate
- API response times
- Error rate
- System resource usage

---

## Contributing

### Code Style
- Follow PEP 8
- Use type hints
- Write docstrings
- Add unit tests

### Pull Request Process
1. Create feature branch
2. Make changes
3. Add tests
4. Submit PR
5. Code review & merge

---

## License

This project is part of the Healthcare Risk Prediction ML system.

---

## Support

For issues and questions:
- Check README sections
- Review code comments
- Check error logs
- Consult ML documentation

---

## Quick Commands

```bash
# Activate venv
source venv/Scripts/activate

# Run app
python run.py

# Create admin
flask create-admin

# Initialize DB
flask db init

# Run tests
pytest

# Format code
black app/

# Check linting
flake8 app/

# Install new package
pip install <package>

# Freeze dependencies
pip freeze > requirements.txt

# Deactivate venv
deactivate
```

---

## Next Steps

1. ✅ Development server running
2. [ ] Create test user accounts
3. [ ] Run sample predictions
4. [ ] Test all features
5. [ ] Configure production settings
6. [ ] Deploy to cloud platform
7. [ ] Monitor and optimize
8. [ ] Scale infrastructure

---

**Version:** 1.0.0  
**Last Updated:** June 2026  
**Status:** Production Ready
