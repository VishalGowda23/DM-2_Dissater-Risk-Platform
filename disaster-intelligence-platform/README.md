# Disaster Intelligence Platform

A production-grade Multi-Hazard Micro-Level Disaster Intelligence Platform for Pune, Maharashtra, India.

## Features

- **Real-time Risk Scoring**: Ward-level flood and heatwave risk assessment
- **Baseline vs Event Modeling**: Compare seasonal baseline with forecast-driven event risk
- **Risk Delta Analysis**: Identify surging risk areas requiring immediate attention
- **Resource Allocation Optimizer**: Constrained proportional allocation of disaster response resources
- **Scenario Simulation**: "What-if" analysis for varying weather and infrastructure conditions
- **Explainable AI**: Detailed risk factor breakdowns and recommendations
- **Neo Brutalist UI**: Bold, authoritative dashboard design

## Architecture

### Backend
- **FastAPI**: Async Python web framework
- **PostgreSQL + PostGIS**: Geospatial database for ward data
- **Redis**: Caching and task queue
- **Celery**: Background task processing
- **Open-Meteo API**: Free weather data (no API key required)

### Frontend
- **React + TypeScript + Vite**
- **Tailwind CSS**: Neo Brutalist styling
- **Leaflet**: Interactive maps
- **Recharts**: Data visualization
- **shadcn/ui**: UI components

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Using Docker Compose

```bash
# Clone the repository
cd disaster-intelligence-platform

# Start all services
docker-compose -f docker/docker-compose.yml up --build

# Initialize database with seed data
curl -X POST http://localhost:8000/api/ingest/weather
curl -X POST http://localhost:8000/api/calculate-risks

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Manual Setup

#### Backend
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python -c "from core.database import init_db; init_db()"
python -c "from ingestion.init_data import initialize_all_data; initialize_all_data()"

# Run server
uvicorn main:app --reload
```

#### Frontend
```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run development server
npm run dev
```

## API Endpoints

### Core Endpoints
- `GET /` - API info
- `GET /health` - Health check
- `GET /api/wards` - List all wards
- `GET /api/wards/{ward_id}` - Get ward details
- `GET /api/risk` - Get current risk scores
- `GET /api/risk/summary` - Get city-wide risk summary
- `GET /api/explain/{ward_id}` - Get risk explanation

### Operations
- `POST /api/ingest/weather` - Trigger weather data ingestion
- `POST /api/calculate-risks` - Calculate risk scores for all wards
- `POST /api/optimize` - Run resource allocation optimizer
- `POST /api/scenario` - Run scenario simulation

## Risk Model

### Flood Risk
**Baseline**: `0.50 × Historical_Frequency + 0.30 × Elevation_Vulnerability + 0.20 × Drainage_Weakness`

**Event**: `0.60 × Forecast_Rainfall_Intensity + 0.20 × 48h_Cumulative_Rain + 0.20 × Baseline_Vulnerability`

### Heatwave Risk
**Event**: `0.70 × Temperature_Anomaly + 0.30 × Baseline_Vulnerability`

### Risk Categories
- **Low**: 0-30%
- **Moderate**: 31-60%
- **High**: 61-80%
- **Critical**: 81-100%

## Data Sources

- **Ward Boundaries**: Pune Municipal Corporation (PMC)
- **Population**: Census 2011
- **Elevation**: SRTM DEM
- **Weather**: Open-Meteo API (free, no key required)
- **Historical Events**: Government reports, news archives

## Project Structure

```
disaster-intelligence-platform/
├── backend/
│   ├── api/              # API endpoints
│   ├── core/             # Config, database, cache
│   ├── ingestion/        # Data ingestion pipelines
│   ├── models/           # Database models
│   ├── optimizer/        # Resource allocation
│   ├── risk_engine/      # Risk calculation engine
│   ├── tests/            # Unit tests
│   ├── main.py           # FastAPI application
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── lib/          # Utilities and types
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── index.html
│   └── package.json
├── docker/
│   └── docker-compose.yml
└── README.md
```

## License

MIT License

## Acknowledgments

- Pune Municipal Corporation for ward data
- Open-Meteo for free weather API
- OpenStreetMap contributors
