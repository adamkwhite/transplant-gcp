"""
Cloud Run Service: Missed Dose Analysis
Uses Google Gemini for real AI medical reasoning
"""

import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
from google.cloud import firestore
import logging

# Add parent directory to path to import gemini_client
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gemini_client import get_gemini_client

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize Firestore
db = firestore.Client(project=os.environ.get('GOOGLE_CLOUD_PROJECT', 'transplant-prediction'))

# Initialize Gemini client
gemini = get_gemini_client()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            "interactions": ["grapefruit", "ketoconazole", "erythromycin"]
        },
        "mycophenolate": {
            "name": "Mycophenolate",
            "category": "antiproliferative",
            "time_window_hours": 12,
            "critical": True,
            "target_levels": "1-3.5 mg/L"
        },
        "prednisone": {
            "name": "Prednisone",
            "category": "corticosteroid",
            "time_window_hours": 24,
            "critical": False
        }
    }
    return medications.get(name.lower())

def get_patient_context(patient_id):
    """Get patient context from Firestore"""
    try:
        doc_ref = db.collection('patients').document(patient_id)
        doc = doc_ref.get()

        if doc.exists:
            data = doc.to_dict()
            return {
                'transplant_type': data.get('transplant_type', 'kidney'),
                'months_post_transplant': data.get('months_post_transplant', 6),
                'medications': data.get('medications', ['tacrolimus', 'mycophenolate']),
                'adherence_rate': data.get('adherence_rate', 0.85)
            }
    except Exception as e:
        logger.error(f"Firestore error: {e}")

    # Default context
    return {
        'transplant_type': 'kidney',
        'months_post_transplant': 6,
        'medications': ['tacrolimus', 'mycophenolate', 'prednisone'],
        'adherence_rate': 0.85
    }

def calculate_adherence(patient_id):
    """Calculate adherence from recent history in Firestore"""
    try:
        # Query recent dose history
        history_ref = db.collection('patient_history')
        week_ago = datetime.now() - timedelta(days=7)

        docs = history_ref.where('patient_id', '==', patient_id)\
                         .where('timestamp', '>=', week_ago)\
                         .stream()

        doses = list(docs)
        if doses:
            on_time = sum(1 for d in doses if d.to_dict().get('hours_late', 0) < 2)
            adherence_rate = on_time / len(doses) if doses else 0.8
            missed_week = sum(1 for d in doses if d.to_dict().get('hours_late', 0) > 12)
            return adherence_rate, missed_week
    except Exception as e:
        logger.error(f"Adherence calculation error: {e}")

    return 0.8, 0

def record_interaction(patient_id, interaction_type, data):
    """Record interaction to Firestore"""
    try:
        doc_ref = db.collection('patient_history').document()
        doc_ref.set({
            'patient_id': patient_id,
            'timestamp': datetime.now(),
            'interaction_type': interaction_type,
            'data': data,
            'ttl': datetime.now() + timedelta(days=90)
        })
    except Exception as e:
        logger.error(f"Error recording interaction: {e}")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Cloud Run"""
    return jsonify({
        'status': 'healthy',
        'service': 'missed-dose-analysis',
        'platform': 'Google Cloud Run',
        'ai_model': 'Gemini 2.0 Flash' if os.environ.get('GEMINI_API_KEY') else 'Mock Mode'
    })

@app.route('/medications/missed-dose', methods=['POST'])
def missed_dose():
    """Analyze missed medication dose with Gemini AI"""
    try:
        # Parse request
        data = request.get_json()
        medication_name = data.get('medication', '').lower()
        scheduled_time = data.get('scheduled_time', '')
        current_time = data.get('current_time', '')
        patient_id = data.get('patient_id', 'demo_patient')

        # Calculate hours late
        try:
            scheduled_dt = datetime.strptime(scheduled_time, "%I:%M %p")
            current_dt = datetime.strptime(current_time, "%I:%M %p")
            time_diff = current_dt - scheduled_dt
            hours_late = time_diff.seconds / 3600
            if time_diff.days < 0:
                hours_late = (24 * 3600 - abs(time_diff.seconds)) / 3600
        except:
            hours_late = 6  # Default

        # Get medication info
        medication = find_medication(medication_name)
        if not medication:
            return jsonify({'error': f'Medication {medication_name} not found'}), 404

        # Get patient context
        patient_context = get_patient_context(patient_id)
        adherence_rate, missed_this_week = calculate_adherence(patient_id)

        patient_context.update({
            'hours_late': hours_late,
            'missed_this_week': missed_this_week,
            'adherence_rate': adherence_rate
        })

        # Get AI-powered recommendation from Gemini
        gemini_response = gemini.analyze_missed_dose(
            medication=medication['name'],
            hours_late=hours_late,
            patient_context=patient_context
        )

        # Enhance message with context
        if medication['critical'] and hours_late > medication['time_window_hours']:
            gemini_response['risk_level'] = 'high'

        if missed_this_week >= 3:
            gemini_response['risk_level'] = 'critical'

        # Record interaction
        record_interaction(patient_id, 'missed_dose', {
            'medication': medication_name,
            'hours_late': hours_late,
            'recommendation': gemini_response.get('recommendation', ''),
            'ai_model': gemini_response.get('ai_model', 'gemini'),
            'risk_level': gemini_response.get('risk_level', 'medium')
        })

        # Build response
        response = {
            'recommendation': gemini_response.get('recommendation', 'Contact doctor'),
            'reasoning_chain': gemini_response.get('reasoning_steps', []),
            'risk_level': gemini_response.get('risk_level', 'medium'),
            'confidence': gemini_response.get('confidence', 0.85),
            'next_steps': gemini_response.get('next_steps', []),
            'adherence_metrics': {
                'current_rate': f"{round(adherence_rate * 100)}%",
                'doses_missed_this_week': missed_this_week
            },
            'medication_details': medication,
            'infrastructure': {
                'platform': 'Google Cloud Run',
                'database': 'Firestore',
                'ai_model': gemini_response.get('ai_model', 'gemini-2.0-flash'),
                'region': os.environ.get('REGION', 'us-central1')
            }
        }

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error in missed_dose: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    return jsonify({
        'service': 'Transplant Medication Adherence - Missed Dose Analysis',
        'version': '1.0',
        'platform': 'Google Cloud Run',
        'endpoints': [
            '/health',
            '/medications/missed-dose'
        ]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)