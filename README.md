# 🦟 Disease Outbreak Predictor

An AI-powered disease outbreak prediction system that fuses real-world health data, climate patterns, and search trends to predict **Dengue fever** outbreak risk across Indian states. Select a region and time period, and the system outputs a predicted risk level (LOW / MEDIUM / HIGH) with confidence scores, visualized through an interactive dashboard and heatmap.

---

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Data Sources](#data-sources)
- [Data Merging Approach](#data-merging-approach)
- [Model Details](#model-details)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)

---

## ✨ Features

- **Multi-source ETL Pipeline** — Automatically fetches and fuses data from 3 real-world sources
- **Ensemble ML Model** — VotingClassifier combining Random Forest + XGBoost for risk prediction
- **Interactive Dashboard** — React-based UI with area charts, metric cards, and AI-generated insights
- **Outbreak Heatmap** — Leaflet-powered heatmap showing case intensity across Indian states
- **Regional Comparison** — Sortable table comparing outbreak severity across regions
- **CSV Export** — Download outbreak data for any region
- **JWT Authentication** — Secure login system protecting all prediction endpoints

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                      DATA PIPELINE (src/)                       │
│                                                                  │
│  Google Trends API ──┐                                          │
│  Open-Meteo API ─────┼──► pipeline.py ──► MongoDB               │
│  Zenodo EpiClim CSV ─┘    (ETL + Feature Engineering)           │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    MODEL TRAINING (src/)                         │
│                                                                  │
│  MongoDB Data ──► train_model.py ──► best_model.pkl             │
│                   (RandomForest + XGBoost VotingClassifier)      │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    FLASK API (backend/)                          │
│                                                                  │
│  /api/auth/login    ──► JWT Token Generation                    │
│  /api/predict       ──► ML Risk Prediction                      │
│  /api/historical    ──► Time-series Data                        │
│  /api/heatmap-data  ──► Geo-weighted Case Data                  │
│  /api/regional-summary ──► Aggregated State Comparison          │
│  /api/export        ──► CSV Download                            │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                  REACT DASHBOARD (frontend-dash/)               │
│                                                                  │
│  Login Gate → 3-Panel Layout:                                   │
│  [Threat Level + Regional Table] [Charts + Metrics] [AI Insights]│
│  + Leaflet Heatmap Modal                                        │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Sources

| Source | What It Provides | API/URL |
|--------|-----------------|---------|
| **Google Trends** (via pytrends) | Weekly search interest for "dengue symptoms" per Indian state | `pytrends.request.TrendReq` |
| **Open-Meteo Archive** | Historical daily weather data (temperature, humidity, rainfall) aggregated to weekly | `https://archive-api.open-meteo.com/v1/archive` |
| **EpiClim Registry** (Zenodo) | Hospital-reported disease case counts by state, disease, and outbreak week | `https://zenodo.org/records/14580510/files/Final_data.csv` |

**Coverage:** Maharashtra, Karnataka, Kerala — Weekly data from 2016 to 2020.

---

## 🔄 Data Merging Approach

The ETL pipeline (`src/pipeline.py`) executes a 3-stage process:

### 1. Extract
- **Google Trends:** Fetches weekly search interest scores for "dengue symptoms" per state with rate-limiting (15s delay between regions)
- **Weather:** Retrieves daily weather data and aggregates to weekly averages (temperature, humidity) and sums (rainfall)
- **Hospital Cases:** Downloads the EpiClim CSV and filters for Dengue cases in target states

### 2. Transform
- All three datasets are standardized to a common schema: `[Year, Week_Num, Region]`
- Hospital cases are aggregated by week and region
- An **inner join** merges all three on `[Year, Week_Num, Region]`

### 3. Feature Engineering
After merging, the pipeline creates time-lag features:
| Feature | Description |
|---------|-------------|
| `Cases_Last_Week` | Reported cases from previous week (1-week lag) |
| `Rainfall_Lag_1` | Rainfall from previous week (mosquito breeding lag) |
| `Temp_Humidity_Index` | Temperature × Humidity interaction term |

### 4. Load
The fused dataset is written to MongoDB collection `fused_outbreak_data`, replacing any existing data.

---

## 🧠 Model Details

| Property | Value |
|----------|-------|
| **Algorithm** | `VotingClassifier` (soft voting) |
| **Base Models** | `RandomForestClassifier` (200 trees, max_depth=10) + `XGBClassifier` |
| **Task** | 3-class classification |
| **Classes** | `0` = LOW risk (≤50 cases), `1` = MEDIUM (51–150), `2` = HIGH (>150) |
| **Features** | Temperature, Humidity, Search Trend Score, Rainfall, Cases Last Week, Rainfall Lag, Temp×Humidity Index |
| **Train/Test Split** | 80/20, `random_state=42` |
| **Output** | Risk label + probability confidence score |

The model is serialized to `backend/models/best_model.pkl` using `joblib` and loaded once at Flask startup for low-latency inference.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Data Pipeline** | Python 3.x, Pandas, pytrends, Requests |
| **ML Training** | Scikit-learn, XGBoost, Joblib |
| **Backend** | Flask, Flask-CORS, PyJWT, PyMongo |
| **Database** | MongoDB |
| **Frontend** | React 19, Vite 8, Recharts, Leaflet, Tailwind CSS v4 |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.9+**
- **Node.js 18+** and npm
- **MongoDB** running locally on port 27017 (default)

### 1. Clone the Repository

```bash
git clone <repo-url>
cd DiseasePredictor
```

### 2. Set Up the Backend

```bash
# Create and activate a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
# Copy the example env file
cp backend/.env.example backend/.env

# Edit backend/.env and set your values:
#   SECRET_KEY=<a-random-secret-string>
#   ADMIN_USERNAME=admin
#   ADMIN_PASSWORD=<your-chosen-password>
#   MONGO_URI=mongodb://localhost:27017/
```

### 4. Run the Data Pipeline

> **Note:** This step fetches real-time data from external APIs and may take 5–10 minutes due to rate limiting.

```bash
cd src
python pipeline.py
```

### 5. Train the ML Model

```bash
# Still in the src/ directory
python train_model.py
```

You should see output like:
```
Voting Ensemble Training Complete. Validation Accuracy: XX.XX%
Model and metadata saved successfully to backend/models/!
```

### 6. Start the Flask API Server

```bash
cd ../backend
python run.py
```

The API will be available at `http://localhost:5000`.

### 7. Start the React Frontend

```bash
# Open a new terminal
cd frontend-dash
npm install
npm run dev
```

The dashboard will open at `http://localhost:5173`.

### 8. Login and Use

1. Open `http://localhost:5173` in your browser
2. Login with the credentials you set in `.env`
3. Select a region (Maharashtra / Karnataka / Kerala) and week number
4. Click **"RUN ANALYSIS"** to see the AI prediction
5. Click **"Heatmap"** to view the geographic outbreak heatmap

---

## 📡 API Reference

All endpoints (except login and heatmap) require a JWT token in the `Authorization: Bearer <token>` header.

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/auth/login` | ❌ | Authenticate and receive JWT token |
| `POST` | `/api/predict` | ✅ | Get ML risk prediction for a region + week |
| `GET` | `/api/historical/<region>` | ✅ | Get time-series outbreak data for charts |
| `GET` | `/api/heatmap-data` | ❌ | Get geo-weighted case data for heatmap |
| `GET` | `/api/regional-summary` | ✅ | Get aggregated comparison across regions |
| `GET` | `/api/export/<region>` | ❌ | Download outbreak data as CSV |

### Example: Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}'
```

### Example: Predict
```bash
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token>" \
  -d '{"region": "Maharashtra", "week": 24, "disease": "Dengue"}'
```

---

## 📁 Project Structure

```
DiseasePredictor/
├── src/                        # Data pipeline & training scripts
│   ├── pipeline.py             # ETL: fetch, transform, load data into MongoDB
│   ├── train_model.py          # Train VotingClassifier and save .pkl model
│   └── db_config.py            # MongoDB connection configuration
│
├── backend/                    # Flask API server
│   ├── run.py                  # Server entry point (port 5000)
│   ├── .env.example            # Environment variable template
│   ├── app/
│   │   ├── __init__.py         # Flask app factory with CORS & Blueprint registration
│   │   └── api/
│   │       ├── auth.py         # JWT login & token_required decorator
│   │       └── route.py        # All API endpoints (predict, historical, heatmap, export)
│   ├── models/
│   │   ├── best_model.pkl      # Trained ML model (generated by train_model.py)
│   │   └── model_metadata.json # Model name & accuracy metadata
│   └── data/
│       └── sample_fused_data.csv  # Sample of the fused training dataset
│
├── frontend-dash/              # React dashboard (Vite)
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── App.jsx             # Main dashboard component
│       ├── App.css             # All styling
│       └── components/
│           └── Heatmap.jsx     # Leaflet heatmap component
│
├── requirements.txt            # Python dependencies
├── Dependencies.md             # Dependency reference document
└── .gitignore
```

---

## 📄 License

This project was built as part of the ACM Club project program.
