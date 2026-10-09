# 🎯 PYQ Quiz Master - Full-Stack Exam Simulator

A full-stack web application that takes any **Previous Year Question (PYQ) PDF with answers**, automatically parses all MCQs, detects topics/subjects (e.g., Physics, Chemistry, Unit 1, Section A), and generates an interactive, timed exam quiz with live scorecards and verified PDF answer reviews.

---

## ✨ Key Features

1. **100% PDF-Derived Questions**: Only questions, options, answers, and explanations present in your uploaded PDF are used. No external hallucinated questions.
2. **Automatic Topic & Subject Detection**: Identifies sections (e.g., *Physics, Mathematics, General Knowledge, Section A, Unit 1*) and categorizes questions into topic cards.
3. **Interactive Exam Simulation**:
   - Live Countdown Timer.
   - Question Navigator Palette (Answered, Marked for Review, Unattempted).
   - Keyboard shortcuts (`A`, `B`, `C`, `D` or `1`, `2`, `3`, `4`).
4. **Detailed Scorecard & Solution Analysis**:
   - Accuracy percentage, correct vs incorrect counts, and topic-wise performance breakdown.
   - Solution review highlighting user selection vs. verified PDF answer key and explanation.
5. **No Database Configuration Required**: Self-contained FastAPI backend with JSON document storage.

---

## 🚀 Quick Start (Run on your Computer)

### 1. Open Terminal in the project folder:
```bash
cd "C:\Users\rokihics\.gemini\antigravity\scratch\pyq-quiz-app"
```

### 2. Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Start the Web Server:
```bash
python app.py
```

### 4. Open in your Browser:
Visit **`http://localhost:8000`** in Chrome, Edge, or Firefox.

---

## 🌐 How to Host Online for Free (Share with Friends / Students)

### Option A: Free Hosting on Render.com (Recommended - 5 Minutes)
1. Push this folder to a GitHub repository.
2. Go to [Render.com](https://render.com) and create a free account.
3. Click **New +** -> **Web Service** -> Connect your GitHub repo.
4. Set:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. Click **Deploy**. Render gives you a free live URL (e.g., `https://my-pyq-quiz.onrender.com`) to share!

---

### Option B: Free Hosting on Hugging Face Spaces (Docker)
1. Go to [Hugging Face Spaces](https://huggingface.co/spaces) -> **Create New Space**.
2. Select **Docker** as the SDK.
3. Upload all files from this project folder.
4. It will build automatically using the included `Dockerfile` and give you an instant public web link.

---

### Option C: Railway.app
1. Create account on [Railway.app](https://railway.app).
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Railway automatically detects the `Procfile` and launches your website.
