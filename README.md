# 🎯 𝕊𝕋ℝ𝔼𝕊𝕊 𝔻𝔼𝕋𝔼ℂ𝕋𝕀𝕆ℕ 𝔽𝕆ℝ 𝕀𝕋 𝔓ℝ𝕆𝔽𝔼𝕊𝕊𝕀𝕆ℕ𝔸𝕃𝕊 🧠

> *A smart AI-powered system to monitor, detect, and manage stress in high-pressure IT environments.
> Your wellbeing companion in the tech world *

---

## 🚀 **Tech Stack**

* **🌐 Django:** Robust Python web framework for interactive UI
* **🤖 Rasa:** Conversational AI for real-time stress management chat
* **📊 Machine Learning:** Scikit-learn, NumPy, Pandas for stress prediction
* **🎧 Librosa:** Audio feature extraction for voice pattern analysis
* **📱 Data Inputs:** Screen time, voice recordings, wearable sensor data

---

## 🧩 **Key Components**

### 🔷 **Django Web Application**

* **🔐 User Authentication**

  * `userregistration.html`, `userlogin.html`, `userprofile.html`
* **📈 Stress Assessment**

  * Form & file uploads via `stress_assessment.html`
  * Audio to: `strees_dection/media/voice_patterns/`
* **📊 Dashboards**

  * `user_dashboard.html` – Stress level visualizations
  * `recommendation_dashboard.html` – Personalized suggestions
* **🗣️ Feedback System**

  * Submit: `submit_feedback.html`
  * View: `view_feedback.html`
* **🎨 Media Handling**

  * Images, `.mp3` files, and wearables for analysis
* **📝 Templates**

  * `post_screen_time.html`, `post_voice_pattern.html`, `post_wearable_data.html`, `report_view.html`

---

### 💬 **Rasa Chatbot**

* **✨ Functionality**

  * Converses with users, offers tips like breathing techniques
* **🧠 Configurations**

  * `nlu.yml`, `rules.yml`, `stories.yml`, `domain.yml`, `config.yml`
* **📦 Models**

  * Trained models:
    `20250425-122133-thin-cuisine.tar.gz`
    `20250425-124518-adiabatic-holder.tar.gz`
* **🌐 Integration**

  * REST API (`endpoints.yml`) or embedded in `usershome.html`

---

### 📊 **Data Analysis & Machine Learning**

#### 🔌 **Inputs**

* **⏱️ Screen Time**
  Uploaded logs or manual entry via `post_screen_time.html`
* **🎤 Voice Patterns**
  `.mp3` files like `__Tech_Talk_Tuesday__Must-Know.mp3` for tone/pitch analysis
* **📶 Wearable Data**
  Metrics like heart rate & sleep via `post_wearable_data.html`

#### ⚙️ **Processing**

* ML models classify stress levels
* Tools: Scikit-learn, Librosa, Pandas
* Algorithms: `Logistic Regression`, `Random Forest`, `Neural Networks`

#### 📢 **Outputs**

* **stress\_result.html** – Stress level classification
* **recommendation\_view\.html** – Suggested interventions
* **Chatbot** – Delivers real-time guidance

---

## 🧱 **Database**

* **🗂 SQLite** (`db.sqlite3`) stores:

  * User data
  * Assessment records
  * Feedback logs
* **🛡️ .gitignore** excludes `db.sqlite3.backup` for data safety

---

## 📁 **Media & Resources**

* **Images**: e.g., `face1.jpg`, `pexels-pixabay-270408.jpg`
* **Audio**: Voice samples in `media/voice_patterns/`
* **Resources**: Stress guides in `media/resources/` → Displayed on `resources.html`

---

## 🔄 **Workflow**

1. ✅ **Login/Register**
2. 📥 **Submit stress data**
3. 🧠 **ML Analysis**
4. 📊 **Dashboard displays results**
5. 💬 **Chatbot provides real-time support**

---

## 🧠 **Stress Detection Logic**

* **Extracted features** from voice (e.g., pitch, rate) + wearables (e.g., HRV, sleep)
* **Classification models** provide:

  * 🔵 Low Stress
  * 🟡 Medium Stress
  * 🔴 High Stress

---

## 🌿 **Personalized Recommendations**

> Based on user’s stress level:

* 🧘 Mindfulness or meditation
* 🛑 Scheduled breaks
* 👩‍⚕️ Referrals to professional support
* 🤖 Chatbot tips & exercises

---

## 🧪 **Assumptions & Future Work**

* ✅ **ML Models:** Assumed Scikit-learn-based (pending confirmation)
* ✅ **Data Sources:** Manual uploads / simulated inputs (e.g., `data.json`)
* 🎵 **Voice Analysis:** Librosa or custom scripts
* 🚀 **Deployment:** Currently local, scalable to Heroku or AWS


---

## 📑 Table of Contents

- [📘 Project Overview](#project-overview)
- [✨ Features](#features)
- [🧰 Technologies Used](#technologies-used)
- [⚙️ Installation](#installation)
- [📁 Project Structure](#project-structure)
- [🚀 Usage](#usage)
- [🤖 Running the Rasa Chatbot](#running-the-rasa-chatbot)
- [🤝 Contributing](#contributing)
- [🪪 License](#license)
- [📬 Contact](#contact)

---

## 📘 Project Overview

This system provides a stress monitoring and management solution for IT professionals by analyzing behavioral and biometric data. It supports:

- Daily stress logging
- Screen time/voice input analysis
- Chatbot-based recommendations
- Visualization dashboards for stress trends

The AI chatbot, built with Rasa, interacts with users to assess and alleviate stress in real-time.

---

## ✨ Features

- ✅ **User Authentication** (Register/Login)
- 📊 **Stress Assessment Dashboard**
- 🧠 **AI-Powered Rasa Chatbot** for mental health support
- 📷 **Voice/Image/Wearable Data Upload**
- 💬 **Feedback System**
- 🌐 **Responsive Django Templates**
- 🧾 **Detailed Recommendations and Reports**

---

## 🧰 Technologies Used

| Layer       | Technologies |
|-------------|--------------|
| Backend     | Django 5.0.7, Python 3.10.2 |
| Chatbot     | Rasa 3.6.20 |
| ML/AI       | Scikit-learn, NumPy, Pandas |
| Frontend    | HTML, CSS, Bootstrap |
| Database    | SQLite |
| Media       | Images, Audio (.mp3), JSON |
| VCS         | Git, Git LFS |

---

## ⚙️ Installation

### 🔧 Prerequisites

- Python 3.8+
- Git
- Virtualenv
- Git LFS
- Rasa CLI

### 🔨 Setup

```bash
git clone https://github.com/suragsunil/STRESS-DETECTION-FOR-IT-PROFESSIONALS.git
cd "Stress Detection for IT Professionals"

python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt

git lfs install
git lfs pull

python manage.py migrate
# Optional: Load demo data
# python manage.py loaddata data.json

python manage.py runserver
````

> 📍 Access at `http://127.0.0.1:8000`

---

## 📁 Project Structure

```
Stress Detection for IT Professionals/
├── strees_dection/
│   ├── app/
│   │   ├── templates/
│   │   │   ├── user_dashboard.html
│   │   │   ├── post_voice_pattern.html
│   │   │   ├── post_screen_time.html
│   │   │   └── ... (forms, feedback, recommendations)
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tests.py
│   ├── media/
│   │   ├── media/
│   │   ├── resources/
│   │   └── voice_patterns/
│   ├── models/
│   │   ├── *.tar.gz (Rasa trained models)
│   ├── data/
│   │   ├── nlu.yml, stories.yml, rules.yml
│   ├── settings.py, urls.py, wsgi.py, asgi.py
│   └── manage.py
├── config.yml
├── domain.yml
├── endpoints.yml
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 🚀 Usage

* 🔐 **Login/Register**: Navigate to `userlogin.html` / `userregistration.html`
* 📈 **Submit Data**: Enter screen time, voice uploads via forms
* 🧠 **Chatbot**: Chat with AI bot for instant support
* 📊 **View Dashboard**: See stress trends, reports, and suggestions
* 📝 **Submit Feedback**: Via `submit_feedback.html`

---

## 🤖 Running the Rasa Chatbot

### 1️⃣ Train the Model

```bash
rasa train
```

This will create models in `strees_dection/models/`.

### 2️⃣ Start Rasa Server

```bash
rasa run --enable-api --cors "*"
```

> Runs at: `http://localhost:5005`

### 3️⃣ Start Actions Server

```bash
rasa run actions
```

### 4️⃣ (Optional) Test in CLI

```bash
rasa shell
```

---

## 🤝 Contributing

```bash
# Fork the repo and clone locally
git checkout -b feature/your-feature-name

# Make changes, then commit
git commit -m "Add: new feature"

# Push to GitHub
git push origin feature/your-feature-name

# Create a pull request
```

---

## 🪪 License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.

---


## 📬 Contact

* **Author**: Surag
* **Email**: [suraagms@gmail.com](mailto:suraagms@gmail.com)
* **GitHub**: [@suragsunil](https://github.com/suragsunil)
* **LinkedIn**: [linkedin.com/in/suragsunil](https://www.linkedin.com/in/suragsunil)
* **Twitter/X**: [@suragsunil](https://twitter.com/suragsunil)
* **Instagram**: [@suragsunil](https://instagram.com/suragsunil)
* **Facebook**: [facebook.com/suragsunil](https://www.facebook.com/suragsunil)
* **YouTube**: [youtube.com/@suragsunil](https://www.youtube.com/@suragsunil)
* **Portfolio / Website**: [suragsunil.github.io](https://suragsunil.github.io)

---

> 💡 *“Helping IT professionals stay mentally healthy — one insight at a time.”*

````
