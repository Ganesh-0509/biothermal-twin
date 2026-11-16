# 72-Hour Build Timeline: BioThermal Twin
## Minute-by-Minute Execution Plan

**Start:** November 16, 2026, 11:30 AM IST  
**Deadline:** November 19, 2026, 11:59 PM IST (Submit Nov 20)  
**Total Time:** 72 hours (realistically ~60 hours with breaks)

---

## ⏰ DAY 1: November 16 (Simulation + PINN)

### **Hours 0-4: Setup & Environment** ✅
**Timeline:** 11:30 AM - 3:30 PM

- [x] ✅ Create planning documents (PRD, Architecture) - DONE
- [ ] Set up GitHub repo (no Claude attribution)
- [ ] Create project structure (`core/`, `models/`, `backend/`, `frontend/`, `tests/`)
- [ ] Install dependencies:
  ```bash
  # Python environment
  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
  pip install fastapi uvicorn sqlalchemy psycopg2-binary
  pip install faster-whisper openai transformers
  pip install numpy pandas scipy matplotlib
  pip install pytest black
  
  # Node.js environment
  cd frontend
  npm install next@latest react@latest react-dom@latest
  npm install @shadcn/ui tailwindcss recharts swr
  ```
- [ ] Verify GPU works with PyTorch
- [ ] Create `.env` file with OpenAI API key

**Deliverable:** Working development environment

---

### **Hours 4-10: Physics Simulation Engine** 
**Timeline:** 3:30 PM - 9:30 PM

#### Hour 4-6: Core Worker Model
- [ ] `core/worker_simulation.py` - WorkerPhysiology class
  - [ ] Init: core_temp, HR, sweat_rate, hydration, age, BMI, acclimatization
  - [ ] `_metabolic_heat()`: Calculate M from work intensity
  - [ ] `_radiative_heat()`: Calculate R from ambient temp + solar load
  - [ ] `_convective_heat()`: Calculate C from ambient temp
  - [ ] `_max_evaporative_cooling()`: Calculate E_max from humidity
  - [ ] `_calculate_heart_rate()`: HR response to thermal load
  - [ ] `_calculate_sweat_rate()`: Sweat response (limited by hydration)
  - [ ] `_calculate_psi()`: Moran 1998 formula
  - [ ] `update_step()`: Main thermodynamic integration loop

#### Hour 6-8: Environment Simulator
- [ ] `core/environment.py` - SiteEnvironment class
  - [ ] Scenario presets: normal, extreme_heat, humidity_spike
  - [ ] `get_conditions_at_time()`: Diurnal variation (cooler morning, peak 2 PM)
  - [ ] `_calculate_wbgt()`: Wet Bulb Globe Temperature formula
  - [ ] Solar radiation curve (sunrise 6 AM, peak noon, sunset 7 PM)

#### Hour 8-10: Validation & Data Generation
- [ ] `tests/test_simulation.py`
  - [ ] Test: Core temp stays in viable range (35-42°C)
  - [ ] Test: PSI increases with heat load
  - [ ] Test: Sweat rate doesn't exceed 2.5 L/hr
  - [ ] Test: Hydration depletes over time
- [ ] `core/data_generator.py`
  - [ ] Generate 100 workers with individual variability
  - [ ] Run 8-hour shifts (480 minutes)
  - [ ] Export CSV: `data/synthetic_telemetry.csv` (48,000 rows)
  - [ ] Export JSON: `data/worker_profiles.json`

**Deliverable:** 48,000 synthetic data points, validated simulation

---

### **Hours 10-14: Dinner Break + PINN Training Prep**
**Timeline:** 9:30 PM - 1:30 AM (includes 1h dinner)

#### Hour 10-11: Dinner Break
- [ ] Eat, rest, review progress

#### Hour 11-14: PINN Model Development
- [ ] `models/pinn_core_temp.py`
  - [ ] Define network: Input(8) → Dense(64) → Dense(128) → Dense(64) → Output(3)
  - [ ] Custom `PhysicsInformedLoss` class
    - [ ] MSE loss (data fitting)
    - [ ] Boundary penalty (35-42°C constraint)
    - [ ] PSI-temperature coupling loss
  - [ ] Training loop with loss tracking
  - [ ] Save best checkpoint
- [ ] `models/train_pinn.py`
  - [ ] Load synthetic data
  - [ ] Train/val split (80/20)
  - [ ] Normalize inputs
  - [ ] Train for 100-200 epochs
  - [ ] Early stopping on validation loss
  - [ ] Save model: `models/checkpoints/pinn_best.pt`

**Sleep:** 1:30 AM - 7:30 AM (6 hours)

---

### **Hours 14-18: PINN Training & Evaluation**
**Timeline:** 7:30 AM - 11:30 AM (Nov 17)

- [ ] Run training (should take ~2-3 hours on MX550)
- [ ] Monitor loss curves, ensure physics loss converges
- [ ] Evaluate on validation set:
  - [ ] Calculate MAE, RMSE, R² for core temp predictions
  - [ ] **RECORD ACTUAL NUMBERS** (don't fabricate)
- [ ] Generate plots:
  - [ ] Training curves (MSE, boundary, physics loss)
  - [ ] Validation predictions vs. ground truth
  - [ ] Residual plot
- [ ] Save results: `results/pinn_validation.json`

**Deliverable:** Trained PINN with measured accuracy metrics

---

## ⏰ DAY 2: November 17 (Backend + Voice)

### **Hours 18-22: Backend API Development**
**Timeline:** 11:30 AM - 3:30 PM

#### Hour 18-20: Database Setup
- [ ] Set up PostgreSQL (local or Render)
- [ ] `backend/database.py` - SQLAlchemy models
  - [ ] Worker, Telemetry, VoiceCheck, Alert tables
  - [ ] Database connection pool
  - [ ] Migration scripts
- [ ] Seed database with 100 worker profiles

#### Hour 20-22: FastAPI Application
- [ ] `backend/main.py`
  - [ ] `POST /api/telemetry/ingest`
    - [ ] Receive batch of telemetry
    - [ ] Run PINN prediction for each reading
    - [ ] Store in database
    - [ ] Generate alerts if PSI > 7.0
  - [ ] `GET /api/workers/{id}/status`
    - [ ] Fetch latest telemetry
    - [ ] Return current state + 60-min history
  - [ ] `GET /api/dashboard/overview`
    - [ ] Aggregate stats (total workers, high risk count, avg PSI)
    - [ ] Return all workers with latest state
  - [ ] Health check endpoint: `GET /health`
- [ ] Test locally with Postman/curl

**Deliverable:** Working FastAPI backend with PINN integration

---

### **Hours 22-26: Lunch Break + Voice Pipeline**
**Timeline:** 3:30 PM - 7:30 PM (includes 1h lunch)

#### Hour 22-23: Lunch Break
- [ ] Eat, rest

#### Hour 23-26: Voice Symptom Extraction
- [ ] `voice/symptom_extractor.py`
  - [ ] Set up Whisper (faster-whisper, base model)
  - [ ] `transcribe_audio()` function
    - [ ] Support Hindi, Arabic
    - [ ] Return transcription + language + confidence
  - [ ] Set up LLM (GPT-4o-mini as primary, Med42 if possible)
  - [ ] `extract_symptoms()` function
    - [ ] Structured prompt for symptom extraction
    - [ ] Parse JSON response
    - [ ] Return: dark_urine, muscle_cramps, dizziness, fatigue, headache, risk_score
- [ ] Test with sample audio files:
  - [ ] Record 5 test cases in Hindi
  - [ ] Record 5 test cases in Arabic
  - [ ] Measure transcription accuracy
  - [ ] Measure symptom extraction accuracy

**Deliverable:** Working voice pipeline with measured accuracy

---

### **Hours 26-30: Backend Voice Integration**
**Timeline:** 7:30 PM - 11:30 PM

- [ ] `backend/main.py` - Add voice endpoint
  - [ ] `POST /api/voice-check`
    - [ ] Accept audio upload + worker_id
    - [ ] Save audio file temporarily
    - [ ] Call transcribe_audio()
    - [ ] Call extract_symptoms()
    - [ ] Store in voice_checks table
    - [ ] Check if combined with PSI > 7.0 → generate alert
    - [ ] Return symptom extraction
- [ ] `backend/alert_generator.py`
  - [ ] Dual-signal alert logic:
    - [ ] HIGH_PSI: PSI > 7.0 only
    - [ ] VOICE_SYMPTOMS: High-risk symptoms only
    - [ ] COMBINED: Both PSI > 7.0 AND symptoms → CRITICAL
  - [ ] Alert severity classification
- [ ] Test end-to-end:
  - [ ] Send telemetry → check PSI calculation
  - [ ] Send voice check → check symptom extraction
  - [ ] Verify combined alert fires

**Deliverable:** Backend with voice integration + alert system

---

### **Hours 30-34: Backend Deployment**
**Timeline:** 11:30 PM - 3:30 AM (Nov 18)

- [ ] Create `backend/Dockerfile`
- [ ] Create `backend/requirements.txt`
- [ ] Deploy to Render:
  - [ ] Create PostgreSQL database
  - [ ] Deploy FastAPI web service
  - [ ] Configure environment variables
  - [ ] Run database migrations
  - [ ] Upload PINN model checkpoint
- [ ] Test deployed API with Postman
- [ ] Verify `/health` endpoint responds
- [ ] Load test with 100 concurrent requests

**Sleep:** 3:30 AM - 9:30 AM (6 hours)

**Deliverable:** Backend deployed and accessible at `https://<project>.onrender.com`

---

## ⏰ DAY 3: November 18 (Frontend + Demo)

### **Hours 34-42: Frontend Development**
**Timeline:** 9:30 AM - 5:30 PM

#### Hour 34-36: Next.js Setup
- [ ] Initialize Next.js app (App Router)
- [ ] Install shadcn/ui:
  ```bash
  npx shadcn@latest init
  npx shadcn@latest add card button badge
  ```
- [ ] Configure Tailwind CSS
- [ ] Set up API client with SWR

#### Hour 36-40: Dashboard Components
- [ ] `components/StatsRow.tsx`
  - [ ] Total workers, high risk count, alerts today, avg PSI
- [ ] `components/WorkerGrid.tsx`
  - [ ] Grid of 100 worker cards
  - [ ] Color-coded by PSI (green <5, yellow 5-7, red >7)
  - [ ] Click to select worker
- [ ] `components/WorkerDetail.tsx`
  - [ ] Worker info panel
  - [ ] PSI/temp trend chart (Recharts line chart)
  - [ ] Voice check-in history
  - [ ] Recent alerts
- [ ] `components/AlertFeed.tsx`
  - [ ] Real-time alert stream
  - [ ] Timestamp, worker ID, alert type, severity

#### Hour 40-42: Main Page Integration
- [ ] `app/page.tsx`
  - [ ] Fetch `/api/dashboard/overview` every 2 seconds with SWR
  - [ ] Render StatsRow, WorkerGrid, WorkerDetail, AlertFeed
  - [ ] Handle loading/error states
- [ ] Test locally: `npm run dev`

**Deliverable:** Working dashboard (local)

---

### **Hours 42-46: Dinner Break + Frontend Polish**
**Timeline:** 5:30 PM - 9:30 PM (includes 1h dinner)

#### Hour 42-43: Dinner Break

#### Hour 43-46: Polish & Deploy
- [ ] Add animations (smooth card transitions)
- [ ] Responsive design (test on mobile)
- [ ] Error handling (API timeout, empty data)
- [ ] Loading skeletons for better UX
- [ ] Deploy to Vercel:
  ```bash
  git push origin main  # Auto-deploys to Vercel
  ```
- [ ] Configure environment variables (API URL)
- [ ] Test deployed site

**Deliverable:** Frontend deployed at `https://<project>.vercel.app`

---

### **Hours 46-50: Simulation Runner**
**Timeline:** 9:30 PM - 1:30 AM (Nov 19)

- [ ] `simulation/run_live_demo.py`
  - [ ] Initialize 100 workers
  - [ ] Run 8-hour shift simulation
  - [ ] Stream telemetry to API in real-time
    - [ ] 1-minute intervals (480 datapoints per worker)
    - [ ] Slow down to 0.1s per minute for demo visibility
  - [ ] Randomly trigger voice check-ins (5% chance per minute)
  - [ ] Log progress to console
- [ ] Test: Run simulation → watch dashboard update live
- [ ] Verify alerts fire correctly

**Sleep:** 1:30 AM - 7:30 AM (6 hours)

**Deliverable:** Simulation runner streaming to live dashboard

---

## ⏰ DAY 4: November 19 (Demo Video + Submission)

### **Hours 50-56: Demo Video Recording**
**Timeline:** 7:30 AM - 1:30 PM

#### Hour 50-52: Video Script & Slides
- [ ] Write 3-minute script:
  - [ ] [0:00-0:30] Problem statement
  - [ ] [0:30-1:30] Live demo walkthrough
  - [ ] [1:30-2:15] Technical architecture
  - [ ] [2:15-3:00] Deployment vision
- [ ] Create slides (Google Slides or Canva)
  - [ ] Problem stats
  - [ ] PINN architecture diagram
  - [ ] System architecture
  - [ ] Training curves
  - [ ] Deployment roadmap

#### Hour 52-54: Recording
- [ ] Start simulation (so dashboard is live)
- [ ] Screen record:
  - [ ] Dashboard showing 100 workers
  - [ ] Click into worker detail
  - [ ] Show PSI climbing, alert firing
  - [ ] Navigate to voice check-ins
  - [ ] Show API docs at `/docs`
  - [ ] Show PINN training curves
- [ ] Record voiceover narration
- [ ] Edit video (simple cuts, no fancy effects)

#### Hour 54-56: Video Finalization
- [ ] Export as MP4 (1080p, <50MB)
- [ ] Upload to YouTube (unlisted)
- [ ] Test link works

**Deliverable:** 3-minute demo video on YouTube

---

### **Hours 56-60: Submission Preparation**
**Timeline:** 1:30 PM - 5:30 PM

#### Hour 56-58: Submission Deck
- [ ] Download hackathon template
- [ ] Fill in slides:
  - [ ] Problem statement
  - [ ] Solution architecture
  - [ ] Technical innovation (PINN)
  - [ ] Demo screenshots
  - [ ] Measured validation metrics (HONEST numbers)
  - [ ] Deployment roadmap
  - [ ] Team info
- [ ] Export as PDF

#### Hour 58-60: Submission Form
- [ ] Fill out Hack2Skill form:
  - [ ] Solution summary (2000 chars)
  - [ ] What was built (1500 chars)
  - [ ] Solution stage: "Proof of Concept"
  - [ ] Prototype link: Vercel URL
  - [ ] Demo video link: YouTube URL
  - [ ] Upload PDF deck
- [ ] Double-check all fields
- [ ] Submit before 11:59 PM deadline

**Deliverable:** Hackathon submission completed ✅

---

### **Hours 60-62: Buffer Time**
**Timeline:** 5:30 PM - 7:30 PM

- [ ] Fix any last-minute bugs
- [ ] Test deployed system one final time
- [ ] Prepare for potential judge questions
- [ ] Rest before submission

---

## 🎯 Critical Path Dependencies

```
Planning Docs (Done) 
    ↓
Environment Setup
    ↓
Simulation Engine → Data Generation
    ↓                     ↓
    ↓                 PINN Training
    ↓                     ↓
Voice Pipeline ← Backend API ← PINN Model
    ↓                     ↓
    └───→ API Integration
              ↓
         Frontend Dashboard
              ↓
         Deployment
              ↓
         Demo Video
              ↓
         Submission
```

**Bottlenecks to Watch:**
1. PINN training (2-3 hours) - can't proceed without trained model
2. Backend deployment (Render can be slow) - deploy early, test often
3. Demo video recording - allocate extra time for reshoots

---

## 📊 Daily Progress Tracking

### Day 1 Checklist:
- [ ] Environment setup complete
- [ ] Simulation engine validated
- [ ] 48,000 synthetic datapoints generated
- [ ] PINN trained with measured accuracy

### Day 2 Checklist:
- [ ] Backend API working locally
- [ ] Voice pipeline tested (10 samples)
- [ ] Backend deployed to Render
- [ ] API accessible and documented

### Day 3 Checklist:
- [ ] Frontend deployed to Vercel
- [ ] Simulation runner streaming live
- [ ] End-to-end system test passed
- [ ] Demo video uploaded

### Day 4 Checklist:
- [ ] Submission form completed
- [ ] All links verified working
- [ ] Deck uploaded
- [ ] Submitted before deadline ✅

---

## 🚨 Contingency Plans

| If This Fails | Do This Instead |
|---------------|-----------------|
| PINN won't train | Use simpler MLP, report honest accuracy |
| Med42 won't load | Use GPT-4o-mini, show Med42 in architecture |
| Render deployment fails | Deploy locally, show video of local version |
| Whisper too slow | Use Whisper tiny (fastest), or OpenAI API |
| Frontend deployment fails | Record local version, upload video |
| GPU out of memory | Reduce batch size to 1, use CPU if needed |

---

**Next Steps:** Complete Task #2 (repo setup), then start Task #3 (simulation engine).

Let's build this. 🚀
