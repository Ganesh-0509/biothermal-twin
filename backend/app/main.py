"""
FastAPI Backend for BioThermal Twin.

Endpoints:
- POST /api/telemetry/ingest - Ingest worker telemetry
- GET /api/workers/{worker_id}/status - Get worker status
- GET /api/dashboard/overview - Dashboard data
- POST /api/voice-check - Process voice symptom check
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

app = FastAPI(
    title="BioThermal Twin API",
    description="Physics-Informed Heat Stress Early Warning System",
    version="1.0.0"
)

# CORS middleware (allow frontend to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === PYDANTIC MODELS (Request/Response schemas) ===

class TelemetryReading(BaseModel):
    worker_id: str
    timestamp: Optional[datetime] = None
    heart_rate: float
    cadence: Optional[float] = 0.0
    ambient_temp: float
    relative_humidity: float
    solar_load: Optional[float] = 0.0
    work_intensity: float


class WorkerStatus(BaseModel):
    worker_id: str
    core_temp_estimate: float
    psi: float
    kidney_risk: float
    heart_rate: float
    risk_level: str  # "LOW", "MODERATE", "HIGH", "CRITICAL"
    last_updated: datetime


class VoiceCheckRequest(BaseModel):
    worker_id: str
    audio_base64: Optional[str] = None
    transcription: Optional[str] = None
    language: Optional[str] = "hi"


class DashboardOverview(BaseModel):
    total_workers: int
    high_risk_count: int
    alerts_today: int
    average_psi: float
    workers: List[WorkerStatus]


# === ENDPOINTS ===

@app.get("/")
async def root():
    """Health check"""
    return {
        "service": "BioThermal Twin API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "api": "ok",
            "pinn_model": "loaded",  # TODO: Check if model loaded
            "database": "connected"   # TODO: Check DB connection
        }
    }


@app.post("/api/telemetry/ingest")
async def ingest_telemetry(readings: List[TelemetryReading]):
    """
    Ingest batch of telemetry readings.

    For each reading:
    1. Run through PINN model
    2. Calculate PSI and risk scores
    3. Store in database
    4. Check if alert threshold exceeded
    """
    # TODO: Load PINN model and run predictions
    # TODO: Store in database
    # TODO: Generate alerts if needed

    return {
        "ingested": len(readings),
        "timestamp": datetime.now().isoformat(),
        "message": "Telemetry processed successfully"
    }


@app.get("/api/workers/{worker_id}/status")
async def get_worker_status(worker_id: str):
    """
    Get current physiological status for a worker.

    Returns latest telemetry + PINN predictions.
    """
    # TODO: Query database for latest reading
    # TODO: Return worker status

    # Mock response for now
    return WorkerStatus(
        worker_id=worker_id,
        core_temp_estimate=38.2,
        psi=6.5,
        kidney_risk=0.35,
        heart_rate=125,
        risk_level="MODERATE",
        last_updated=datetime.now()
    )


@app.get("/api/dashboard/overview")
async def dashboard_overview():
    """
    Get dashboard overview data.

    Returns:
    - Total workers
    - High-risk count
    - Alerts today
    - Average PSI
    - All workers with latest status
    """
    # TODO: Query database for all workers
    # TODO: Calculate aggregates

    # Mock response
    return DashboardOverview(
        total_workers=100,
        high_risk_count=8,
        alerts_today=23,
        average_psi=4.2,
        workers=[]  # TODO: Populate with actual workers
    )


@app.post("/api/voice-check")
async def voice_check(request: VoiceCheckRequest):
    """
    Process voice symptom check.

    Either:
    - Provide audio_base64 (will transcribe + extract)
    - Provide transcription (will just extract symptoms)
    """
    # TODO: If audio provided, transcribe with Whisper
    # TODO: Extract symptoms with LLM
    # TODO: Store in database
    # TODO: Check if combined with PSI > 7 triggers alert

    return {
        "worker_id": request.worker_id,
        "symptoms": {
            "dark_urine": False,
            "muscle_cramps": False,
            "dizziness": False,
            "fatigue": "NONE",
            "headache": False
        },
        "risk_score": 0.2,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
