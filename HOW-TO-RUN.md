# 🚀 How to Run - Stress Detection for IT Professionals

Complete guide for setting up and running the full stress detection system with Django web application and Rasa chatbot.

## 📋 System Requirements

- **Operating System**: Windows 10/11 (tested) or Linux/macOS
- **Python**: 3.8+ (Python 3.9 recommended)
- **RAM**: 8GB minimum (16GB recommended)
- **Storage**: 5GB free space
- **Git**: Latest version

## 🛠️ Installation Guide

### 1. Clone the Repository

```bash
git clone https://github.com/suragsunil/STRESS-DETECTION-FOR-IT-PROFESSIONALS.git
cd "Stress Detection for IT Professionals"
```

### 2. Set Up Python Virtual Environment

```bash
# Navigate to Django project directory
cd strees_dection

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/Mac:
# source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Install core Django dependencies
pip install Django==4.2.20 djangorestframework==3.15.2

# Install database and utility packages
pip install psycopg2-binary python-dotenv whitenoise

# Install JWT authentication
pip install djangorestframework-simplejwt PyJWT==2.4.0

# Install machine learning packages
pip install numpy pandas scikit-learn matplotlib librosa

# Install cryptography (specific version for compatibility)
pip install cryptography==3.4.8

# Install Rasa (global installation recommended)
pip install rasa==3.6.21 rasa-sdk==3.6.2
```

### 4. Database Setup

```bash
# Run migrations
python manage.py migrate

# Optional: Create superuser for admin access
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

## ▶️ Running the Complete System

### Terminal 1: Django Web Application

```bash
# Navigate to project directory
cd "d:\surag_projects\Stress Detection for IT Professionals\STRESS-DETECTION-FOR-IT-PROFESSIONALS\strees_dection"

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start Django development server
python manage.py runserver

# Server will be available at: http://127.0.0.1:8000
```

### Terminal 2: Rasa Actions Server

```bash
# Navigate to project directory
cd "d:\surag_projects\Stress Detection for IT Professionals\STRESS-DETECTION-FOR-IT-PROFESSIONALS\strees_dection"

# Start Rasa actions server using global Python installation
& "C:\Program Files\Python39\python.exe" -m rasa run actions --port 5055

# Server will be available at: http://0.0.0.0:5055
```

### Terminal 3: Rasa Core Server

```bash
# Navigate to project directory
cd "d:\surag_projects\Stress Detection for IT Professionals\STRESS-DETECTION-FOR-IT-PROFESSIONALS\strees_dection"

# Start Rasa core server with API enabled
& "C:\Program Files\Python39\python.exe" -m rasa run --enable-api --cors "*" --port 5005

# Server will be available at: http://localhost:5005
```

## 🧪 Quick Verification Commands

### Check if all services are running:

```bash
# Windows PowerShell
Get-NetTCPConnection -LocalPort 8000,5005,5055 -ErrorAction SilentlyContinue

# Expected output should show all three ports listening
```

### Test Rasa API:

```bash
# Test Rasa server health
curl http://localhost:5005/

# Test Rasa actions server
curl http://localhost:5055/health
```

## 🌐 Access Points

- **Main Web Application**: `http://127.0.0.1:8000`
- **Rasa Chatbot API**: `http://localhost:5005`
- **Rasa Actions Server**: `http://0.0.0.0:5055`
- **Django Admin**: `http://127.0.0.1:8000/admin`

## 📁 Project Structure Overview

```
STRESS-DETECTION-FOR-IT-PROFESSIONALS/
├── strees_dection/                 # Main Django project
│   ├── app/                       # Django application
│   │   ├── templates/             # HTML templates
│   │   ├── models.py              # Database models
│   │   ├── views.py               # View logic
│   │   └── urls.py                # URL routing
│   ├── media/                     # Uploaded files
│   │   ├── voice_patterns/        # Audio uploads
│   │   └── resources/             # Stress resources
│   ├── models/                    # Rasa trained models
│   ├── data/                      # Rasa training data
│   │   ├── nlu.yml               # Natural Language Understanding
│   │   ├── stories.yml           # Conversation flows
│   │   └── rules.yml             # Business rules
│   ├── actions/                   # Custom Rasa actions
│   │   └── actions.py            # Action implementations
│   ├── manage.py                  # Django management script
│   └── requirements.txt           # Python dependencies
├── config.yml                     # Rasa configuration
├── domain.yml                     # Rasa domain definition
├── endpoints.yml                  # Rasa endpoints configuration
└── HOW-TO-RUN.md                  # This file
```

## 🔧 Troubleshooting Common Issues

### 1. Cryptography Import Errors

**Problem**: `ImportError: DLL load failed while importing _rust`

**Solution**:
```bash
pip uninstall cryptography -y
pip install cryptography==3.4.8
pip uninstall PyJWT -y
pip install PyJWT==2.4.0
```

### 2. Rasa Server Won't Start

**Problem**: Module not found errors

**Solution**:
```bash
# Use system Python instead of virtual environment for Rasa
& "C:\Program Files\Python39\python.exe" -m rasa run --enable-api --cors "*" --port 5005
```

### 3. Database Migration Issues

**Problem**: Migration conflicts or errors

**Solution**:
```bash
# Reset migrations (use with caution)
python manage.py migrate app zero
python manage.py migrate
```

### 4. Port Already in Use

**Problem**: Ports 8000, 5005, or 5055 already occupied

**Solution**:
```bash
# Windows - Kill processes using specific ports
netstat -ano | findstr :8000
taskkill /PID <process_id> /F
```

## 🔄 Development Workflow

### Making Changes to Rasa

1. **Update training data** in `data/` directory
2. **Retrain model**:
   ```bash
   rasa train
   ```
3. **Restart Rasa server** to load new model

### Making Changes to Django

1. **Update models**: Modify `app/models.py`
2. **Create migration**:
   ```bash
   python manage.py makemigrations
   ```
3. **Apply migration**:
   ```bash
   python manage.py migrate
   ```
4. **Restart Django server**

## 🛡️ Production Deployment Notes

For production deployment, consider:

1. **Use production WSGI server** (Gunicorn, uWSGI)
2. **Configure proper database** (PostgreSQL recommended)
3. **Set up reverse proxy** (Nginx, Apache)
4. **Enable HTTPS** with SSL certificates
5. **Configure environment variables** for secrets
6. **Set up process monitoring** (Supervisor, systemd)

## 📞 Support

For issues or questions:
- Check the project README.md for additional documentation
- Review error logs in terminal outputs
- Ensure all dependencies are correctly installed
- Verify Python and package versions match requirements

---
*Last Updated: January 31, 2026*