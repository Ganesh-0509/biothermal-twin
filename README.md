# BioThermal Twin
**Physics-Informed Heat Stress Early Warning System**

![Status](https://img.shields.io/badge/status-proof--of--concept-yellow)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 🎯 Overview

BioThermal Twin is an anticipatory occupational health platform that predicts heat stress in extreme-climate workers using physics-informed AI. Unlike reactive systems that respond after collapse, we predict physiological strain 30-60 minutes in advance using thermodynamic modeling and multilingual symptom extraction.

**Built for:** Future Health Digital Innovation Challenge 2026 (Abu Dhabi DoH + M42 + MBZUAI)

---

## 🚀 Key Features

- **Physics-Informed Neural Network (PINN):** Predicts core body temperature while respecting thermodynamic energy conservation laws
- **Thermodynamic Simulation:** Gagge Two-Node heat balance model with individual worker variability
- **Multilingual Voice Triage:** Symptom extraction in Hindi and Arabic using Whisper + LLM
- **Real-Time Monitoring:** Dashboard tracking 100+ workers with live PSI/temperature trends
- **Dual-Signal Alerts:** Combined physiological (PSI > 7.0) and symptomatic validation to reduce false alarms

---

## 🏗️ System Architecture

```
Simulation Layer (Gagge Thermodynamics)
          ↓
   PINN Prediction Engine
          ↓
    FastAPI Backend ← Voice Pipeline (Whisper + LLM)
          ↓
   Next.js Dashboard
```

**Tech Stack:**
- **Backend:** FastAPI, PostgreSQL, PyTorch
- **Frontend:** Next.js 14, Tailwind CSS, shadcn/ui, Recharts
- **AI:** PyTorch PINN, Faster-Whisper, GPT-4o-mini / Med42
- **Deployment:** Render (backend), Vercel (frontend)

---

## 📦 Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- CUDA-capable GPU (recommended, 2GB+ VRAM)
- PostgreSQL 14+

### Backend Setup

```bash
# Clone repository
git clone https://github.com/Ganesh-0509/biothermal-twin.git
cd biothermal-twin

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your OpenAI API key and database URL

# Run database migrations
python backend/database/migrate.py

# Start backend server
cd backend
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

**Access:**
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

---

## 🧪 Running the Simulation

```bash
# Generate synthetic data (100 workers, 8-hour shifts)
python core/data_generator.py

# Train PINN model
python models/train_pinn.py

# Run live simulation (streams to API)
python simulation/run_live_demo.py
```

---

## 📊 Validation & Metrics

All reported metrics are **measured from actual system runs**, not fabricated:

- **PINN Accuracy:** See `results/pinn_validation.json` for real MAE/RMSE
- **Voice Pipeline:** See `results/voice_pipeline_results.json` for WER measurements  
- **API Latency:** See `results/api_latency.json` for p50/p95/p99
- **System Tests:** Run `pytest tests/ -v`

**Read:** [VALIDATION-PLAN.md](./VALIDATION-PLAN.md) for our measurement methodology.

---

## 📖 Documentation

- [PRD.md](./PRD.md) - Product Requirements & Scope
- [TECHNICAL-ARCHITECTURE.md](./TECHNICAL-ARCHITECTURE.md) - System Design
- [BUILD-TIMELINE.md](./BUILD-TIMELINE.md) - 72-Hour Development Plan
- [VALIDATION-PLAN.md](./VALIDATION-PLAN.md) - Testing & Metrics Framework

---

## 🎬 Demo

**Video:** [3-minute demo on YouTube](#) *(link after recording)*

**Live Prototype:**
- Frontend: https://biothermal-twin.vercel.app
- Backend API: https://biothermal-twin.onrender.com

---

## 🔬 Scientific Basis

### Thermodynamic Heat Balance (Gagge Two-Node Model)

```
S = M - W ± R ± C - E

Where:
S = Heat storage (W/m²)
M = Metabolic heat production
R = Radiative exchange
C = Convective exchange
E = Evaporative cooling
```

### Physiological Strain Index (Moran et al. 1998)

```
PSI = 5·(Tc - Tc0)/(39.5 - Tc0) + 5·(HR - HR0)/(180 - HR0)

Where:
Tc = Core temperature (°C)
HR = Heart rate (bpm)
Subscript 0 = Baseline values
```

**References:**
- Gagge et al. (1971). "A two node model of human temperature regulation"
- Moran et al. (1998). "A physiological strain index to evaluate heat stress." PMID: 9688970
- ISO 9886:2004 - Ergonomics — Evaluation of thermal strain

---

## ⚠️ Limitations & Future Work

**Current Status:** Proof-of-concept with simulated data

**Known Limitations:**
- Uses synthetic data (no real workers or wearable sensors)
- Not clinically validated (requires IRB-approved trials)
- Hindi/Arabic only (not full 6-language coverage)
- Med42 integration pending API access
- Not a medical device (no regulatory approval)

**Deployment Roadmap:**
1. **Phase 1 (Months 1-2):** Real BLE wearable integration
2. **Phase 2 (Months 3-6):** Clinical validation with M42/ADPHC partnership
3. **Phase 3 (Months 7-12):** Medical device certification (ISO 13485, ADPHC registration)
4. **Phase 4 (Months 13-18):** Malaffi HIE integration, multi-site deployment

---

## 👤 Author

**Ganesh Kumar T**
- Email: ganesh957kumar@gmail.com
- GitHub: [@Ganesh-0509](https://github.com/Ganesh-0509)
- LinkedIn: [ganesh-kumar-957t](https://linkedin.com/in/ganesh-kumar-957t)

---

## 📄 License

MIT License - See [LICENSE](./LICENSE) for details

---

## 🙏 Acknowledgments

- Abu Dhabi Department of Health (ADPHC) for OSHAD standards
- M42 Health for Med42 clinical LLM
- MBZUAI for AI research foundations
- Published research on occupational heat stress and CKDu epidemic

---

## 🔗 Links

- **Hackathon:** [Future Health Digital Innovation Challenge 2026](https://hack2skill.com/event/futurehealthchallenge/)
- **Submission Date:** November 20, 2026
- **Track:** Population & Workforce Health Early Warning

---

**Built with precision. Validated with rigor. Deployed with honesty.**
