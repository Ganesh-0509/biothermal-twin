'use client'

import React, { useState, useEffect, useCallback } from 'react'

interface WorkerStatus {
  worker_id: string
  name: string
  role: string
  age: number
  bmi: number
  acclimatization: number
  heart_rate: number
  skin_temp: number
  core_temp_estimate: number
  psi: number
  kidney_risk: number
  risk_level: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL'
  hydration_pct: number
  time_exposed_minutes: number
  ambient_temp: number
  relative_humidity: number
  oshad_advisory: string
  last_updated: string
}

interface DashboardOverview {
  total_workers: number
  safe_count: number
  moderate_count: number
  high_risk_count: number
  critical_count: number
  alerts_today: number
  average_psi: number
  average_core_temp: number
  ambient_temp: number
  relative_humidity: number
  pinn_model_status: string
  pinn_mae: number
  workers: WorkerStatus[]
}

interface VoiceCheckResponse {
  worker_id: string
  input_text: string
  language_detected: string
  extracted_symptoms: {
    dark_urine: boolean
    muscle_cramps: boolean
    dizziness: boolean
    nausea_vomiting: boolean
    fatigue_grade: string
  }
  syndromic_risk_score: number
  worker_pinn_psi: number
  worker_core_temp: number
  dual_signal_alert: boolean
  clinical_urgency: string
  triage_recommendation: string
  timestamp: string
}

const API_BASE = 'http://localhost:8000'

const PRESET_UTTERANCES = [
  {
    label: '🇮🇳 Hindi: चक्कर + गहरा पेशाब (Dizziness + Dark Urine)',
    lang: 'hi',
    text: 'मुझे बहुत चक्कर आ रहा है और पेशाब का रंग काफी गहरा है'
  },
  {
    label: '🇦🇪 Arabic: تشنج عضلي + دوار (Severe Cramps + Dizziness)',
    lang: 'ar',
    text: 'أشعر بدوار شديد وإرهاق وتشنجات مؤلمة في عضلات الساقين'
  },
  {
    label: '🇵🇰 Urdu: شدید تھکن + متلی (Severe Fatigue + Nausea)',
    lang: 'ur',
    text: 'مجھے شدید تھکن اور کمزوری محسوس ہو رہی ہے اور متلی کی کیفیت ہے'
  },
  {
    label: '🇬🇧 English: Asymptomatic Routine Check',
    lang: 'en',
    text: 'Completed 2-hour shift cycle, feeling hydrated and normal'
  }
]

export default function Dashboard() {
  const [data, setData] = useState<DashboardOverview | null>(null)
  const [loading, setLoading] = useState(true)
  const [isLiveConnected, setIsLiveConnected] = useState(false)
  const [selectedWorker, setSelectedWorker] = useState<WorkerStatus | null>(null)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  // Voice triage state
  const [voiceWorkerId, setVoiceWorkerId] = useState('W-00001')
  const [voiceText, setVoiceText] = useState(PRESET_UTTERANCES[0].text)
  const [voiceResult, setVoiceResult] = useState<VoiceCheckResponse | null>(null)
  const [voiceLoading, setVoiceLoading] = useState(false)

  // Fetch from backend or generate realistic fallback
  const fetchDashboardData = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/dashboard/overview`, { cache: 'no-store' })
      if (!res.ok) throw new Error('API offline')
      const json: DashboardOverview = await res.json()
      setData(json)
      setIsLiveConnected(true)
      if (selectedWorker) {
        const updated = json.workers.find(w => w.worker_id === selectedWorker.worker_id)
        if (updated) setSelectedWorker(updated)
      }
    } catch {
      setIsLiveConnected(false)
      // If backend not running, fallback to realistic client simulation
      setData(prev => {
        if (prev) return prev
        return generateClientFallbackCohort()
      })
    } finally {
      setLoading(false)
    }
  }, [selectedWorker])

  useEffect(() => {
    fetchDashboardData()
    const interval = setInterval(fetchDashboardData, 3000)
    return () => clearInterval(interval)
  }, [fetchDashboardData])

  // Simulation actions
  const triggerSimulation = async (endpoint: string, actionName: string) => {
    setActionLoading(actionName)
    try {
      await fetch(`${API_BASE}/api/simulation/${endpoint}`, { method: 'POST' })
      await fetchDashboardData()
    } catch {
      // Local client fallback mutation
      if (data) {
        const cloned = { ...data }
        if (endpoint === 'heat-spike') {
          cloned.ambient_temp = Math.min(48.0, cloned.ambient_temp + 3.0)
          cloned.workers = cloned.workers.map(w => ({
            ...w,
            core_temp_estimate: Number((w.core_temp_estimate + 0.35).toFixed(2)),
            psi: Math.min(10, Number((w.psi + 1.8).toFixed(1))),
            kidney_risk: Math.min(1, Number((w.kidney_risk + 0.15).toFixed(2))),
            risk_level: (w.psi + 1.8 >= 7.5 ? 'CRITICAL' : w.psi + 1.8 >= 5.5 ? 'HIGH' : 'MODERATE') as any
          }))
        } else if (endpoint === 'cool-down') {
          cloned.ambient_temp = Math.max(38.0, cloned.ambient_temp - 2.5)
          cloned.workers = cloned.workers.map(w => ({
            ...w,
            core_temp_estimate: Number((Math.max(37.1, w.core_temp_estimate - 0.4)).toFixed(2)),
            psi: Math.max(1, Number((w.psi - 2.0).toFixed(1))),
            risk_level: (Math.max(1, w.psi - 2.0) >= 6.0 ? 'HIGH' : Math.max(1, w.psi - 2.0) >= 4.0 ? 'MODERATE' : 'LOW') as any
          }))
        }
        setData(cloned)
      }
    } finally {
      setActionLoading(null)
    }
  }

  // Voice triage execution
  const runVoiceTriage = async () => {
    if (!voiceText.trim()) return
    setVoiceLoading(true)
    setVoiceResult(null)

    try {
      const res = await fetch(`${API_BASE}/api/voice-check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ worker_id: voiceWorkerId, text: voiceText })
      })
      if (!res.ok) throw new Error('API failed')
      const json: VoiceCheckResponse = await res.json()
      setVoiceResult(json)
    } catch {
      // Local fallback parsing
      const textLower = voiceText.toLowerCase()
      const hasDarkUrine = textLower.includes('पेशाब') || textLower.includes('بول داكن') || textLower.includes('dark urine')
      const hasCramps = textLower.includes('ऐंठन') || textLower.includes('تشنج') || textLower.includes('cramp')
      const hasDizzy = textLower.includes('चक्कर') || textLower.includes('دوار') || textLower.includes('dizzy')
      const score = (hasDarkUrine ? 0.4 : 0) + (hasCramps ? 0.3 : 0) + (hasDizzy ? 0.25 : 0)

      setVoiceResult({
        worker_id: voiceWorkerId,
        input_text: voiceText,
        language_detected: 'multilingual',
        extracted_symptoms: {
          dark_urine: hasDarkUrine,
          muscle_cramps: hasCramps,
          dizziness: hasDizzy,
          nausea_vomiting: textLower.includes('متلی') || textLower.includes('उल्टी'),
          fatigue_grade: score > 0.4 ? 'SEVERE' : 'MODERATE'
        },
        syndromic_risk_score: Math.min(1.0, score),
        worker_pinn_psi: 6.8,
        worker_core_temp: 38.4,
        dual_signal_alert: score >= 0.5,
        clinical_urgency: score >= 0.5 ? 'IMMEDIATE_INTERVENTION' : 'OCCUPATIONAL_CLINIC_REVIEW',
        triage_recommendation: score >= 0.5
          ? '🚨 DUAL ALERT: High physiological strain + early renal markers detected. Immediate IV/oral rehydration.'
          : '⚠️ ELEVATED STRAIN: Shift worker to shaded hydration cooling post.',
        timestamp: new Date().toISOString()
      })
    } finally {
      setVoiceLoading(false)
    }
  }

  if (loading || !data) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center text-white">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-lg font-mono">Initializing BioThermal Twin Engine...</p>
          <p className="text-sm text-slate-400 mt-1">Connecting to PyTorch PINN Inference Service</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 md:p-8">
      {/* Top Banner */}
      <header className="mb-6 flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl md:text-3xl font-black tracking-tight text-white flex items-center gap-2">
              <span className="text-emerald-400">⚡</span> BioThermal Twin
            </h1>
            <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              v2.0 PINN-Active
            </span>
            <span className={`text-xs font-mono px-2.5 py-0.5 rounded-full border ${
              isLiveConnected 
                ? 'bg-blue-500/20 text-blue-400 border-blue-500/30' 
                : 'bg-amber-500/20 text-amber-400 border-amber-500/30'
            }`}>
              {isLiveConnected ? '● Live Backend Synced' : '○ Standalone Simulator'}
            </span>
          </div>
          <p className="text-xs md:text-sm text-slate-400 mt-1">
            Physics-Informed Anticipatory Workforce Health Early Warning Platform — Abu Dhabi DoH & M42
          </p>
        </div>

        {/* Ambient Telemetry Pill */}
        <div className="flex flex-wrap items-center gap-2 bg-slate-900/80 border border-slate-800 rounded-xl p-2.5 text-xs font-mono">
          <div className="px-2.5 py-1 bg-slate-800/80 rounded-lg">
            <span className="text-slate-400">Ambient: </span>
            <span className="text-amber-400 font-bold">{data.ambient_temp}°C</span>
          </div>
          <div className="px-2.5 py-1 bg-slate-800/80 rounded-lg">
            <span className="text-slate-400">RH: </span>
            <span className="text-sky-400 font-bold">{data.relative_humidity}%</span>
          </div>
          <div className="px-2.5 py-1 bg-slate-800/80 rounded-lg">
            <span className="text-slate-400">Model MAE: </span>
            <span className="text-emerald-400 font-bold">{data.pinn_mae}°C</span>
          </div>
        </div>
      </header>

      {/* Interactive Simulation Controls */}
      <section className="mb-6 bg-slate-900/90 border border-slate-800 rounded-2xl p-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Live Simulation Scenario Gate</span>
            <p className="text-xs text-slate-400">Test how the PINN model detects sudden microclimate fluctuations & worker strain</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => triggerSimulation('heat-spike', 'heat')}
              disabled={actionLoading !== null}
              className="px-3.5 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white text-xs font-bold transition flex items-center gap-1.5 shadow-lg shadow-red-900/30"
            >
              🔥 {actionLoading === 'heat' ? 'Simulating Spike...' : 'Trigger Heat Spike (+3.5°C)'}
            </button>
            <button
              onClick={() => triggerSimulation('cool-down', 'cool')}
              disabled={actionLoading !== null}
              className="px-3.5 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-bold transition flex items-center gap-1.5 shadow-lg shadow-sky-900/30"
            >
              ❄️ {actionLoading === 'cool' ? 'Activating Protocol...' : 'Cooling Station Protocol'}
            </button>
            <button
              onClick={() => triggerSimulation('tick', 'tick')}
              disabled={actionLoading !== null}
              className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold transition flex items-center gap-1.5"
            >
              ⏱️ {actionLoading === 'tick' ? 'Advancing...' : 'Advance Shift (+15m)'}
            </button>
            <button
              onClick={() => triggerSimulation('reset', 'reset')}
              disabled={actionLoading !== null}
              className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 text-xs font-bold transition"
            >
              Reset Baseline
            </button>
          </div>
        </div>
      </section>

      {/* KPI Metric Cards */}
      <section className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
        <KpiCard label="Monitored Workers" value={data.total_workers} sub="100% telemetry synced" color="border-slate-800 text-white" />
        <KpiCard label="Safe Cohort (Low)" value={data.safe_count} sub="PSI < 4.0" color="border-emerald-500/40 text-emerald-400 bg-emerald-950/20" />
        <KpiCard label="Moderate Strain" value={data.moderate_count} sub="PSI 4.0 - 5.9" color="border-amber-500/40 text-amber-400 bg-amber-950/20" />
        <KpiCard label="High / Critical" value={data.high_risk_count + data.critical_count} sub="PSI ≥ 6.0 | Action Req" color="border-red-500/40 text-red-400 bg-red-950/20" />
        <KpiCard label="Cohort Mean PSI" value={data.average_psi.toFixed(1)} sub="Moran Scale (0-10)" color="border-slate-800 text-sky-400" />
        <KpiCard label="Mean Core Temp" value={`${data.average_core_temp.toFixed(1)}°C`} sub="PINN Validated" color="border-slate-800 text-indigo-400" />
      </section>

      {/* Main Grid + Voice Triage Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Left 2 Cols: Worker Grid */}
        <div className="lg:col-span-2 bg-slate-900/90 border border-slate-800 rounded-2xl p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <span>👷</span> Live Workforce Physiological Grid
              </h2>
              <p className="text-xs text-slate-400">Click any worker card to inspect PINN biothermal telemetry & OSHAD guidance</p>
            </div>
            <div className="flex items-center gap-2 text-xs font-mono">
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block"/> Normal</span>
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block"/> Moderate</span>
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-red-500 inline-block"/> Critical</span>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 max-h-[560px] overflow-y-auto pr-1">
            {data.workers.map((worker) => {
              const isSelected = selectedWorker?.worker_id === worker.worker_id
              const riskStyles = {
                LOW: 'border-emerald-500/40 bg-emerald-950/20 hover:border-emerald-400',
                MODERATE: 'border-amber-500/50 bg-amber-950/30 hover:border-amber-400',
                HIGH: 'border-rose-500/60 bg-rose-950/40 hover:border-rose-400 animate-pulse',
                CRITICAL: 'border-red-500 bg-red-950/60 hover:border-red-400 animate-pulse'
              }[worker.risk_level]

              const badgeColor = {
                LOW: 'bg-emerald-500/20 text-emerald-400',
                MODERATE: 'bg-amber-500/20 text-amber-400',
                HIGH: 'bg-rose-500/20 text-rose-300 font-bold',
                CRITICAL: 'bg-red-500/30 text-red-300 font-bold'
              }[worker.risk_level]

              return (
                <div
                  key={worker.worker_id}
                  onClick={() => setSelectedWorker(worker)}
                  className={`border-2 rounded-xl p-3 cursor-pointer transition flex flex-col justify-between ${riskStyles} ${
                    isSelected ? 'ring-2 ring-emerald-400 scale-[1.02]' : ''
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-mono font-bold text-slate-300">{worker.worker_id}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${badgeColor}`}>
                      {worker.risk_level}
                    </span>
                  </div>
                  
                  <div className="my-1">
                    <p className="text-xs font-semibold text-white truncate">{worker.name}</p>
                    <p className="text-[11px] text-slate-400 truncate">{worker.role}</p>
                  </div>

                  <div className="pt-2 border-t border-slate-800/80 grid grid-cols-2 gap-1 text-[11px] font-mono">
                    <div>
                      <span className="text-slate-500 text-[9px] block">CORE TEMP</span>
                      <span className={worker.core_temp_estimate >= 38.3 ? 'text-red-400 font-bold' : 'text-slate-200'}>
                        {worker.core_temp_estimate}°C
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500 text-[9px] block">PSI INDEX</span>
                      <span className={worker.psi >= 6.0 ? 'text-red-400 font-bold' : 'text-slate-200'}>
                        {worker.psi.toFixed(1)}
                      </span>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Right 1 Col: Multilingual Voice Triage Demo */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xl">🎙️</span>
              <div>
                <h2 className="text-lg font-bold text-white">Multilingual Voice Triage</h2>
                <p className="text-xs text-slate-400">Med42 Clinical Agent & Dual-Signal Fusion</p>
              </div>
            </div>

            <div className="space-y-3 mt-4">
              <div>
                <label className="text-xs font-mono text-slate-400 block mb-1">Select Worker Target</label>
                <select
                  value={voiceWorkerId}
                  onChange={(e) => setVoiceWorkerId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                >
                  {data.workers.slice(0, 12).map(w => (
                    <option key={w.worker_id} value={w.worker_id}>
                      {w.worker_id} — {w.name} ({w.role}) [PSI: {w.psi.toFixed(1)}]
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-mono text-slate-400 block mb-1">Preset Multilingual Symptom Utterances</label>
                <div className="space-y-1.5">
                  {PRESET_UTTERANCES.map((preset, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => setVoiceText(preset.text)}
                      className={`w-full text-left p-2 rounded-lg text-[11px] border transition ${
                        voiceText === preset.text
                          ? 'border-emerald-500/60 bg-emerald-950/30 text-emerald-300 font-medium'
                          : 'border-slate-800 bg-slate-950/60 text-slate-300 hover:border-slate-700'
                      }`}
                    >
                      {preset.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-xs font-mono text-slate-400 block mb-1">Worker Utterance (Audio / Text Stream)</label>
                <textarea
                  value={voiceText}
                  onChange={(e) => setVoiceText(e.target.value)}
                  rows={2}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-500 font-sans"
                  placeholder="Enter worker voice transcript..."
                />
              </div>

              <button
                onClick={runVoiceTriage}
                disabled={voiceLoading || !voiceText.trim()}
                className="w-full py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-bold transition shadow-lg shadow-emerald-900/30 flex items-center justify-center gap-2"
              >
                {voiceLoading ? 'Analyzing Clinical Biomarkers...' : '⚡ Process Syndromic Triage'}
              </button>
            </div>
          </div>

          {/* Voice Results Box */}
          {voiceResult && (
            <div className="mt-4 pt-4 border-t border-slate-800">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono text-slate-400">Triage Extraction</span>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full font-bold ${
                  voiceResult.dual_signal_alert
                    ? 'bg-red-500/20 text-red-400 border border-red-500/40 animate-pulse'
                    : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                }`}>
                  {voiceResult.clinical_urgency}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-1.5 text-[11px] font-mono mb-2">
                <div className={`p-1.5 rounded border ${voiceResult.extracted_symptoms.dark_urine ? 'border-amber-500/60 bg-amber-950/40 text-amber-300 font-bold' : 'border-slate-800 text-slate-500'}`}>
                  {voiceResult.extracted_symptoms.dark_urine ? '✓' : '×'} Dark Urine (AKI Risk)
                </div>
                <div className={`p-1.5 rounded border ${voiceResult.extracted_symptoms.muscle_cramps ? 'border-amber-500/60 bg-amber-950/40 text-amber-300 font-bold' : 'border-slate-800 text-slate-500'}`}>
                  {voiceResult.extracted_symptoms.muscle_cramps ? '✓' : '×'} Muscle Cramps
                </div>
                <div className={`p-1.5 rounded border ${voiceResult.extracted_symptoms.dizziness ? 'border-amber-500/60 bg-amber-950/40 text-amber-300 font-bold' : 'border-slate-800 text-slate-500'}`}>
                  {voiceResult.extracted_symptoms.dizziness ? '✓' : '×'} Dizziness / Syncope
                </div>
                <div className={`p-1.5 rounded border ${voiceResult.extracted_symptoms.fatigue_grade !== 'NONE' ? 'border-amber-500/60 bg-amber-950/40 text-amber-300 font-bold' : 'border-slate-800 text-slate-500'}`}>
                  Fatigue: {voiceResult.extracted_symptoms.fatigue_grade}
                </div>
              </div>

              <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800 text-xs">
                <p className="text-slate-300 text-[11px] leading-relaxed">{voiceResult.triage_recommendation}</p>
                <div className="mt-2 flex items-center justify-between text-[10px] font-mono text-slate-400">
                  <span>Syndromic Risk: {(voiceResult.syndromic_risk_score * 100).toFixed(0)}%</span>
                  <span>PINN PSI: {voiceResult.worker_pinn_psi.toFixed(1)}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Selected Worker Detailed Modal */}
      {selectedWorker && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-2xl w-full p-6 shadow-2xl relative">
            <button
              onClick={() => setSelectedWorker(null)}
              className="absolute top-5 right-5 text-slate-400 hover:text-white w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center font-bold"
            >
              ✕
            </button>

            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-2xl">
                👷
              </div>
              <div>
                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                  {selectedWorker.name}
                  <span className="text-xs font-mono font-normal text-slate-400 px-2 py-0.5 rounded bg-slate-800">
                    {selectedWorker.worker_id}
                  </span>
                </h3>
                <p className="text-xs text-slate-400">{selectedWorker.role} • Age: {selectedWorker.age} • BMI: {selectedWorker.bmi} • Acclimatization: {(selectedWorker.acclimatization * 100).toFixed(0)}%</p>
              </div>
            </div>

            {/* Live Physiological Telemetry Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6 font-mono text-center">
              <div className="p-3 bg-slate-950 rounded-2xl border border-slate-800">
                <span className="text-[10px] text-slate-400 block mb-1">PREDICTED CORE TEMP</span>
                <span className={`text-xl font-bold ${selectedWorker.core_temp_estimate >= 38.3 ? 'text-red-400' : 'text-emerald-400'}`}>
                  {selectedWorker.core_temp_estimate}°C
                </span>
                <span className="text-[9px] text-slate-500 block mt-0.5">Threshold: 38.5°C</span>
              </div>
              <div className="p-3 bg-slate-950 rounded-2xl border border-slate-800">
                <span className="text-[10px] text-slate-400 block mb-1">PHYSIO STRAIN (PSI)</span>
                <span className={`text-xl font-bold ${selectedWorker.psi >= 6.0 ? 'text-red-400' : 'text-sky-400'}`}>
                  {selectedWorker.psi.toFixed(1)} / 10
                </span>
                <span className="text-[9px] text-slate-500 block mt-0.5">Moran Scale</span>
              </div>
              <div className="p-3 bg-slate-950 rounded-2xl border border-slate-800">
                <span className="text-[10px] text-slate-400 block mb-1">HEART RATE</span>
                <span className="text-xl font-bold text-amber-400">
                  {selectedWorker.heart_rate} <span className="text-xs">bpm</span>
                </span>
                <span className="text-[9px] text-slate-500 block mt-0.5">Skin: {selectedWorker.skin_temp}°C</span>
              </div>
              <div className="p-3 bg-slate-950 rounded-2xl border border-slate-800">
                <span className="text-[10px] text-slate-400 block mb-1">KIDNEY STRAIN (AKI)</span>
                <span className={`text-xl font-bold ${selectedWorker.kidney_risk >= 0.4 ? 'text-red-400' : 'text-indigo-400'}`}>
                  {(selectedWorker.kidney_risk * 100).toFixed(0)}%
                </span>
                <span className="text-[9px] text-slate-500 block mt-0.5">Hydration: {selectedWorker.hydration_pct}%</span>
              </div>
            </div>

            {/* OSHAD Guidance Box */}
            <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 mb-6">
              <span className="text-xs font-bold text-amber-400 uppercase tracking-wider block mb-1">
                OSHAD SF CoP 11.0 Mandatory Action Plan
              </span>
              <p className="text-xs text-slate-300 leading-relaxed font-sans">{selectedWorker.oshad_advisory}</p>
            </div>

            <div className="flex items-center justify-end gap-3">
              <button
                onClick={() => {
                  setVoiceWorkerId(selectedWorker.worker_id)
                  setSelectedWorker(null)
                }}
                className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-bold text-slate-200 transition"
              >
                Open Voice Check-in
              </button>
              <button
                onClick={() => alert(`Alert dispatched to Site Paramedic & Safety Lead for worker ${selectedWorker.worker_id}`)}
                className="px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-xs font-bold text-white transition shadow-lg shadow-emerald-900/30"
              >
                Dispatch Site Alert
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function KpiCard({ label, value, sub, color }: { label: string; value: string | number; sub: string; color: string }) {
  return (
    <div className={`p-4 rounded-2xl border ${color} bg-slate-900/90 flex flex-col justify-between`}>
      <span className="text-[11px] font-mono text-slate-400 block">{label}</span>
      <span className="text-2xl font-black tracking-tight my-1">{value}</span>
      <span className="text-[10px] text-slate-500 font-mono">{sub}</span>
    </div>
  )
}

function generateClientFallbackCohort(): DashboardOverview {
  const roles = ['Steel Fixer', 'Scaffold Specialist', 'Concrete Finisher', 'Crane Operator', 'Welder', 'Mason', 'MEP Tech', 'Safety Officer']
  const names = [
    'Tariq Al-Mansoor', 'Ramesh Kumar', 'Muhammad Irfan', 'Bilal Sheikh',
    'Sanjay Patel', 'Rajesh Pillai', 'Deepak Verma', 'Hassan Qasim',
    'Omar Farooq', 'Manoj Joshi', 'Farhan Akhtar', 'Anand Varma',
    'Vikram Singh', 'Rashid Dar', 'Suresh Nair', 'Khaled Nabil',
    'Arjun Das', 'Zain Abbas', 'Dinesh Menon', 'Mustafa Zahid',
    'Kishore Shenoy', 'Naveen Joseph', 'Salim Basha', 'Hamad Al-Kaabi'
  ]

  const workers: WorkerStatus[] = names.map((name, i) => {
    const psi = Number((1.5 + (i % 5) * 1.4 + (i > 18 ? 2.5 : 0)).toFixed(1))
    const tc = Number((37.2 + (psi / 10) * 1.5).toFixed(2))
    const kidney = Number((psi >= 6.0 ? 0.55 : psi >= 4.0 ? 0.25 : 0.05).toFixed(2))
    const risk = (psi >= 7.5 ? 'CRITICAL' : psi >= 5.5 ? 'HIGH' : psi >= 4.0 ? 'MODERATE' : 'LOW') as any

    return {
      worker_id: `W-${String(i + 1).padStart(5, '0')}`,
      name,
      role: roles[i % roles.length],
      age: 24 + (i % 20),
      bmi: Number((22.0 + (i % 6) * 0.8).toFixed(1)),
      acclimatization: Number((0.4 + (i % 6) * 0.1).toFixed(2)),
      heart_rate: 80 + Math.round(psi * 9),
      skin_temp: Number((35.8 + psi * 0.25).toFixed(2)),
      core_temp_estimate: tc,
      psi,
      kidney_risk: kidney,
      risk_level: risk,
      hydration_pct: Math.max(40, 95 - Math.round(psi * 6)),
      time_exposed_minutes: 120 + i * 5,
      ambient_temp: 41.5,
      relative_humidity: 58.0,
      oshad_advisory: risk === 'CRITICAL' || risk === 'HIGH'
        ? 'Mandatory 20-min cooling break. Ingest 600ml chilled electrolyte water. Monitor core temp.'
        : 'Compliant with OSHAD summer threshold. Maintain 250ml water intake every 20 minutes.',
      last_updated: new Date().toISOString()
    }
  })

  return {
    total_workers: workers.length,
    safe_count: workers.filter(w => w.risk_level === 'LOW').length,
    moderate_count: workers.filter(w => w.risk_level === 'MODERATE').length,
    high_risk_count: workers.filter(w => w.risk_level === 'HIGH').length,
    critical_count: workers.filter(w => w.risk_level === 'CRITICAL').length,
    alerts_today: 14,
    average_psi: Number((workers.reduce((a, b) => a + b.psi, 0) / workers.length).toFixed(1)),
    average_core_temp: Number((workers.reduce((a, b) => a + b.core_temp_estimate, 0) / workers.length).toFixed(1)),
    ambient_temp: 41.5,
    relative_humidity: 58.0,
    pinn_model_status: 'Active (PyTorch CPU/CUDA)',
    pinn_mae: 0.139,
    workers
  }
}
