# 🐣 Hatched — Gamified Workout & Streak Tracker

A full-stack, gamified workout and streak tracking application. Stay consistent with your fitness journey, meet your weekly workout goals, and watch your companion avatar evolve from an egg into a free-flying bird!

---

## 🌟 Key Features

* **Gamified Avatar Evolution**:
  * 🥚 **Egg Stage**: The beginning of your fitness journey.
  * 🐣 **Gym Chick** (*30 Active Days*): Hatches once you reach 30 active workout days.
  * 🐦 **Free Bird** (*60 Active Days*): Fully evolved bird with interactive flight animations on tap.
* **Weekly Streak & Cycle System**:
  * Set customizable weekly goals (e.g., target 3–5 workouts/week).
  * Weekly cycles track completed vs. target workout days.
  * Built-in **Auto-Rest Protection**: Once your weekly target is achieved, remaining days are safe rest days that will never break your streak.
* **Anti-Exploit Guarantees**:
  * Workouts cannot be pre-logged for future dates.
  * Workouts cannot be backdated across previous weeks.
  * Only one workout counts per calendar day.
  * Calendar week gaps break streaks accurately even if no workout was logged.
* **Workout & Set Logging**:
  * Interactive exercise selector (Bench Press, Squat, Deadlift, Overhead Press, Pull-Ups, Barbell Rows).
  * Detailed set logger (Reps, Weight in kg, RPE, Best Score calculation).
* **ML-Ready Daily Metrics**:
  * Aggregates total workout volume (`reps × weight`), total sets, and average RPE for fatigue forecasting and predictive training models.
* **Secure Authentication**:
  * JWT access tokens with direct bcrypt password hashing.

---

## 🏗️ Project Architecture

```
hatched-workout-tracker/
├── backend-project/             # FastAPI Backend
│   ├── api/
│   │   └── routes/
│   │       ├── auth.py          # Registration & JWT login
│   │       ├── gamification.py  # Avatar evolution & status
│   │       ├── goals.py         # Weekly target configuration
│   │       └── workouts.py      # Workout & set logging, streaks
│   ├── models/
│   │   └── models.py            # SQLAlchemy ORM models
│   ├── services/
│   │   └── streak_service.py    # Anti-exploit streak & gamification engine
│   ├── database.py              # Database connection (PostgreSQL / SQLite)
│   ├── main.py                  # FastAPI app entry point & CORS
│   └── requirements.txt         # Python dependencies
│
└── expo-project/                # React Native / Expo Mobile App
    ├── assets/avatars/          # Avatar sprite graphics (egg, chick, bird)
    ├── components/
    │   └── AvatarBird.js        # Interactive animated avatar component
    ├── screens/
    │   ├── DashboardScreen.js   # Main progress dashboard & streak view
    │   └── WorkoutScreen.js     # Workout & set logger screen
    ├── services/
    │   └── api.js               # Client API wrapper
    ├── App.js                   # Tab Navigation & app container
    └── package.json             # NPM dependencies
```

---

## 🚀 Getting Started

### Prerequisites

* **Python 3.10+**
* **Node.js 18+** & **npm**
* **Expo Go** app on your iOS or Android mobile device (optional, for physical device testing)

---

### 1. Backend Setup (FastAPI)

1. Open a terminal and navigate to `backend-project`:
   ```bash
   cd backend-project
   ```

2. (Optional) Create and activate a Python virtual environment:
   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # macOS / Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Choose your database:
   * **Quick Local Run (SQLite - Zero Setup)**:
     ```powershell
     $env:DATABASE_URL="sqlite:///./workout_tracker.db"
     ```
   * **PostgreSQL (Default)**:
     Ensure PostgreSQL is running and set:
     ```powershell
     $env:DATABASE_URL="postgresql://postgres:password@localhost:5432/workout_tracker"
     ```

5. Start the API server:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   * **API Root**: `http://localhost:8000`
   * **Interactive Swagger Docs**: `http://localhost:8000/docs`
   * **Health Check**: `http://localhost:8000/health`

---

### 2. Frontend Setup (Expo / React Native)

1. Open a second terminal and navigate to `expo-project`:
   ```bash
   cd expo-project
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Configure API Host:
   In `expo-project/services/api.js`, set `BASE_URL`:
   * **Testing in a Web Browser**: `'http://localhost:8000'`
   * **Testing in Android Emulator**: `'http://10.0.2.2:8000'`
   * **Testing on Physical Phone via Expo Go**: `'http://<YOUR_COMPUTER_LOCAL_IP>:8000'` (e.g. `http://192.168.0.71:8000`)

4. Start the Expo development server:
   ```bash
   npm start
   ```

5. Run the app:
   * **Web**: Press `w` in the terminal to view in your browser.
   * **Mobile**: Open the **Expo Go** app on your phone and scan the QR code.
   * **Android Emulator**: Press `a`.
   * **iOS Simulator**: Press `i`.

---

## 📡 API Endpoints Overview

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Register new user account |
| `POST` | `/api/auth/login` | Log in and receive JWT access token |
| `POST` | `/api/goals` | Set weekly workout frequency and hour goals |
| `GET` | `/api/goals/active` | Get current active weekly goal |
| `POST` | `/api/workouts/log` | Log workout and update streak / active days |
| `GET` | `/api/workouts/streak` | Get current streak weeks and evolution stage |
| `GET` | `/api/workouts/weekly-cycle` | Get current week's workout progress & rest status |
| `POST` | `/api/workouts/sets` | Log individual exercise set |
| `GET` | `/api/gamification` | Fetch avatar evolution and active day milestones |
| `POST` | `/api/workouts/admin/finalize-weeks` | Cron job endpoint to finalize completed weeks |

---

## 📄 License

This project is licensed under the MIT License.
