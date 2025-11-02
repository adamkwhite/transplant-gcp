# 🚀 Transplant Medication Adherence - Google Cloud Run

## For Google Cloud Run Hackathon

### 🏗️ Architecture
- **Google ADK (Agent Development Kit)** - Multi-agent AI system
- **Google Cloud Run** - Serverless containers
- **Firestore** - NoSQL database
- **Gemini 2.0 Flash** - AI medical reasoning across 4 specialized agents
- **Cloud Build** - Automatic container builds

### 🎯 Features
- **Multi-Agent AI System** using Google ADK with 4 specialized agents:
  - **TransplantCoordinator** - Routes patient requests to appropriate specialists
  - **MedicationAdvisor** - Analyzes missed doses and medication timing
  - **SymptomMonitor** - Assesses rejection risk from symptoms
  - **DrugInteractionChecker** - Checks medication, food, and supplement interactions
- **Real AI Inference** using Gemini 2.0 Flash (not mock!)
- **Intelligent Routing** - Automatically determines which specialists to consult
- Patient dashboard with history

### 📁 Project Structure
```
transplant-gcp/
├── services/
│   ├── agents/               # ADK multi-agent system
│   │   ├── coordinator_agent.py        # Coordinator agent
│   │   ├── medication_advisor_agent.py # Medication specialist
│   │   ├── symptom_monitor_agent.py    # Symptom specialist
│   │   └── drug_interaction_agent.py   # Interaction specialist
│   ├── config/
│   │   └── adk_config.py     # ADK agent configurations
│   ├── missed-dose/          # Cloud Run REST API service
│   │   ├── main.py           # Flask app (ADK-integrated)
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── gemini_client.py      # Legacy Gemini client (deprecated)
├── tests/
│   ├── unit/agents/          # Unit tests for all 4 agents
│   └── integration/          # ADK orchestration tests
├── benchmarks/               # Performance comparison data
├── deploy.sh                 # Deployment script
└── README.md
```

### 🚀 Quick Deploy

1. **Get Gemini API Key** (Free):
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Click "Create API Key"
   - Copy the key

2. **Deploy to Cloud Run**:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

3. **Add Gemini API Key**:
   ```bash
   gcloud run services update missed-dose-service \
     --set-env-vars GEMINI_API_KEY=your-key-here \
     --region=us-central1
   ```

### 🧪 Test Endpoints

After deployment, test with your service URL:

```bash
# Health check
curl https://your-service-url.run.app/health

# Missed dose analysis (with real AI!)
curl -X POST https://your-service-url.run.app/medications/missed-dose \
  -H "Content-Type: application/json" \
  -d '{
    "medication": "tacrolimus",
    "scheduled_time": "8:00 AM",
    "current_time": "2:00 PM",
    "patient_id": "maria_rodriguez"
  }'
```

### 💰 Cost Analysis

**Free Tier Coverage:**
- Cloud Run: 2M requests/month free
- Firestore: 1GB storage, 50K reads/day free
- Gemini API: Free tier available
- **Total: $0 for hackathon**

### 🏆 Why This Wins

1. **Advanced Multi-Agent AI** - Google ADK with 4 specialized agents working together
2. **Real AI Integration** - Gemini 2.0 Flash provides actual medical reasoning
3. **Intelligent Orchestration** - Coordinator routes to appropriate specialists automatically
4. **Serverless Architecture** - Scales to millions automatically on Cloud Run
5. **Medical Impact** - Saves transplant patients' lives through AI-powered guidance
6. **Production Ready** - Error handling, logging, monitoring, comprehensive testing
7. **Google Cloud Showcase** - ADK, Cloud Run, Firestore, Gemini API

### 📊 Hackathon Category

**Best of AI Agents Category** - Multi-agent AI system using Google ADK framework

**Key Differentiators:**
- ✅ 4 specialized ADK agents with distinct medical expertise
- ✅ Intelligent coordinator that routes requests to appropriate specialists
- ✅ Real-world medical application (transplant patient care)
- ✅ Production-ready with comprehensive testing and benchmarking
- ✅ Benchmarked 3 architectures: ADK Orchestration (winner at 2.72s), Pub/Sub, In-Process

### 🎯 Bonus Points Strategy

- ✅ Using Gemini models (+0.4 points)
- ✅ Multiple Cloud Run services (+0.4 points)
- 📝 Blog post about Cloud Run (+0.4 points)
- 📱 Social media with #CloudRunHackathon (+0.4 points)

### 🔗 Links

- [Google Cloud Console](https://console.cloud.google.com/run?project=transplant-prediction)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [Hackathon Details](https://run.devpost.com)

### 📅 Timeline

- **Oct 26**: Project setup ✅
- **Nov 3**: Submit NVIDIA-AWS hackathon
- **Nov 4-9**: Complete Google Cloud migration
- **Nov 10**: Submit to Google Cloud Run hackathon

---

**Built for Google Cloud Run Hackathon 2025**
