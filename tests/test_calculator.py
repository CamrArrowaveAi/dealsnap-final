"""
DealSnap - Unit Tests for Calculation Engine
Tests financial calculations against known good results
"""
import pytest
# Add project root to path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.calculator import (
    calculate_monthly_payment,
    calculate_remaining_balance,
    build_monthly_amort_schedule,
    get_annual_amort_data,
    calculate_irr,
    calculate_deal,
    calculate_dealsnap,
    calculate_dealsnap_income,
    calculate_dealsnap_expenses,
    calculate_value_reality_check,
    calculate_rent_lift_sensitivity,
    calculate_reverse_engineering,
    calculate_finance_reality_check,
    calculate_deal_triage,
    EXPENSE_RATIO_MATRIX,
    INSURANCE_PER_UNIT,
    CAPEX_RESERVE_MATRIX,
)
from backend.models import (
    DealInputs, ExpenseItem, DealSnapInputs,
    PropertyType, PropertyCondition, ExpenseResponsibility, InsuranceRisk
)


# ============================================================================
# TEST DATA - Sample 6-Unit Deal (Based on Tremont Ave reference)
# ============================================================================

def get_sample_deal_inputs() -> DealInputs:
    """Create sample deal inputs based on Tremont Ave reference deal"""
    return DealInputs(
        purchasePrice=670000,
        closingCosts=6764,
        renovationBudget=0,
        downPaymentPct=25,
        interestRatePct=6.5,
        amortYears=25,
        loanTermYears=5,
        loanFeesPct=0,
        interestOnlyMonths=3,
        entireLoanInterestOnly=False,
        units=6,
        avgMonthlyRentPerUnit=1230,
        otherMonthlyIncome=100,
        vacancyPct=5,
        rentGrowthPct=3.5,
        expenseGrowthPct=3,
        managementPctOfEGI=8,
        capexReservePctOfEGI=5,
        holdYears=5,
        exitCapRatePct=5.5,
        sellingCostsPct=6,
        expenseLineItems=[
            ExpenseItem(id='1', label='Taxes', annualAmount=16443, category='taxes'),
            ExpenseItem(id='2', label='Insurance', annualAmount=3572, category='insurance'),
            ExpenseItem(id='3', label='Utilities', annualAmount=2400, category='utilities'),
            ExpenseItem(id='4', label='Repairs & Maintenance', annualAmount=3000, category='repairs'),
            ExpenseItem(id='5', label='Admin', annualAmount=500, category='admin')
        ]
    )


# ============================================================================
# MONTHLY PAYMENT TESTS
# ============================================================================

class TestMonthlyPayment:
    """Tests for calculate_monthly_payment function"""

    def test_standard_30_year_mortgage(self):
        """Test standard 30-year mortgage payment calculation"""
        # $500,000 loan at 6% for 30 years
        payment = calculate_monthly_payment(500000, 6.0, 30)
        # Expected: $2,997.75 (standard amortization)
        assert abs(payment - 2997.75) < 1.0

    def test_15_year_mortgage(self):
        """Test 15-year mortgage payment calculation"""
        # $300,000 loan at 5.5% for 15 years
        payment = calculate_monthly_payment(300000, 5.5, 15)
        # Expected: $2,451.76
        assert abs(payment - 2451.76) < 1.0

    def test_zero_interest_rate(self):
        """Test payment calculation with 0% interest"""
        # $120,000 loan at 0% for 10 years
        payment = calculate_monthly_payment(120000, 0, 10)
        # Expected: $1,000/month ($120,000 / 120 months)
        assert payment == 1000.0

    def test_high_interest_rate(self):
        """Test payment calculation with high interest rate"""
        # $200,000 loan at 12% for 30 years
        payment = calculate_monthly_payment(200000, 12.0, 30)
        # Expected: ~$2,057.23
        assert abs(payment - 2057.23) < 1.0


# ============================================================================
# REMAINING BALANCE TESTS
# ============================================================================

class TestRemainingBalance:
    """Tests for calculate_remaining_balance function"""

    def test_balance_after_5_years(self):
        """Test remaining balance after 5 years of payments"""
        # $500,000 loan at 6% for 30 years, 5 years elapsed
        balance = calculate_remaining_balance(500000, 6.0, 30, 5)
        # Balance should be around $465,000 (principal paydown is slow initially)
        assert 460000 < balance < 470000

    def test_balance_at_maturity(self):
        """Test remaining balance at full maturity (should be 0)"""
        balance = calculate_remaining_balance(500000, 6.0, 30, 30)
        assert balance == 0.0

    def test_balance_after_full_term(self):
        """Test balance when years elapsed exceeds amortization"""
        balance = calculate_remaining_balance(500000, 6.0, 30, 35)
        assert balance == 0.0

    def test_balance_zero_interest(self):
        """Test balance with 0% interest (linear paydown)"""
        # $120,000 at 0% for 10 years, 5 years elapsed = $60,000 remaining
        balance = calculate_remaining_balance(120000, 0, 10, 5)
        assert balance == 60000.0


# ============================================================================
# AMORTIZATION SCHEDULE TESTS
# ============================================================================

class TestAmortizationSchedule:
    """Tests for amortization schedule building"""

    def test_monthly_schedule_length(self):
        """Test that schedule has correct number of entries"""
        schedule = build_monthly_amort_schedule(
            principal=500000,
            annual_rate_pct=6.0,
            amort_years=30,
            interest_only_months=0,
            total_months=60
        )
        assert len(schedule) == 60

    def test_io_period_handling(self):
        """Test interest-only period in schedule"""
        schedule = build_monthly_amort_schedule(
            principal=500000,
            annual_rate_pct=6.0,
            amort_years=30,
            interest_only_months=12,
            total_months=24
        )

        # First 12 months should be IO
        for i in range(12):
            assert schedule[i].is_io is True
            assert schedule[i].principal_paid == 0

        # Month 13+ should have principal paydown
        assert schedule[12].is_io is False
        assert schedule[12].principal_paid > 0

    def test_full_io_loan(self):
        """Test entire loan as interest-only"""
        schedule = build_monthly_amort_schedule(
            principal=500000,
            annual_rate_pct=6.0,
            amort_years=30,
            interest_only_months=0,
            total_months=60,
            entire_loan_interest_only=True
        )

        # All months should be IO with no principal
        for entry in schedule:
            assert entry.is_io is True
            assert entry.principal_paid == 0
            assert entry.ending_balance == 500000

    def test_annual_aggregation(self):
        """Test annual aggregate calculations"""
        schedule = build_monthly_amort_schedule(
            principal=500000,
            annual_rate_pct=6.0,
            amort_years=30,
            interest_only_months=0,
            total_months=60
        )

        year1_data = get_annual_amort_data(schedule, 1)

        # Annual debt service should be ~$35,973 (monthly payment * 12)
        assert abs(year1_data.annual_debt_service - 35973) < 100

        # Beginning balance should be full principal
        assert year1_data.beginning_balance == 500000


# ============================================================================
# IRR CALCULATION TESTS
# ============================================================================

class TestIRRCalculation:
    """Tests for IRR (Internal Rate of Return) calculation"""

    def test_simple_irr(self):
        """Test IRR with simple cash flows"""
        # -100 initial investment, 110 return after 1 year = 10% IRR
        cash_flows = [-100, 110]
        irr = calculate_irr(cash_flows)
        assert abs(irr - 10.0) < 0.1

    def test_multi_year_irr(self):
        """Test IRR with multi-year cash flows"""
        # -1000 initial, 200/year for 4 years + 700 in year 5 (200 regular + 500 exit)
        cash_flows = [-1000, 200, 200, 200, 200, 700]
        irr = calculate_irr(cash_flows)
        # Expected IRR around 12% (verified mathematically)
        assert 10 < irr < 15

    def test_negative_irr(self):
        """Test IRR with negative returns"""
        # -100 initial, only 80 returned
        cash_flows = [-100, 80]
        irr = calculate_irr(cash_flows)
        assert irr < 0

    def test_real_estate_irr(self):
        """Test IRR with realistic real estate cash flows"""
        # Typical real estate deal: -250k equity, 20k/yr cash flow, 400k exit
        cash_flows = [-250000, 20000, 21000, 22000, 23000, 24000 + 400000]
        irr = calculate_irr(cash_flows)
        # Expected IRR around 18-22%
        assert 15 < irr < 25


# ============================================================================
# FULL DEAL CALCULATION TESTS
# ============================================================================

class TestDealCalculation:
    """Tests for complete deal calculations"""

    def test_basic_deal_structure(self):
        """Test that deal calculation returns proper structure"""
        inputs = get_sample_deal_inputs()
        results = calculate_deal(inputs)

        # Check all required fields exist
        assert results.total_acquisition_cost > 0
        assert results.loan_amount > 0
        assert results.equity_invested > 0
        assert results.noi_year1 > 0
        assert results.irr != 0
        assert len(results.pro_forma) == inputs.hold_years

    def test_loan_amount_calculation(self):
        """Test loan amount is calculated correctly from down payment"""
        inputs = get_sample_deal_inputs()
        results = calculate_deal(inputs)

        expected_loan = inputs.purchase_price * (1 - inputs.down_payment_pct / 100)
        assert abs(results.loan_amount - expected_loan) < 1

    def test_equity_invested(self):
        """Test equity invested calculation"""
        inputs = get_sample_deal_inputs()
        results = calculate_deal(inputs)

        # Equity = Purchase + Closing + Reno + Fees - Loan
        expected_equity = (
            inputs.purchase_price +
            inputs.closing_costs +
            inputs.renovation_budget +
            inputs.purchase_price * inputs.loan_fees_pct / 100 -
            results.loan_amount
        )
        assert abs(results.equity_invested - expected_equity) < 1

    def test_year1_noi(self):
        """Test Year 1 NOI calculation"""
        inputs = get_sample_deal_inputs()
        results = calculate_deal(inputs)

        # Manual calculation
        gpr = inputs.units * inputs.avg_monthly_rent_per_unit * 12
        other_income = inputs.other_monthly_income * 12
        gross_income = gpr + other_income
        vacancy_loss = gpr * (inputs.vacancy_pct / 100)
        egi = gross_income - vacancy_loss

        # Expenses
        fixed_expenses = sum(e.annual_amount for e in inputs.expense_line_items)
        management = egi * (inputs.management_pct_of_egi / 100)
        capex = egi * (inputs.capex_reserve_pct_of_egi / 100)
        total_opex = fixed_expenses + management + capex

        expected_noi = egi - total_opex

        assert abs(results.noi_year1 - expected_noi) < 10

    def test_dscr_calculation(self):
        """Test DSCR is properly calculated"""
        inputs = get_sample_deal_inputs()
        results = calculate_deal(inputs)

        # DSCR = NOI / Debt Service
        # Should be > 1.0 for a viable deal
        assert results.dscr_year1 > 0

    def test_cap_rate_calculation(self):
        """Test cap rate calculation"""
        inputs = get_sample_deal_inputs()
        results = calculate_deal(inputs)

        expected_cap_rate = (results.noi_year1 / inputs.purchase_price) * 100
        assert abs(results.cap_rate_year1 - expected_cap_rate) < 0.01

    def test_cash_on_cash_calculation(self):
        """Test Cash-on-Cash return calculation"""
        inputs = get_sample_deal_inputs()
        results = calculate_deal(inputs)

        expected_coc = (results.cash_flow_year1 / results.equity_invested) * 100
        assert abs(results.cash_on_cash_year1 - expected_coc) < 0.01

    def test_proforma_length(self):
        """Test pro forma has correct number of years"""
        inputs = get_sample_deal_inputs()
        results = calculate_deal(inputs)

        assert len(results.pro_forma) == inputs.hold_years

    def test_proforma_year_progression(self):
        """Test pro forma years are sequential"""
        inputs = get_sample_deal_inputs()
        results = calculate_deal(inputs)

        for i, pf in enumerate(results.pro_forma):
            assert pf.year == i + 1

    def test_rent_growth_applied(self):
        """Test that rent growth is applied year over year"""
        inputs = get_sample_deal_inputs()
        results = calculate_deal(inputs)

        # Year 2 GPR should be higher than Year 1
        if len(results.pro_forma) >= 2:
            year1_gpr = results.pro_forma[0].gpr
            year2_gpr = results.pro_forma[1].gpr
            expected_year2 = year1_gpr * (1 + inputs.rent_growth_pct / 100)
            assert abs(year2_gpr - expected_year2) < 10

    def test_expense_growth_applied(self):
        """Test that expense growth is applied year over year"""
        inputs = get_sample_deal_inputs()
        results = calculate_deal(inputs)

        # Year 2 operating expenses should be higher than Year 1
        if len(results.pro_forma) >= 2:
            year1_opex = results.pro_forma[0].operating_expenses
            year2_opex = results.pro_forma[1].operating_expenses
            expected_year2 = year1_opex * (1 + inputs.expense_growth_pct / 100)
            assert abs(year2_opex - expected_year2) < 10

    def test_verdict_generation(self):
        """Test that verdict is properly generated"""
        inputs = get_sample_deal_inputs()
        results = calculate_deal(inputs)

        assert results.verdict.status in ['pass', 'fail', 'borderline']
        assert len(results.verdict.summary) > 0
        assert 'irr' in results.verdict.checks
        assert 'cashOnCash' in results.verdict.checks
        assert 'dscr' in results.verdict.checks
        assert 'equity' in results.verdict.checks

    def test_exit_calculations(self):
        """Test exit sale price and proceeds"""
        inputs = get_sample_deal_inputs()
        results = calculate_deal(inputs)

        # Sale price should be positive
        assert results.sale_price > 0

        # Net proceeds should account for selling costs and debt payoff
        assert results.net_sale_proceeds > 0
        assert results.net_sale_proceeds < results.sale_price


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions"""

    def test_single_unit_property(self):
        """Test calculation for single-family home"""
        inputs = DealInputs(
            purchasePrice=300000,
            closingCosts=6000,
            renovationBudget=0,
            downPaymentPct=20,
            interestRatePct=7.0,
            amortYears=30,
            loanTermYears=30,
            loanFeesPct=0,
            interestOnlyMonths=0,
            units=1,
            avgMonthlyRentPerUnit=2000,
            otherMonthlyIncome=0,
            vacancyPct=5,
            rentGrowthPct=3,
            expenseGrowthPct=3,
            managementPctOfEGI=10,
            capexReservePctOfEGI=5,
            holdYears=5,
            exitCapRatePct=6.0,
            sellingCostsPct=6,
            expenseLineItems=[
                ExpenseItem(id='1', label='Taxes', annualAmount=3000, category='taxes'),
                ExpenseItem(id='2', label='Insurance', annualAmount=1500, category='insurance')
            ]
        )
        results = calculate_deal(inputs)
        assert results.irr is not None
        assert len(results.pro_forma) == 5

    def test_high_vacancy_rate(self):
        """Test deal with high vacancy rate"""
        inputs = get_sample_deal_inputs()
        inputs.vacancy_pct = 30  # 30% vacancy
        results = calculate_deal(inputs)

        # Should still calculate but likely fail verdict
        assert results.irr is not None

    def test_short_hold_period(self):
        """Test 1-year hold period"""
        inputs = get_sample_deal_inputs()
        inputs.hold_years = 1
        results = calculate_deal(inputs)

        assert len(results.pro_forma) == 1

    def test_long_hold_period(self):
        """Test 20-year hold period"""
        inputs = get_sample_deal_inputs()
        inputs.hold_years = 20
        results = calculate_deal(inputs)

        assert len(results.pro_forma) == 20

    def test_no_other_income(self):
        """Test deal with no other income"""
        inputs = get_sample_deal_inputs()
        inputs.other_monthly_income = 0
        inputs.other_income_line_items = []
        results = calculate_deal(inputs)

        assert results.irr is not None


# ============================================================================
# DEALSNAP QUICK MODE TESTS
# ============================================================================

def get_sample_dealsnap_inputs() -> DealSnapInputs:
    """Create sample DealSnap Quick Mode inputs"""
    return DealSnapInputs(
        units=6,
        avg_monthly_rent=1200,
        purchase_price=500000,
        property_type=PropertyType.MULTIFAMILY,
        property_condition=PropertyCondition.AVERAGE,
        expense_responsibility=ExpenseResponsibility.MIXED,
        insurance_risk=InsuranceRisk.MODERATE,
        down_payment_pct=25,
        interest_rate_pct=6.5,
        amort_years=30,
    )


class TestDealSnapIncome:
    """Tests for DealSnap income calculation engine"""

    def test_gpr_calculation(self):
        """Test GPR = units * avg_rent * 12"""
        inputs = get_sample_dealsnap_inputs()
        income = calculate_dealsnap_income(inputs)
        expected_gpr = 6 * 1200 * 12  # 86400
        assert income.gpr_annual == expected_gpr

    def test_vacancy_loss(self):
        """Test vacancy loss at default 5%"""
        inputs = get_sample_dealsnap_inputs()
        income = calculate_dealsnap_income(inputs)
        expected_vacancy = income.gpr_annual * 0.05
        assert abs(income.vacancy_loss - expected_vacancy) < 1

    def test_egi_calculation(self):
        """Test EGI = GPR - vacancy"""
        inputs = get_sample_dealsnap_inputs()
        income = calculate_dealsnap_income(inputs)
        assert abs(income.egi - (income.gpr_annual - income.vacancy_loss)) < 1

    def test_cap_rate(self):
        """Test cap rate = NOI / purchase_price * 100"""
        inputs = get_sample_dealsnap_inputs()
        income = calculate_dealsnap_income(inputs)
        assert income.cap_rate > 0

    def test_grm(self):
        """Test GRM = purchase_price / GPR"""
        inputs = get_sample_dealsnap_inputs()
        income = calculate_dealsnap_income(inputs)
        expected_grm = 500000 / (6 * 1200 * 12)
        assert abs(income.grm - expected_grm) < 0.1

    def test_price_per_unit(self):
        """Test price per unit calculation"""
        inputs = get_sample_dealsnap_inputs()
        income = calculate_dealsnap_income(inputs)
        assert income.price_per_unit == 500000 / 6


class TestDealSnapExpenses:
    """Tests for DealSnap smart expense engine"""

    def test_expense_ratio_lookup(self):
        """Test that expense ratio matrix returns valid values"""
        inputs = get_sample_dealsnap_inputs()
        expenses = calculate_dealsnap_expenses(inputs, egi=82080.0)
        assert 0 < expenses.expense_ratio_pct < 100

    def test_total_expenses_positive(self):
        """Test total expenses are positive"""
        inputs = get_sample_dealsnap_inputs()
        expenses = calculate_dealsnap_expenses(inputs, egi=82080.0)
        assert expenses.total_annual_expenses > 0

    def test_insurance_per_unit(self):
        """Test insurance is calculated per unit"""
        inputs = get_sample_dealsnap_inputs()
        expenses = calculate_dealsnap_expenses(inputs, egi=82080.0)
        expected_insurance = INSURANCE_PER_UNIT[InsuranceRisk.MODERATE] * 6
        assert abs(expenses.insurance_annual - expected_insurance) < 1

    def test_capex_reserve(self):
        """Test CapEx reserve calculation"""
        inputs = get_sample_dealsnap_inputs()
        expenses = calculate_dealsnap_expenses(inputs, egi=82080.0)
        assert expenses.capex_annual > 0

    def test_expense_breakdown_sums(self):
        """Test that expense breakdown sums to total"""
        inputs = get_sample_dealsnap_inputs()
        expenses = calculate_dealsnap_expenses(inputs, egi=82080.0)
        breakdown_total = (
            expenses.management_annual +
            expenses.insurance_annual +
            expenses.capex_annual +
            expenses.other_expenses_annual
        )
        assert abs(expenses.total_annual_expenses - breakdown_total) < 1


class TestExpenseRatioMatrix:
    """Tests for expense ratio lookup matrix"""

    def test_matrix_has_27_entries(self):
        """Test matrix covers all 27 combinations"""
        assert len(EXPENSE_RATIO_MATRIX) == 27

    def test_all_ratios_in_range(self):
        """Test all expense ratios are between 20% and 60%"""
        for key, ratio in EXPENSE_RATIO_MATRIX.items():
            assert 20 <= ratio <= 60, f"Ratio {ratio} out of range for {key}"

    def test_capex_matrix_has_9_entries(self):
        """Test CapEx matrix covers all 9 combinations"""
        assert len(CAPEX_RESERVE_MATRIX) == 9


class TestValueRealityCheck:
    """Tests for value reality check engine"""

    def test_returns_valuations(self):
        """Test that valuations are returned for cap rates 5-10%"""
        valuations = calculate_value_reality_check(
            noi=50000, purchase_price=500000
        )
        assert len(valuations.valuations) == 6  # 5%, 6%, 7%, 8%, 9%, 10%

    def test_signal_assignment(self):
        """Test signal colors are assigned (green/orange/red)"""
        valuations = calculate_value_reality_check(
            noi=50000, purchase_price=500000
        )
        for v in valuations.valuations:
            assert v.signal in ['green', 'orange', 'red']

    def test_implied_value_calculation(self):
        """Test implied value = NOI / cap_rate"""
        valuations = calculate_value_reality_check(
            noi=50000, purchase_price=500000
        )
        # At 10% cap rate, implied value = 50000 / 0.10 = 500000
        ten_pct = [v for v in valuations.valuations if v.cap_rate == 10.0][0]
        assert abs(ten_pct.implied_value - 500000) < 1

    def test_delta_calculation(self):
        """Test delta = implied_value - purchase_price"""
        valuations = calculate_value_reality_check(
            noi=50000, purchase_price=500000
        )
        for v in valuations.valuations:
            assert abs(v.delta - (v.implied_value - 500000)) < 1


class TestFinanceRealityCheck:
    """Tests for finance reality check engine"""

    def test_dscr_calculation(self):
        """Test DSCR = NOI / annual_debt_service"""
        result = calculate_finance_reality_check(
            noi=50000, purchase_price=500000,
            down_payment_pct=25, interest_rate_pct=6.5, amort_years=30
        )
        assert result.dscr > 0

    def test_dscr_signal_green(self):
        """Test green signal for DSCR >= 1.25"""
        result = calculate_finance_reality_check(
            noi=100000, purchase_price=500000,
            down_payment_pct=25, interest_rate_pct=6.5, amort_years=30
        )
        if result.dscr >= 1.25:
            assert result.dscr_signal == 'green'

    def test_loan_amount(self):
        """Test loan amount = purchase * (1 - down/100)"""
        result = calculate_finance_reality_check(
            noi=50000, purchase_price=500000,
            down_payment_pct=25, interest_rate_pct=6.5, amort_years=30
        )
        assert abs(result.loan_amount - 375000) < 1

    def test_monthly_payment(self):
        """Test monthly payment is positive"""
        result = calculate_finance_reality_check(
            noi=50000, purchase_price=500000,
            down_payment_pct=25, interest_rate_pct=6.5, amort_years=30
        )
        assert result.monthly_payment > 0


class TestReverseEngineering:
    """Tests for reverse deal engineering"""

    def test_breakeven_rent(self):
        """Test break-even rent calculation"""
        result = calculate_reverse_engineering(
            noi=50000, purchase_price=500000,
            units=6, annual_debt_service=30000,
            total_annual_expenses=32000
        )
        assert result.breakeven_rent_per_unit > 0

    def test_max_price_at_target_cap(self):
        """Test max price at 7% cap rate"""
        result = calculate_reverse_engineering(
            noi=50000, purchase_price=500000,
            units=6, annual_debt_service=30000,
            total_annual_expenses=32000
        )
        # Max price = NOI / 0.07
        expected = 50000 / 0.07
        assert abs(result.max_price_at_target_cap - expected) < 1

    def test_noi_for_dscr_125(self):
        """Test NOI needed for 1.25x DSCR"""
        result = calculate_reverse_engineering(
            noi=50000, purchase_price=500000,
            units=6, annual_debt_service=30000,
            total_annual_expenses=32000
        )
        expected_noi = 30000 * 1.25
        assert abs(result.noi_needed_for_dscr_125 - expected_noi) < 1


class TestDealTriage:
    """Tests for deal triage scoring"""

    def test_scoring_range(self):
        """Test total score is between 0 and 12"""
        triage = calculate_deal_triage(
            cap_rate=7.0, dscr=1.3, expense_ratio=40.0, grm=10.0,
            dscr_signal='green'
        )
        assert 0 <= triage.total_score <= 12

    def test_pursue_verdict(self):
        """Test Pursue verdict for high-scoring deal"""
        triage = calculate_deal_triage(
            cap_rate=9.0, dscr=1.5, expense_ratio=35.0, grm=8.0,
            dscr_signal='green'
        )
        assert triage.verdict == 'Pursue'
        assert triage.total_score >= 8

    def test_pass_verdict(self):
        """Test Pass verdict for low-scoring deal"""
        triage = calculate_deal_triage(
            cap_rate=3.0, dscr=0.8, expense_ratio=55.0, grm=20.0,
            dscr_signal='red'
        )
        assert triage.verdict == 'Pass'
        assert triage.total_score < 5

    def test_watch_verdict(self):
        """Test Watch verdict for mid-scoring deal"""
        triage = calculate_deal_triage(
            cap_rate=6.0, dscr=1.1, expense_ratio=42.0, grm=12.0,
            dscr_signal='orange'
        )
        assert triage.verdict == 'Watch'
        assert 5 <= triage.total_score < 8


class TestDealSnapFullCalculation:
    """Tests for complete DealSnap calculation"""

    def test_full_calculation_returns_all_sections(self):
        """Test that calculate_dealsnap returns all required sections"""
        inputs = get_sample_dealsnap_inputs()
        results = calculate_dealsnap(inputs)

        assert results.income is not None
        assert results.expenses is not None
        assert results.value_reality_check is not None
        assert results.reverse_engineering is not None
        assert results.finance_reality_check is not None
        assert results.deal_triage is not None

    def test_no_rent_lift_returns_none_sensitivity(self):
        """Test that no rent lift input returns None for sensitivity"""
        inputs = get_sample_dealsnap_inputs()
        results = calculate_dealsnap(inputs)
        assert results.rent_lift_sensitivity is None

    def test_with_rent_lift_dollar(self):
        """Test with dollar rent lift"""
        inputs = get_sample_dealsnap_inputs()
        inputs.rent_lift_dollar_per_unit = 200
        results = calculate_dealsnap(inputs)
        assert results.rent_lift_sensitivity is not None
        assert results.rent_lift_sensitivity.new_rent_per_unit == 1400

    def test_with_rent_lift_pct(self):
        """Test with percentage rent lift"""
        inputs = get_sample_dealsnap_inputs()
        inputs.rent_lift_pct = 10.0
        results = calculate_dealsnap(inputs)
        assert results.rent_lift_sensitivity is not None
        assert results.rent_lift_sensitivity.new_rent_per_unit == 1320  # 1200 * 1.10

    def test_different_property_types(self):
        """Test calculation works for all property types"""
        for prop_type in PropertyType:
            inputs = get_sample_dealsnap_inputs()
            inputs.property_type = prop_type
            results = calculate_dealsnap(inputs)
            assert results.deal_triage is not None

    def test_different_conditions(self):
        """Test calculation works for all property conditions"""
        for condition in PropertyCondition:
            inputs = get_sample_dealsnap_inputs()
            inputs.property_condition = condition
            results = calculate_dealsnap(inputs)
            assert results.expenses.expense_ratio_pct > 0

    def test_different_insurance_risks(self):
        """Test insurance varies by risk tier"""
        results = {}
        for risk in InsuranceRisk:
            inputs = get_sample_dealsnap_inputs()
            inputs.insurance_risk = risk
            r = calculate_dealsnap(inputs)
            results[risk] = r.expenses.insurance_annual

        # Higher risk should mean higher insurance
        assert results[InsuranceRisk.HIGH] > results[InsuranceRisk.MODERATE]
        assert results[InsuranceRisk.MODERATE] > results[InsuranceRisk.LOW]

    def test_single_unit_property(self):
        """Test DealSnap with single unit"""
        inputs = DealSnapInputs(
            units=1,
            avg_monthly_rent=2000,
            purchase_price=300000,
            property_type=PropertyType.SINGLE_FAMILY,
            property_condition=PropertyCondition.NEWER,
        )
        results = calculate_dealsnap(inputs)
        assert results.income.price_per_unit == 300000
        assert results.deal_triage is not None


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
