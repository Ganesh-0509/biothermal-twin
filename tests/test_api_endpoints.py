"""
Comprehensive test script for all BioThermal Twin FastAPI endpoints.
Uses FastAPI TestClient to test routes, status codes, payload structures, and mathematical boundaries.
"""

import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from backend.app.main import app

def test_all_endpoints():
    print("=" * 70)
    print("RUNNING BIOTHERMAL TWIN ENDPOINT AUDIT (FASTAPI TESTCLIENT)")
    print("=" * 70)
    
    client = TestClient(app)
    passed = 0
    total = 0

    # 1. GET /
    total += 1
    r = client.get("/")
    assert r.status_code == 200, f"Root endpoint failed: {r.status_code}"
    data = r.json()
    assert data["status"] == "operational"
    assert data["pinn_model_loaded"] is True
    print(f"[{passed+1}/{total}] GET / -> 200 OK (Model loaded: {data['pinn_model_loaded']})")
    passed += 1

    # 2. GET /health
    total += 1
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"
    assert "pinn_model" in data
    print(f"[{passed+1}/{total}] GET /health -> 200 OK (MAE: {data['pinn_model']['mae_core_temp']})")
    passed += 1

    # 3. GET /api/dashboard/overview
    total += 1
    r = client.get("/api/dashboard/overview")
    assert r.status_code == 200
    data = r.json()
    assert data["total_workers"] >= 20
    assert len(data["workers"]) == data["total_workers"]
    assert 35.0 <= data["average_core_temp"] <= 42.0
    assert 0.0 <= data["average_psi"] <= 10.0
    print(f"[{passed+1}/{total}] GET /api/dashboard/overview -> 200 OK ({data['total_workers']} workers, Avg PSI: {data['average_psi']}, Avg Tc: {data['average_core_temp']}°C)")
    passed += 1

    # 4. GET /api/workers/{worker_id}/status (Valid and Invalid)
    total += 1
    r = client.get("/api/workers/W-00001/status")
    assert r.status_code == 200
    w = r.json()
    assert w["worker_id"] == "W-00001"
    assert 36.0 <= w["core_temp_estimate"] <= 42.0
    assert 0.0 <= w["psi"] <= 10.0
    assert w["risk_level"] in ["LOW", "MODERATE", "HIGH", "CRITICAL"]
    print(f"[{passed+1}/{total}] GET /api/workers/W-00001/status -> 200 OK (Worker: {w['name']}, PSI: {w['psi']}, Risk: {w['risk_level']})")
    passed += 1

    total += 1
    r = client.get("/api/workers/W-99999/status")
    assert r.status_code == 404, f"Expected 404 for invalid worker, got {r.status_code}"
    print(f"[{passed+1}/{total}] GET /api/workers/W-99999/status -> 404 Not Found (Correct rejection)")
    passed += 1

    # 5. POST /api/telemetry/ingest
    total += 1
    telemetry_payload = {
        "worker_id": "W-00001",
        "heart_rate": 135.0,
        "skin_temp": 37.2,
        "work_intensity_met": 3.0,
        "ambient_temp": 43.5,
        "relative_humidity": 65.0,
        "wbgt": 36.0,
        "time_exposed_minutes": 150.0,
        "prev_core_temp": 37.9
    }
    r = client.post("/api/telemetry/ingest", json=telemetry_payload)
    assert r.status_code == 200
    res = r.json()
    assert "pinn_inference" in res
    assert 36.0 <= res["pinn_inference"]["core_temp"] <= 42.0
    print(f"[{passed+1}/{total}] POST /api/telemetry/ingest -> 200 OK (Inferred Tc: {res['pinn_inference']['core_temp']}°C, PSI: {res['pinn_inference']['psi']})")
    passed += 1

    # 6. POST /api/simulation/heat-spike
    total += 1
    r = client.post("/api/simulation/heat-spike")
    assert r.status_code == 200
    res = r.json()
    assert res["status"] == "heat_spike_triggered"
    assert res["ambient_temp"] >= 43.0
    print(f"[{passed+1}/{total}] POST /api/simulation/heat-spike -> 200 OK (New Ambient Temp: {res['ambient_temp']}°C)")
    passed += 1

    # 7. POST /api/simulation/cool-down
    total += 1
    r = client.post("/api/simulation/cool-down")
    assert r.status_code == 200
    res = r.json()
    assert res["status"] == "cooling_protocol_active"
    print(f"[{passed+1}/{total}] POST /api/simulation/cool-down -> 200 OK (Cooling Protocol Active)")
    passed += 1

    # 8. POST /api/simulation/tick
    total += 1
    r = client.post("/api/simulation/tick")
    assert r.status_code == 200
    res = r.json()
    assert res["status"] == "advanced"
    print(f"[{passed+1}/{total}] POST /api/simulation/tick -> 200 OK (Shift Advanced)")
    passed += 1

    # 9. POST /api/simulation/reset
    total += 1
    r = client.post("/api/simulation/reset")
    assert r.status_code == 200
    res = r.json()
    assert res["status"] == "reset_to_baseline"
    print(f"[{passed+1}/{total}] POST /api/simulation/reset -> 200 OK (Baseline Restored)")
    passed += 1

    # 10. POST /api/voice-check (Multilingual tests)
    voice_tests = [
        ("hi", "मुझे बहुत चक्कर आ रहा है और पेशाब गहरा है", ["dark_urine", "dizziness"]),
        ("ar", "أشعر بدوار شديد وتشنجات مؤلمة في عضلات الساقين", ["muscle_cramps", "dizziness"]),
        ("ur", "مجھے شدید تھکن اور کمزوری ہے اور متلی کی کیفیت ہے", ["nausea_vomiting"]),
        ("en", "Normal shift, drinking water, feeling good", [])
    ]

    for lang, text, expected_flags in voice_tests:
        total += 1
        payload = {"worker_id": "W-00001", "text": text, "language": lang}
        r = client.post("/api/voice-check", json=payload)
        assert r.status_code == 200
        v_res = r.json()
        assert "extracted_symptoms" in v_res
        assert "syndromic_risk_score" in v_res
        assert "dual_signal_alert" in v_res
        for flag in expected_flags:
            assert v_res["extracted_symptoms"][flag] is True, f"Expected {flag}=True for '{text}'"
        print(f"[{passed+1}/{total}] POST /api/voice-check ({lang.upper()}) -> 200 OK (Risk: {v_res['syndromic_risk_score']}, Urgency: {v_res['clinical_urgency']})")
        passed += 1

    print("=" * 70)
    print(f"ALL {passed}/{total} ENDPOINT CHECKS PASSED WITH ZERO ERRORS!")
    print("=" * 70)

if __name__ == "__main__":
    test_all_endpoints()
