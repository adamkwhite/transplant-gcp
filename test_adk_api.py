#!/usr/bin/env python3
"""
Quick test script for ADK-integrated REST API
Tests that the Flask app can start and respond to requests
"""

import os
import sys

# Set up test environment
os.environ["GOOGLE_CLOUD_PROJECT"] = "transplant-prediction-test"

# Mock Firestore to avoid requiring credentials
sys.modules["google.cloud.firestore"] = type(sys)("mock_firestore")


class MockFirestoreClient:
    def __init__(self, project=None):
        self.project = project

    def collection(self, name):  # noqa: ARG002 — mock signature must match Firestore client
        return MockCollection()


class MockCollection:
    def document(self, doc_id=None):  # noqa: ARG002 — mock signature must match Firestore client
        return MockDocument()


class MockDocument:
    def get(self):
        return MockDocSnapshot()

    def set(self, data):
        pass


class MockDocSnapshot:
    exists = True

    def to_dict(self):
        return {
            "transplant_type": "kidney",
            "months_post_transplant": 6,
            "medications": ["tacrolimus", "mycophenolate"],
            "adherence_rate": 0.85,
        }


sys.modules["google.cloud.firestore"].Client = MockFirestoreClient  # type: ignore[attr-defined]


def test_health_endpoint():
    """Test that the /health endpoint works"""
    # Import after mocking Firestore
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "services"))
    sys.path.insert(
        0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "services", "missed-dose")
    )

    # Import main module directly
    import importlib.util

    spec = importlib.util.spec_from_file_location("main", "services/missed-dose/main.py")
    main_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main_module)
    app = main_module.app

    with app.test_client() as client:
        response = client.get("/health")
        print("✓ Health endpoint test:")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.get_json()}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"
        assert data["ai_system"] == "Google ADK Multi-Agent System"
        assert "MedicationAdvisor" in data["agents"]["specialists"]
        print("  ✓ All assertions passed\n")


def test_root_endpoint():
    """Test that the root endpoint works"""
    # Import main module directly
    import importlib.util

    spec = importlib.util.spec_from_file_location("main", "services/missed-dose/main.py")
    main_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main_module)
    app = main_module.app

    with app.test_client() as client:
        response = client.get("/")
        print("✓ Root endpoint test:")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.get_json()}")
        assert response.status_code == 200
        print("  ✓ All assertions passed\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing ADK-Integrated REST API")
    print("=" * 60 + "\n")

    try:
        test_health_endpoint()
        test_root_endpoint()
        print("=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
