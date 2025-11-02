"""
Cloud Run Service: Missed Dose Analysis
Uses Google ADK Multi-Agent System for AI medical reasoning
"""

import logging
import os
import sys
from datetime import datetime, timedelta

from flask import Flask, jsonify, request
from flask_cors import CORS
from google.cloud import firestore

# Add parent directory to path to import ADK agents
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.agents.coordinator_agent import TransplantCoordinatorAgent
from services.agents.drug_interaction_agent import DrugInteractionCheckerAgent
from services.agents.medication_advisor_agent import MedicationAdvisorAgent
from services.agents.symptom_monitor_agent import SymptomMonitorAgent

# Constants
PLATFORM_NAME = "Google Cloud Run"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize Firestore
db = firestore.Client(project=os.environ.get("GOOGLE_CLOUD_PROJECT", "transplant-prediction"))

# Initialize ADK agents
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    logger.warning("GEMINI_API_KEY not set - agents will use config default")

medication_advisor = MedicationAdvisorAgent(api_key=api_key)
symptom_monitor = SymptomMonitorAgent(api_key=api_key)
drug_interaction_checker = DrugInteractionCheckerAgent(api_key=api_key)
coordinator = TransplantCoordinatorAgent(
    api_key=api_key,
    medication_advisor=medication_advisor,
    symptom_monitor=symptom_monitor,
    drug_interaction_checker=drug_interaction_checker,
)


def find_medication(name):
    """Medication database lookup"""
    medications = {
        "tacrolimus": {
            "name": "Tacrolimus",
            "category": "calcineurin_inhibitor",
            "time_window_hours": 12,
            "critical": True,
            "target_levels": "5-15 ng/mL",
            "half_life": "12 hours",
            "interactions": ["grapefruit", "ketoconazole", "erythromycin"],
        },
        "mycophenolate": {
            "name": "Mycophenolate",
            "category": "antiproliferative",
            "time_window_hours": 12,
            "critical": True,
            "target_levels": "1-3.5 mg/L",
        },
        "prednisone": {
            "name": "Prednisone",
            "category": "corticosteroid",
            "time_window_hours": 24,
            "critical": False,
        },
    }
    return medications.get(name.lower())


def get_patient_context(patient_id):
    """Get patient context from Firestore"""
    try:
        doc_ref = db.collection("patients").document(patient_id)
        doc = doc_ref.get()

        if doc.exists:
            data = doc.to_dict()
            return {
                "transplant_type": data.get("transplant_type", "kidney"),
                "months_post_transplant": data.get("months_post_transplant", 6),
                "medications": data.get("medications", ["tacrolimus", "mycophenolate"]),
                "adherence_rate": data.get("adherence_rate", 0.85),
            }
    except Exception as e:
        logger.error(f"Firestore error: {e}")

    # Default context
    return {
        "transplant_type": "kidney",
        "months_post_transplant": 6,
        "medications": ["tacrolimus", "mycophenolate", "prednisone"],
        "adherence_rate": 0.85,
    }


def calculate_adherence(patient_id):
    """Calculate adherence from recent history in Firestore"""
    try:
        # Query recent dose history
        history_ref = db.collection("patient_history")
        week_ago = datetime.now() - timedelta(days=7)

        docs = (
            history_ref.where("patient_id", "==", patient_id)
            .where("timestamp", ">=", week_ago)
            .stream()
        )

        doses = list(docs)
        if doses:
            on_time = sum(1 for d in doses if d.to_dict().get("hours_late", 0) < 2)
            adherence_rate = on_time / len(doses) if doses else 0.8
            missed_week = sum(1 for d in doses if d.to_dict().get("hours_late", 0) > 12)
            return adherence_rate, missed_week
    except Exception as e:
        logger.error(f"Adherence calculation error: {e}")

    return 0.8, 0


def record_interaction(patient_id, interaction_type, data):
    """Record interaction to Firestore"""
    try:
        doc_ref = db.collection("patient_history").document()
        doc_ref.set(
            {
                "patient_id": patient_id,
                "timestamp": datetime.now(),
                "interaction_type": interaction_type,
                "data": data,
                "ttl": datetime.now() + timedelta(days=90),
            }
        )
    except Exception as e:
        logger.error(f"Error recording interaction: {e}")


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for Cloud Run"""
    return jsonify(
        {
            "status": "healthy",
            "service": "missed-dose-analysis",
            "platform": PLATFORM_NAME,
            "ai_system": "Google ADK Multi-Agent System",
            "agents": {
                "coordinator": "TransplantCoordinator",
                "specialists": [
                    "MedicationAdvisor",
                    "SymptomMonitor",
                    "DrugInteractionChecker",
                ],
            },
            "ai_model": "gemini-2.0-flash-exp",
            "adk_version": "1.17.0",
        }
    )


@app.route("/medications/missed-dose", methods=["POST"])
def missed_dose():
    """Analyze missed medication dose with Gemini AI"""
    try:
        # Parse request
        data = request.get_json()
        medication_name = data.get("medication", "").lower()
        scheduled_time = data.get("scheduled_time", "")
        current_time = data.get("current_time", "")
        patient_id = data.get("patient_id", "demo_patient")

        # Calculate hours late
        try:
            scheduled_dt = datetime.strptime(scheduled_time, "%I:%M %p")
            current_dt = datetime.strptime(current_time, "%I:%M %p")
            time_diff = current_dt - scheduled_dt
            hours_late = time_diff.seconds / 3600
            if time_diff.days < 0:
                hours_late = (24 * 3600 - abs(time_diff.seconds)) / 3600
        except (ValueError, TypeError):
            hours_late = 6  # Default

        # Get medication info
        medication = find_medication(medication_name)
        if not medication:
            return jsonify({"error": f"Medication {medication_name} not found"}), 404

        # Get patient context
        patient_context = get_patient_context(patient_id)
        adherence_rate, missed_this_week = calculate_adherence(patient_id)

        patient_context.update(
            {
                "hours_late": hours_late,
                "missed_this_week": missed_this_week,
                "adherence_rate": adherence_rate,
                "transplant_type": patient_context.get("transplant_type", "kidney"),
                "months_post_transplant": patient_context.get("months_post_transplant", 6),
            }
        )

        # Get AI-powered recommendation from ADK MedicationAdvisor agent
        agent_response = medication_advisor.analyze_missed_dose(
            medication=medication["name"],
            scheduled_time=scheduled_time,
            current_time=current_time,
            patient_id=patient_id,
            patient_context=patient_context,
        )

        # Enhance response with context-based risk assessment
        if medication["critical"] and hours_late > medication["time_window_hours"]:
            agent_response["risk_level"] = "high"

        if missed_this_week >= 3:
            agent_response["risk_level"] = "critical"

        # Record interaction
        record_interaction(
            patient_id,
            "missed_dose",
            {
                "medication": medication_name,
                "hours_late": hours_late,
                "recommendation": agent_response.get("recommendation", ""),
                "ai_system": "ADK MedicationAdvisor",
                "risk_level": agent_response.get("risk_level", "medium"),
            },
        )

        # Build response (maintain backward compatibility with existing API format)
        response = {
            "recommendation": agent_response.get("recommendation", "Contact doctor"),
            "reasoning_chain": agent_response.get("reasoning_steps", []),
            "risk_level": agent_response.get("risk_level", "medium"),
            "confidence": agent_response.get("confidence", 0.85),
            "next_steps": agent_response.get("next_steps", []),
            "adherence_metrics": {
                "current_rate": f"{round(adherence_rate * 100)}%",
                "doses_missed_this_week": missed_this_week,
            },
            "medication_details": medication,
            "infrastructure": {
                "platform": PLATFORM_NAME,
                "database": "Firestore",
                "ai_system": "Google ADK Multi-Agent System",
                "ai_model": "gemini-2.0-flash-exp",
                "agent_used": "MedicationAdvisor",
                "region": os.environ.get("REGION", "us-central1"),
            },
        }

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error in missed_dose: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def index():
    """Root endpoint"""
    return jsonify(
        {
            "service": "Transplant Medication Adherence - Missed Dose Analysis",
            "version": "1.0",
            "platform": PLATFORM_NAME,
            "endpoints": ["/health", "/medications/missed-dose"],
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)  # nosec B104 - Cloud Run requires binding to all interfaces
