"""
Integration tests for Cloud Run deployment with ADK multi-agent system.

Tests the live deployed service at:
https://missed-dose-service-64rz4skmdq-uc.a.run.app

Requires:
- Service deployed to Cloud Run
- GEMINI_API_KEY configured in Cloud Run environment
"""

import os
import time

import pytest
import requests  # type: ignore[import-untyped]

# Cloud Run service URL
SERVICE_URL = os.getenv(
    "CLOUD_RUN_SERVICE_URL", "https://missed-dose-service-64rz4skmdq-uc.a.run.app"
)


class TestCloudRunHealth:
    """Test Cloud Run service health and configuration."""

    def test_health_endpoint_responds(self):
        """Test that health endpoint is accessible."""
        response = requests.get(f"{SERVICE_URL}/health", timeout=30)
        assert response.status_code == 200

    def test_health_shows_adk_system(self):
        """Test that health endpoint shows ADK multi-agent system."""
        response = requests.get(f"{SERVICE_URL}/health", timeout=30)
        data = response.json()

        assert data["status"] == "healthy"
        assert data["ai_system"] == "Google ADK Multi-Agent System"
        assert data["platform"] == "Google Cloud Run"
        assert data["adk_version"] == "1.17.0"

    def test_health_shows_all_agents(self):
        """Test that all 4 agents are listed in health response."""
        response = requests.get(f"{SERVICE_URL}/health", timeout=30)
        data = response.json()

        assert "agents" in data
        assert data["agents"]["coordinator"] == "TransplantCoordinator"

        specialists = data["agents"]["specialists"]
        assert "MedicationAdvisor" in specialists
        assert "SymptomMonitor" in specialists
        assert "DrugInteractionChecker" in specialists
        assert len(specialists) == 3

    def test_health_shows_correct_model(self):
        """Test that health endpoint shows correct AI model."""
        response = requests.get(f"{SERVICE_URL}/health", timeout=30)
        data = response.json()

        assert data["ai_model"] == "gemini-2.0-flash-exp"


class TestMissedDoseEndpoint:
    """Test missed dose analysis endpoint with real Gemini API."""

    def test_missed_dose_basic_request(self):
        """Test basic missed dose request returns 200."""
        payload = {
            "medication": "tacrolimus",
            "scheduled_time": "8:00 AM",
            "current_time": "2:00 PM",
            "patient_id": "test_patient_basic",
        }

        response = requests.post(f"{SERVICE_URL}/medications/missed-dose", json=payload, timeout=60)

        assert response.status_code == 200

    def test_missed_dose_uses_medication_advisor(self):
        """Test that MedicationAdvisor agent is used for missed dose."""
        payload = {
            "medication": "tacrolimus",
            "scheduled_time": "8:00 AM",
            "current_time": "10:00 AM",
            "patient_id": "test_patient_advisor",
        }

        response = requests.post(f"{SERVICE_URL}/medications/missed-dose", json=payload, timeout=60)

        data = response.json()
        assert data["infrastructure"]["agent_used"] == "MedicationAdvisor"
        assert data["infrastructure"]["ai_system"] == "Google ADK Multi-Agent System"

    def test_missed_dose_returns_recommendation(self):
        """Test that real AI recommendation is returned."""
        payload = {
            "medication": "tacrolimus",
            "scheduled_time": "8:00 AM",
            "current_time": "11:00 AM",
            "patient_id": "test_patient_recommendation",
        }

        response = requests.post(f"{SERVICE_URL}/medications/missed-dose", json=payload, timeout=60)

        data = response.json()

        # Check required fields
        assert "recommendation" in data
        assert "risk_level" in data
        assert "confidence" in data
        assert "next_steps" in data

        # Verify recommendation is not empty
        assert len(data["recommendation"]) > 0
        assert data["confidence"] > 0

    def test_missed_dose_includes_medication_details(self):
        """Test that medication details are included."""
        payload = {
            "medication": "tacrolimus",
            "scheduled_time": "8:00 AM",
            "current_time": "12:00 PM",
            "patient_id": "test_patient_details",
        }

        response = requests.post(f"{SERVICE_URL}/medications/missed-dose", json=payload, timeout=60)

        data = response.json()
        med_details = data["medication_details"]

        assert med_details["name"] == "Tacrolimus"
        assert med_details["critical"] is True
        assert med_details["category"] == "calcineurin_inhibitor"
        assert "half_life" in med_details

    def test_missed_dose_different_medications(self):
        """Test different immunosuppressant medications."""
        medications = ["tacrolimus", "cyclosporine", "mycophenolate"]

        for med in medications:
            payload = {
                "medication": med,
                "scheduled_time": "8:00 AM",
                "current_time": "10:00 AM",
                "patient_id": f"test_patient_{med}",
            }

            response = requests.post(
                f"{SERVICE_URL}/medications/missed-dose", json=payload, timeout=60
            )

            assert response.status_code == 200
            data = response.json()
            assert "recommendation" in data

            # Add delay to avoid rate limiting
            time.sleep(2)

    def test_missed_dose_time_windows(self):
        """Test different time delay scenarios."""
        test_cases = [
            ("8:00 AM", "9:00 AM", "short delay"),
            ("8:00 AM", "12:00 PM", "medium delay"),
            ("8:00 AM", "6:00 PM", "long delay"),
        ]

        for scheduled, current, scenario in test_cases:
            payload = {
                "medication": "tacrolimus",
                "scheduled_time": scheduled,
                "current_time": current,
                "patient_id": f"test_patient_{scenario.replace(' ', '_')}",
            }

            response = requests.post(
                f"{SERVICE_URL}/medications/missed-dose", json=payload, timeout=60
            )

            assert response.status_code == 200, f"Failed for {scenario}"
            data = response.json()
            assert "risk_level" in data

            # Add delay to avoid rate limiting
            time.sleep(2)


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_missing_required_fields(self):
        """Test that missing required fields return 400."""
        payload = {
            "medication": "tacrolimus"
            # Missing scheduled_time, current_time, patient_id
        }

        response = requests.post(f"{SERVICE_URL}/medications/missed-dose", json=payload, timeout=30)

        assert response.status_code == 400

    def test_invalid_medication(self):
        """Test handling of invalid medication."""
        payload = {
            "medication": "invalid_medication_xyz",
            "scheduled_time": "8:00 AM",
            "current_time": "10:00 AM",
            "patient_id": "test_patient_invalid",
        }

        response = requests.post(f"{SERVICE_URL}/medications/missed-dose", json=payload, timeout=60)

        # Should still return 200 but with appropriate handling
        assert response.status_code in [200, 400]

    def test_malformed_json(self):
        """Test handling of malformed JSON."""
        response = requests.post(
            f"{SERVICE_URL}/medications/missed-dose",
            data="not valid json",
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        assert response.status_code == 400


class TestPerformance:
    """Test performance and latency."""

    def test_health_endpoint_fast(self):
        """Test that health endpoint responds quickly."""
        start = time.time()
        response = requests.get(f"{SERVICE_URL}/health", timeout=30)
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 5.0  # Should be under 5 seconds

    def test_missed_dose_reasonable_latency(self):
        """Test that API calls complete in reasonable time."""
        payload = {
            "medication": "tacrolimus",
            "scheduled_time": "8:00 AM",
            "current_time": "10:00 AM",
            "patient_id": "test_patient_latency",
        }

        start = time.time()
        response = requests.post(f"{SERVICE_URL}/medications/missed-dose", json=payload, timeout=60)
        elapsed = time.time() - start

        assert response.status_code == 200

        # ADK agent + Gemini API call should complete in under 30 seconds
        assert elapsed < 30.0

        print(f"\nMissed dose API latency: {elapsed:.2f}s")

    def test_concurrent_requests(self):
        """Test handling of concurrent requests."""
        import concurrent.futures

        def make_request(patient_num):
            payload = {
                "medication": "tacrolimus",
                "scheduled_time": "8:00 AM",
                "current_time": "10:00 AM",
                "patient_id": f"concurrent_test_{patient_num}",
            }

            response = requests.post(
                f"{SERVICE_URL}/medications/missed-dose", json=payload, timeout=60
            )

            return response.status_code

        # Test 3 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_request, i) for i in range(3)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All requests should succeed
        assert all(status == 200 for status in results)


class TestInfrastructure:
    """Test infrastructure and platform details."""

    def test_platform_is_cloud_run(self):
        """Verify service is running on Cloud Run."""
        response = requests.get(f"{SERVICE_URL}/health", timeout=30)
        data = response.json()

        assert data["platform"] == "Google Cloud Run"

    def test_service_url_accessible(self):
        """Test that the service URL is publicly accessible."""
        # Health endpoint should be publicly accessible
        response = requests.get(f"{SERVICE_URL}/health", timeout=30)
        assert response.status_code == 200

    def test_response_includes_infrastructure_details(self):
        """Test that API responses include infrastructure details."""
        payload = {
            "medication": "tacrolimus",
            "scheduled_time": "8:00 AM",
            "current_time": "10:00 AM",
            "patient_id": "test_infrastructure",
        }

        response = requests.post(f"{SERVICE_URL}/medications/missed-dose", json=payload, timeout=60)

        data = response.json()
        infra = data["infrastructure"]

        assert infra["platform"] == "Google Cloud Run"
        assert infra["ai_system"] == "Google ADK Multi-Agent System"
        assert infra["ai_model"] == "gemini-2.0-flash-exp"
        assert infra["region"] == "us-central1"


if __name__ == "__main__":
    # Run with: pytest tests/integration/test_cloud_run_deployment.py -v
    pytest.main([__file__, "-v", "-s"])
