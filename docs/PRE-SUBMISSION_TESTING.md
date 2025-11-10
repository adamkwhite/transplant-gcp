# Pre-Submission Testing Checklist
## Google Cloud Run Hackathon 2025 - Final Verification

**Date:** 2025-11-10 (Submission Day)
**Service URL:** https://missed-dose-service-978611421547.us-central1.run.app

---

## Critical Fix Applied

**Problem:** GEMINI_API_KEY was being lost on every deployment
**Root Cause:** `deploy.sh` only set `GOOGLE_CLOUD_PROJECT` env var, not `GEMINI_API_KEY`
**Fix:** Updated `deploy.sh` to automatically load API key from `.env` and set it on Cloud Run
**Status:** ✅ Fixed in commit 4aec8a3

---

## Test Checklist

### 1. Cloud Run Landing Page
**URL:** https://missed-dose-service-978611421547.us-central1.run.app/

**Expected:**
- ✅ Professional landing page with Google brand colors
- ✅ Shows 5 AI agent cards
- ✅ Technology stack badges (Cloud Run, ADK, Gemini 2.0 Flash, Firestore)
- ✅ Curl command shows `/medications/missed-dose` endpoint (not `/health`)
- ✅ Description mentions: "AI reasoning chain • Medical recommendation • Risk assessment • SRTR data citations"
- ✅ GitHub link works: https://github.com/adamkwhite/transplant-gcp
- ✅ Health button works: /health endpoint

**Test Command:**
```bash
curl -s https://missed-dose-service-978611421547.us-central1.run.app/ | grep "TransplantGuard AI"
```

---

### 2. Health Endpoint
**URL:** https://missed-dose-service-978611421547.us-central1.run.app/health

**Expected JSON:**
```json
{
  "status": "healthy",
  "service": "missed-dose-analysis",
  "platform": "Google Cloud Run",
  "ai_system": "Google ADK Multi-Agent System",
  "agents": {
    "coordinator": "TransplantCoordinator",
    "specialists": [
      "MedicationAdvisor",
      "RejectionRiskAnalyzer",
      "SymptomMonitor",
      "DrugInteractionChecker"
    ]
  },
  "ai_model": "gemini-2.0-flash-exp",
  "adk_version": "1.17.0"
}
```

**Test Command:**
```bash
curl -s https://missed-dose-service-978611421547.us-central1.run.app/health | jq .
```

**Critical Check:**
- ✅ Returns 200 status
- ✅ Shows all 5 agents (4 specialists + coordinator)
- ✅ ai_model is "gemini-2.0-flash-exp"
- ✅ adk_version is "1.17.0"

---

### 3. Medication Missed Dose API (Most Important!)
**URL:** https://missed-dose-service-978611421547.us-central1.run.app/medications/missed-dose

**Test Command:**
```bash
curl -X POST https://missed-dose-service-978611421547.us-central1.run.app/medications/missed-dose \
  -H "Content-Type: application/json" \
  -d '{
    "medication": "tacrolimus",
    "scheduled_time": "8:00 AM",
    "current_time": "2:00 PM",
    "patient_id": "demo_patient"
  }' | jq .
```

**Expected Response Structure:**
```json
{
  "recommendation": "Take the Tacrolimus dose now. Do not double the next dose.",
  "reasoning_chain": [
    "The patient is 6 hours late on their Tacrolimus dose.",
    "Tacrolimus has a narrow therapeutic window and is critical for preventing rejection.",
    "The patient is within the 12-hour window for taking the dose.",
    "Given the importance of Tacrolimus, it is better to take the dose late than to skip it.",
    "The patient's adherence rate is 0.8, indicating generally good adherence...",
    "The patient has not missed any doses this week..."
  ],
  "risk_level": "medium" or "moderate",
  "confidence": 0.85,
  "next_steps": [
    "Monitor for any signs of rejection...",
    "Check Tacrolimus levels at the next scheduled blood draw...",
    "Reinforce the importance of medication adherence...",
    "Investigate the reason for the missed dose...",
    "Consider a follow-up phone call in 24 hours..."
  ],
  "adherence_metrics": {
    "current_rate": "80%",
    "doses_missed_this_week": 0
  },
  "medication_details": {
    "name": "Tacrolimus",
    "category": "calcineurin_inhibitor",
    "critical": true,
    "time_window_hours": 12,
    "target_levels": "5-15 ng/mL",
    "half_life": "12 hours",
    "interactions": ["grapefruit", "ketoconazole", "erythromycin"]
  },
  "infrastructure": {
    "platform": "Google Cloud Run",
    "database": "Firestore",
    "ai_system": "Google ADK Multi-Agent System",
    "ai_model": "gemini-2.0-flash-exp",
    "agent_used": "MedicationAdvisor",
    "region": "us-central1"
  }
}
```

**Critical Checks:**
- ✅ NO ERROR about missing API key
- ✅ Returns medical recommendation (not error)
- ✅ reasoning_chain has 5+ steps showing AI logic
- ✅ next_steps has 5+ clinical actions
- ✅ SRTR data source cited
- ✅ infrastructure shows "gemini-2.0-flash-exp"
- ✅ Response time < 5 seconds

**If Error:** "Missing key inputs argument" = API key not set (FAILED)

---

### 4. Rejection Risk Analysis API
**URL:** https://missed-dose-service-978611421547.us-central1.run.app/rejection/analyze

**Test Command:**
```bash
curl -X POST https://missed-dose-service-978611421547.us-central1.run.app/rejection/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "symptoms": {
      "fever": true,
      "decreased_urine_output": true,
      "tenderness": true,
      "fever_temperature": 101.5
    },
    "patient_id": "demo_patient"
  }' | jq .
```

**Expected Response Structure:**
```json
{
  "rejection_probability": 0.75,
  "urgency": "HIGH",
  "risk_level": "critical",
  "recommended_action": "Contact transplant team immediately",
  "reasoning_steps": [
    "Analysis of symptoms...",
    "Comparison with SRTR rejection data...",
    "Risk assessment based on patient context..."
  ],
  "similar_cases": [
    {
      "organ": "kidney",
      "outcome": "rejection",
      "similarity": 0.85
    }
  ],
  "infrastructure": {
    "platform": "Google Cloud Run",
    "database": "Firestore",
    "ai_system": "Google ADK Multi-Agent System",
    "ai_model": "gemini-2.0-flash-exp",
    "agent_used": "RejectionRiskAnalyzer",
    "region": "us-central1"
  }
}
```

**Critical Checks:**
- ✅ NO ERROR about missing API key
- ✅ Returns rejection_probability (0.0 - 1.0)
- ✅ urgency is set (LOW, MEDIUM, HIGH)
- ✅ recommended_action is provided
- ✅ reasoning_steps shows AI logic
- ✅ similar_cases from SRTR data
- ✅ Response time < 5 seconds

---

### 5. Netlify Frontend Demo
**URL:** https://transplant-medication-demo.netlify.app

**Expected:**
- ✅ Loads without errors
- ✅ Google Blue/Green brand colors (not purple)
- ✅ Title is "TransplantGuard AI" (not "Transplant Medication Adherence Agent")
- ✅ Subtitle: "Multi-Agent AI System | Google ADK + Gemini 2.0 Flash + Cloud Run"
- ✅ Can select patient (Maria Rodriguez, John Chen, Sarah Ahmed)
- ✅ "Analyze Missed Dose" button works
- ✅ Calls correct Cloud Run URL: https://missed-dose-service-978611421547.us-central1.run.app
- ✅ Response shows AI reasoning and recommendations

**Test:**
1. Open https://transplant-medication-demo.netlify.app in browser
2. Select patient: Maria Rodriguez
3. Select medication: Tacrolimus
4. Set scheduled time: 8:00 AM
5. Set current time: 2:00 PM
6. Click "Analyze Missed Dose"
7. Verify response appears with:
   - Recommendation text
   - Risk level badge
   - Reasoning steps
   - Next steps
   - Infrastructure info showing Cloud Run

---

### 6. Environment Variables Verification
**Check Cloud Run has GEMINI_API_KEY set:**

```bash
gcloud run services describe missed-dose-service \
  --region=us-central1 \
  --format="value(spec.template.spec.containers[0].env)"
```

**Expected Output:**
```
{'name': 'GOOGLE_CLOUD_PROJECT', 'value': 'transplant-prediction'}
{'name': 'GEMINI_API_KEY', 'value': 'AIza...'}
```

**Critical Check:**
- ✅ GEMINI_API_KEY is present
- ✅ Value starts with "AIza"

**If Missing:** Run `./deploy.sh` again (should auto-load from .env)

---

### 7. Error Cases (Should Handle Gracefully)

**Test Unknown Medication:**
```bash
curl -X POST https://missed-dose-service-978611421547.us-central1.run.app/medications/missed-dose \
  -H "Content-Type: application/json" \
  -d '{
    "medication": "unknown_drug",
    "scheduled_time": "8:00 AM",
    "current_time": "2:00 PM",
    "patient_id": "demo_patient"
  }' | jq .
```

**Expected:**
- ✅ Returns 200 status (not error)
- ✅ Message: "Medication 'unknown_drug' is not in our database"
- ✅ Recommendation: "Contact your transplant team immediately"
- ✅ risk_level: "unknown"

**Test Missing Required Fields:**
```bash
curl -X POST https://missed-dose-service-978611421547.us-central1.run.app/medications/missed-dose \
  -H "Content-Type: application/json" \
  -d '{"medication": "tacrolimus"}' | jq .
```

**Expected:**
- ✅ Returns 400 status
- ✅ Error message: "Missing required fields"
- ✅ Lists which fields are missing

**Test Invalid JSON:**
```bash
curl -X POST https://missed-dose-service-978611421547.us-central1.run.app/medications/missed-dose \
  -H "Content-Type: application/json" \
  -d 'not valid json' | jq .
```

**Expected:**
- ✅ Returns 400 status
- ✅ Error: "Invalid JSON - request body must be valid JSON"

---

## Demo Video Verification

**After final deployment, test these exact commands for the video:**

### Command 1: Health Check
```bash
curl https://missed-dose-service-978611421547.us-central1.run.app/health | jq
```

### Command 2: Missed Dose (Main Demo)
```bash
curl -X POST https://missed-dose-service-978611421547.us-central1.run.app/medications/missed-dose \
  -H "Content-Type: application/json" \
  -d '{
    "medication": "tacrolimus",
    "scheduled_time": "8:00 AM",
    "current_time": "2:00 PM",
    "patient_id": "demo_patient"
  }' | jq
```

### Command 3: Rejection Analysis
```bash
curl -X POST https://missed-dose-service-978611421547.us-central1.run.app/rejection/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "symptoms": {
      "fever": true,
      "decreased_urine_output": true,
      "tenderness": true,
      "fever_temperature": 101.5
    },
    "patient_id": "demo_patient"
  }' | jq
```

**All three commands MUST work for the video!**

---

## Final Deployment Checklist

Before recording demo video:

- [ ] Run `./deploy.sh` one final time
- [ ] Wait for deployment to complete (3-5 minutes)
- [ ] Test all 3 API endpoints above
- [ ] Verify Netlify demo works
- [ ] Check GitHub repo is public
- [ ] Verify all URLs in DEVPOST_COMPLETE_SUBMISSION.md are correct
- [ ] Open landing page in browser to verify professional design
- [ ] Practice curl commands to ensure smooth video recording

---

## If Something Fails

**API Key Error:**
```bash
# Manually set the key
gcloud run services update missed-dose-service \
  --set-env-vars GEMINI_API_KEY=$(grep GEMINI_API_KEY .env | cut -d '=' -f2) \
  --region=us-central1
```

**Deployment Issues:**
```bash
# Check logs
gcloud run services logs read missed-dose-service --region=us-central1 --limit=50

# Check service status
gcloud run services describe missed-dose-service --region=us-central1
```

**Landing Page Not Showing:**
- Make sure you're visiting the root: https://missed-dose-service-978611421547.us-central1.run.app/
- NOT /health endpoint

---

## Success Criteria

**All systems are GO when:**

1. ✅ Landing page loads with professional design
2. ✅ `/health` returns all 5 agents
3. ✅ `/medications/missed-dose` returns AI recommendation with reasoning
4. ✅ `/rejection/analyze` returns risk assessment with SRTR data
5. ✅ Netlify demo connects to Cloud Run and shows responses
6. ✅ No "Missing key inputs argument" errors
7. ✅ All responses include "gemini-2.0-flash-exp" in infrastructure
8. ✅ Response times < 5 seconds

**If all checks pass → Ready to record demo video!**

---

**Last Updated:** 2025-11-10 00:48 UTC (Deployment Day)
