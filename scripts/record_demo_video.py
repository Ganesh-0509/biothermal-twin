"""
Automated Playwright Screen Recorder + Synchronized Voiceover Muxer
Produces the official 1080p demonstration video for BioThermal Twin.
Future Health Digital Innovation Challenge 2026.
"""

import os
import sys
import time
import subprocess
import requests
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT_DIR = Path(__file__).resolve().parent.parent
TEMP_VIDEO_DIR = ROOT_DIR / "temp_video"
TEMP_AUDIO_DIR = ROOT_DIR / "temp_audio"
OUTPUT_MP4 = ROOT_DIR / "biothermal_twin_demo_video.mp4"

os.makedirs(TEMP_VIDEO_DIR, exist_ok=True)
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)

SCENE_TIMINGS = {
    'scene1': 27.2,
    'scene2': 29.2,
    'scene3': 26.9,
    'scene4': 26.5,
    'scene5': 35.1
}

def safe_action(action_fn, desc="action"):
    try:
        action_fn()
    except Exception as e:
        print(f"    [WARN] Skipped {desc}: {e}")

def record_walkthrough():
    print("=" * 70)
    print("STEP 1: Starting Backend & Frontend Subprocesses...")
    print("=" * 70)

    # Clean existing temp videos
    for f in TEMP_VIDEO_DIR.glob("*.webm"):
        try: f.unlink()
        except: pass

    # Start FastAPI backend
    backend = subprocess.Popen(
        ['python', '-m', 'uvicorn', 'backend.app.main:app', '--port', '8000'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Start Next.js frontend (production build)
    frontend = subprocess.Popen(
        ['npm', '--prefix', 'frontend', 'run', 'start', '--', '-p', '3000'],
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    ready = False
    for attempt in range(25):
        time.sleep(1)
        try:
            b_ok = requests.get('http://127.0.0.1:8000/health', timeout=1).status_code == 200
            f_ok = requests.get('http://127.0.0.1:3000', timeout=1).status_code == 200
            if b_ok and f_ok:
                print(f"[OK] Both servers active in {attempt+1} seconds!")
                ready = True
                break
        except:
            pass

    if not ready:
        backend.terminate()
        frontend.terminate()
        raise RuntimeError("Failed to connect to backend or frontend servers")

    try:
        print("=" * 70)
        print("STEP 2: Initializing Playwright 1080p Video Recording...")
        print("=" * 70)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                record_video_dir=str(TEMP_VIDEO_DIR),
                record_video_size={"width": 1920, "height": 1080}
            )
            page = context.new_page()

            # --- SCENE 1: Introduction & Problem Scope (~27s) ---
            print("[1/5] Recording Scene 1: Header, Telemetry, Problem Context...")
            t0 = time.time()
            page.goto("http://127.0.0.1:3000", wait_until="networkidle")
            page.wait_for_selector('h1:has-text("BioThermal Twin")')
            time.sleep(3.0)

            safe_action(lambda: page.locator('text=AMBIENT').first.hover(), "hover AMBIENT")
            time.sleep(3.0)
            safe_action(lambda: page.locator('text=MODEL MAE').first.hover(), "hover MODEL MAE")
            time.sleep(3.0)
            safe_action(lambda: page.locator('text=Monitored Workers').first.hover(), "hover Monitored Workers")
            time.sleep(3.0)
            safe_action(lambda: page.locator('text=Cohort Mean PSI').first.hover(), "hover Cohort Mean PSI")
            time.sleep(3.0)

            elapsed = time.time() - t0
            if elapsed < SCENE_TIMINGS['scene1']:
                time.sleep(SCENE_TIMINGS['scene1'] - elapsed)

            # --- SCENE 2: Live Workforce Physiological Grid & Modal (~29s) ---
            print("[2/5] Recording Scene 2: Live Grid & Worker Detail Modal...")
            t0 = time.time()
            safe_action(lambda: page.evaluate("window.scrollBy({ top: 380, behavior: 'smooth' })"), "scroll to grid")
            time.sleep(3.0)

            safe_action(lambda: page.locator('text=W-00001').first.hover(), "hover W-00001")
            time.sleep(2.5)
            safe_action(lambda: page.locator('text=W-00002').first.hover(), "hover W-00002")
            time.sleep(2.5)

            # Click worker W-00001 to open modal
            safe_action(lambda: page.locator('text=W-00001').first.click(), "click W-00001")
            time.sleep(5.0)

            safe_action(lambda: page.locator('text=PINN CORE TEMP').first.hover(), "hover PINN CORE TEMP")
            time.sleep(3.0)
            safe_action(lambda: page.locator('text=PHYSIO STRAIN').first.hover(), "hover PHYSIO STRAIN")
            time.sleep(3.0)
            safe_action(lambda: page.locator('text=KIDNEY STRAIN').first.hover(), "hover KIDNEY STRAIN")
            time.sleep(3.0)

            # Close modal via Close Dialog button
            safe_action(lambda: page.locator('button:has-text("Close Dialog")').first.click(), "close modal")
            time.sleep(3.0)

            elapsed = time.time() - t0
            if elapsed < SCENE_TIMINGS['scene2']:
                time.sleep(SCENE_TIMINGS['scene2'] - elapsed)

            # --- SCENE 3: Acute Heat Spike Scenario & Cooldown (~27s) ---
            print("[3/5] Recording Scene 3: Thermal Scenario Injection (Heat Spike)...")
            t0 = time.time()
            safe_action(lambda: page.evaluate("window.scrollTo({ top: 120, behavior: 'smooth' })"), "scroll up")
            time.sleep(2.0)

            safe_action(lambda: page.locator('button:has-text("Trigger Heat Spike")').first.click(), "click Heat Spike")
            time.sleep(4.0)

            safe_action(lambda: page.evaluate("window.scrollBy({ top: 280, behavior: 'smooth' })"), "scroll to workers")
            time.sleep(7.0)

            safe_action(lambda: page.evaluate("window.scrollTo({ top: 120, behavior: 'smooth' })"), "scroll up to cooldown")
            time.sleep(2.0)
            safe_action(lambda: page.locator('button:has-text("Cooling Station Protocol")').first.click(), "click Cooldown")
            time.sleep(4.0)

            safe_action(lambda: page.evaluate("window.scrollBy({ top: 280, behavior: 'smooth' })"), "scroll to see recovery")
            time.sleep(4.0)

            elapsed = time.time() - t0
            if elapsed < SCENE_TIMINGS['scene3']:
                time.sleep(SCENE_TIMINGS['scene3'] - elapsed)

            # --- SCENE 4: Multilingual Voice Triage with Med42 (~26.5s) ---
            print("[4/5] Recording Scene 4: Multilingual Voice Triage Station...")
            t0 = time.time()
            safe_action(lambda: page.evaluate("window.scrollTo({ top: 80, behavior: 'smooth' })"), "scroll to tabs")
            time.sleep(1.5)

            safe_action(lambda: page.locator('button:has-text("Multilingual Voice Triage")').first.click(), "click Voice Triage tab")
            time.sleep(3.0)

            safe_action(lambda: page.locator('button:has-text("Hindi:")').first.click(), "click Hindi preset")
            time.sleep(3.0)

            safe_action(lambda: page.locator('button:has-text("Process Syndromic Triage")').first.click(), "click Triage Process")
            time.sleep(7.0)

            safe_action(lambda: page.locator('text=Dark Urine').first.hover(), "hover Dark Urine")
            time.sleep(3.0)
            safe_action(lambda: page.locator('text=Dizziness').first.hover(), "hover Dizziness")
            time.sleep(4.0)

            elapsed = time.time() - t0
            if elapsed < SCENE_TIMINGS['scene4']:
                time.sleep(SCENE_TIMINGS['scene4'] - elapsed)

            # --- SCENE 5: PINN Physics Formulation & OSHAD Matrix (~35s) ---
            print("[5/5] Recording Scene 5: PINN Mathematical Equations & OSHAD Compliance...")
            t0 = time.time()

            safe_action(lambda: page.locator('button:has-text("PINN Physics & Math")').first.click(), "click PINN tab")
            time.sleep(3.0)
            safe_action(lambda: page.evaluate("window.scrollBy({ top: 250, behavior: 'smooth' })"), "scroll down PINN")
            time.sleep(6.0)

            safe_action(lambda: page.locator('text=Core Body Temp').first.hover(), "hover validation metric")
            time.sleep(4.0)

            safe_action(lambda: page.evaluate("window.scrollTo({ top: 80, behavior: 'smooth' })"), "scroll to tabs")
            time.sleep(1.5)
            safe_action(lambda: page.locator('button:has-text("OSHAD SF Compliance")').first.click(), "click OSHAD tab")
            time.sleep(4.0)
            safe_action(lambda: page.evaluate("window.scrollBy({ top: 200, behavior: 'smooth' })"), "scroll OSHAD table")
            time.sleep(6.0)

            safe_action(lambda: page.evaluate("window.scrollTo({ top: 0, behavior: 'smooth' })"), "scroll to top")
            time.sleep(1.5)
            safe_action(lambda: page.locator('button:has-text("Workforce Live Grid")').first.click(), "click Live Grid tab")
            time.sleep(5.0)

            elapsed = time.time() - t0
            if elapsed < SCENE_TIMINGS['scene5']:
                time.sleep(SCENE_TIMINGS['scene5'] - elapsed)

            # Finalize video recording
            print("[*] Finalizing browser video capture...")
            page.close()
            context.close()
            browser.close()

    finally:
        print("Stopping backend and frontend servers...")
        try: backend.terminate()
        except: pass
        try: frontend.terminate()
        except: pass

    # Find the recorded WebM file
    webm_files = list(TEMP_VIDEO_DIR.glob("*.webm"))
    if not webm_files:
        raise FileNotFoundError("Playwright video was not generated in temp_video")

    raw_video = webm_files[0]
    narration_audio = TEMP_AUDIO_DIR / "full_narration.wav"

    print("=" * 70)
    print(f"STEP 3: Muxing Video ({raw_video.name}) + Voiceover Audio ({narration_audio.name})...")
    print("=" * 70)

    ffmpeg_cmd = [
        'ffmpeg', '-y',
        '-i', str(raw_video),
        '-i', str(narration_audio),
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '22',
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-shortest',
        str(OUTPUT_MP4)
    ]

    res = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("[ERROR] FFmpeg failed:", res.stderr)
        raise RuntimeError("FFmpeg muxing failed")

    size_mb = OUTPUT_MP4.stat().st_size / (1024 * 1024)
    print("=" * 70)
    print(f"SUCCESS: Demo video created successfully at:")
    print(f"  --> {OUTPUT_MP4}")
    print(f"  --> Size: {size_mb:.2f} MB")
    print("=" * 70)

if __name__ == "__main__":
    record_walkthrough()
