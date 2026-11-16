# 03 — Med42 Clinical LLM Integration
*Multilingual Conversational Triage & Subclinical Syndromic Extraction*

---

## 1. Why Med42 is the Strategic Anchor for This Challenge

**Med42** is an open-access, clinical-grade Large Language Model developed in Abu Dhabi by **M42** in collaboration with **MBZUAI** and **Cerebras**. Achieving an **85.1% zero-shot score on the USMLE**, it matches proprietary foundation models like GPT-4 and Med-Gemini while running on sovereign infrastructure.

By making Med42 the clinical reasoning engine for BioThermal Twin, this project directly showcases the operational utility of the organizers' own sovereign technology stack within the Abu Dhabi healthcare and occupational safety ecosystem.

---

## 2. The Multilingual Voice Ingestion Flow

In high-density industrial and construction zones in Abu Dhabi (e.g., Musaffah, ICAD, Khalifa Port), workers speak a variety of languages:

```
[Worker Voice Response (Malayalam, Urdu, Hindi, Arabic, Tagalog)]
                           ↓
[Edge Automatic Speech Recognition (Faster-Whisper / OpenAI Whisper)]
                           ↓
[Native Transcribed Text + Detected Language Token]
                           ↓
[Med42-v2 Clinical Reasoning & Syndromic Parser]
                           ↓
[Structured JSON Clinical Biomarker Profile]
```

### The 15-Second Hydration Station Voice Interaction:
When a worker badges in at a chilled water station or transport kiosk, a short audio prompt asks two concise questions in their chosen language:
1. *"How are your muscles feeling today? Any cramps, spasms, or unusual stiffness?"*
2. *"What color was your urine during your last break? (Clear, light yellow, or dark like tea?)"*

---

## 3. Med42 Prompt Engineering & Structured Extraction

Med42 is constrained by a deterministic system prompt to prevent clinical hallucinations and enforce strict JSON output.

### System Prompt Definition:
```markdown
You are Med42-Occupational, a specialized clinical AI designed for the Abu Dhabi Public Health Center (ADPHC) and Department of Health (DoH) occupational surveillance framework.

Your task is to analyze conversational worker self-reports collected during shift hydration check-ins and extract subclinical early indicators of heat-related illness, thermal exhaustion, dehydration, and acute kidney strain (rhabdomyolysis risks).

INPUTS:
- Worker Transcript: Raw text from speech-to-text
- Detected Language: (e.g., ur, ml, hi, ar, en, tl)
- Current Ambient WBGT: (e.g., 34.2°C)

OUTPUT SPECIFICATION:
You must respond strictly with a valid JSON object matching the following schema:
{
  "hydration_status": "NORMAL" | "MILD_DEHYDRATION" | "SEVERE_DEHYDRATION",
  "oliguria_reported": boolean,
  "dark_urine_indicator": boolean,
  "neuromuscular_symptoms": {
    "cramps": boolean,
    "fasciculations": boolean,
    "severe_weakness": boolean
  },
  "cns_symptoms": {
    "headache": boolean,
    "dizziness": boolean,
    "confusion": boolean
  },
  "syndromic_risk_tier": "TIER_0_SAFE" | "TIER_1_MONITOR" | "TIER_2_HYDRATE_REST" | "TIER_3_CLINICAL_TRIAGE",
  "clinical_rationale": "Concise medical reasoning behind the assigned risk tier.",
  "prescribed_immediate_action": "Specific preventive or clinical step."
}
```

### Representative Example 1: Malayalam Input
* **Worker Audio Transcription (Malayalam):**  
  *"Innalkaale thottu kaalukalil nalla vedhana undu, pinne muthram chuvanna niram pole aanu varunnathu."*  
  *(Translation: "Since this morning my legs have severe pain, and my urine is coming out reddish/dark.")*
* **Med42 Extraction Output:**
```json
{
  "hydration_status": "SEVERE_DEHYDRATION",
  "oliguria_reported": true,
  "dark_urine_indicator": true,
  "neuromuscular_symptoms": {
    "cramps": true,
    "fasciculations": false,
    "severe_weakness": true
  },
  "cns_symptoms": {
    "headache": false,
    "dizziness": false,
    "confusion": false
  },
  "syndromic_risk_tier": "TIER_3_CLINICAL_TRIAGE",
  "clinical_rationale": "Reported dark/reddish urine combined with lower-limb myalgia strongly suggests subclinical rhabdomyolysis and myoglobinuria resulting from thermal overexertion.",
  "prescribed_immediate_action": "Immediate cessation of physical labor; transfer to shaded cool recovery zone; administer oral electrolyte solution; schedule baseline serum creatinine and CK test at site medical clinic."
}
```

---

## 4. Integration with the Deterministic Safety Gate

The LLM is **never allowed to make unilateral medical or employment decisions**. 

Its JSON output passes directly into our deterministic `OSHAD Safety Gate`:
1. **Validation Check:** Verifies that all required JSON fields are present and typed correctly.
2. **Co-Occurrence Verification:** Cross-references the LLM's `TIER_3_CLINICAL_TRIAGE` classification against the PINN's real-time Physiological Strain Index ($PSI$).
   * If **both** $PSI \ge 7.0$ **and** Med42 flags dark urine/cramping $\rightarrow$ **Immediate Clinical Alert & Shift Relief Triggered**.
   * If $PSI < 4.0$ but Med42 flags symptoms $\rightarrow$ **Flagged for Routine Secondary Review** (prevents malingering or false positives).
3. **Audit Log:** Writes the entire prompt, raw audio hash, transcription, and JSON output to an immutable JSONL log for clinical governance.

