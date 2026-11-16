# Validation & Truth Framework
## How We Measure Everything (No Fabricated Metrics)

**Date:** November 16, 2026  
**Principle:** Every number we report must be MEASURED, not invented.

---

## 1. Simulation Validation (Against Published Research)

### 1.1 Core Temperature Validation
**Reference:** ISO 9886:2004 - Ergonomics — Evaluation of thermal strain

**Expected Ranges:**
- Normal resting: 36.5-37.5°C
- Light work in heat: 37.5-38.0°C
- Moderate work in heat: 38.0-38.5°C  
- Heat exhaustion: 38.5-40.0°C
- Heat stroke: >40.0°C

**Our Test:**
```python
def test_core_temp_progression():
    """Verify simulated core temps match literature"""
    worker = WorkerPhysiology(age=30, baseline_hr=65, acclimatization=0.5)
    
    # Scenario 1: Moderate work, 38°C ambient
    for _ in range(120):  # 2 hours
        state = worker.update_step(38, 60, 800, 3.0)
    
    assert 37.5 <= state['core_temp'] <= 38.5, f"Expected 37.5-38.5°C, got {state['core_temp']}"
    
    # Scenario 2: Heavy work, 45°C ambient
    worker2 = WorkerPhysiology(age=28, baseline_hr=68, acclimatization=0.3)
    for _ in range(180):  # 3 hours
        state = worker2.update_step(45, 70, 900, 4.5)
    
    assert 38.5 <= state['core_temp'] <= 40.5, f"Should reach heat exhaustion range"
```

### 1.2 Heart Rate Validation
**Reference:** Moran et al. (1998) - Heart rate response to heat stress

**Expected:**
- Baseline: 55-75 bpm (resting)
- Thermal compensation: +40-80 bpm above baseline
- Maximum sustainable: ~180 bpm

**Our Test:**
```python
def test_heart_rate_thermal_response():
    worker = WorkerPhysiology(baseline_hr=65)
    
    # Cool conditions - HR should stay near baseline
    for _ in range(60):
        state = worker.update_step(25, 40, 600, 2.0)
    assert 65 <= state['heart_rate'] <= 90
    
    # Extreme heat - HR should elevate significantly
    worker2 = WorkerPhysiology(baseline_hr=65)
    for _ in range(120):
        state = worker2.update_step(47, 80, 950, 4.0)
    assert 105 <= state['heart_rate'] <= 160
```

### 1.3 PSI Validation
**Reference:** Moran et al. (1998) PMID: 9688970

**Expected PSI Scale:**
- 0-2: No/little strain
- 3-4: Low strain
- 5-6: Moderate strain
- 7-8: High strain
- 9-10: Very high strain (medical risk)

**Our Test:**
```python
def test_psi_calculation():
    """Verify PSI formula matches Moran 1998"""
    # Formula: PSI = 5·(Tc - Tc0)/(39.5 - Tc0) + 5·(HR - HR0)/(180 - HR0)
    
    # Test case from paper: Tc=38.5, HR=140, baseline Tc=37, baseline HR=70
    psi = 5 * ((38.5 - 37.0) / (39.5 - 37.0)) + \
          5 * ((140 - 70) / (180 - 70))
    
    expected = 5 * (1.5/2.5) + 5 * (70/110) = 3.0 + 3.18 = 6.18
    assert abs(psi - 6.18) < 0.1
```

### 1.4 Sweat Rate Validation
**Reference:** Armstrong et al. (2007) - Human sweating rate in hot environments

**Expected:**
- Resting in heat: 0.2-0.5 L/hr
- Light work: 0.5-1.0 L/hr
- Moderate work: 1.0-1.5 L/hr
- Heavy work: 1.5-2.0 L/hr
- Maximum physiological: 2.5 L/hr (brief bursts)

**Our Test:**
```python
def test_sweat_rate_limits():
    worker = WorkerPhysiology(...)
    
    for _ in range(240):  # 4 hours heavy work
        state = worker.update_step(45, 65, 900, 4.5)
        assert state['sweat_rate'] <= 2.5, "Exceeded physiological maximum"
        assert state['sweat_rate'] >= 0.0, "Negative sweat rate impossible"
```

---

## 2. PINN Model Validation

### 2.1 Training Metrics (MUST REPORT ACTUAL)

**Metrics to Track:**
```python
validation_results = {
    'mae_core_temp': None,     # Mean Absolute Error in °C (REPORT ACTUAL)
    'rmse_core_temp': None,    # Root Mean Squared Error
    'r2_core_temp': None,      # R² coefficient
    'mae_psi': None,           # PSI prediction error
    'physics_loss': None,      # Physics constraint violation
    'boundary_violations': 0,  # Count of predictions outside 35-42°C
}
```

**How to Measure:**
```python
# After training, on validation set
from sklearn.metrics import mean_absolute_error, r2_score
import numpy as np

predictions = model.predict(X_val)
ground_truth = y_val

mae = mean_absolute_error(ground_truth[:, 0], predictions[:, 0])
rmse = np.sqrt(np.mean((ground_truth[:, 0] - predictions[:, 0])**2))
r2 = r2_score(ground_truth[:, 0], predictions[:, 0])

# Save to file
with open('results/pinn_validation.json', 'w') as f:
    json.dump({
        'mae_core_temp_celsius': float(mae),
        'rmse_core_temp_celsius': float(rmse),
        'r2_score': float(r2),
        'validation_samples': len(X_val),
        'timestamp': datetime.now().isoformat()
    }, f, indent=2)
```

**Honesty Thresholds:**
- ✅ MAE < 0.5°C: Excellent for simulation-trained model
- ✅ MAE 0.5-1.0°C: Good, report it honestly
- ✅ MAE 1.0-1.5°C: Acceptable for POC, state limitations
- ❌ MAE > 1.5°C: Model needs debugging, don't deploy

### 2.2 Physics Constraint Validation

**Test 1: Biological Boundary Respect**
```python
def test_pinn_boundaries():
    model = load_trained_model()
    
    # Generate 10,000 random valid inputs
    test_inputs = generate_random_inputs(10000)
    predictions = model.predict(test_inputs)
    
    violations = np.sum((predictions[:, 0] < 35) | (predictions[:, 0] > 42))
    violation_rate = violations / len(predictions)
    
    assert violation_rate < 0.01, f"Boundary violation rate: {violation_rate:.2%}"
    return violation_rate
```

**Test 2: PSI-Temperature Coupling**
```python
def test_pinn_physics_coupling():
    """Verify PSI increases with temperature"""
    model = load_trained_model()
    
    # Hold all inputs constant except ambient temp
    base_input = [75, 65, 45, 38, 60, 850, 120, 37.5]
    
    psi_values = []
    for temp in range(35, 50):
        input_vector = base_input.copy()
        input_vector[3] = temp  # Vary ambient temp
        pred = model.predict([input_vector])
        psi_values.append(pred[0][1])  # PSI is 2nd output
    
    # PSI should generally increase with temp
    increasing = sum(psi_values[i] > psi_values[i-1] for i in range(1, len(psi_values)))
    monotonicity = increasing / (len(psi_values) - 1)
    
    assert monotonicity > 0.8, f"PSI-temp coupling weak: {monotonicity:.2%}"
    return monotonicity
```

### 2.3 Generalization Test

**Scenario-Based Validation:**
```python
def test_pinn_realistic_scenarios():
    """Test on hand-crafted realistic scenarios"""
    scenarios = [
        # (name, input, expected_core_temp_range, expected_psi_range)
        ("Morning shift start", [70, 65, 30, 32, 50, 600, 0, 37.0], (36.8, 37.3), (0, 2)),
        ("Midday peak heat", [130, 65, 60, 46, 70, 950, 180, 38.5], (38.2, 39.2), (6, 8)),
        ("Post-break recovery", [85, 65, 10, 38, 60, 800, 240, 38.0], (37.5, 38.2), (3, 5)),
    ]
    
    model = load_trained_model()
    results = []
    
    for name, input_vec, temp_range, psi_range in scenarios:
        pred = model.predict([input_vec])[0]
        pred_temp, pred_psi = pred[0], pred[1]
        
        temp_ok = temp_range[0] <= pred_temp <= temp_range[1]
        psi_ok = psi_range[0] <= pred_psi <= psi_range[1]
        
        results.append({
            'scenario': name,
            'pred_temp': float(pred_temp),
            'pred_psi': float(pred_psi),
            'temp_valid': temp_ok,
            'psi_valid': psi_ok
        })
    
    return results  # Include in validation report
```

---

## 3. Voice Pipeline Validation

### 3.1 Whisper Transcription Accuracy

**Test Dataset:** 10 sample recordings (5 Hindi, 5 Arabic)

**Recording Script:**
```
Hindi samples:
1. "मुझे चक्कर आ रहा है" (I'm feeling dizzy)
2. "मेरा मूत्र गहरे रंग का है" (My urine is dark colored)
3. "मुझे बहुत थकान महसूस हो रही है" (I'm feeling very tired)
4. "मेरे पैरों में ऐंठन है" (I have cramps in my legs)
5. "मुझे सिरदर्द है" (I have a headache)

Arabic samples:
1. "أشعر بالدوار" (I feel dizzy)
2. "بولي داكن اللون" (My urine is dark)
3. "أشعر بتعب شديد" (I feel very tired)
4. "لدي تشنجات في العضلات" (I have muscle cramps)
5. "لدي صداع" (I have a headache)
```

**Measurement:**
```python
def test_transcription_accuracy():
    results = []
    
    for audio_file, reference_text in test_cases:
        transcription = transcribe_audio(audio_file)
        
        # Word Error Rate (WER)
        wer = calculate_wer(reference_text, transcription['text'])
        
        results.append({
            'audio': audio_file,
            'reference': reference_text,
            'transcription': transcription['text'],
            'language': transcription['language'],
            'wer': wer,
            'confidence': transcription['confidence']
        })
    
    avg_wer = np.mean([r['wer'] for r in results])
    return avg_wer, results  # Report actual WER, not "95% accuracy"
```

**Honesty Thresholds:**
- ✅ WER < 10%: Excellent
- ✅ WER 10-20%: Good for demo
- ✅ WER 20-30%: Acceptable, note limitations
- ❌ WER > 30%: Use OpenAI API instead of local model

### 3.2 Symptom Extraction Validation

**Test Cases:** Same 10 recordings + expected JSON output

**Example:**
```python
test_cases = [
    {
        'audio': 'hindi_01.wav',
        'transcription': 'मुझे चक्कर आ रहा है',
        'expected_symptoms': {
            'dark_urine': False,
            'muscle_cramps': False,
            'dizziness': True,
            'fatigue': 'NONE',
            'headache': False
        }
    },
    # ... 9 more
]

def test_symptom_extraction():
    correct = 0
    total = 0
    
    for test in test_cases:
        extracted = extract_symptoms(test['transcription'], 'hi')
        
        for symptom, expected_value in test['expected_symptoms'].items():
            total += 1
            if extracted[symptom] == expected_value:
                correct += 1
    
    accuracy = correct / total
    return accuracy  # Report actual accuracy
```

---

## 4. End-to-End System Validation

### 4.1 Latency Measurements

**API Response Times:**
```python
import time

def test_api_latency():
    endpoints = [
        ('POST', '/api/telemetry/ingest', telemetry_payload),
        ('GET', '/api/workers/W-00042/status', None),
        ('POST', '/api/voice-check', voice_payload),
        ('GET', '/api/dashboard/overview', None)
    ]
    
    results = {}
    
    for method, endpoint, payload in endpoints:
        latencies = []
        
        for _ in range(100):  # 100 requests
            start = time.time()
            
            if method == 'POST':
                response = requests.post(API_URL + endpoint, json=payload)
            else:
                response = requests.get(API_URL + endpoint)
            
            latency = (time.time() - start) * 1000  # milliseconds
            latencies.append(latency)
        
        results[endpoint] = {
            'p50': np.percentile(latencies, 50),
            'p95': np.percentile(latencies, 95),
            'p99': np.percentile(latencies, 99),
            'mean': np.mean(latencies),
            'max': np.max(latencies)
        }
    
    return results  # Include in technical documentation
```

### 4.2 Alert Accuracy Test

**Scenario-Based Testing:**
```python
def test_alert_system():
    """Verify alerts fire correctly"""
    
    # Scenario 1: High PSI, no voice symptoms → Should alert (WARNING)
    send_telemetry(worker='W-001', psi=8.2)
    time.sleep(1)
    alerts = get_alerts(worker='W-001')
    assert len(alerts) > 0
    assert alerts[0]['severity'] == 'WARNING'
    
    # Scenario 2: Normal PSI, high voice symptoms → Should alert (WARNING)
    send_telemetry(worker='W-002', psi=5.0)
    send_voice_check(worker='W-002', symptoms={'dizziness': True, 'fatigue': 'SEVERE'})
    alerts = get_alerts(worker='W-002')
    assert len(alerts) > 0
    
    # Scenario 3: High PSI + voice symptoms → Should alert (CRITICAL)
    send_telemetry(worker='W-003', psi=7.5)
    send_voice_check(worker='W-003', symptoms={'dark_urine': True, 'muscle_cramps': True})
    alerts = get_alerts(worker='W-003')
    assert any(a['severity'] == 'CRITICAL' for a in alerts)
    
    # Scenario 4: Normal PSI, no symptoms → Should NOT alert
    send_telemetry(worker='W-004', psi=3.2)
    send_voice_check(worker='W-004', symptoms={'dizziness': False, 'fatigue': 'NONE'})
    alerts = get_alerts(worker='W-004')
    assert len(alerts) == 0
```

---

## 5. Documentation of Results

### 5.1 Validation Report Template

**File:** `results/VALIDATION_REPORT.md`

```markdown
# BioThermal Twin Validation Report
**Date:** [Date]
**System Version:** v1.0-poc

## 1. Simulation Validation
- Core temp ranges: ✅ Match ISO 9886 standards
- Heart rate response: ✅ Within expected ±10 bpm
- PSI calculation: ✅ Matches Moran 1998 formula
- Sweat rate limits: ✅ Never exceeds 2.5 L/hr

## 2. PINN Model Performance
- **MAE (Core Temp):** [ACTUAL NUMBER]°C
- **RMSE:** [ACTUAL NUMBER]°C
- **R² Score:** [ACTUAL NUMBER]
- **Physics Loss:** [ACTUAL NUMBER]
- **Boundary Violations:** [COUNT] / 10,000 (X.XX%)
- **Validation Samples:** 10,000

## 3. Voice Pipeline Accuracy
- **Transcription WER:** [ACTUAL %] (avg across 10 samples)
- **Symptom Extraction Accuracy:** [ACTUAL %] (50 symptoms tested)
- **Languages Tested:** Hindi, Arabic

## 4. System Performance
- **API Latency (p95):** [ACTUAL]ms
- **End-to-End Test:** ✅ Passed [X/Y] scenarios
- **Alert System:** ✅ Verified dual-signal logic

## 5. Known Limitations
- Model trained on synthetic data only (no real workers)
- Hindi/Arabic support only (not full 6-language coverage)
- Running on simulation (no real IoT hardware)
- Clinical validation pending IRB approval
```

### 5.2 What Goes in the Submission

**HONEST Claims:**
- ✅ "Our PINN achieves X°C MAE on simulated validation data"
- ✅ "Physics loss converged to Y, demonstrating thermodynamic constraint satisfaction"
- ✅ "Voice transcription achieved Z% WER on Hindi/Arabic test samples"
- ✅ "System processes 100 concurrent worker streams with <100ms p95 latency"

**FORBIDDEN Claims:**
- ❌ "Clinical-grade accuracy of ±0.18°C" (unless you actually measure this with invasive sensors)
- ❌ "86.3% false alarm reduction" (unless you have baseline comparison)
- ❌ "48-72 hour AKI prediction validated" (requires clinical trial)
- ❌ "Ready for deployment" (it's a POC)

---

## 6. Pre-Submission Validation Checklist

**Before clicking "Submit":**
- [ ] `results/pinn_validation.json` exists with REAL numbers
- [ ] `results/voice_pipeline_results.json` exists with measured WER
- [ ] `results/api_latency.json` exists with p50/p95/p99
- [ ] `results/VALIDATION_REPORT.md` completed
- [ ] All test cases passing (`pytest tests/ -v`)
- [ ] Demo video shows REAL system output (not mockup)
- [ ] Submission deck cites ACTUAL metrics (no fabrications)

---

**Next Steps:** Complete repo setup, start building with measurement-first mindset.
