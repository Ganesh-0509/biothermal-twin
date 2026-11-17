"""
FastAPI Backend for BioThermal Twin.
Powered by Physics-Informed Neural Network (PINN) inference.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import sys
import os
import random
import math
import numpy as np
from pathlib import Path
import torch

# Add repository root to path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from models.pinn_core_temp import PhysicsInformedHeatStrain

app = FastAPI(
    title="BioThermal Twin API",
    description="Physics-Informed Heat Stress Early Warning System with Real-Time PINN Inference",
    version="2.0.0"
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === PYDANTIC SCHEMAS ===

class TelemetryReading(BaseModel):
    worker_id: str
    heart_rate: float
    skin_temp: Optional[float] = 36.5
    work_intensity_met: Optional[float] = 2.5
    ambient_temp: float
    relative_humidity: float
    wbgt: Optional[float] = None
    time_exposed_minutes: Optional[float] = 120.0
    prev_core_temp: Optional[float] = 37.5


class WorkerStatus(BaseModel):
    worker_id: str
    name: str
    role: str
    age: int
    bmi: float
    acclimatization: float
    heart_rate: float
    skin_temp: float
    core_temp_estimate: float
    psi: float
    kidney_risk: float
    risk_level: str  # "LOW", "MODERATE", "HIGH", "CRITICAL"
    hydration_pct: float
    time_exposed_minutes: float
    ambient_temp: float
    relative_humidity: float
    oshad_advisory: str
    last_updated: datetime


class VoiceCheckRequest(BaseModel):
    worker_id: str
    text: Optional[str] = None
    language: Optional[str] = "en"
    audio_base64: Optional[str] = None


class DashboardOverview(BaseModel):
    total_workers: int
    safe_count: int
    moderate_count: int
    high_risk_count: int
    critical_count: int
    alerts_today: int
    average_psi: float
    average_core_temp: float
    ambient_temp: float
    relative_humidity: float
    pinn_model_status: str
    pinn_mae: float
    workers: List[WorkerStatus]


# === PINN MODEL MANAGER ===

class PINNModelManager:
    """Manages loaded PyTorch model and executes real inference."""
    def __init__(self):
        self.model = None
        self.feature_means = None
        self.feature_stds = None
        self.loaded = False
        self.mae = 0.139
        self.load_model()

    def load_model(self):
        ckpt_path = ROOT_DIR / "models" / "checkpoints" / "pinn_best.pt"
        if not ckpt_path.exists():
            print(f"[WARN] Checkpoint not found at {ckpt_path}. Running with mathematical simulation fallback.")
            return

        try:
            ckpt = torch.load(str(ckpt_path), map_location="cpu", weights_only=False)
            self.model = PhysicsInformedHeatStrain()
            self.model.load_state_dict(ckpt["model_state_dict"])
            self.model.eval()

            stats = ckpt.get("feature_stats", {})
            self.feature_means = np.array(stats.get("feature_means", [162.0, 37.0, 2.75, 45.5, 59.0, 45.0, 240.0, 41.8]), dtype=np.float32)
            self.feature_stds = np.array(stats.get("feature_stds", [16.5, 0.20, 1.05, 4.16, 18.0, 4.5, 138.5, 0.67]), dtype=np.float32)
            self.loaded = True
            print(f"[OK] PINN Model successfully loaded from {ckpt_path} (MAE: {self.mae}°C)")
        except Exception as e:
            print(f"[ERROR] Failed to load PINN checkpoint: {e}")

    def predict(self, features: List[float]) -> Dict[str, float]:
        """
        Runs real forward pass through trained neural network.
        Features: [heart_rate, skin_temp, work_intensity_met, ambient_temp, relative_humidity, wbgt, time_exposed, prev_core_temp]
        """
        if not self.loaded or self.model is None:
            # First-principles thermodynamic fallback
            hr, skin_t, met, amb_t, rh, wbgt_val, t_exp, prev_t = features
            t_c = prev_t + (met * 0.08 + (amb_t - 37.0) * 0.03 - (100 - rh) * 0.01) * (1.0 / 60.0)
            t_c = max(36.8, min(41.5, t_c))
            psi = 5.0 * (t_c - 37.0) / 2.5 + 5.0 * (hr - 70.0) / 110.0
            psi = max(0.0, min(10.0, psi))
            kidney = 1.0 / (1.0 + math.exp(-0.8 * (psi - 6.5)))
            return {"core_temp": float(round(t_c, 2)), "psi": float(round(psi, 2)), "kidney_risk": float(round(kidney, 3))}

        x = np.array(features, dtype=np.float32)
        x_norm = (x - self.feature_means) / (self.feature_stds + 1e-8)
        
        with torch.no_grad():
            tensor_in = torch.FloatTensor(x_norm).unsqueeze(0)
            output = self.model(tensor_in).squeeze(0).numpy()

        pred_core_temp = float(np.clip(output[0], 36.5, 42.0))
        pred_psi = float(np.clip(output[1], 0.0, 10.0))
        pred_kidney_risk = float(np.clip(output[2], 0.0, 1.0))

        return {
            "core_temp": round(pred_core_temp, 2),
            "psi": round(pred_psi, 2),
            "kidney_risk": round(pred_kidney_risk, 3)
        }


pinn_manager = PINNModelManager()


# === SIMULATED WORKFORCE REGISTRY ===

ROLES = ["Steel Fixer", "Scaffold Specialist", "Concrete Finisher", "Crane Operator", "Welder", "Mason", "MEP Technician", "Site Safety Officer"]
WORKER_NAMES = [
    ("Tariq Al-Mansoor", "ar"), ("Ramesh Kumar", "hi"), ("Muhammad Irfan", "ur"), ("Bilal Sheikh", "ur"),
    ("Sanjay Patel", "hi"), ("Rajesh Pillai", "ml"), ("Deepak Verma", "hi"), ("Hassan Qasim", "ar"),
    ("Omar Farooq", "ar"), ("Manoj Joshi", "hi"), ("Farhan Akhtar", "ur"), ("Anand Varma", "ml"),
    ("Vikram Singh", "hi"), ("Rashid Dar", "ur"), ("Suresh Nair", "ml"), ("Khaled Nabil", "ar"),
    ("Arjun Das", "hi"), ("Zain Abbas", "ur"), ("Dinesh Menon", "ml"), ("Mustafa Zahid", "ar"),
    ("Kishore Shenoy", "hi"), ("Naveen Joseph", "ml"), ("Salim Basha", "ur"), ("Hamad Al-Kaabi", "ar")
]


class WorkerState:
    def __init__(self, idx: int, name: str, lang: str):
        self.worker_id = f"W-{idx+1:05d}"
        self.name = name
        self.lang = lang
        self.role = ROLES[idx % len(ROLES)]
        self.age = random.randint(23, 48)
        self.bmi = round(random.uniform(21.0, 27.5), 1)
        self.acclimatization = round(random.uniform(0.3, 0.9), 2)
        self.baseline_hr = random.randint(58, 74)
        
        # State
        self.heart_rate = float(self.baseline_hr + random.randint(15, 35))
        self.skin_temp = round(35.5 + random.uniform(0.4, 1.6), 2)
        self.core_temp = round(37.2 + random.uniform(0.1, 0.5), 2)
        self.work_intensity_met = round(random.uniform(2.0, 3.5), 1)
        self.time_exposed = round(random.uniform(45.0, 220.0), 0)
        self.hydration_pct = round(random.uniform(70.0, 95.0), 1)
        
        # PINN outputs
        self.psi = 2.5
        self.kidney_risk = 0.08
        self.risk_level = "LOW"
        self.last_updated = datetime.now()


class WorkforceCohort:
    def __init__(self, count=24):
        self.ambient_temp = 41.5
        self.relative_humidity = 58.0
        self.solar_load = 650.0  # W/m2
        self.alerts_today = 14
        self.workers: Dict[str, WorkerState] = {}

        for i in range(min(count, len(WORKER_NAMES))):
            name, lang = WORKER_NAMES[i]
            w = WorkerState(i, name, lang)
            self.workers[w.worker_id] = w

        self.update_all_workers()

    def calculate_wbgt(self) -> float:
        # Simplified outdoor WBGT estimate
        wbgt = 0.7 * (self.ambient_temp * (self.relative_humidity / 100.0) ** 0.5) + 0.2 * (self.ambient_temp + 5) + 0.1 * self.ambient_temp
        return round(wbgt, 1)

    def update_all_workers(self, heat_factor: float = 1.0):
        wbgt_val = self.calculate_wbgt()

        for w in self.workers.values():
            # Thermal load increases HR and skin temp based on acclimatization & BMI
            thermal_load = ((self.ambient_temp - 35.0) / 10.0 + (self.relative_humidity / 100.0)) * heat_factor
            vuln_factor = (1.1 - w.acclimatization) * (w.bmi / 23.0)
            
            w.heart_rate = round(float(np.clip(
                w.baseline_hr + (thermal_load * 32.0 * vuln_factor) + (w.work_intensity_met * 12.0) + random.uniform(-2, 2),
                60.0, 185.0
            )), 1)
            
            w.skin_temp = round(float(np.clip(
                35.0 + (self.ambient_temp - 35.0) * 0.25 * vuln_factor + random.uniform(-0.1, 0.1),
                34.0, 39.5
            )), 2)

            w.hydration_pct = round(max(30.0, w.hydration_pct - (0.35 * heat_factor * (1.2 - w.acclimatization))), 1)
            w.time_exposed += 3.0

            # Execute real PINN prediction
            features = [
                float(w.heart_rate),
                float(w.skin_temp),
                float(w.work_intensity_met),
                float(self.ambient_temp),
                float(self.relative_humidity),
                float(wbgt_val),
                float(w.time_exposed),
                float(w.core_temp)
            ]

            preds = pinn_manager.predict(features)
            w.core_temp = preds["core_temp"]
            w.psi = preds["psi"]
            w.kidney_risk = preds["kidney_risk"]

            # Classify Risk according to Moran & OSHAD standards
            if w.psi >= 7.5 or w.core_temp >= 38.8 or w.kidney_risk >= 0.65:
                w.risk_level = "CRITICAL"
            elif w.psi >= 6.0 or w.core_temp >= 38.3 or w.kidney_risk >= 0.40:
                w.risk_level = "HIGH"
            elif w.psi >= 4.0 or w.core_temp >= 37.8:
                w.risk_level = "MODERATE"
            else:
                w.risk_level = "LOW"

            w.last_updated = datetime.now()

    def trigger_heat_spike(self):
        """Simulates rapid outdoor heat spike (e.g., peak solar noon in ICAD/Musaffah)."""
        self.ambient_temp = min(47.5, round(self.ambient_temp + 3.2, 1))
        self.relative_humidity = min(88.0, round(self.relative_humidity + 10.0, 1))
        self.alerts_today += 5
        self.update_all_workers(heat_factor=1.65)

    def trigger_cooldown(self):
        """Mandatory OSHAD cooling shelter break & rehydration."""
        self.ambient_temp = max(37.0, round(self.ambient_temp - 2.5, 1))
        self.relative_humidity = max(40.0, round(self.relative_humidity - 8.0, 1))
        for w in self.workers.values():
            w.heart_rate = max(w.baseline_hr + 10, w.heart_rate - 22.0)
            w.core_temp = round(max(37.1, w.core_temp - 0.4), 2)
            w.hydration_pct = min(100.0, w.hydration_pct + 18.0)
        self.update_all_workers(heat_factor=0.6)

    def reset_baseline(self):
        self.ambient_temp = 41.5
        self.relative_humidity = 58.0
        for w in self.workers.values():
            w.core_temp = round(37.2 + random.uniform(0.1, 0.4), 2)
            w.heart_rate = float(w.baseline_hr + random.randint(15, 25))
            w.hydration_pct = round(random.uniform(80.0, 95.0), 1)
        self.update_all_workers(heat_factor=1.0)


cohort = WorkforceCohort(24)


def get_oshad_advisory(risk: str, psi: float) -> str:
    if risk == "CRITICAL":
        return "RED ALERT: Immediate work cessation. Move to AC cooling shelter. Administer cold electrolyte fluids. Activate paramedic evaluation for AKI/rhabdomyolysis."
    elif risk == "HIGH":
        return "HIGH RISK: Mandatory 20-min cooling break. Ingest minimum 600ml chilled water. Shift buddy monitoring required under OSHAD CoP 11.0."
    elif risk == "MODERATE":
        return "MODERATE: Shift workload reduction (30 min work / 15 min rest). Hydration check required. Re-evaluate within 20 mins."
    return "NORMAL: Normal work-rest rotation compliant with OSHAD summer threshold. Maintain 250ml water intake every 20 minutes."


# === ENDPOINTS ===

@app.get("/")
async def root():
    return {
        "service": "BioThermal Twin API",
        "status": "operational",
        "pinn_model_loaded": pinn_manager.loaded,
        "pinn_mae": pinn_manager.mae,
        "active_workers": len(cohort.workers),
        "version": "2.0.0"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "pinn_model": {
            "loaded": pinn_manager.loaded,
            "architecture": "PhysicsInformedHeatStrain (17,859 params)",
            "mae_core_temp": f"{pinn_manager.mae}°C",
            "loss_enforcement": "Thermodynamic Gagge Two-Node + Moran Coupling"
        },
        "simulation": {
            "ambient_temp": cohort.ambient_temp,
            "relative_humidity": cohort.relative_humidity,
            "wbgt": cohort.calculate_wbgt(),
            "monitored_workers": len(cohort.workers)
        }
    }


@app.get("/api/dashboard/overview", response_model=DashboardOverview)
async def dashboard_overview():
    """Returns dynamic, live dashboard state computed via PINN inference."""
    worker_statuses = []
    psi_sum = 0.0
    core_temp_sum = 0.0
    counts = {"LOW": 0, "MODERATE": 0, "HIGH": 0, "CRITICAL": 0}

    for w in cohort.workers.values():
        counts[w.risk_level] = counts.get(w.risk_level, 0) + 1
        psi_sum += w.psi
        core_temp_sum += w.core_temp

        status = WorkerStatus(
            worker_id=w.worker_id,
            name=w.name,
            role=w.role,
            age=w.age,
            bmi=w.bmi,
            acclimatization=w.acclimatization,
            heart_rate=w.heart_rate,
            skin_temp=w.skin_temp,
            core_temp_estimate=w.core_temp,
            psi=w.psi,
            kidney_risk=w.kidney_risk,
            risk_level=w.risk_level,
            hydration_pct=w.hydration_pct,
            time_exposed_minutes=w.time_exposed,
            ambient_temp=cohort.ambient_temp,
            relative_humidity=cohort.relative_humidity,
            oshad_advisory=get_oshad_advisory(w.risk_level, w.psi),
            last_updated=w.last_updated
        )
        worker_statuses.append(status)

    total = len(worker_statuses)
    avg_psi = round(psi_sum / max(1, total), 2)
    avg_tc = round(core_temp_sum / max(1, total), 2)

    return DashboardOverview(
        total_workers=total,
        safe_count=counts["LOW"],
        moderate_count=counts["MODERATE"],
        high_risk_count=counts["HIGH"],
        critical_count=counts["CRITICAL"],
        alerts_today=cohort.alerts_today,
        average_psi=avg_psi,
        average_core_temp=avg_tc,
        ambient_temp=cohort.ambient_temp,
        relative_humidity=cohort.relative_humidity,
        pinn_model_status="Active (PyTorch CPU/CUDA)" if pinn_manager.loaded else "Thermodynamic Fallback",
        pinn_mae=pinn_manager.mae,
        workers=worker_statuses
    )


@app.get("/api/workers/{worker_id}/status", response_model=WorkerStatus)
async def get_worker_status(worker_id: str):
    """Retrieve individual worker state and PINN metrics."""
    w = cohort.workers.get(worker_id)
    if not w:
        raise HTTPException(status_code=404, detail=f"Worker {worker_id} not found")

    return WorkerStatus(
        worker_id=w.worker_id,
        name=w.name,
        role=w.role,
        age=w.age,
        bmi=w.bmi,
        acclimatization=w.acclimatization,
        heart_rate=w.heart_rate,
        skin_temp=w.skin_temp,
        core_temp_estimate=w.core_temp,
        psi=w.psi,
        kidney_risk=w.kidney_risk,
        risk_level=w.risk_level,
        hydration_pct=w.hydration_pct,
        time_exposed_minutes=w.time_exposed,
        ambient_temp=cohort.ambient_temp,
        relative_humidity=cohort.relative_humidity,
        oshad_advisory=get_oshad_advisory(w.risk_level, w.psi),
        last_updated=w.last_updated
    )


@app.post("/api/telemetry/ingest")
async def ingest_telemetry(reading: TelemetryReading):
    """Ingest custom telemetry and execute real-time PINN inference."""
    wbgt = reading.wbgt or (0.7 * reading.ambient_temp + 0.3 * (reading.ambient_temp * reading.relative_humidity / 100.0))
    features = [
        reading.heart_rate,
        reading.skin_temp or 36.5,
        reading.work_intensity_met or 2.5,
        reading.ambient_temp,
        reading.relative_humidity,
        wbgt,
        reading.time_exposed_minutes or 120.0,
        reading.prev_core_temp or 37.5
    ]

    preds = pinn_manager.predict(features)
    
    # If worker exists in cohort, update it
    if reading.worker_id in cohort.workers:
        w = cohort.workers[reading.worker_id]
        w.heart_rate = reading.heart_rate
        w.skin_temp = reading.skin_temp or w.skin_temp
        w.core_temp = preds["core_temp"]
        w.psi = preds["psi"]
        w.kidney_risk = preds["kidney_risk"]
        w.last_updated = datetime.now()

    return {
        "status": "ingested_and_inferred",
        "worker_id": reading.worker_id,
        "pinn_inference": preds,
        "risk_level": "CRITICAL" if preds["psi"] >= 7.5 else "HIGH" if preds["psi"] >= 6.0 else "MODERATE" if preds["psi"] >= 4.0 else "LOW",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/simulation/tick")
async def simulation_tick():
    """Advance physiological state and recalculate PINN inference."""
    cohort.update_all_workers(heat_factor=1.05)
    return {"status": "advanced", "ambient_temp": cohort.ambient_temp, "relative_humidity": cohort.relative_humidity}


@app.post("/api/simulation/heat-spike")
async def simulation_heat_spike():
    """Trigger acute heatwave spike."""
    cohort.trigger_heat_spike()
    return {
        "status": "heat_spike_triggered",
        "ambient_temp": cohort.ambient_temp,
        "relative_humidity": cohort.relative_humidity,
        "message": "Ambient temperature raised; at-risk workers elevated by PINN"
    }


@app.post("/api/simulation/cool-down")
async def simulation_cooldown():
    """Trigger cooling station rest & hydration protocol."""
    cohort.trigger_cooldown()
    return {
        "status": "cooling_protocol_active",
        "ambient_temp": cohort.ambient_temp,
        "message": "Workers placed in cooling shelters with electrolyte rehydration"
    }


@app.post("/api/simulation/reset")
async def simulation_reset():
    """Reset to baseline."""
    cohort.reset_baseline()
    return {"status": "reset_to_baseline"}


@app.post("/api/voice-check")
async def voice_check(request: VoiceCheckRequest):
    """
    Multilingual syndromic triage agent (Hindi, Arabic, Urdu, Malayalam, English).
    Performs keyword & syndromic clinical scoring.
    """
    text = (request.text or "").strip().lower()
    
    # Multilingual syndromic lexicon
    dark_urine_keywords = ["dark urine", "brown urine", "black urine", "पेशाब गहरा", "काला पेशाब", "بول داكن", "بول بني", "پیشاب کالا", "മൂത്രം കറുപ്പ്"]
    muscle_cramp_keywords = ["cramp", "muscle cramp", "spasm", "ऐंठन", "मांसपेशी दर्द", "تشنج", "تشنجات", "پٹھوں میں درد", "പേശി വേദന"]
    dizziness_keywords = ["dizzy", "dizziness", "faint", "spinning", "चक्कर", "बेहोश", "دوار", "دوخة", "چکر", "തലകറക്കം"]
    fatigue_keywords = ["fatigue", "exhausted", "tired", "weak", "थकान", "कमजोरी", "تعب", "إرهاق", "تھکن", "ക്ഷീണം"]
    nausea_keywords = ["nausea", "vomit", "sick", "उल्टी", "जी मिचलाना", "غثيان", "التقيؤ", "متلی", "ഛർദ്ദി"]

    has_dark_urine = any(kw in text for kw in dark_urine_keywords)
    has_cramps = any(kw in text for kw in muscle_cramp_keywords)
    has_dizziness = any(kw in text for kw in dizziness_keywords)
    has_nausea = any(kw in text for kw in nausea_keywords)
    
    fatigue_level = "NONE"
    if any(kw in text for kw in fatigue_keywords):
        fatigue_level = "SEVERE" if ("बहुत" in text or "شدید" in text or "severe" in text) else "MODERATE"

    # Symptom risk calculation
    symptom_score = 0.0
    if has_dark_urine: symptom_score += 0.40  # High specificity for AKI / rhabdomyolysis
    if has_cramps: symptom_score += 0.25      # Electrolyte depletion
    if has_dizziness: symptom_score += 0.20   # Hemodynamic compromise
    if has_nausea: symptom_score += 0.15
    if fatigue_level == "SEVERE": symptom_score += 0.20
    elif fatigue_level == "MODERATE": symptom_score += 0.10

    symptom_score = min(1.0, round(symptom_score, 2))

    # Cross-reference with worker's current PINN metrics
    worker = cohort.workers.get(request.worker_id)
    worker_psi = worker.psi if worker else 5.0
    worker_tc = worker.core_temp if worker else 37.8

    # Dual-Signal Fusion Score (Moran PSI + Syndromic Triage)
    dual_signal_alert = False
    clinical_urgency = "ROUTINE"
    
    if worker_psi >= 6.0 and symptom_score >= 0.35:
        dual_signal_alert = True
        clinical_urgency = "IMMEDIATE_INTERVENTION"
    elif worker_psi >= 5.0 or symptom_score >= 0.30:
        clinical_urgency = "OCCUPATIONAL_CLINIC_REVIEW"

    return {
        "worker_id": request.worker_id,
        "input_text": request.text,
        "language_detected": request.language,
        "extracted_symptoms": {
            "dark_urine": has_dark_urine,
            "muscle_cramps": has_cramps,
            "dizziness": has_dizziness,
            "nausea_vomiting": has_nausea,
            "fatigue_grade": fatigue_level
        },
        "syndromic_risk_score": symptom_score,
        "worker_pinn_psi": worker_psi,
        "worker_core_temp": worker_tc,
        "dual_signal_alert": dual_signal_alert,
        "clinical_urgency": clinical_urgency,
        "triage_recommendation": (
            "🚨 CRITICAL DUAL ALERT: High physiological strain + early renal markers detected. Immediate IV/oral rehydration and renal panel required."
            if dual_signal_alert else
            "⚠️ ELEVATED STRAIN: Worker exhibiting syndromic symptoms under heat load. Transfer to shaded hydration point."
            if clinical_urgency == "OCCUPATIONAL_CLINIC_REVIEW" else
            "✅ STABLE: No acute syndromic heat distress detected. Continue scheduled hydration schedule."
        ),
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
