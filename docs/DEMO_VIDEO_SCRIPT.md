# Demo Video Script - TransplantGuard AI
## 3-Minute Demo for Google Cloud Run Hackathon 2025

**Total Duration:** 2:50 (10 seconds buffer)

---

## Scene 1: Hook + Personal Story (0:00 - 0:30)

**Visual:** You on camera or screen recording with title slide

**Script:**
"Hi, I'm [Your Name]. Four months ago, I lost my mom to lung disease. Before that, I spent months researching whether she could be a candidate for a lung transplant. That's when I discovered something alarming: 50-60% of transplant failures aren't caused by medical complications—they're caused by patients missing or incorrectly timing their medications.

That's why I built TransplantGuard AI."

**Key Points:**
- Personal, authentic story
- Clear problem statement
- Sets up the "why"

---

## Scene 2: The Problem (0:30 - 0:50)

**Visual:** Show statistics or diagrams

**Script:**
"There are over 200,000 transplant recipients in the US right now. They take 10-15 medications daily, with some requiring timing precision down to the hour. Miss a dose of tacrolimus by 6 hours? You risk organ rejection. Mix it with grapefruit? Dangerous drug interaction.

Patients need instant, expert-level guidance—but transplant clinics are closed after 5 PM."

**Key Points:**
- Scale of the problem
- Real stakes (organ rejection)
- Gap in current care

---

## Scene 3: The Solution - Live Demo (0:50 - 2:20)

### Part A: Show the Landing Page (0:50 - 1:05)

**Visual:** Navigate to https://missed-dose-service-978611421547.us-central1.run.app/

**Script:**
"TransplantGuard AI is a multi-agent medical guidance system powered by Google Cloud Run, Google ADK, and Gemini 2.0 Flash.

Here's our Cloud Run service—five specialized AI agents working together to provide 24/7 medical guidance."

**Show:**
- Professional landing page
- Agent cards (Coordinator, Medication Advisor, Symptom Monitor, Drug Interaction, Rejection Risk)
- Technology badges

### Part B: Missed Dose Analysis (1:05 - 1:35)

**Visual:** Use curl or Postman to call `/medications/missed-dose` API

**Script:**
"Let's see it in action. A patient missed their tacrolimus dose—it was scheduled for 8 AM, but it's now 2 PM. That's 6 hours late for a critical immunosuppressant.

I'll send this to our API..."

**Show Terminal Command:**
```bash
curl -X POST https://missed-dose-service-978611421547.us-central1.run.app/medications/missed-dose \
  -H "Content-Type: application/json" \
  -d '{
    "medication": "tacrolimus",
    "scheduled_time": "8:00 AM",
    "current_time": "2:00 PM",
    "patient_id": "demo_patient"
  }'
```

**Script (continued):**
"Within 2-3 seconds, our multi-agent system analyzes the situation. The MedicationAdvisor agent consults the patient's history in Firestore, checks drug half-life calculations, and provides personalized guidance.

The response says: 'Take the dose immediately and contact your transplant team to discuss monitoring.' It also shows the reasoning chain—exactly how the AI reached this conclusion."

**Show in Response:**
- Recommendation text
- Risk level: "high"
- Reasoning steps
- Next steps

### Part C: Rejection Risk Analysis (1:35 - 2:00)

**Visual:** Call `/rejection/analyze` API

**Script:**
"Now let's try something more complex. A patient reports symptoms: fever, decreased urine output, and tenderness over the transplant site.

Our RejectionRisk agent uses real transplant outcomes data from SRTR—the Scientific Registry of Transplant Recipients—to assess rejection probability."

**Show Terminal Command:**
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
  }'
```

**Show in Response:**
- Rejection probability: 75%
- Urgency: HIGH
- Recommended action
- Similar cases from SRTR data

**Script (continued):**
"The system identifies a 75% rejection probability with HIGH urgency and recommends immediate contact with the transplant team. This is evidence-based AI—grounded in real transplant outcomes."

---

## Scene 4: Architecture + Technology (2:00 - 2:30)

**Visual:** Show architecture diagram from docs/architecture/architecture-diagram.png

**Script:**
"Here's how it works architecturally:

**Point to diagram as you explain:**
- Five specialized ADK agents orchestrated by a coordinator
- Each agent calls Gemini 2.0 Flash for AI reasoning
- Patient data stored in Firestore
- Real transplant outcomes from SRTR BigQuery
- All deployed on Google Cloud Run for auto-scaling and serverless operation

The beauty of Cloud Run? Zero infrastructure management. I just deploy a Docker container, and Google handles scaling from zero to thousands of requests."

**Key Technologies to Mention:**
- Google Cloud Run (serverless containers)
- Google ADK 1.17.0 (multi-agent orchestration)
- Gemini 2.0 Flash (AI model)
- Firestore (patient database)
- Python 3.12 + Flask

---

## Scene 5: Impact + Close (2:30 - 2:50)

**Visual:** Back to you on camera or closing slide

**Script:**
"This could save lives. 200,000+ transplant recipients need this level of instant, expert guidance.

But more than that—this is deeply personal for me. I built this in memory of my mom, and for every family that's navigating the impossible complexity of transplant care.

TransplantGuard AI is live on Cloud Run right now. You can try it yourself at the URL shown here.

Thank you."

**Show on screen:**
- Cloud Run URL: https://missed-dose-service-978611421547.us-central1.run.app
- GitHub: https://github.com/adamkwhite/transplant-gcp
- "Built for Google Cloud Run Hackathon 2025"

---

## Recording Tips

### Tools to Use
1. **Screen Recording:** OBS Studio (free) or Loom
2. **Video Editing:** DaVinci Resolve (free) or iMovie
3. **Terminal:** Use a large font (18-20pt) for readability
4. **Presentation:** Google Slides for title slides

### Setup Checklist
- [ ] Clear desktop (close unnecessary apps)
- [ ] Large terminal font for screen recording
- [ ] Test API endpoints before recording
- [ ] Have curl commands ready in a text file to copy/paste
- [ ] Use jq for pretty JSON formatting: `| jq`
- [ ] Good microphone (even a headset is fine)
- [ ] Quiet environment
- [ ] Practice run to stay under 3 minutes

### Terminal Commands (Ready to Copy)

**Missed Dose Test:**
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

**Rejection Analysis Test:**
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

**Health Check:**
```bash
curl https://missed-dose-service-978611421547.us-central1.run.app/health | jq
```

### Visual Suggestions
1. **Title Slide:** "TransplantGuard AI - Multi-Agent Medical Guidance System"
2. **Problem Slide:** Show the 50-60% failure statistic visually
3. **Architecture Diagram:** Use the one from docs/architecture/architecture-diagram.png
4. **Closing Slide:** Your name, project links, "In memory of [Mom's name]"

### Upload Requirements
- **Platform:** YouTube or Vimeo (make sure it's public or unlisted, not private)
- **Title:** "TransplantGuard AI - Google Cloud Run Hackathon 2025"
- **Description:** Include project links and #CloudRunHackathon
- **Subtitles:** If English is not your first language, add English subtitles

---

## Timeline Breakdown

| Time | Section | Duration | Purpose |
|------|---------|----------|---------|
| 0:00 - 0:30 | Hook + Personal Story | 30s | Emotional connection, establish credibility |
| 0:30 - 0:50 | Problem Statement | 20s | Show scale and stakes |
| 0:50 - 2:20 | Live Demo | 90s | Show Cloud Run deployment working |
| 2:00 - 2:30 | Architecture | 30s | Technical depth for judges |
| 2:30 - 2:50 | Impact + Close | 20s | Leave lasting impression |

**Total:** 2:50 (with 10-second buffer)

---

## What Judges Are Looking For

According to hackathon rules, judges will evaluate:

1. ✅ **Technical Implementation** - Show Cloud Run deployment, multi-agent architecture
2. ✅ **AI Agent Design** - Demonstrate 5 specialized agents working together
3. ✅ **Innovation** - Multi-agent system with real medical data (SRTR)
4. ✅ **User Impact** - Personal story + 200,000 potential users
5. ✅ **Code Quality** - Mention 94.8% test coverage, 156 passing tests

**Make sure to emphasize:**
- Google Cloud Run auto-scaling
- Google ADK multi-agent orchestration
- Gemini 2.0 Flash AI model
- Real-world medical impact

---

## After Recording

1. **Upload to YouTube/Vimeo** (public or unlisted)
2. **Get the video URL**
3. **Add URL to Devpost submission**
4. **Share on LinkedIn with #CloudRunHackathon** (+0.4 bonus points!)

Good luck! Your story is powerful—let that come through in your delivery.
