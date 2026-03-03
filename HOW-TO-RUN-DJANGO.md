# How to Run Django – Stress Detection Web App

Step-by-step guide to set up and run the Django web application: Python version, virtual environment, dependencies, database, and runserver.

---

## Python version

| Requirement | Version |
|-------------|---------|
| **Recommended** | **Python 3.9** |
| Minimum | Python 3.8 |
| Django | 4.2.20 |
| Django REST framework | 3.15.2 |

Check your version:

```bash
python --version
# or
py -3.9 --version
```

---

## 1. Project directory

All Django commands are run from the project folder where `manage.py` lives:

```bash
cd "D:\surag_projects\Stress Detection for IT Professionals\STRESS-DETECTION-FOR-IT-PROFESSIONALS\strees_dection"
```

*(Use your actual path if different.)*

---

## 2. Virtual environment

Create and activate a venv (recommended):

```bash
# Create
python -m venv venv

# Activate – Windows PowerShell
.\venv\Scripts\Activate.ps1

# Activate – Windows CMD
venv\Scripts\activate.bat

# Activate – Linux/macOS
source venv/bin/activate
```

You should see `(venv)` in your prompt when it’s active.

---

## 3. Install dependencies

From the same directory (with venv activated):

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Or install core Django packages only:

```bash
pip install Django==4.2.20 djangorestframework==3.15.2
pip install djangorestframework-simplejwt PyJWT==2.4.0
pip install psycopg2-binary python-dotenv whitenoise cryptography==3.4.8
```

---

## 4. Environment variables (optional)

The app uses `python-dotenv`. For custom settings (e.g. database path), create a `.env` file in `strees_dection/`:

```env
# Optional: custom SQLite path (default: db.sqlite3 in project root)
# DB_PATH=path/to/db.sqlite3
```

Leave it empty or omit it to use defaults (SQLite at `strees_dection/db.sqlite3`).

---

## 5. Database setup

Run migrations and (optionally) create an admin user and collect static files:

```bash
# Apply migrations (required before first run)
python manage.py migrate

# Optional: create superuser for /admin
python manage.py createsuperuser

# Optional: collect static files (for production / WhiteNoise)
python manage.py collectstatic --noinput
```

---

## 6. Run Django development server

Start the dev server:

```bash
python manage.py runserver
```

- **URL:** http://127.0.0.1:8000  
- Default port: **8000**. To use another port: `python manage.py runserver 8080`

**Windows – batch file (from `strees_dection`):**

```batch
start-django.bat
```

This activates the venv and runs `python manage.py runserver`.

---

## 7. Run order with Rasa (full stack)

To use the web app with the chatbot:

1. **Terminal 1 – Django**
   ```bash
   cd strees_dection
   .\venv\Scripts\Activate.ps1
   python manage.py runserver
   ```

2. **Terminal 2 – Rasa actions**  
   See [HOW-TO-RUN-RASA.md](HOW-TO-RUN-RASA.md): `rasa run actions --port 5055`

3. **Terminal 3 – Rasa core**  
   See [HOW-TO-RUN-RASA.md](HOW-TO-RUN-RASA.md): `rasa run --enable-api --cors "*" --port 5005`

The app talks to the bot at `http://localhost:5005/webhooks/rest/webhook`.

---

## 8. Useful Django commands

| Command | Purpose |
|--------|--------|
| `python manage.py runserver` | Start development server (port 8000) |
| `python manage.py migrate` | Apply database migrations |
| `python manage.py makemigrations` | Create migrations after model changes |
| `python manage.py createsuperuser` | Create admin user |
| `python manage.py collectstatic --noinput` | Gather static files for deployment |
| `python manage.py shell` | Django shell |
| `python manage.py test` | Run tests |

---

## 9. Project layout (Django)

```
strees_dection/
├── manage.py              # Django CLI entry point
├── requirements.txt       # Python dependencies
├── .env                   # Optional env vars (e.g. DB_PATH)
├── db.sqlite3             # SQLite DB (after migrate)
├── strees_dection/        # Project package
│   ├── settings.py        # Settings (DB, static, apps)
│   ├── urls.py            # Root URL config
│   └── wsgi.py            # WSGI app
├── app/                   # Main Django app
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── templates/
├── static/                # App static sources
├── staticfiles/           # Collected static (after collectstatic)
├── media/                 # Uploaded files
└── start-django.bat       # Windows: start dev server
```

---

## 10. Troubleshooting

**Port 8000 already in use**

```bash
# Use another port
python manage.py runserver 8080
```

**“No module named …”**

- Ensure the venv is activated and you installed deps: `pip install -r requirements.txt`
- Run commands from `strees_dection` (where `manage.py` is).

**Database / migration errors**

```bash
# Re-run migrations
python manage.py migrate
# If needed (resets app migrations – use with care):
# python manage.py migrate app zero
# python manage.py migrate
```

**Static files 404 in production**

- Run `python manage.py collectstatic --noinput`
- Ensure WhiteNoise is in `MIDDLEWARE` in `settings.py` (already configured).

**Chatbot not responding in the app**

- Start Rasa actions (port 5055) and Rasa core (port 5005) as in [HOW-TO-RUN-RASA.md](HOW-TO-RUN-RASA.md).
- In the frontend, the Rasa URL should be `http://localhost:5005/webhooks/rest/webhook`.

---

*Last updated: March 2025*
