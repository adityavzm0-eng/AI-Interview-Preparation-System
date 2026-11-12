# 🎯 PrepAI - AI Interview Preparation System

A production-grade, full-stack **AI Mock Interview Platform** built with **Python**, **Streamlit**, **Google Gemini API**, **NLP text analytics**, and **SQLite**.

Designed specifically to empower freshers and experienced software professionals to practice, evaluate, and master technical and HR interviews with real-time AI scoring, personalized constructive feedback, and interactive Plotly analytics.

---

## 🌟 Key Features

### 1. 🔐 User Authentication & Session Security
- User registration and login with input validation.
- Secure password hashing using `bcrypt` and salt-secured hashing.
- Individual user profile and isolated interview history tracking.

### 2. 👤 Candidate Profile Customization
- Target Job Role selection (`Python Developer`, `Data Scientist`, `Machine Learning Engineer`, `AI/ML Engineer`, `Java Developer`, `Full Stack Developer`, `SQL Developer`, `Data Analyst`, `Software Engineer`).
- Experience level calibration: `Fresher (0 - 1 years)`, `Experienced (1 - 3 years)`, `Experienced (3+ years)`.
- Educational background and technical skills inventory for personalized question generation.

### 3. 🤖 AI Question Generation (Google Gemini API)
- Zero-repetition question synthesis based on candidate profile and selected parameters.
- Mode support:
  - **Technical Interview**: 100% technical, algorithmic logic, architecture, debugging, and real-world system questions.
  - **HR Interview**: 100% behavioral, STAR framework, situational, and culture-fit questions.
  - **Mixed Interview**: Balanced technical and behavioral challenges.
- Difficulty tiers: `Easy`, `Medium`, and `Hard`.
- Real-world scenario-based questions with custom fresher guidance hints.

### 4. 📝 Real-Time Multidimensional Evaluation
Every submitted response is evaluated across **5 critical industry dimensions** (scored 0 to 10):
1. **Technical Correctness**: Precision of code, syntax, logic, and factual rigor.
2. **Conceptual Understanding**: Depth of comprehension ('why' things work).
3. **Relevance**: Direct focus on what the question asks.
4. **Clarity**: Structure, terminology, and communication quality.
5. **Completeness**: Handling edge cases, practical examples, and trade-offs.

#### Generated Feedback Artifacts:
- Overall Score out of 10.
- Radar Chart of dimension scores.
- Strengths & areas done well.
- Weaknesses & missing critical points.
- **Model 10/10 Answer** for interview comparison.
- Actionable improvement suggestions tailored for freshers.
- **NLP Text Metrics**: Word count, vocabulary richness (Type-Token Ratio), reading time, and structural rating.

### 5. 📊 Interactive Performance Dashboard & History
- Aggregate KPIs: Total Interviews Completed, Questions Practiced, Average Score, Best Performance.
- Plotly interactive charts:
  - Score progression timeline.
  - Technical vs. HR comparative performance.
  - Performance by difficulty level.
- Filterable interview history explorer with complete question-by-question review.

---

## 🏗️ Architecture & Folder Structure

```
ai_interview_system/
│
├── app.py                     # Streamlit application entrypoint & routing
├── config.py                  # Global configurations & environment constants
├── database.py                # SQLite schema, connection manager & CRUD queries
├── requirements.txt           # Project dependencies
├── .env                       # Environment variables (ignored in Git)
├── .env.example               # Example environment variable template
├── .gitignore                 # Standard Python & SQLite ignores
├── README.md                  # Comprehensive documentation & setup guide
│
├── modules/
│   ├── authentication.py      # Registration, login, session state
│   ├── profile.py             # Candidate profile management
│   ├── interview.py           # Interview simulator & live evaluation engine
│   ├── question_generator.py  # Gemini-powered question synthesis
│   ├── answer_evaluator.py    # 5-dimension scoring & model answer engine
│   └── dashboard.py           # Plotly analytics & historical drilldown
│
├── utils/
│   ├── gemini_client.py       # Google Gemini SDK & API handler with fallback
│   ├── helpers.py             # Password hashing, NLP analysis & JSON parsers
│   └── validators.py          # Form and answer input validators
│
└── assets/
    └── style.css              # Custom responsive stylesheet & UI typography
```

---

## 🗄️ SQLite Database Schema

The database is automatically initialized at `ai_interview_system.db` with cascading foreign keys:

1. **`users`**:
   - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
   - `name`: TEXT NOT NULL
   - `email`: TEXT UNIQUE NOT NULL
   - `password_hash`: TEXT NOT NULL
   - `created_at`: TIMESTAMP

2. **`profiles`**:
   - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
   - `user_id`: INTEGER FOREIGN KEY -> `users(id)`
   - `education`: TEXT
   - `skills`: TEXT
   - `experience_level`: TEXT
   - `target_role`: TEXT
   - `updated_at`: TIMESTAMP

3. **`interviews`**:
   - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
   - `user_id`: INTEGER FOREIGN KEY -> `users(id)`
   - `job_role`: TEXT NOT NULL
   - `interview_type`: TEXT NOT NULL
   - `difficulty`: TEXT NOT NULL
   - `total_questions`: INTEGER NOT NULL
   - `average_score`: REAL DEFAULT 0.0
   - `created_at`: TIMESTAMP

4. **`questions`**:
   - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
   - `interview_id`: INTEGER FOREIGN KEY -> `interviews(id)`
   - `question_text`: TEXT NOT NULL
   - `candidate_answer`: TEXT
   - `evaluation`: TEXT (JSON serialized evaluation)
   - `score`: REAL DEFAULT 0.0
   - `question_number`: INTEGER
   - `category`: TEXT
   - `created_at`: TIMESTAMP

---

## 🚀 Step-by-Step Installation & Setup

### Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13 installed.
- Free Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/app/apikey).

### 1. Navigate to Project Directory
```bash
cd ai_interview_system
```

### 2. Create and Activate Virtual Environment
**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**On Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` in an editor and insert your Gemini API Key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash
```
*(Note: You can also configure or override your API key dynamically from the Streamlit sidebar under **Configure API Key**).*

### 5. Run the Application
```bash
streamlit run app.py
```
The application will launch automatically in your default browser at `http://localhost:8501`.

---

## 📋 Sample Interview Workflow

1. **Sign Up / Log In**:
   - Create a test account (e.g. `alex@example.com` / `password123`).
2. **Setup Profile**:
   - Navigate to **My Profile** in the sidebar.
   - Enter your education (e.g., `B.Tech in Computer Science`) and skills (e.g., `Python, Pandas, SQL, Git, Machine Learning`).
3. **Configure Interview**:
   - Go to **Start Interview**.
   - Select Role: `Python Developer`.
   - Select Type: `Technical Interview`.
   - Select Difficulty: `Medium`.
   - Select Number of Questions: `5`.
   - Click **Generate Interview & Begin**.
4. **Answer Questions & Submit**:
   - Read the scenario-based question and the optional **Fresher Guidance Hint**.
   - Type your response in the text area.
   - Click **Submit Answer & Get AI Feedback**.
   - Review your 5-dimension radar chart, strengths, missing points, and the **Model 10/10 Answer**.
   - Click **Next Question**.
5. **View Final Report & Analytics**:
   - Inspect your overall performance tier (`Strong Hire`, `Hire Ready`, etc.).
   - Navigate to **Dashboard** to view score trends, difficulty distributions, and technical vs. HR comparisons.
   - Navigate to **Interview History** to inspect past submissions.

---

## 🛡️ Production & Reliability Features

- **Dynamic Gemini SDK Support**: Automatically utilizes Google's modern `google-genai` SDK with fallback to `google-generativeai` and direct REST API endpoints.
- **Fail-Safe JSON Parsers**: Sanitizes and extracts structured JSON responses even if LLMs return code blocks or conversational text.
- **Quota & Error Handling**: Gracefully informs candidates if quota limits or connection issues occur without crashing the session.
- **Safe State Transitions**: Retains answers and progress in session state and SQLite so navigation remains seamless.
