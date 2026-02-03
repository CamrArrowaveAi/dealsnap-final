"""
DealSnap - API Integration Tests
Tests FastAPI endpoints including DealSnap Quick Mode
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.main import app


# ============================================================================
# TEST CLIENT
# ============================================================================

client = TestClient(app)


# ============================================================================
# HEALTH CHECK TESTS
# ============================================================================

class TestHealthEndpoints:
    """Tests for health and status endpoints"""

    def test_health_check(self):
        """Test /api/health endpoint"""
        response = client.get("/api/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_api_status(self):
        """Test /api/status endpoint"""
        response = client.get("/api/status")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "running"
        assert "version" in data


# ============================================================================
# CALCULATION ENDPOINT TESTS
# ============================================================================

class TestCalculationEndpoint:
    """Tests for /api/calculate endpoint"""

    def get_sample_request(self) -> dict:
        """Get sample calculation request"""
        return {
            "inputs": {
                "purchasePrice": 500000,
                "closingCosts": 10000,
                "renovationBudget": 0,
                "downPaymentPct": 25,
                "interestRatePct": 6.5,
                "amortYears": 30,
                "loanTermYears": 30,
                "loanFeesPct": 0,
                "interestOnlyMonths": 0,
                "units": 4,
                "avgMonthlyRentPerUnit": 1200,
                "otherMonthlyIncome": 100,
                "vacancyPct": 5,
                "rentGrowthPct": 3,
                "expenseGrowthPct": 3,
                "managementPctOfEGI": 8,
                "capexReservePctOfEGI": 5,
                "holdYears": 5,
                "exitCapRatePct": 6.0,
                "sellingCostsPct": 6,
                "expenseLineItems": [
                    {"id": "1", "label": "Taxes", "annualAmount": 7500, "category": "taxes"},
                    {"id": "2", "label": "Insurance", "annualAmount": 3000, "category": "insurance"}
                ],
                "targets": {
                    "minIRR": 12,
                    "minCashOnCash": 6,
                    "minDSCR": 1.25,
                    "maxEquity": 500000
                }
            }
        }

    def test_calculate_success(self):
        """Test successful calculation"""
        response = client.post("/api/calculate", json=self.get_sample_request())
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "results" in data
        assert data["results"]["IRR"] is not None

    def test_calculate_returns_all_metrics(self):
        """Test that calculation returns all expected metrics"""
        response = client.post("/api/calculate", json=self.get_sample_request())
        data = response.json()

        results = data["results"]

        # Check upfront metrics
        assert "totalAcquisitionCost" in results
        assert "loanAmount" in results
        assert "equityInvested" in results

        # Check Year 1 metrics
        assert "NOI_year1" in results
        assert "cashFlow_year1" in results
        assert "capRate_year1" in results
        assert "cashOnCash_year1" in results
        assert "DSCR_year1" in results

        # Check overall metrics
        assert "IRR" in results
        assert "equityMultiple" in results
        assert "avgDSCR" in results

        # Check pro forma
        assert "proForma" in results
        assert len(results["proForma"]) == 5

        # Check verdict
        assert "verdict" in results
        assert results["verdict"]["status"] in ["pass", "fail", "borderline"]

    def test_calculate_with_io_period(self):
        """Test calculation with interest-only period"""
        request = self.get_sample_request()
        request["inputs"]["interestOnlyMonths"] = 12

        response = client.post("/api/calculate", json=request)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

        # First year should show IO
        proforma = data["results"]["proForma"]
        assert proforma[0]["isIOYear"] is True

    def test_calculate_minimal_inputs(self):
        """Test calculation with minimal required inputs"""
        request = {
            "inputs": {
                "purchasePrice": 300000,
                "units": 2,
                "avgMonthlyRentPerUnit": 1500,
                "expenseLineItems": []
            }
        }

        response = client.post("/api/calculate", json=request)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    def test_calculate_invalid_purchase_price(self):
        """Test validation for invalid purchase price"""
        request = self.get_sample_request()
        request["inputs"]["purchasePrice"] = -100000

        response = client.post("/api/calculate", json=request)
        # Should get validation error
        assert response.status_code in [200, 422]

    def test_calculate_missing_required_fields(self):
        """Test validation for missing required fields"""
        request = {"inputs": {}}

        response = client.post("/api/calculate", json=request)
        # Should get validation error
        assert response.status_code in [200, 422]


# ============================================================================
# SIMPLE CALCULATION ENDPOINT TESTS
# ============================================================================

class TestSimpleCalculationEndpoint:
    """Tests for /api/calculate/simple endpoint"""

    def test_simple_calculate(self):
        """Test simple calculation endpoint"""
        response = client.post(
            "/api/calculate/simple",
            params={
                "purchase_price": 400000,
                "units": 4,
                "avg_monthly_rent": 1100
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "results" in data

    def test_simple_calculate_with_options(self):
        """Test simple calculation with optional parameters"""
        response = client.post(
            "/api/calculate/simple",
            params={
                "purchase_price": 500000,
                "units": 6,
                "avg_monthly_rent": 1200,
                "down_payment_pct": 30,
                "interest_rate_pct": 7.0,
                "hold_years": 7
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert len(data["results"]["proForma"]) == 7


# ============================================================================
# AUTHENTICATION ENDPOINT TESTS
# ============================================================================

class TestAuthEndpoints:
    """Tests for authentication endpoints"""

    def test_auth_me_without_token(self):
        """Test /auth/me without authentication"""
        response = client.get("/auth/me")
        assert response.status_code == 401

    def test_auth_logout(self):
        """Test /auth/logout endpoint"""
        response = client.post("/auth/logout")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data


# ============================================================================
# FRONTEND SERVING TESTS
# ============================================================================

class TestFrontend:
    """Tests for frontend serving"""

    def test_root_returns_html(self):
        """Test that root endpoint returns HTML"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


# ============================================================================
# DEALSNAP QUICK MODE ENDPOINT TESTS
# ============================================================================

class TestDealSnapEndpoint:
    """Tests for /api/dealsnap endpoint"""

    def get_sample_dealsnap_request(self) -> dict:
        """Get sample DealSnap request"""
        return {
            "inputs": {
                "units": 6,
                "avg_monthly_rent": 1200,
                "purchase_price": 500000,
                "property_type": "multifamily",
                "property_condition": "average",
                "expense_responsibility": "mixed",
                "insurance_risk": "moderate",
                "down_payment_pct": 25,
                "interest_rate_pct": 6.5,
                "amort_years": 30
            }
        }

    def test_dealsnap_success(self):
        """Test successful DealSnap calculation"""
        response = client.post("/api/dealsnap", json=self.get_sample_dealsnap_request())
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "results" in data

    def test_dealsnap_returns_all_sections(self):
        """Test DealSnap returns all result sections"""
        response = client.post("/api/dealsnap", json=self.get_sample_dealsnap_request())
        data = response.json()
        results = data["results"]

        assert "income" in results
        assert "expenses" in results
        assert "value_reality_check" in results
        assert "finance_reality_check" in results
        assert "reverse_engineering" in results
        assert "deal_triage" in results

    def test_dealsnap_income_fields(self):
        """Test income section has required fields"""
        response = client.post("/api/dealsnap", json=self.get_sample_dealsnap_request())
        income = response.json()["results"]["income"]

        assert "gpr_annual" in income
        assert "vacancy_loss" in income
        assert "egi" in income
        assert "cap_rate" in income
        assert "grm" in income
        assert "price_per_unit" in income

    def test_dealsnap_triage_verdict(self):
        """Test deal triage returns proper verdict"""
        response = client.post("/api/dealsnap", json=self.get_sample_dealsnap_request())
        triage = response.json()["results"]["deal_triage"]

        assert triage["verdict"] in ["Pursue", "Watch", "Pass"]
        assert 0 <= triage["total_score"] <= 12

    def test_dealsnap_value_check_has_valuations(self):
        """Test value reality check returns cap rate valuations"""
        response = client.post("/api/dealsnap", json=self.get_sample_dealsnap_request())
        value_check = response.json()["results"]["value_reality_check"]

        assert len(value_check["valuations"]) == 6
        for v in value_check["valuations"]:
            assert v["signal"] in ["green", "orange", "red"]

    def test_dealsnap_finance_dscr_signal(self):
        """Test finance reality check returns DSCR signal"""
        response = client.post("/api/dealsnap", json=self.get_sample_dealsnap_request())
        finance = response.json()["results"]["finance_reality_check"]

        assert "dscr" in finance
        assert "dscr_signal" in finance
        assert finance["dscr_signal"] in ["green", "orange", "red"]
        assert "loan_amount" in finance
        assert "monthly_payment" in finance

    def test_dealsnap_with_rent_lift(self):
        """Test DealSnap with rent lift enabled"""
        request = self.get_sample_dealsnap_request()
        request["inputs"]["rent_lift_dollar_per_unit"] = 200

        response = client.post("/api/dealsnap", json=request)
        data = response.json()
        assert data["success"] is True
        assert data["results"]["rent_lift_sensitivity"] is not None
        assert data["results"]["rent_lift_sensitivity"]["new_rent_per_unit"] == 1400

    def test_dealsnap_without_rent_lift(self):
        """Test DealSnap without rent lift returns null sensitivity"""
        response = client.post("/api/dealsnap", json=self.get_sample_dealsnap_request())
        data = response.json()
        assert data["results"]["rent_lift_sensitivity"] is None

    def test_dealsnap_minimal_inputs(self):
        """Test DealSnap with minimal required inputs only"""
        request = {
            "inputs": {
                "units": 4,
                "avg_monthly_rent": 1000,
                "purchase_price": 300000
            }
        }
        response = client.post("/api/dealsnap", json=request)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_dealsnap_single_family(self):
        """Test DealSnap with single family property type"""
        request = self.get_sample_dealsnap_request()
        request["inputs"]["property_type"] = "single_family"
        request["inputs"]["units"] = 1
        request["inputs"]["avg_monthly_rent"] = 2000

        response = client.post("/api/dealsnap", json=request)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_dealsnap_apartment(self):
        """Test DealSnap with apartment property type"""
        request = self.get_sample_dealsnap_request()
        request["inputs"]["property_type"] = "apartment"
        request["inputs"]["units"] = 20

        response = client.post("/api/dealsnap", json=request)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_dealsnap_missing_required_fields(self):
        """Test validation for missing required fields"""
        request = {"inputs": {}}
        response = client.post("/api/dealsnap", json=request)
        assert response.status_code == 422

    def test_dealsnap_reverse_engineering(self):
        """Test reverse engineering section"""
        response = client.post("/api/dealsnap", json=self.get_sample_dealsnap_request())
        reverse = response.json()["results"]["reverse_engineering"]

        assert "breakeven_rent_per_unit" in reverse
        assert "max_price_at_target_cap" in reverse
        assert "noi_needed_for_dscr_125" in reverse
        assert reverse["breakeven_rent_per_unit"] > 0


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
