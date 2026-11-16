# Demo Video Script - HONEST VERSION
**Duration: 3 minutes | For: Future Health Challenge 2026**

---

## 🎬 Recording Setup

**Tools:**
- OBS Studio (free screen recorder)
- Or: Windows Game Bar (Win + G)
- Or: Loom (loom.com - free 5 min videos)

**What to Record:**
- Your screen showing code, terminal, and browser
- Your voice narrating (microphone)

---

## 📝 HONEST SCRIPT (What to Say & Show)

### **[0:00-0:30] Problem Statement**

**SAY:**
"In the UAE, over 1.5 million construction and industrial workers operate in temperatures exceeding 45°C. Current heat safety systems are reactive—they respond after workers collapse. The medical reality is that heat illness begins 24 to 72 hours earlier, through subclinical kidney damage. Additionally, most workers speak Hindi, Urdu, or Arabic, making it difficult to report early symptoms in English-only systems."

**SHOW:** 
- Open README.md on GitHub showing the problem statement section

---

### **[0:30-1:30] What We Built - BE HONEST**

**SAY:**
"We built BioThermal Twin—a validated proof-of-concept demonstrating three core innovations:

First, a physics-based simulation engine using the Gagge Two-Node thermodynamic heat balance model. This generates physiologically accurate training data validated against published research from ISO 9886 and Moran 1998.

Second, a Physics-Informed Neural Network—not just any machine learning model, but one that embeds thermodynamic equations directly into the loss function. This prevents biologically impossible predictions.

Third, a multilingual voice symptom extraction pipeline using Whisper for transcription and GPT-4o-mini for symptom classification in Hindi, Arabic, and other languages.

I want to be transparent: this is an architectural prototype. The individual components work and are validated, but they're not yet fully integrated into a real-time system. Let me show you what actually works."

**SHOW:**
- Open project in VS Code showing directory structure
- Briefly show `core/worker_simulation.py` (scroll through code)
- Show `models/pinn_core_temp.py` (physics loss function)

---

### **[1:30-2:15] The Real Validation - SHOW ACTUAL METRICS**

**SAY:**
"Here's what's actually validated with measured metrics, not made-up numbers.

The PINN model was trained on 144,000 thermodynamically accurate datapoints. The training completed successfully, and here are the REAL measured results: Core temperature prediction accuracy is 0.139 degrees Celsius mean absolute error. That's excellent—well below the 0.5 degree threshold for clinical relevance. The PSI prediction achieved an R-squared of 0.965, meaning we're explaining 96.5% of the variance. These numbers came from actual training runs, not speculation."

**SHOW:**
1. **Terminal:** Run this command and show output:
   ```bash
   python -c "import torch; ckpt = torch.load('models/checkpoints/pinn_best.pt', weights_only=False, map_location='cpu'); import json; print(json.dumps(ckpt['val_metrics'], indent=2))"
   ```
   - This displays the ACTUAL metrics from the trained model

2. **File Explorer:** Show `models/checkpoints/pinn_best.pt` exists (231KB file)

3. **VS Code:** Open `core/data/dataset_metadata.json` showing:
   - 144,000 total datapoints
   - Core temp range: 37.15-42.0°C
   - All validation checks passed

---

### **[2:15-2:45] Architecture & Code Quality**

**SAY:**
"The system architecture is production-ready even though it's not fully connected yet. We have a FastAPI backend with defined endpoints for telemetry ingestion, worker status, and voice processing. The frontend is a Next.js dashboard designed to display 100 workers in real-time with color-coded risk levels.

Currently, the dashboard displays mock data because the integration isn't complete. But the architecture is sound, the PINN model is trained and validated, and the individual components work. This is a validated technical foundation, not vaporware."

**SHOW:**
- **Browser:** Open `http://localhost:3000` (start frontend if needed: `cd frontend && npm run dev`)
  - Show the dashboard with worker grid
  - **SAY:** "This UI works, but it's currently showing simulated data. The real innovation is in the ML model and physics simulation behind it."

- **Browser:** Open `http://localhost:8000/docs` (start backend if needed: `cd backend/app && python main.py`)
  - Show FastAPI Swagger docs with API endpoints

---

### **[2:45-3:00] Honest Next Steps**

**SAY:**
"To deploy this in the real world requires three things we don't have yet: real IoT wearable sensors, IRB-approved clinical validation trials, and medical device regulatory certification. That's an estimated 18 to 24-month pathway.

What we've proven is technical feasibility. The physics is sound, the ML model works and is validated, and the architecture is ready. This is a honest foundation for a system that could genuinely save lives in extreme heat environments. Thank you."

**SHOW:**
- GitHub repository: https://github.com/Ganesh-0509/biothermal-twin
- README.md showing the "Honest Limitations" section

---

## 📹 Recording Checklist

**Before Recording:**
- [ ] Start backend: `cd backend/app && python main.py`
- [ ] Start frontend: `cd frontend && npm run dev`
- [ ] Open browser tabs: localhost:3000, localhost:8000/docs, GitHub repo
- [ ] Open VS Code with project
- [ ] Have terminal ready for metrics command
- [ ] Test microphone

**What to Show:**
1. GitHub README (problem statement)
2. VS Code (directory structure, key code files)
3. Terminal (actual PINN metrics command output)
4. File explorer (trained model checkpoint exists)
5. Browser (dashboard UI at localhost:3000)
6. Browser (FastAPI docs at localhost:8000/docs)
7. GitHub (Honest Limitations section)

**What NOT to Claim:**
- ❌ "Fully integrated real-time system" (it's not)
- ❌ "Clinical-grade validated" (not yet)
- ❌ "Ready for deployment" (needs 18-24 months)
- ❌ "Connected to live sensors" (simulation only)

**What TO Emphasize:**
- ✅ "Validated proof-of-concept"
- ✅ "Physics-informed approach"
- ✅ "Actual measured metrics: 0.139°C MAE"
- ✅ "Technical feasibility demonstrated"
- ✅ "Honest about limitations"

---

## 🎥 After Recording

1. **Export video** (MP4, 1080p)
2. **Upload to YouTube:**
   - Title: "BioThermal Twin - Physics-Informed Heat Stress Warning (Future Health Challenge 2026)"
   - Visibility: **Unlisted** (not public, but shareable via link)
   - Description: "Validated proof-of-concept for anticipatory heat stress detection using Physics-Informed Neural Networks. PINN achieves 0.139°C core temperature MAE. Built for Future Health Digital Innovation Challenge 2026."

3. **Copy YouTube link** and paste into hackathon submission form

---

## 💡 Key Messages for Judges

**Your Differentiators:**
1. **Ground truth validation** - Every metric is measured, not fabricated
2. **Physics-informed AI** - Not a black box, thermodynamically explainable
3. **Technical depth** - 500+ lines of thermodynamic simulation, custom loss functions
4. **Intellectual honesty** - Transparent about what works vs what's needed
5. **Production-ready architecture** - Even if not fully connected, the design is sound

**Honest Positioning:**
"We're not claiming to have a deployed medical device. We're demonstrating that physics-informed AI for heat stress prediction is technically feasible, scientifically validated, and architecturally sound. This is a foundation that, with proper clinical trials and regulatory approval, could genuinely protect workers in extreme heat."

---

**Good luck! Be confident about what you built, and honest about what's next.**
