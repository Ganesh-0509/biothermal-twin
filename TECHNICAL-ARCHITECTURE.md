# Technical Architecture: BioThermal Twin
## System Design & Implementation Specifications

**Version:** 1.0  
**Date:** November 16, 2026  
**Hardware:** NVIDIA MX550 (2GB VRAM), Windows 11, Python 3.10+, Node.js 18+

---

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                  TIER 1: SIMULATION LAYER                       │
│  ┌──────────────────────┐  ┌───────────────────────────────┐   │
│  │  Worker Physiology   │  │  Environment Simulator        │   │
│  │  (Gagge Model)       │  │  (Abu Dhabi Conditions)       │   │
│  │  - Core Temp        │  │  - Ambient Temp: 38-47°C     │   │
│  │  - Heart Rate       │  │  - Humidity: 45-85%          │   │
│  │  - Sweat Rate       │  │  - Solar Load: 700-950 W/m²  │   │
│  │  - Kidney Stress    │  │  - WBGT calculation          │   │
│  └──────────┬───────────┘  └───────────────┬───────────────┘   │
└─────────────┼──────────────────────────────┼───────────────────┘
              │                              │
              └──────────────┬───────────────┘
                             │
         ┌───────────────────▼──────────────────────┐
         │     SYNTHETIC DATA GENERATOR              │
         │  - 100 Workers × 8 Hours = 48,000 points │
         │  - Individual variability (age/BMI/accl) │
         │  - Export: CSV, JSON, SQL                │
         └───────────────────┬──────────────────────┘
                             │
    ┌────────────────────────┼────────────────────────┐
    │                        │                        │
    ▼                        ▼                        ▼
┌───────────┐      ┌─────────────────┐      ┌────────────────┐
│  PINN     │      │  Voice Pipeline │      │  FastAPI       │
│  Training │      │  (Whisper+LLM)  │      │  Backend       │
│           │      │                 │      │                │
│  Input:   │      │  Audio → Text   │      │  Endpoints:    │
│  HR,      │      │  Text → JSON    │      │  /ingest       │
│  Cadence, │      │  (symptoms)     │      │  /workers/{id} │
│  Ambient  │      │                 │      │  /voice-check  │
│           │      │  Languages:     │      │  /dashboard    │
│  Output:  │      │  - Hindi        │      │                │
│  Core     │      │  - Arabic       │      │  Database:     │
│  Temp,    │      │                 │      │  PostgreSQL    │
│  PSI,     │      │                 │      │  (Render)      │
│  Risk     │      │                 │      │                │
└─────┬─────┘      └────────┬────────┘      └───────┬────────┘
      │                     │                       │
      │                     │                       │
      └─────────────────────┴───────────────────────┘
                            │
                ┌───────────▼──────────┐
                │   Next.js Dashboard   │
                │   (Vercel Deploy)     │
                │                       │
                │  - Worker Grid (100)  │
                │  - PSI/Temp Charts    │
                │  - Alert Feed         │
                │  - Voice Check-ins    │
                └───────────────────────┘
```

---

## 2. Component Specifications

### 2.1 Physics Simulation Engine

**File:** `core/worker_simulation.py`

**Class: `WorkerPhysiology`**

```python
# Thermodynamic state variables
core_temp: float          # 35.0 - 42.0°C (viable range)
skin_temp: float          # 30.0 - 37.0°C
heart_rate: float         # baseline + thermal load
sweat_rate: float         # 0.0 - 2.5 L/hr (physiological max)
hydration_status: float   # 1.0 (fully hydrated) to 0.0 (severe dehydration)

# Individual factors
age: int                  # 22-45 years
bmi: float                # 20-28 kg/m²
acclimatization: float    # 0.0 (non-acclimatized) to 1.0 (full acclimatization)
baseline_hr: int          # Resting heart rate (55-75 bpm)

# Metabolic factors
metabolic_rate: float     # 1.0 (resting) to 5.0 (heavy work) met units
work_intensity: float     # Dynamic based on time of day
```

**Heat Balance Equation (Simplified Gagge):**

```
S = M - W ± R ± C - E

Where:
S = Rate of body heat storage (W/m²)
M = Metabolic heat production = f(work_intensity, body_mass)
W = External work (negligible for most tasks, ~0)
R = Radiative heat exchange = σε[(T_mrt + 273)⁴ - (T_skin + 273)⁴]
C = Convective heat exchange = h_c × (T_ambient - T_skin)
E = Evaporative cooling = min(sweat_rate × 2430 kJ/L, E_max)

E_max = Maximum evaporative capacity, limited by:
  - Vapor pressure gradient (ambient humidity)
  - Air velocity
  - Skin wettedness
```

**Update Step (1-minute resolution):**

```python
def update_step(self, ambient_temp, humidity, solar_load, work_intensity, dt=60):
    """
    One timestep of thermodynamic simulation
    
    Args:
        ambient_temp: °C
        humidity: % (0-100)
        solar_load: W/m²
        work_intensity: met units (1.0-5.0)
        dt: seconds (default 60 for 1-minute steps)
    
    Returns:
        dict with core_temp, heart_rate, psi, kidney_stress, etc.
    """
    # 1. Calculate heat fluxes
    M = self._metabolic_heat(work_intensity)
    R = self._radiative_heat(ambient_temp, solar_load)
    C = self._convective_heat(ambient_temp)
    E_max = self._max_evaporative_cooling(ambient_temp, humidity)
    E_actual = min(self.sweat_rate * 2430, E_max)
    
    # 2. Net heat storage
    S = M + R + C - E_actual  # W/m²
    
    # 3. Update core temperature (thermodynamic integration)
    heat_capacity = 3.5  # kJ/(kg·°C) for human body
    body_mass = self._estimate_body_mass()  # from BMI
    body_surface_area = 1.8  # m² (average adult)
    
    # Heat storage in Joules = S (W/m²) × area (m²) × time (s)
    heat_stored = S * body_surface_area * dt
    
    # Temperature change = heat / (mass × heat_capacity)
    temp_change = heat_stored / (body_mass * heat_capacity * 1000)
    
    self.core_temp += temp_change
    
    # 4. Physiological responses
    self.heart_rate = self._calculate_heart_rate()  # Increases with temp
    self.sweat_rate = self._calculate_sweat_rate()  # Increases with temp, limited by hydration
    self.hydration_status -= (self.sweat_rate * dt / 3600) / 5.0  # Dehydration
    
    # 5. Kidney stress index
    kidney_stress = self._calculate_renal_hypoperfusion()
    
    # 6. PSI (Moran 1998)
    psi = 5 * ((self.core_temp - 37.0) / (39.5 - 37.0)) + \
          5 * ((self.heart_rate - self.baseline_hr) / (180 - self.baseline_hr))
    psi = max(0, min(10, psi))  # Clamp to [0, 10]
    
    return {
        'core_temp': self.core_temp,
        'skin_temp': self.skin_temp,
        'heart_rate': self.heart_rate,
        'sweat_rate': self.sweat_rate,
        'hydration': self.hydration_status,
        'psi': psi,
        'kidney_stress': kidney_stress,
        'metabolic_rate': M
    }
```

**Validation Targets (from literature):**
- Core temp range: 36.5-38.5°C (normal), 38.5-40°C (heat exhaustion), >40°C (heatstroke)
- HR increase: +40-80 bpm above baseline under heat stress
- Sweat rate: 0.5-1.5 L/hr (typical), up to 2.5 L/hr (max physiological)
- PSI: 0-2 (no strain), 3-4 (low), 5-6 (moderate), 7-8 (high), 9-10 (extreme)

---

### 2.2 PINN Model Architecture

**File:** `models/pinn_core_temp.py`

**Input Features (8 dimensions):**
```python
[
    heart_rate,          # Current HR (bpm)
    heart_rate_baseline, # Resting HR (bpm)
    cadence,             # Steps per minute (0-120)
    ambient_temp,        # °C
    relative_humidity,   # % (0-100)
    solar_load,          # W/m² (0-1000)
    time_exposed,        # Minutes in heat (0-480)
    prev_core_temp       # Previous timestep core temp (°C)
]
```

**Output (3 dimensions):**
```python
[
    core_temp_estimate,  # °C (35-42 range)
    psi_estimate,        # 0-10 scale
    kidney_risk_score    # 0-1 probability
]
```

**Network Architecture:**
```
Input (8) → Dense(64, Tanh) → Dense(128, Tanh) → Dense(64, Tanh) → Output(3)

Total params: ~10,000 (fits easily in MX550 2GB VRAM)
```

**Why Tanh over ReLU:**
- Tanh outputs are bounded (-1, 1), better for physics constraints
- ReLU can explode to infinity, violating biological bounds
- Tanh gradient is smooth, helps physics loss convergence

**Custom Physics Loss Function:**

```python
def physics_loss(pred, inputs, targets, lambda_boundary=0.5, lambda_physics=0.3):
    """
    L_total = L_MSE + λ1·L_boundary + λ2·L_physics
    """
    pred_core_temp = pred[:, 0]
    pred_psi = pred[:, 1]
    
    # Standard data-fitting loss
    mse_loss = F.mse_loss(pred, targets)
    
    # Physics Constraint 1: Biological boundary enforcement
    # Penalize predictions outside viable core temp range
    boundary_loss = torch.relu(pred_core_temp - 42.0).mean() + \
                   torch.relu(35.0 - pred_core_temp).mean()
    
    # Physics Constraint 2: PSI-Temperature coupling
    # PSI must correlate with thermal load (from Moran formula)
    hr = inputs[:, 0]
    hr_baseline = inputs[:, 1]
    expected_psi = 5 * ((pred_core_temp - 37.0) / 2.5) + \
                  5 * ((hr - hr_baseline) / (180 - hr_baseline))
    expected_psi = torch.clamp(expected_psi, 0, 10)
    
    physics_coupling_loss = F.mse_loss(pred_psi, expected_psi)
    
    # Physics Constraint 3: Energy conservation check
    # If ambient < core temp and no metabolic heat, core temp should decrease
    # (simplified version - full version requires time-series PINN)
    
    # Combined loss
    total_loss = mse_loss + \
                lambda_boundary * boundary_loss + \
                lambda_physics * physics_coupling_loss
    
    return total_loss, {
        'mse': mse_loss.item(),
        'boundary': boundary_loss.item(),
        'physics': physics_coupling_loss.item()
    }
```

**Training Procedure:**
1. Generate 50,000 simulated worker-minutes (100 workers × 8h × 60min + validation)
2. Train/val split: 80/20 (40,000 train, 10,000 val)
3. Optimizer: Adam, lr=0.001
4. Batch size: 32 (fits in 2GB VRAM)
5. Epochs: 100-200 (with early stopping)
6. Track: MSE loss, physics loss components, validation MAE

**Success Metrics (HONEST):**
- Report ACTUAL validation MAE (Mean Absolute Error) in °C
- Show physics loss convergence (proves constraints are satisfied)
- Don't claim "±0.18°C" unless we actually measure it

---

### 2.3 Voice Symptom Extraction Pipeline

**File:** `voice/symptom_extractor.py`

**Component A: Speech-to-Text (Whisper)**

```python
# Use local Whisper (not OpenAI API) to save costs
# Model: whisper-tiny or whisper-base (fits in 2GB VRAM)

from faster_whisper import WhisperModel

model = WhisperModel("base", device="cuda", compute_type="float16")

def transcribe_audio(audio_path, language=None):
    """
    Args:
        audio_path: Path to audio file (WAV, MP3)
        language: 'hi' (Hindi), 'ar' (Arabic), or None (auto-detect)
    
    Returns:
        {
            'text': "मुझे चक्कर आ रहा है",  # transcription
            'language': 'hi',
            'confidence': 0.92
        }
    """
    segments, info = model.transcribe(audio_path, language=language)
    
    text = " ".join([segment.text for segment in segments])
    
    return {
        'text': text,
        'language': info.language,
        'confidence': info.language_probability
    }
```

**Component B: Symptom Extraction (LLM)**

Option 1: GPT-4o-mini (fallback if Med42 fails)
```python
import openai

def extract_symptoms_gpt(transcription, language):
    prompt = f"""You are a medical triage assistant for occupational heat stress.

Worker statement ({language}): "{transcription}"

Extract these symptoms:
1. Dark urine or reduced urination: YES/NO
2. Muscle cramps or twitching: YES/NO
3. Dizziness or confusion: YES/NO
4. Severe fatigue: NONE/MILD/MODERATE/SEVERE
5. Headache: YES/NO

Return ONLY valid JSON, no other text:
{{"dark_urine": bool, "muscle_cramps": bool, "dizziness": bool, "fatigue": "NONE|MILD|MODERATE|SEVERE", "headache": bool, "risk_score": float}}"""

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,  # Low temp for consistent structured output
        max_tokens=150
    )
    
    return json.loads(response.choices[0].message.content)
```

Option 2: Med42 (if we can load quantized 8B model)
```python
from transformers import AutoTokenizer, AutoModelForCausalLM

tokenizer = AutoTokenizer.from_pretrained("m42-health/med42-v2-8b")
model = AutoModelForCausalLM.from_pretrained(
    "m42-health/med42-v2-8b",
    device_map="auto",
    load_in_4bit=True,  # Quantization to fit in 2GB VRAM
    torch_dtype=torch.float16
)

# Same prompt structure as GPT-4o-mini
```

**Supported Languages:**
- Hindi (hi): Primary migrant worker language in UAE
- Arabic (ar): Local language
- (Future: Urdu, Malayalam, Tagalog)

**Output Schema:**
```json
{
  "worker_id": "W-00042",
  "timestamp": "2026-11-16T14:32:00Z",
  "transcription": "मुझे बहुत थकान है और चक्कर आ रहा है",
  "language": "hi",
  "symptoms": {
    "dark_urine": false,
    "muscle_cramps": false,
    "dizziness": true,
    "fatigue": "SEVERE",
    "headache": false
  },
  "risk_score": 0.72,
  "requires_medical_attention": true
}
```

---

### 2.4 Backend API (FastAPI)

**File:** `backend/main.py`

**Database Schema (PostgreSQL):**

```sql
-- Worker registry
CREATE TABLE workers (
    id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100),
    age INTEGER,
    baseline_hr INTEGER,
    acclimatization_level FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Telemetry time-series
CREATE TABLE telemetry (
    id SERIAL PRIMARY KEY,
    worker_id VARCHAR(20) REFERENCES workers(id),
    timestamp TIMESTAMPTZ NOT NULL,
    heart_rate INTEGER,
    cadence INTEGER,
    ambient_temp FLOAT,
    humidity FLOAT,
    solar_load FLOAT,
    core_temp_estimate FLOAT,
    psi FLOAT,
    kidney_risk FLOAT,
    INDEX idx_worker_time (worker_id, timestamp DESC)
);

-- Voice assessments
CREATE TABLE voice_checks (
    id SERIAL PRIMARY KEY,
    worker_id VARCHAR(20) REFERENCES workers(id),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    transcription TEXT,
    language VARCHAR(10),
    symptoms JSONB,
    risk_score FLOAT
);

-- Alerts
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    worker_id VARCHAR(20) REFERENCES workers(id),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    alert_type VARCHAR(50),  -- 'HIGH_PSI', 'VOICE_SYMPTOMS', 'COMBINED'
    severity VARCHAR(20),     -- 'WARNING', 'CRITICAL'
    message TEXT,
    acknowledged BOOLEAN DEFAULT FALSE
);
```

**API Endpoints:**

```python
@app.post("/api/telemetry/ingest")
async def ingest_telemetry(batch: List[TelemetryReading]):
    """
    Ingests batch of telemetry readings, runs PINN prediction, generates alerts
    
    Body:
    [
      {
        "worker_id": "W-00001",
        "timestamp": "2026-11-16T14:00:00Z",
        "heart_rate": 125,
        "cadence": 45,
        "ambient_temp": 45.2,
        "humidity": 68,
        "solar_load": 890
      },
      ...
    ]
    
    Returns: {"ingested": 100, "alerts_generated": 3}
    """
    pass

@app.get("/api/workers/{worker_id}/status")
async def get_worker_status(worker_id: str):
    """
    Returns current physiological state
    
    Response:
    {
      "worker_id": "W-00001",
      "current_state": {
        "core_temp_estimate": 38.2,
        "psi": 7.4,
        "heart_rate": 125,
        "risk_level": "HIGH"
      },
      "recent_history": [...],  # Last 60 minutes
      "voice_checks": [...]     # Recent voice assessments
    }
    """
    pass

@app.post("/api/voice-check")
async def voice_check(audio: UploadFile, worker_id: str):
    """
    Processes voice symptom check
    
    1. Save audio file
    2. Transcribe with Whisper
    3. Extract symptoms with LLM
    4. Store in database
    5. Check if alert needed
    
    Returns: symptom extraction JSON
    """
    pass

@app.get("/api/dashboard/overview")
async def dashboard_overview():
    """
    Powers live dashboard
    
    Response:
    {
      "total_workers": 100,
      "high_risk_count": 8,
      "alerts_today": 23,
      "average_psi": 4.2,
      "workers": [...]  # All workers with latest state
    }
    """
    pass
```

**Deployment:** Render.com free tier (PostgreSQL + FastAPI)

---

### 2.5 Frontend Dashboard (Next.js)

**File:** `frontend/app/page.tsx`

**Tech Stack:**
- Next.js 14 (App Router)
- Tailwind CSS
- shadcn/ui components
- Recharts for data visualization
- SWR for data fetching (2-second poll)

**Layout:**

```
┌────────────────────────────────────────────────────────────┐
│  BioThermal Twin Dashboard                    [Refresh ⟳] │
├────────────────────────────────────────────────────────────┤
│  Stats Row:                                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │ Workers  │ │ High Risk│ │ Alerts   │ │ Avg PSI  │    │
│  │   100    │ │    8     │ │   23     │ │   4.2    │    │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │
├────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐  ┌────────────────────────────┐ │
│  │  Worker Grid        │  │  Worker Detail             │ │
│  │  [100 cards,        │  │  [Click worker to see:     │ │
│  │   color-coded by    │  │   - PSI/temp chart         │ │
│  │   risk level]       │  │   - Voice check-ins        │ │
│  │                     │  │   - Alert history]         │ │
│  │  🟢 Low (PSI<5)     │  │                            │ │
│  │  🟡 Moderate (5-7)  │  │                            │ │
│  │  🔴 High (>7)       │  │                            │ │
│  └─────────────────────┘  └────────────────────────────┘ │
├────────────────────────────────────────────────────────────┤
│  Real-Time Alert Feed:                                     │
│  🔴 14:32 | W-00042 | PSI 8.2 + Voice symptoms detected  │
│  🟡 14:28 | W-00015 | PSI 7.1 (no voice symptoms)        │
│  🔴 14:15 | W-00089 | Voice: severe fatigue + dizziness  │
└────────────────────────────────────────────────────────────┘
```

**Key Features:**
- Auto-refresh every 2 seconds via SWR polling
- Color-coded worker cards (green/yellow/red)
- Click worker → detail panel slides in
- Recharts line chart for PSI/temp trends
- Voice check-in history with transcriptions
- Alert feed with timestamps

**Deployment:** Vercel (automatic from GitHub push)

---

## 3. Development Timeline (72 Hours)

See `BUILD-TIMELINE.md` for detailed hour-by-hour plan.

**Day 1 (24h):** Simulation + PINN training  
**Day 2 (24h):** Backend API + Voice pipeline  
**Day 3 (24h):** Frontend + Demo video + Submission

---

## 4. Testing & Validation

### 4.1 Simulation Validation
```python
# tests/test_simulation.py
def test_core_temp_stays_in_bounds():
    worker = WorkerPhysiology(...)
    for _ in range(480):  # 8 hours
        state = worker.update_step(45, 65, 900, 3.0)
        assert 35 < state['core_temp'] < 42, "Core temp out of viable range"

def test_psi_increases_with_heat():
    worker = WorkerPhysiology(...)
    psi_values = []
    for temp in [38, 40, 42, 44, 46]:
        state = worker.update_step(temp, 60, 850, 3.0)
        psi_values.append(state['psi'])
    assert psi_values == sorted(psi_values), "PSI should increase with ambient temp"
```

### 4.2 PINN Validation
```python
# tests/test_pinn.py
def test_pinn_respects_physics():
    model = load_trained_pinn()
    
    # Test case: If ambient temp drops, core temp should stabilize/drop
    for t in range(100):
        pred = model.predict([70, 65, 0, 45-t*0.1, 50, 800, t, 37.5])
        # Core temp should not keep rising when environment cools
        assert pred['core_temp'] < 39.0
```

### 4.3 End-to-End Test
```python
# tests/test_e2e.py
async def test_full_pipeline():
    # 1. Start simulation
    worker = WorkerPhysiology(...)
    
    # 2. Send telemetry to API
    response = await api_client.post('/api/telemetry/ingest', data)
    assert response.status_code == 200
    
    # 3. Check dashboard updates
    overview = await api_client.get('/api/dashboard/overview')
    assert overview['total_workers'] == 100
    
    # 4. Verify alert generation
    alerts = await db.query("SELECT * FROM alerts WHERE worker_id = 'W-00042'")
    assert len(alerts) > 0
```

---

## 5. Deployment Checklist

- [ ] Backend deployed to Render (PostgreSQL + FastAPI)
- [ ] Frontend deployed to Vercel
- [ ] Environment variables configured
- [ ] Database migrations run
- [ ] PINN model checkpoint uploaded
- [ ] Whisper model downloaded
- [ ] API documentation accessible at `/docs`
- [ ] CORS enabled for frontend → backend
- [ ] Health check endpoint responding

---

**Next Document:** `MODEL-SPECIFICATION.md` (PINN training details)
