# Product Requirements Document: BioThermal Twin
## Physics-Informed Heat Stress Early Warning System

**Version:** 1.0  
**Date:** November 16, 2026  
**Status:** Proof-of-Concept Development  
**Hackathon:** Future Health Digital Innovation Challenge 2026  
**Deadline:** November 20, 2026 (72 hours)

---

## 1. Executive Summary

BioThermal Twin is a proof-of-concept early warning system that predicts heat stress in extreme-climate workers using physics-informed AI. Unlike reactive systems that respond after workers collapse, we anticipate physiological strain 30-60 minutes in advance using thermodynamic modeling and multilingual symptom extraction.

**Key Differentiator:** Physics-Informed Neural Network (PINN) that respects energy conservation laws, preventing biologically impossible predictions.

**Honest Scope:** This is a validated simulation environment demonstrating technical feasibility. Real deployment requires IoT hardware integration, clinical trials, and regulatory approval.

---

## 2. Problem Statement

### 2.1 The Clinical Reality
In UAE and GCC regions, 1.5M+ construction/industrial workers operate in environments exceeding 45°C with high humidity. Current heat safety relies on:
- Static ambient temperature thresholds (e.g., "stop work at 40°C")
- Generic WBGT indices that ignore individual physiology
- English-only safety systems (workforce speaks Hindi/Urdu/Malayalam/Arabic/Tagalog)

**Result:** Workers suffer subclinical acute kidney injury (AKI) 24-72 hours before physical collapse, leading to chronic kidney disease (CKDu) epidemic in young workers aged 22-38.

### 2.2 Regulatory Context
- **ADPHC OSHAD CoP 11.0:** Mandates Heat Stress Management Programs at sites ≥35°C
- **UAE MOHRE Midday Break:** Outdoor work ban 12:30-3:00 PM (June 15 - Sept 15)
- **Structural Failure:** Ambient rules fail because human thermal strain varies by metabolic rate, acclimatization, hydration, and individual factors

### 2.3 Core Problems We Address
1. **Biological Heterogeneity:** Same environment, vastly different individual responses
2. **Silent Injury Window:** Heat illness begins 24-72h before collapse (reversible window)
3. **Language Barrier:** Workers can't report early symptoms in English
4. **Reactive Systems:** Current solutions respond post-collapse, not pre-injury

---

## 3. Solution Overview

### 3.1 System Architecture (4 Tiers)

**Tier 1: Data Sources (Simulated)**
- Thermodynamic worker simulation (Gagge Two-Node heat balance)
- Environmental microclimate simulation (UAE summer conditions)
- Synthetic voice symptom reports (Hindi/Arabic)

**Tier 2: AI Prediction Engine**
- Physics-Informed Neural Network (PINN) predicting core temperature
- Physiological Strain Index (PSI) calculator (Moran 1998 formula)
- Voice symptom extraction (Whisper + LLM)

**Tier 3: Backend API**
- FastAPI real-time telemetry ingestion
- PostgreSQL time-series database
- Alert generation and risk scoring

**Tier 4: Monitoring Dashboard**
- Next.js live worker grid (100 simulated workers)
- Real-time PSI/temperature charts
- Alert feed and voice check-in display

### 3.2 Key Innovation: Physics-Informed Loss Function

Traditional ML models hallucinate when encountering extreme conditions. Our PINN enforces:
- **Energy Conservation:** Heat storage = Metabolic + Environmental - Evaporative
- **Biological Boundaries:** Core temp constrained to viable range (35-42°C)
- **PSI-Temperature Coupling:** PSI must increase with thermal load
- **Thermodynamic Feasibility:** Predictions respect physical laws

**Result:** Model generalizes reliably even with limited training data because physics constrains the solution space.

---

## 4. Functional Requirements

### 4.1 Physics Simulation Engine
**Requirement:** Thermodynamically accurate worker simulation

**Acceptance Criteria:**
- [x] Implements Gagge Two-Node heat balance (simplified but valid)
- [x] Simulates 100 workers with individual variability (age, BMI, acclimatization)
- [x] Models 8-hour shifts in UAE summer conditions (45°C, 65% RH)
- [x] Outputs: core temp, HR, sweat rate, hydration status, kidney stress
- [x] Validation: Results match published thermal stress research ranges

**Non-Goal:** Full Fiala multi-node thermal model (PhD thesis complexity, not needed for POC)

### 4.2 PINN Model
**Requirement:** Neural network with physics constraints

**Acceptance Criteria:**
- [x] PyTorch model: [HR, cadence, ambient_temp, humidity, time_exposed] → [core_temp, PSI, kidney_risk]
- [x] Custom loss function enforcing thermodynamic constraints
- [x] Training on 50,000+ simulated worker-hours
- [x] Measured accuracy (honest metric, not fabricated)
- [x] Physics loss convergence demonstrates constraint satisfaction

**Non-Goal:** ±0.18°C accuracy claim (that requires invasive validation data we don't have)

### 4.3 Voice Symptom Extraction
**Requirement:** Multilingual symptom detection

**Acceptance Criteria:**
- [x] Whisper tiny/base model (runs locally on MX550 GPU)
- [x] Support: Hindi, Arabic (minimum viable)
- [x] Extracts: dark urine, muscle cramps, dizziness, fatigue severity
- [x] LLM backend: GPT-4o-mini or quantized Med42
- [x] Returns structured JSON

**Non-Goal:** 6 languages (not needed for POC), Med42 if API access fails

### 4.4 Backend API
**Requirement:** Real-time telemetry processing

**Acceptance Criteria:**
- [x] FastAPI application deployed on Render
- [x] Endpoints: `/api/telemetry/ingest`, `/api/workers/{id}/status`, `/api/voice-check`
- [x] PostgreSQL database (time-series optimized indexes)
- [x] Alert generation when PSI > 7.0 AND voice symptoms present
- [x] API documentation (auto-generated from FastAPI)

**Performance Target:** <100ms response time for single worker query

### 4.5 Monitoring Dashboard
**Requirement:** Live visualization

**Acceptance Criteria:**
- [x] Next.js app deployed on Vercel
- [x] Worker grid: 100 workers, color-coded by risk level
- [x] Detail view: PSI/temp trends, voice check-ins
- [x] Alert feed: real-time notifications
- [x] Mobile responsive

**Non-Goal:** Enterprise SSO, multi-tenancy (out of scope for POC)

---

## 5. Non-Functional Requirements

### 5.1 Performance
- Simulation: Generate 480 minutes (8-hour shift) in <5 minutes
- PINN inference: <50ms per prediction
- Dashboard updates: Poll API every 2 seconds
- Database: Handle 100 workers × 480 readings = 48,000 records

### 5.2 Scalability (Deployment Roadmap, Not POC)
- Current: 100 simulated workers
- Phase 1: 500 workers with real BLE wearables
- Phase 2: 10,000 workers across multiple sites

### 5.3 Reliability
- Simulation must complete without crashes
- API must handle missing/malformed data gracefully
- Frontend must display loading states, not crash on empty data

### 5.4 Security (Basic POC Level)
- API: No authentication (it's a demo)
- Database: Local PostgreSQL or Render free tier
- Secrets: `.env` file, not committed to git

**Deployment Security (Future):**
- JWT authentication
- HTTPS only
- Malaffi HIE integration requires: TLS 1.3, HL7 FHIR OAuth 2.0

---

## 6. Technical Constraints

### 6.1 Hardware Limitations
- **GPU:** NVIDIA MX550, 2GB VRAM
  - Can run: Whisper tiny/base, small PINN
  - Cannot run: Med42-70B, Whisper large-v3
- **Deployment:** Free tiers (Render backend, Vercel frontend)

### 6.2 Time Constraint
- **72 hours** from Nov 16 → Nov 19 (submit Nov 20)
- Must prioritize: working demo > documentation polish

### 6.3 Data Limitations
- No real worker data (ethically impossible to collect in 72h)
- No invasive core temp measurements (gold standard)
- Solution: High-fidelity simulation validated against published research

---

## 7. Success Criteria

### 7.1 Minimum Viable Demo (Must Have)
- [ ] Simulation runs, generates realistic data
- [ ] PINN trains, produces predictions (with HONEST accuracy metric)
- [ ] Voice pipeline works (record audio → transcribe → extract symptoms)
- [ ] Backend API deployed, responds to requests
- [ ] Frontend dashboard shows live workers, updates in real-time
- [ ] Demo video recorded (3 minutes)
- [ ] Submission form completed

### 7.2 Technical Validation (Must Measure)
- [ ] PINN accuracy on validation set (report actual number, not invented)
- [ ] Physics loss convergence (proves constraints are satisfied)
- [ ] Voice symptom extraction accuracy (test on 10 sample recordings)
- [ ] API latency measurements (p50, p95, p99)
- [ ] End-to-end system test (simulation → API → dashboard)

### 7.3 Judging Criteria Alignment
- **Innovation:** Physics-informed AI (not generic ML black box)
- **Technical Depth:** Real thermodynamic simulation + PINN implementation
- **Abu Dhabi Relevance:** Addresses workforce health, cites OSHAD/Malaffi
- **Deployability:** Architecture designed for production (even if POC uses simulation)
- **Demo Quality:** Live system judges can interact with

---

## 8. Out of Scope (Post-Hackathon)

### 8.1 Not Building in 72 Hours
- ❌ Real IoT hardware integration
- ❌ Med42 full deployment (if API access fails)
- ❌ Malaffi HIE connection (requires government approval)
- ❌ Clinical validation trials (requires IRB)
- ❌ Medical device certification (18-month process)
- ❌ Redis Streams (overkill for POC, use PostgreSQL)
- ❌ TimescaleDB (use regular PostgreSQL with indexes)
- ❌ Zero-knowledge cryptography (future work)
- ❌ Multi-site deployment
- ❌ Mobile app

### 8.2 Explicitly NOT Claiming
- ❌ "Clinical-grade accuracy" (not validated)
- ❌ "Ready for deployment" (it's a POC)
- ❌ "Replaces medical professionals" (decision support only)
- ❌ "FDA/CE/ADPHC approved" (no regulatory submissions)

---

## 9. Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Med42 API access fails | High | Medium | Use GPT-4o-mini as fallback, show Med42 in architecture |
| PINN doesn't converge | Medium | High | Extensive hyperparameter tuning, physics loss debugging |
| Simulation unrealistic | Low | High | Validate against published thermal stress papers |
| Dashboard deployment fails | Low | Medium | Have video backup, show local version |
| Voice pipeline latency | Medium | Low | Use Whisper tiny (fastest), cache transcriptions |
| GPU memory overflow | Medium | High | Quantize models, batch size = 1 for training |

---

## 10. Validation & Truth Requirements

**Every metric we report must be MEASURED, not invented.**

### 10.1 Simulation Validation
- Compare core temp ranges to published research (Moran 1998, ISO 9886)
- Verify PSI values align with known heat stress thresholds
- Check sweat rates against physiological literature (1.5-2.5 L/hr max)

### 10.2 Model Validation
- Train/validation split: 80/20
- Report ACTUAL MAE, RMSE, R² on validation set
- Show physics loss components (boundary, conservation, PSI coupling)
- Include loss curves in demo

### 10.3 System Validation
- Measure API latency (use `time.time()` in endpoint)
- Count alert false positives/negatives on test scenarios
- Record actual inference times for PINN

### 10.4 What We Won't Fake
- ❌ No "±0.18°C accuracy" unless we actually measure it
- ❌ No "86.3% false alarm reduction" without baseline comparison
- ❌ No "48-72 hour AKI prediction" unless simulation demonstrates it
- ✅ Report: "Our model achieves X°C MAE on simulated validation data"
- ✅ Report: "Physics loss converged to Y, demonstrating constraint satisfaction"

---

## 11. Submission Deliverables

### 11.1 Code Repository
- GitHub repo (public, no AI attribution in commits)
- README with: setup instructions, architecture diagram, demo video link
- Clean commit history showing 72-hour build progression

### 11.2 Deployed Prototype
- Backend: `https://<project>.onrender.com`
- Frontend: `https://<project>.vercel.app`
- Both functional for judges to test

### 11.3 Demo Video (3 minutes)
- Problem statement (30 sec)
- Live system demonstration (90 sec)
- Technical architecture explanation (45 sec)
- Deployment vision (15 sec)

### 11.4 Submission Deck
- Use hackathon template
- Honest claims: "proof-of-concept", "simulated data", "future clinical validation needed"
- Technical depth: show PINN architecture, physics equations, real metrics

---

## 12. Post-Hackathon Roadmap (If We Win/Place)

### Phase 1: Hardware Integration (Months 1-2)
- Procure BLE wearables (Xiaomi Mi Band, $20/unit)
- Build IoT gateway (ESP32 aggregators)
- Test with 10 volunteer workers (IRB exempt pilot)

### Phase 2: Clinical Validation (Months 3-6)
- Partner with M42/ADPHC for IRB approval
- Recruit 100 workers for observational study
- Collect gold-standard core temp (ingestible pills) + wearable data
- Retrain PINN on real data, measure ACTUAL accuracy

### Phase 3: Regulatory (Months 7-12)
- Medical device classification (likely Class IIa)
- ISO 13485 quality management system
- ADPHC/DHA registration
- Malaffi HIE technical integration

### Phase 4: Deployment (Months 13-18)
- Pilot at 2-3 Abu Dhabi construction sites
- Real-world alert validation
- OSHAD compliance audit
- Scale to 10,000 workers

---

## 13. Appendix: Key References

1. **Gagge Two-Node Model:** Gagge et al. (1971). "A two node model of human temperature regulation"
2. **PSI Formula:** Moran et al. (1998). "A physiological strain index to evaluate heat stress." *Am J Physiol*. PMID: 9688970
3. **OSHAD Standards:** ADPHC OSHAD SF Code of Practice 11.0 Version 4.0 (July 2024)
4. **CKDu in Workers:** *The Lancet Planetary Health*, *NEJM* chronic kidney disease studies
5. **ISO 9886:** Ergonomics — Evaluation of thermal strain by physiological measurements

---

**Document Sign-Off:**

This PRD represents what we will ACTUALLY build in 72 hours. No fake claims, no fabricated metrics, no regulatory oversights. We're building a technically impressive proof-of-concept that demonstrates feasibility while being honest about its limitations.

**Next Steps:** Technical Architecture Document → Model Specification → Code Implementation
