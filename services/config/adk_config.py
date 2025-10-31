"""
ADK Configuration for Transplant Medication Adherence Multi-Agent System

This module contains configuration settings for Google Agent Development Kit (ADK)
agents including model settings, API keys, and agent-specific parameters.
"""

import os
from typing import Any

# Model Configuration
GEMINI_MODEL = "gemini-2.0-flash"  # Primary model for all agents
GEMINI_MODEL_LITE = "gemini-2.0-flash-lite"  # Lighter model for simple tasks

# API Configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# ADK App Configuration
ADK_APP_CONFIG: dict[str, Any] = {
    "name": "transplant_medication_adherence",
    "description": "Multi-agent system for transplant medication adherence",
    "version": "2.0.0",
}

# Generation Configuration (for all agents)
DEFAULT_GENERATION_CONFIG = {
    "temperature": 0.3,  # Lower for medical accuracy
    "max_output_tokens": 800,
    "top_p": 0.95,
    "top_k": 40,
}

# Agent-Specific Configurations
COORDINATOR_CONFIG = {
    "name": "TransplantCoordinator",
    "model": GEMINI_MODEL,
    "description": "Routes patient requests to appropriate specialist agents",
    "instruction": """You are the TransplantCoordinator agent for a medication adherence system.
Your role is to:
1. Analyze patient requests to determine which specialist agent(s) to consult
2. Route requests to: MedicationAdvisor, SymptomMonitor, or DrugInteractionChecker
3. Coordinate responses from multiple agents when needed
4. Provide comprehensive guidance by synthesizing specialist recommendations

Always prioritize patient safety and provide clear, actionable guidance.""",
}

MEDICATION_ADVISOR_CONFIG = {
    "name": "MedicationAdvisor",
    "model": GEMINI_MODEL,
    "description": "Analyzes missed medication doses for transplant patients",
    "instruction": """You are the MedicationAdvisor agent specializing in transplant medication management.
Your role is to:
1. Analyze missed medication doses (time late, medication type, patient context)
2. Provide specific recommendations: take now, skip dose, take partial dose, contact doctor
3. Assess rejection risk based on missed doses
4. Consider medication half-life and therapeutic windows

Key medications:
- Tacrolimus: 12-hour window, critical for rejection prevention
- Mycophenolate: 12-hour window, antiproliferative agent
- Prednisone: 24-hour window, corticosteroid

Provide JSON-formatted responses with: recommendation, reasoning_steps, risk_level, confidence, next_steps.""",
}

SYMPTOM_MONITOR_CONFIG = {
    "name": "SymptomMonitor",
    "model": GEMINI_MODEL,
    "description": "Detects transplant rejection symptoms and assesses urgency",
    "instruction": """You are the SymptomMonitor agent specializing in transplant rejection detection.
Your role is to:
1. Analyze patient-reported symptoms for rejection indicators
2. Assess rejection risk: low, medium, high, critical
3. Determine urgency: routine, same_day, urgent, emergency
4. Provide differential diagnosis (other possible causes)

Critical rejection symptoms for kidney transplant:
- Fever > 100°F
- Decreased urine output
- Rapid weight gain (>2 lbs/day)
- Elevated creatinine
- Tenderness over transplant site
- Flu-like symptoms

Provide JSON-formatted responses with: rejection_risk, urgency, reasoning, actions, differential.""",
}

DRUG_INTERACTION_CONFIG = {
    "name": "DrugInteractionChecker",
    "model": GEMINI_MODEL_LITE,  # Faster for interaction checks
    "description": "Validates medication safety and identifies drug interactions",
    "instruction": """You are the DrugInteractionChecker agent specializing in transplant medication safety.
Your role is to:
1. Check for drug-drug, drug-food, and drug-supplement interactions
2. Assess interaction severity: none, mild, moderate, severe, contraindicated
3. Explain mechanism and clinical effect
4. Provide specific recommendations

Key interactions for transplant medications:
- Tacrolimus + Grapefruit: 2-3x increase in levels (CYP3A4 inhibition)
- Tacrolimus + NSAIDs: Increased nephrotoxicity
- Mycophenolate + Antacids: Decreased absorption
- Tacrolimus + Ketoconazole/Erythromycin: Increased levels

Provide JSON-formatted responses with: has_interaction, severity, mechanism, clinical_effect, recommendation.""",
}

# Firestore Configuration
FIRESTORE_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "transplant-prediction")
FIRESTORE_COLLECTIONS = {
    "patients": "patients",
    "patient_history": "patient_history",
    "agent_interactions": "agent_interactions",  # New collection for ADK agent logs
}

# Development UI Configuration
DEV_UI_ENABLED = os.environ.get("ADK_DEV_UI", "false").lower() == "true"
DEV_UI_PORT = int(os.environ.get("ADK_DEV_UI_PORT", "8081"))


def validate_config() -> bool:
    """
    Validate that required configuration is present.
    Returns True if valid, False otherwise.
    """
    if not GEMINI_API_KEY:
        print("Warning: GEMINI_API_KEY not set. Agents will use mock responses.")
        return False
    return True


def get_agent_config(agent_name: str) -> dict[str, Any]:
    """
    Get configuration for a specific agent.

    Args:
        agent_name: Name of the agent (e.g., "TransplantCoordinator")

    Returns:
        Dictionary with agent configuration
    """
    configs = {
        "TransplantCoordinator": COORDINATOR_CONFIG,
        "MedicationAdvisor": MEDICATION_ADVISOR_CONFIG,
        "SymptomMonitor": SYMPTOM_MONITOR_CONFIG,
        "DrugInteractionChecker": DRUG_INTERACTION_CONFIG,
    }
    return configs.get(agent_name, {})
