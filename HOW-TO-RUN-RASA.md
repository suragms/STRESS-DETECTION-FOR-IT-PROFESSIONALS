# How to Run Rasa – Stress Detection Chatbot

Step-by-step guide to set up and run the Rasa assistant: Python version, training, actions server, and core API.

---

## Python version

| Requirement | Version |
|-------------|---------|
| **Recommended** | **Python 3.9** |
| Minimum | Python 3.8 |
| Rasa | 3.6.21 |
| Rasa SDK | 3.6.2 |

Rasa 3.6.x is tested with Python 3.8–3.10. This project uses **Python 3.9** (e.g. `C:\Program Files\Python39\python.exe` on Windows).

Check your version:

```bash
python --version
# or
py -3.9 --version
```

---

## 1. Project directory

All Rasa commands are run from the Django project folder where `config.yml`, `domain.yml`, and `data/` live:

```bash
cd "D:\surag_projects\Stress Detection for IT Professionals\STRESS-DETECTION-FOR-IT-PROFESSIONALS\strees_dection"
```

*(Use your actual path if different.)*

---

## 2. Virtual environment and install

Create and activate a venv (optional but recommended):

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

Install Rasa and the SDK:

```bash
pip install --upgrade pip
pip install rasa==3.6.21 rasa-sdk==3.6.2
```

Or install from the project’s requirements (includes Django and other deps):

```bash
pip install -r requirements.txt
```

---

## 3. Rasa train

Train the NLU and dialogue model from `data/`, `config.yml`, and `domain.yml`:

```bash
# From strees_dection directory, with venv activated
rasa train
```

- Reads: `config.yml`, `domain.yml`, `data/nlu.yml`, `data/stories.yml`, `data/rules.yml`.
- Writes: a timestamped model under `models/` (e.g. `models/20250425-123419-neat-salmon.tar.gz`).

Use a specific config or domain if you have multiple:

```bash
rasa train --config config.yml --domain domain.yml
```

Train with a fixed model name (optional):

```bash
rasa train --fixed-model-name stress_bot
```

After changing intents, stories, rules, or config, run `rasa train` again, then restart the Rasa server so it loads the new model.

---

## 4. Rasa actions server

Custom actions (e.g. mental health assessment) run in a separate process. The core server calls them via `endpoints.yml`.

Start the actions server:

```bash
rasa run actions --port 5055
```

- Default port: **5055**
- Serves: `actions/actions.py` (and any other modules in `actions/`).

**Windows – batch file (from `strees_dection`):**

```batch
start-rasa-actions.bat
```

Or explicitly with Python 3.9:

```powershell
& "C:\Program Files\Python39\python.exe" -m rasa run actions --port 5055
```

**Health check:**

```bash
curl http://localhost:5055/health
```

`endpoints.yml` must point the core server to this URL, e.g.:

```yaml
action_endpoint:
  url: "http://localhost:5055/webhook"
```

---

## 5. Rasa core server (API)

Run the main Rasa server (NLU + dialogue, REST API):

```bash
rasa run --enable-api --cors "*" --port 5005
```

- Port: **5005**
- `--enable-api`: enables REST and webhook endpoints.
- `--cors "*"`: allows the Django frontend to call the API.

**Windows – batch file (from `strees_dection`):**

```batch
start-rasa-core.bat
```

Or with Python 3.9:

```powershell
& "C:\Program Files\Python39\python.exe" -m rasa run --enable-api --cors "*" --port 5005
```

**Use a specific model:**

```bash
rasa run --enable-api --cors "*" --port 5005 --model models/20250425-123419-neat-salmon.tar.gz
```

**Quick API check:**

```bash
curl http://localhost:5005/
```

---

## 6. Run order (full stack)

1. **Terminal 1 – Actions** (so the core can call custom actions):
   ```bash
   cd strees_dection
   rasa run actions --port 5055
   ```

2. **Terminal 2 – Rasa core**:
   ```bash
   cd strees_dection
   rasa run --enable-api --cors "*" --port 5005
   ```

3. **Terminal 3 – Django** (optional, for the web UI):
   ```bash
   cd strees_dection
   python manage.py runserver
   ```

The chatbot in the app uses: `http://localhost:5005/webhooks/rest/webhook`.

---

## 7. Useful Rasa commands

| Command | Purpose |
|--------|--------|
| `rasa train` | Train model from `data/`, `config.yml`, `domain.yml` |
| `rasa run` | Start core server (use `--enable-api --cors "*"` for API) |
| `rasa run actions` | Start custom actions server |
| `rasa shell` | Chat in the terminal (uses latest model) |
| `rasa test` | Run tests (e.g. `tests/test_stories.yml`) |
| `rasa data validate` | Check `data/` and `domain.yml` for errors |
| `rasa interactive` | Collect new training data interactively |

---

## 8. Project layout (Rasa)

```
strees_dection/
├── config.yml          # NLU pipeline & policies
├── domain.yml          # Intents, entities, slots, responses, actions
├── endpoints.yml       # action_endpoint URL (e.g. http://localhost:5055/webhook)
├── credentials.yml     # Optional channel config
├── data/
│   ├── nlu.yml         # Intents & entities
│   ├── stories.yml     # Conversation flows
│   └── rules.yml       # Rules (e.g. one-shot responses)
├── actions/
│   └── actions.py      # Custom action code (e.g. MentalHealthAssessment)
├── models/             # Trained models (*.tar.gz)
├── start-rasa-core.bat
└── start-rasa-actions.bat
```

---

## 9. Troubleshooting

**“Module not found” when running Rasa**

- Use the same Python that has `rasa` and `rasa-sdk` installed (e.g. `python -m rasa ...` or full path to `python.exe`).
- If you use a global Python 3.9 for Rasa, run:  
  `"C:\Program Files\Python39\python.exe" -m rasa run ...`  
  and the same for `rasa run actions`.

**Actions not running / 404 from core**

- Start the actions server first (`rasa run actions --port 5055`).
- In `endpoints.yml`, set `action_endpoint.url` to `http://localhost:5055/webhook` (or the host/port you use).

**Port 5005 or 5055 in use**

- Windows: `netstat -ano | findstr :5005` then `taskkill /PID <pid> /F`.
- Or use different ports: `rasa run --port 5006`, `rasa run actions --port 5056`, and update `endpoints.yml` and the frontend URL.

**Model not updating**

- Run `rasa train` after changing `data/` or `config.yml`.
- Restart the core server so it loads the new model from `models/`.

---

*Last updated: March 2025*
