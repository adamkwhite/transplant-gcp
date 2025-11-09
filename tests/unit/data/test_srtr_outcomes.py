"""
Unit tests for SRTR Outcomes Data Query Module.

Tests all methods in SRTROutcomesData class with focus on:
- Multi-organ support
- Data loading and caching
- Query methods (rejection rates, survival, context)
- Error handling for missing data
- Prompt formatting
"""

import json
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from services.data.srtr_outcomes import SRTROutcomesData, get_srtr_data


@pytest.fixture
def mock_kidney_data():
    """Sample kidney outcomes data for testing."""
    return [
        {
            "metric": "acute_rejection_rate",
            "organ": "kidney",
            "year": 2022,
            "demographic": "35-49",
            "value": 6.19,
        },
        {
            "metric": "acute_rejection_rate",
            "organ": "kidney",
            "year": 2022,
            "demographic": "18-34 years",
            "value": 8.00,
        },
    ]


@pytest.fixture
def mock_kidney_summary():
    """Sample kidney summary data for testing."""
    return {
        "organ": "kidney",
        "total_records": 2,
        "latest_acute_rejection_rates": {
            "35-49": 6.19,
            "18-34 years": 8.00,
        },
    }


@pytest.fixture
def mock_lung_data():
    """Sample lung outcomes data for testing."""
    return [
        {
            "metric": "acute_rejection_rate",
            "organ": "lung",
            "year": 2022,
            "demographic": "35-49",
            "value": 8.47,
        },
    ]


@pytest.fixture
def mock_lung_summary():
    """Sample lung summary data for testing."""
    return {
        "organ": "lung",
        "total_records": 1,
        "latest_acute_rejection_rates": {
            "35-49": 8.47,
        },
    }


@pytest.fixture
def temp_data_dir(mock_kidney_data, mock_kidney_summary, mock_lung_data, mock_lung_summary):
    """Create temporary data directory with mock SRTR data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_path = Path(tmpdir)

        # Write kidney data
        with open(data_path / "kidney_outcomes_flat.json", "w") as f:
            json.dump(mock_kidney_data, f)
        with open(data_path / "kidney_summary.json", "w") as f:
            json.dump(mock_kidney_summary, f)

        # Write lung data
        with open(data_path / "lung_outcomes_flat.json", "w") as f:
            json.dump(mock_lung_data, f)
        with open(data_path / "lung_summary.json", "w") as f:
            json.dump(mock_lung_summary, f)

        yield str(data_path)


class TestSRTROutcomesData:
    """Test suite for SRTROutcomesData class."""

    def test_init_kidney_default(self, temp_data_dir):
        """Test initialization with default kidney organ."""
        srtr = SRTROutcomesData(organ="kidney", data_dir=temp_data_dir)
        assert srtr.organ == "kidney"
        assert srtr._data is not None
        assert srtr._summary is not None

    def test_init_lung(self, temp_data_dir):
        """Test initialization with lung organ."""
        srtr = SRTROutcomesData(organ="lung", data_dir=temp_data_dir)
        assert srtr.organ == "lung"
        assert srtr._data is not None
        assert srtr._summary is not None

    def test_init_unsupported_organ(self, temp_data_dir):
        """Test initialization fails with unsupported organ."""
        with pytest.raises(ValueError, match="Unsupported organ"):
            SRTROutcomesData(organ="brain", data_dir=temp_data_dir)

    def test_init_missing_files(self):
        """Test initialization with missing data files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            srtr = SRTROutcomesData(organ="kidney", data_dir=tmpdir)
            assert srtr._data is None
            assert srtr._summary is None

    def test_get_acute_rejection_rate_specific_age(self, temp_data_dir):
        """Test getting rejection rate for specific age group."""
        srtr = SRTROutcomesData(organ="kidney", data_dir=temp_data_dir)
        rate = srtr.get_acute_rejection_rate("35-49")
        assert rate == 6.19

    def test_get_acute_rejection_rate_all_ages(self, temp_data_dir):
        """Test getting all rejection rates."""
        srtr = SRTROutcomesData(organ="kidney", data_dir=temp_data_dir)
        rates = srtr.get_acute_rejection_rate()
        assert isinstance(rates, dict)
        assert rates["35-49"] == 6.19
        assert rates["18-34 years"] == 8.00

    def test_get_acute_rejection_rate_missing_age_group(self, temp_data_dir):
        """Test getting rejection rate for non-existent age group."""
        srtr = SRTROutcomesData(organ="kidney", data_dir=temp_data_dir)
        rate = srtr.get_acute_rejection_rate("65+")
        assert rate == 0.0

    def test_get_acute_rejection_rate_no_summary(self):
        """Test getting rejection rate when no summary data available."""
        with tempfile.TemporaryDirectory() as tmpdir:
            srtr = SRTROutcomesData(organ="kidney", data_dir=tmpdir)
            rate = srtr.get_acute_rejection_rate("35-49")
            assert rate == 0.0

    def test_get_graft_survival_rate_default(self, temp_data_dir):
        """Test getting graft survival rate (returns default when no data)."""
        srtr = SRTROutcomesData(organ="kidney", data_dir=temp_data_dir)
        survival = srtr.get_graft_survival_rate(6, "35-49")
        assert survival == 98.0  # Default value

    def test_get_graft_survival_rate_no_data(self):
        """Test getting graft survival rate with no data loaded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            srtr = SRTROutcomesData(organ="kidney", data_dir=tmpdir)
            survival = srtr.get_graft_survival_rate(6, "35-49")
            assert survival == 99.0  # Conservative default

    def test_get_population_context(self, temp_data_dir):
        """Test getting comprehensive population context."""
        srtr = SRTROutcomesData(organ="kidney", data_dir=temp_data_dir)
        context = srtr.get_population_context("35-49", 6)

        assert context["age_group"] == "35-49"
        assert context["months_post_transplant"] == 6
        assert context["baseline_rejection_rate"] == 6.19
        assert context["data_source"] == "SRTR 2023 Annual Data Report"
        assert context["population_size"] == 2

    def test_format_for_prompt(self, temp_data_dir):
        """Test formatting population data for AI prompt."""
        srtr = SRTROutcomesData(organ="lung", data_dir=temp_data_dir)
        prompt = srtr.format_for_prompt("35-49", 6)

        assert "Lung Transplant" in prompt
        assert "35-49" in prompt
        assert "6 months" in prompt
        assert "8.47%" in prompt
        assert "SRTR 2023" in prompt

    def test_get_risk_multiplier_minimal_delay(self, temp_data_dir):
        """Test risk multiplier for minimal delay (<2h)."""
        srtr = SRTROutcomesData(organ="kidney", data_dir=temp_data_dir)
        multiplier, explanation = srtr.get_risk_multiplier(1.5, "35-49")

        assert multiplier == 1.0
        assert "Minimal risk" in explanation
        assert "6.19%" in explanation

    def test_get_risk_multiplier_moderate_delay(self, temp_data_dir):
        """Test risk multiplier for moderate delay (6-12h)."""
        srtr = SRTROutcomesData(organ="kidney", data_dir=temp_data_dir)
        multiplier, explanation = srtr.get_risk_multiplier(8, "35-49")

        assert multiplier == 1.2
        assert "moderately increases" in explanation
        assert "6.19%" in explanation

    def test_get_risk_multiplier_significant_delay(self, temp_data_dir):
        """Test risk multiplier for significant delay (>12h)."""
        srtr = SRTROutcomesData(organ="kidney", data_dir=temp_data_dir)
        multiplier, explanation = srtr.get_risk_multiplier(15, "18-34 years")

        assert multiplier == 1.5
        assert "significantly increases" in explanation
        assert "8.00%" in explanation

    def test_get_risk_multiplier_slight_delay(self, temp_data_dir):
        """Test risk multiplier for slight delay (2-6h)."""
        srtr = SRTROutcomesData(organ="kidney", data_dir=temp_data_dir)
        multiplier, explanation = srtr.get_risk_multiplier(4, "35-49")

        assert multiplier == 1.1
        assert "Slight risk" in explanation


class TestGetSRTRDataFunction:
    """Test suite for get_srtr_data() singleton function."""

    def test_get_srtr_data_caching(self, temp_data_dir):
        """Test that get_srtr_data caches instances."""
        with mock.patch("services.data.srtr_outcomes.SRTROutcomesData.__init__") as mock_init:
            mock_init.return_value = None

            # First call should create instance
            srtr1 = get_srtr_data("kidney")

            # Second call should return cached instance
            srtr2 = get_srtr_data("kidney")

            assert srtr1 is srtr2
            assert mock_init.call_count == 1

    def test_get_srtr_data_different_organs(self, temp_data_dir):
        """Test that different organs get separate cached instances."""
        # Clear cache first
        from services.data import srtr_outcomes

        srtr_outcomes._srtr_data_cache.clear()

        with mock.patch("services.data.srtr_outcomes.SRTROutcomesData") as mock_class:
            mock_kidney = mock.Mock()
            mock_lung = mock.Mock()
            mock_class.side_effect = [mock_kidney, mock_lung]

            srtr_kidney = get_srtr_data("kidney")
            srtr_lung = get_srtr_data("lung")

            assert srtr_kidney is mock_kidney
            assert srtr_lung is mock_lung
            assert srtr_kidney is not srtr_lung

    def test_supported_organs_constant(self):
        """Test SUPPORTED_ORGANS constant is complete."""
        expected = ["kidney", "liver", "heart", "lung", "pancreas", "intestine"]
        assert expected == SRTROutcomesData.SUPPORTED_ORGANS
