"""
DealSnap - Financial Calculation Engine
Core financial metrics + DealSnap Quick Mode Analysis

Full Underwrite:
- IRR, DSCR, CoC, Cap Rate, NOI, Pro Forma

DealSnap Quick Mode:
- Expense ratio engine with smart defaults
- Value reality check (cap rate valuation ranges)
- Rent lift sensitivity
- Reverse deal engineering
- Finance reality check (DSCR bands)
- CapEx reserves by property type
- Deal triage score (Pursue/Watch/Pass)
"""
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
import math

from backend.models import (
    DealInputs, DealResults, AnnualProForma, DealVerdict, VerdictCheck,
    OperatingRatios, AuditData, ExpenseCategory, ExpensePayer,
    DealSnapInputs, DealSnapResults,
    IncomeAnalysis, ExpenseAnalysis, ValueRealityCheck, ValuationRange,
    RentLiftSensitivity, ReverseDealEngineering, FinanceRealityCheck,
    DealTriageResult,
    PropertyType, PropertyCondition, ExpenseResponsibility, InsuranceRisk,
    TriageScore
)


# ============================================================================
# HELPER DATA STRUCTURES
# ============================================================================

@dataclass
class MonthlyAmortEntry:
    """Monthly amortization schedule entry"""
    month: int  # 1-indexed
    is_io: bool
    payment: float
    interest_paid: float
    principal_paid: float
    beginning_balance: float
    ending_balance: float


@dataclass
class AnnualAmortData:
    """Annual aggregates from monthly schedule"""
    annual_debt_service: float
    principal_paydown: float
    beginning_balance: float
    ending_balance: float
    io_months_in_year: int
    is_io_year: bool


# ============================================================================
# CORE FINANCIAL FUNCTIONS
# ============================================================================

def calculate_monthly_payment(principal: float, annual_rate_pct: float, amort_years: int) -> float:
    """
    Calculate monthly P&I payment using standard amortization formula.

    Formula: P * [r(1+r)^n] / [(1+r)^n - 1]
    Where:
      P = principal
      r = monthly interest rate
      n = number of payments
    """
    if annual_rate_pct == 0:
        return principal / (amort_years * 12)

    monthly_rate = annual_rate_pct / 100 / 12
    num_payments = amort_years * 12

    factor = math.pow(1 + monthly_rate, num_payments)
    return principal * (monthly_rate * factor) / (factor - 1)


def calculate_remaining_balance(
    principal: float,
    annual_rate_pct: float,
    amort_years: int,
    years_elapsed: int
) -> float:
    """
    Calculate remaining loan balance after specified years.

    Formula: P * [(1+r)^N - (1+r)^k] / [(1+r)^N - 1]
    """
    if years_elapsed >= amort_years:
        return 0.0

    if annual_rate_pct == 0:
        return principal - (principal / amort_years) * years_elapsed

    monthly_rate = annual_rate_pct / 100 / 12
    num_payments_total = amort_years * 12
    payments_made = years_elapsed * 12

    factor_n = math.pow(1 + monthly_rate, num_payments_total)
    factor_k = math.pow(1 + monthly_rate, payments_made)

    return principal * (factor_n - factor_k) / (factor_n - 1)


def build_monthly_amort_schedule(
    principal: float,
    annual_rate_pct: float,
    amort_years: int,
    interest_only_months: int,
    total_months: Optional[int] = None,
    entire_loan_interest_only: bool = False
) -> List[MonthlyAmortEntry]:
    """
    Build monthly amortization schedule with IO period support.
    """
    monthly_rate = annual_rate_pct / 100 / 12
    total_amort_months = amort_years * 12

    io_payment = monthly_rate * principal if monthly_rate > 0 else 0

    if entire_loan_interest_only:
        schedule = []
        max_months = total_months if total_months else total_amort_months

        for m in range(1, max_months + 1):
            schedule.append(MonthlyAmortEntry(
                month=m,
                is_io=True,
                payment=io_payment,
                interest_paid=io_payment,
                principal_paid=0,
                beginning_balance=principal,
                ending_balance=principal
            ))

        return schedule

    remaining_amort_months = total_amort_months - interest_only_months

    amort_payment = 0.0
    if remaining_amort_months > 0:
        if annual_rate_pct == 0:
            amort_payment = principal / remaining_amort_months
        else:
            factor = math.pow(1 + monthly_rate, remaining_amort_months)
            amort_payment = principal * (monthly_rate * factor) / (factor - 1)

    schedule = []
    balance = principal
    max_months = total_months if total_months else total_amort_months

    for m in range(1, max_months + 1):
        is_io = m <= interest_only_months
        payment = io_payment if is_io else amort_payment
        interest_paid = balance * monthly_rate
        principal_paid = 0 if is_io else (payment - interest_paid)
        beginning_balance = balance
        ending_balance = max(0, balance - principal_paid)

        schedule.append(MonthlyAmortEntry(
            month=m,
            is_io=is_io,
            payment=payment,
            interest_paid=interest_paid,
            principal_paid=principal_paid,
            beginning_balance=beginning_balance,
            ending_balance=ending_balance
        ))

        balance = ending_balance

    return schedule


def get_annual_amort_data(schedule: List[MonthlyAmortEntry], year: int) -> AnnualAmortData:
    """Get annual aggregates from monthly amortization schedule."""
    start_month = (year - 1) * 12 + 1
    end_month = year * 12

    months_in_year = [m for m in schedule if start_month <= m.month <= end_month]

    if not months_in_year:
        return AnnualAmortData(
            annual_debt_service=0,
            principal_paydown=0,
            beginning_balance=0,
            ending_balance=0,
            io_months_in_year=0,
            is_io_year=False
        )

    annual_debt_service = sum(m.payment for m in months_in_year)
    principal_paydown = sum(m.principal_paid for m in months_in_year)
    beginning_balance = months_in_year[0].beginning_balance
    ending_balance = months_in_year[-1].ending_balance
    io_months_in_year = sum(1 for m in months_in_year if m.is_io)
    is_io_year = io_months_in_year > 0

    return AnnualAmortData(
        annual_debt_service=annual_debt_service,
        principal_paydown=principal_paydown,
        beginning_balance=beginning_balance,
        ending_balance=ending_balance,
        io_months_in_year=io_months_in_year,
        is_io_year=is_io_year
    )


def calculate_irr(cash_flows: List[float], guess: float = 0.1) -> float:
    """
    Calculate IRR using Newton-Raphson method.
    Returns IRR as a percentage (e.g., 15.0 for 15%)
    """
    max_iterations = 100
    precision = 0.00001
    rate = guess

    for _ in range(max_iterations):
        npv = 0.0
        d_npv = 0.0

        for t, cf in enumerate(cash_flows):
            discount = math.pow(1 + rate, t)
            npv += cf / discount
            d_npv -= (t * cf) / math.pow(1 + rate, t + 1)

        if abs(npv) < precision:
            return rate * 100

        if d_npv == 0:
            return 0.0

        new_rate = rate - npv / d_npv

        if not math.isfinite(new_rate):
            return 0.0

        if abs(new_rate - rate) < precision:
            return new_rate * 100

        rate = new_rate

    return rate * 100


def calculate_npv(cash_flows: List[float], discount_rate: float) -> float:
    """Calculate Net Present Value at given discount rate."""
    npv = 0.0
    for t, cf in enumerate(cash_flows):
        npv += cf / math.pow(1 + discount_rate, t)
    return npv


# ============================================================================
# DEALSNAP SMART DEFAULTS ENGINE
# ============================================================================

# Expense ratio matrix: (property_type, condition, responsibility) -> base_ratio%
EXPENSE_RATIO_MATRIX: Dict[tuple, float] = {
    # Single Family
    (PropertyType.SINGLE_FAMILY, PropertyCondition.NEWER, ExpenseResponsibility.MOSTLY_OWNER): 35.0,
    (PropertyType.SINGLE_FAMILY, PropertyCondition.NEWER, ExpenseResponsibility.MIXED): 30.0,
    (PropertyType.SINGLE_FAMILY, PropertyCondition.NEWER, ExpenseResponsibility.MOSTLY_TENANT): 22.0,
    (PropertyType.SINGLE_FAMILY, PropertyCondition.AVERAGE, ExpenseResponsibility.MOSTLY_OWNER): 42.0,
    (PropertyType.SINGLE_FAMILY, PropertyCondition.AVERAGE, ExpenseResponsibility.MIXED): 35.0,
    (PropertyType.SINGLE_FAMILY, PropertyCondition.AVERAGE, ExpenseResponsibility.MOSTLY_TENANT): 28.0,
    (PropertyType.SINGLE_FAMILY, PropertyCondition.OLDER, ExpenseResponsibility.MOSTLY_OWNER): 52.0,
    (PropertyType.SINGLE_FAMILY, PropertyCondition.OLDER, ExpenseResponsibility.MIXED): 42.0,
    (PropertyType.SINGLE_FAMILY, PropertyCondition.OLDER, ExpenseResponsibility.MOSTLY_TENANT): 35.0,

    # Multifamily (2-4 units)
    (PropertyType.MULTIFAMILY, PropertyCondition.NEWER, ExpenseResponsibility.MOSTLY_OWNER): 40.0,
    (PropertyType.MULTIFAMILY, PropertyCondition.NEWER, ExpenseResponsibility.MIXED): 33.0,
    (PropertyType.MULTIFAMILY, PropertyCondition.NEWER, ExpenseResponsibility.MOSTLY_TENANT): 25.0,
    (PropertyType.MULTIFAMILY, PropertyCondition.AVERAGE, ExpenseResponsibility.MOSTLY_OWNER): 48.0,
    (PropertyType.MULTIFAMILY, PropertyCondition.AVERAGE, ExpenseResponsibility.MIXED): 40.0,
    (PropertyType.MULTIFAMILY, PropertyCondition.AVERAGE, ExpenseResponsibility.MOSTLY_TENANT): 32.0,
    (PropertyType.MULTIFAMILY, PropertyCondition.OLDER, ExpenseResponsibility.MOSTLY_OWNER): 55.0,
    (PropertyType.MULTIFAMILY, PropertyCondition.OLDER, ExpenseResponsibility.MIXED): 48.0,
    (PropertyType.MULTIFAMILY, PropertyCondition.OLDER, ExpenseResponsibility.MOSTLY_TENANT): 38.0,

    # Apartment (5+ units)
    (PropertyType.APARTMENT, PropertyCondition.NEWER, ExpenseResponsibility.MOSTLY_OWNER): 38.0,
    (PropertyType.APARTMENT, PropertyCondition.NEWER, ExpenseResponsibility.MIXED): 32.0,
    (PropertyType.APARTMENT, PropertyCondition.NEWER, ExpenseResponsibility.MOSTLY_TENANT): 25.0,
    (PropertyType.APARTMENT, PropertyCondition.AVERAGE, ExpenseResponsibility.MOSTLY_OWNER): 45.0,
    (PropertyType.APARTMENT, PropertyCondition.AVERAGE, ExpenseResponsibility.MIXED): 38.0,
    (PropertyType.APARTMENT, PropertyCondition.AVERAGE, ExpenseResponsibility.MOSTLY_TENANT): 30.0,
    (PropertyType.APARTMENT, PropertyCondition.OLDER, ExpenseResponsibility.MOSTLY_OWNER): 52.0,
    (PropertyType.APARTMENT, PropertyCondition.OLDER, ExpenseResponsibility.MIXED): 45.0,
    (PropertyType.APARTMENT, PropertyCondition.OLDER, ExpenseResponsibility.MOSTLY_TENANT): 35.0,
}

# Insurance cost per unit by risk tier
INSURANCE_PER_UNIT: Dict[InsuranceRisk, float] = {
    InsuranceRisk.LOW: 600,
    InsuranceRisk.MODERATE: 900,
    InsuranceRisk.HIGH: 1400,
}

# CapEx reserve % of EGI by property type and condition
CAPEX_RESERVE_MATRIX: Dict[tuple, float] = {
    (PropertyType.SINGLE_FAMILY, PropertyCondition.NEWER): 3.0,
    (PropertyType.SINGLE_FAMILY, PropertyCondition.AVERAGE): 5.0,
    (PropertyType.SINGLE_FAMILY, PropertyCondition.OLDER): 8.0,
    (PropertyType.MULTIFAMILY, PropertyCondition.NEWER): 4.0,
    (PropertyType.MULTIFAMILY, PropertyCondition.AVERAGE): 6.0,
    (PropertyType.MULTIFAMILY, PropertyCondition.OLDER): 9.0,
    (PropertyType.APARTMENT, PropertyCondition.NEWER): 4.0,
    (PropertyType.APARTMENT, PropertyCondition.AVERAGE): 6.0,
    (PropertyType.APARTMENT, PropertyCondition.OLDER): 10.0,
}


def get_expense_ratio(
    property_type: PropertyType,
    condition: PropertyCondition,
    responsibility: ExpenseResponsibility
) -> float:
    """Look up base expense ratio from the matrix."""
    key = (property_type, condition, responsibility)
    return EXPENSE_RATIO_MATRIX.get(key, 45.0)


def get_capex_reserve_pct(
    property_type: PropertyType,
    condition: PropertyCondition
) -> float:
    """Look up CapEx reserve % from the matrix."""
    key = (property_type, condition)
    return CAPEX_RESERVE_MATRIX.get(key, 6.0)


def get_insurance_per_unit(risk: InsuranceRisk) -> float:
    """Look up insurance cost per unit."""
    return INSURANCE_PER_UNIT.get(risk, 900)


def compute_taxes(inputs: DealSnapInputs) -> float:
    """Compute annual taxes from user input or estimate."""
    if inputs.annual_taxes is not None:
        return inputs.annual_taxes
    if inputs.tax_rate_pct is not None:
        return inputs.purchase_price * (inputs.tax_rate_pct / 100)
    # Default: 1.2% of purchase price
    return inputs.purchase_price * 0.012


# ============================================================================
# DEALSNAP CALCULATION ENGINES
# ============================================================================

def calculate_dealsnap_income(inputs: DealSnapInputs) -> IncomeAnalysis:
    """Engine 1: Income analysis."""
    gsr = inputs.units * inputs.avg_monthly_rent * 12
    vacancy_loss = gsr * (inputs.vacancy_pct / 100)
    egi = gsr - vacancy_loss

    return IncomeAnalysis(
        grossScheduledRent=round(gsr, 2),
        vacancyLoss=round(vacancy_loss, 2),
        effectiveGrossIncome=round(egi, 2)
    )


def calculate_dealsnap_expenses(inputs: DealSnapInputs, egi: float) -> ExpenseAnalysis:
    """Engine 2: Operating expenses from smart defaults."""
    expense_ratio = get_expense_ratio(
        inputs.property_type,
        inputs.property_condition,
        inputs.expense_responsibility
    )

    operating_expenses = egi * (expense_ratio / 100)
    noi = egi - operating_expenses

    capex_pct = get_capex_reserve_pct(inputs.property_type, inputs.property_condition)
    capex_reserve = egi * (capex_pct / 100)

    return ExpenseAnalysis(
        expenseRatioPct=round(expense_ratio, 2),
        operatingExpenses=round(operating_expenses, 2),
        NOI=round(noi, 2),
        capexReserve=round(capex_reserve, 2),
        capexReservePct=round(capex_pct, 2)
    )


def calculate_value_reality_check(noi: float, purchase_price: float) -> ValueRealityCheck:
    """Engine 3: Value reality check across cap rate spectrum."""
    cap_rates = [5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    valuations = []

    for cap in cap_rates:
        if cap > 0:
            implied_value = noi / (cap / 100)
        else:
            implied_value = 0

        ratio = implied_value / purchase_price if purchase_price > 0 else 0
        if ratio >= 1.0:
            signal = "green"
        elif ratio >= 0.85:
            signal = "orange"
        else:
            signal = "red"

        valuations.append(ValuationRange(
            capRatePct=cap,
            impliedValue=round(implied_value, 2),
            signal=signal
        ))

    return ValueRealityCheck(
        purchasePrice=round(purchase_price, 2),
        valuations=valuations
    )


def calculate_rent_lift_sensitivity(
    inputs: DealSnapInputs,
    current_egi: float,
    expense_ratio: float,
    purchase_price: float
) -> Optional[RentLiftSensitivity]:
    """Engine 4: Rent lift sensitivity analysis."""
    lift_amount = None
    if inputs.rent_lift_amount is not None:
        lift_amount = inputs.rent_lift_amount
    elif inputs.rent_lift_pct is not None:
        lift_amount = inputs.avg_monthly_rent * (inputs.rent_lift_pct / 100)

    if lift_amount is None:
        return None

    lifted_rent = inputs.avg_monthly_rent + lift_amount
    lift_pct = (lift_amount / inputs.avg_monthly_rent * 100) if inputs.avg_monthly_rent > 0 else 0

    new_gsr = inputs.units * lifted_rent * 12
    new_vacancy_loss = new_gsr * (inputs.vacancy_pct / 100)
    new_egi = new_gsr - new_vacancy_loss
    new_opex = new_egi * (expense_ratio / 100)
    new_noi = new_egi - new_opex

    new_value_range = []
    for cap in [6.0, 7.0, 8.0, 9.0]:
        implied = new_noi / (cap / 100) if cap > 0 else 0
        ratio = implied / purchase_price if purchase_price > 0 else 0
        signal = "green" if ratio >= 1.0 else ("orange" if ratio >= 0.85 else "red")
        new_value_range.append(ValuationRange(
            capRatePct=cap,
            impliedValue=round(implied, 2),
            signal=signal
        ))

    return RentLiftSensitivity(
        currentRent=round(inputs.avg_monthly_rent, 2),
        liftedRent=round(lifted_rent, 2),
        liftAmount=round(lift_amount, 2),
        liftPct=round(lift_pct, 2),
        newGSR=round(new_gsr, 2),
        newNOI=round(new_noi, 2),
        newValueRange=new_value_range
    )


def calculate_reverse_engineering(
    inputs: DealSnapInputs,
    expense_ratio: float
) -> ReverseDealEngineering:
    """Engine 5: Reverse deal engineering - what rent is needed for target cap."""
    required_noi = inputs.purchase_price * (inputs.target_cap_rate_pct / 100)
    factor = 1.0 - (expense_ratio / 100)
    required_egi = required_noi / factor if factor > 0 else 0

    vac_factor = 1.0 - (inputs.vacancy_pct / 100)
    required_gsr = required_egi / vac_factor if vac_factor > 0 else 0

    required_avg_rent = required_gsr / (inputs.units * 12) if inputs.units > 0 else 0

    return ReverseDealEngineering(
        purchasePrice=round(inputs.purchase_price, 2),
        targetCapRatePct=round(inputs.target_cap_rate_pct, 2),
        expenseRatioPct=round(expense_ratio, 2),
        requiredNOI=round(required_noi, 2),
        requiredEGI=round(required_egi, 2),
        requiredAvgRent=round(required_avg_rent, 2)
    )


def calculate_finance_reality_check(
    inputs: DealSnapInputs,
    noi: float
) -> FinanceRealityCheck:
    """Engine 6: Finance reality check with DSCR bands."""
    loan_amount = inputs.purchase_price * (1 - inputs.down_payment_pct / 100)
    cash_required = inputs.purchase_price - loan_amount

    if loan_amount > 0 and inputs.interest_rate_pct > 0:
        monthly_payment = calculate_monthly_payment(
            loan_amount, inputs.interest_rate_pct, inputs.amort_years
        )
    elif loan_amount > 0:
        monthly_payment = loan_amount / (inputs.amort_years * 12)
    else:
        monthly_payment = 0

    annual_debt_service = monthly_payment * 12
    dscr = noi / annual_debt_service if annual_debt_service > 0 else 0

    if dscr >= 1.25:
        dscr_signal = "green"
        dscr_note = "Strong debt coverage. Most lenders comfortable."
    elif dscr >= 1.0:
        dscr_signal = "orange"
        dscr_note = "Thin coverage. Lender may require additional reserves or higher down payment."
    else:
        dscr_signal = "red"
        dscr_note = "Negative leverage. NOI does not cover debt service."

    return FinanceRealityCheck(
        cashRequired=round(cash_required, 2),
        loanAmount=round(loan_amount, 2),
        annualDebtService=round(annual_debt_service, 2),
        monthlyPayment=round(monthly_payment, 2),
        DSCR=round(dscr, 2),
        dscrSignal=dscr_signal,
        dscrNote=dscr_note
    )


def calculate_deal_triage(
    inputs: DealSnapInputs,
    noi: float,
    expense_ratio: float,
    dscr: float,
    purchase_price: float
) -> DealTriageResult:
    """Engine 7: Deal triage scoring - Pursue / Watch / Pass."""
    cap_rate = (noi / purchase_price * 100) if purchase_price > 0 else 0

    points = 0
    factors = {}
    notes = []

    # Cap rate scoring (0-3 points)
    if cap_rate >= 8.0:
        points += 3
        factors["capRate"] = {"value": round(cap_rate, 2), "score": 3, "label": "Strong"}
        notes.append(f"Cap rate {cap_rate:.1f}% is strong for the asset class.")
    elif cap_rate >= 6.0:
        points += 2
        factors["capRate"] = {"value": round(cap_rate, 2), "score": 2, "label": "Moderate"}
        notes.append(f"Cap rate {cap_rate:.1f}% is moderate. Check comps.")
    elif cap_rate >= 4.5:
        points += 1
        factors["capRate"] = {"value": round(cap_rate, 2), "score": 1, "label": "Thin"}
        notes.append(f"Cap rate {cap_rate:.1f}% is thin. Verify value-add potential.")
    else:
        factors["capRate"] = {"value": round(cap_rate, 2), "score": 0, "label": "Weak"}
        notes.append(f"Cap rate {cap_rate:.1f}% is below minimum threshold.")

    # DSCR scoring (0-3 points)
    if dscr >= 1.25:
        points += 3
        factors["dscr"] = {"value": round(dscr, 2), "score": 3, "label": "Strong"}
    elif dscr >= 1.10:
        points += 2
        factors["dscr"] = {"value": round(dscr, 2), "score": 2, "label": "Adequate"}
        notes.append("DSCR is adequate but tight. Budget conservatively.")
    elif dscr >= 1.0:
        points += 1
        factors["dscr"] = {"value": round(dscr, 2), "score": 1, "label": "Thin"}
        notes.append("DSCR near breakeven. Consider higher down payment.")
    else:
        factors["dscr"] = {"value": round(dscr, 2), "score": 0, "label": "Negative"}
        notes.append("Negative leverage. NOI does not cover debt service.")

    # Expense ratio scoring (0-2 points)
    if expense_ratio <= 40:
        points += 2
        factors["expenseRatio"] = {"value": round(expense_ratio, 2), "score": 2, "label": "Efficient"}
    elif expense_ratio <= 50:
        points += 1
        factors["expenseRatio"] = {"value": round(expense_ratio, 2), "score": 1, "label": "Average"}
    else:
        factors["expenseRatio"] = {"value": round(expense_ratio, 2), "score": 0, "label": "High"}
        notes.append(f"Expense ratio {expense_ratio:.0f}% is above average. Review cost structure.")

    # Per-unit price
    price_per_unit = purchase_price / inputs.units if inputs.units > 0 else 0
    factors["pricePerUnit"] = {"value": round(price_per_unit, 2)}

    # GRM (Gross Rent Multiplier) scoring (0-2 points)
    annual_rent = inputs.units * inputs.avg_monthly_rent * 12
    grm = purchase_price / annual_rent if annual_rent > 0 else 0
    if grm <= 8:
        points += 2
        factors["grm"] = {"value": round(grm, 2), "score": 2, "label": "Strong"}
    elif grm <= 12:
        points += 1
        factors["grm"] = {"value": round(grm, 2), "score": 1, "label": "Average"}
    else:
        factors["grm"] = {"value": round(grm, 2), "score": 0, "label": "High"}
        notes.append(f"GRM of {grm:.1f}x is high. Rents may not support price.")

    # Triage decision (max 12 points)
    if points >= 8:
        score = TriageScore.PURSUE
        notes.insert(0, "PURSUE: Deal metrics align well across key factors.")
    elif points >= 5:
        score = TriageScore.WATCH
        notes.insert(0, "WATCH: Some metrics are favorable but others need validation.")
    else:
        score = TriageScore.PASS_DEAL
        notes.insert(0, "PASS: Metrics suggest the deal does not meet investment criteria.")

    factors["totalPoints"] = {"value": points, "max": 12}

    return DealTriageResult(
        score=score,
        factors=factors,
        investorNotes=notes
    )


# ============================================================================
# DEALSNAP QUICK MODE - MAIN ENTRY POINT
# ============================================================================

def calculate_dealsnap(inputs: DealSnapInputs) -> DealSnapResults:
    """
    DealSnap Quick Mode calculation.
    Takes minimal inputs and produces comprehensive deal screening results.
    """
    # Engine 1: Income
    income = calculate_dealsnap_income(inputs)

    # Engine 2: Expenses
    expenses = calculate_dealsnap_expenses(inputs, income.effective_gross_income)

    # Engine 3: Value Reality Check
    value_check = calculate_value_reality_check(expenses.noi, inputs.purchase_price)

    # Engine 4: Rent Lift Sensitivity (optional)
    rent_sensitivity = calculate_rent_lift_sensitivity(
        inputs,
        income.effective_gross_income,
        expenses.expense_ratio_pct,
        inputs.purchase_price
    )

    # Engine 5: Reverse Deal Engineering
    reverse_engineering = calculate_reverse_engineering(inputs, expenses.expense_ratio_pct)

    # Engine 6: Finance Reality Check
    finance_check = calculate_finance_reality_check(inputs, expenses.noi)

    # Engine 7: Deal Triage
    triage = calculate_deal_triage(
        inputs,
        expenses.noi,
        expenses.expense_ratio_pct,
        finance_check.dscr,
        inputs.purchase_price
    )

    # Purchase cap rate
    purchase_cap_rate = (expenses.noi / inputs.purchase_price * 100) if inputs.purchase_price > 0 else 0

    # Consolidated investor notes
    investor_notes = list(triage.investor_notes)

    if finance_check.dscr_signal == "red":
        investor_notes.append(f"Finance: {finance_check.dscr_note}")
    elif finance_check.dscr_signal == "orange":
        investor_notes.append(f"Finance: {finance_check.dscr_note}")

    if rent_sensitivity:
        investor_notes.append(
            f"With ${rent_sensitivity.lift_amount:.0f}/unit rent lift, "
            f"NOI increases to ${rent_sensitivity.new_noi:,.0f}."
        )

    rent_gap = reverse_engineering.required_avg_rent - inputs.avg_monthly_rent
    if rent_gap > 0:
        investor_notes.append(
            f"To hit {inputs.target_cap_rate_pct:.0f}% cap, "
            f"avg rent needs to be ${reverse_engineering.required_avg_rent:,.0f}/mo "
            f"(+${rent_gap:,.0f} from current)."
        )
    else:
        investor_notes.append(
            f"Current rents already exceed the ${reverse_engineering.required_avg_rent:,.0f}/mo "
            f"needed for a {inputs.target_cap_rate_pct:.0f}% cap rate."
        )

    return DealSnapResults(
        income=income,
        expenses=expenses,
        valueCheck=value_check,
        rentSensitivity=rent_sensitivity,
        reverseEngineering=reverse_engineering,
        financeCheck=finance_check,
        triage=triage,
        investorNotes=investor_notes,
        purchaseCapRatePct=round(purchase_cap_rate, 2)
    )


# ============================================================================
# FULL UNDERWRITE - MAIN CALCULATION ENGINE (preserved from V1)
# ============================================================================

def calculate_deal(inputs: DealInputs) -> DealResults:
    """
    Main calculation function - computes all deal metrics.

    Flow:
    1. Calculate upfront costs and loan amount
    2. Build amortization schedule
    3. Build year-by-year pro forma
    4. Calculate exit metrics
    5. Calculate IRR and overall returns
    6. Generate verdict
    """

    # ========== 1. UPFRONT CALCULATIONS ==========

    loan_fees = inputs.purchase_price * (inputs.loan_fees_pct / 100)
    total_acquisition_cost = (
        inputs.purchase_price +
        inputs.renovation_budget +
        inputs.closing_costs +
        loan_fees
    )
    loan_amount = inputs.purchase_price * (1 - inputs.down_payment_pct / 100)
    equity_invested = total_acquisition_cost - loan_amount

    # ========== 2. BUILD AMORTIZATION SCHEDULE ==========

    entire_loan_io = inputs.entire_loan_interest_only
    io_months = 0 if entire_loan_io else inputs.interest_only_months
    remaining_amort_months = 0 if entire_loan_io else (inputs.amort_years * 12 - io_months)

    amort_schedule = build_monthly_amort_schedule(
        principal=loan_amount,
        annual_rate_pct=inputs.interest_rate_pct,
        amort_years=inputs.amort_years,
        interest_only_months=io_months,
        total_months=inputs.hold_years * 12 + 12,
        entire_loan_interest_only=entire_loan_io
    )

    monthly_rate = inputs.interest_rate_pct / 100 / 12
    io_monthly_payment = monthly_rate * loan_amount if monthly_rate > 0 else 0

    if entire_loan_io:
        amort_monthly_payment = io_monthly_payment
    elif remaining_amort_months > 0:
        amort_monthly_payment = calculate_monthly_payment(
            loan_amount,
            inputs.interest_rate_pct,
            remaining_amort_months / 12
        )
    else:
        amort_monthly_payment = io_monthly_payment

    year1_amort = get_annual_amort_data(amort_schedule, 1)
    annual_debt_service = year1_amort.annual_debt_service

    if entire_loan_io:
        monthly_payment = io_monthly_payment
    elif io_months >= 12:
        monthly_payment = io_monthly_payment
    else:
        monthly_payment = amort_monthly_payment

    # ========== 3. BUILD PRO FORMA ==========

    pro_forma: List[AnnualProForma] = []
    cash_flows_for_irr: List[float] = [-equity_invested]
    sum_dscr = 0.0

    current_avg_rent = inputs.avg_monthly_rent_per_unit

    if inputs.other_income_line_items:
        base_other_income = sum(item.monthly_amount for item in inputs.other_income_line_items)
    else:
        base_other_income = inputs.other_monthly_income
    current_other_income = base_other_income

    current_vacancy_pct = inputs.vacancy_pct

    current_expenses_by_category: Dict[str, float] = {cat.value: 0.0 for cat in ExpenseCategory}

    for item in inputs.expense_line_items:
        cat = item.category.value if item.category else "other"
        if cat != "management":
            if item.payer == ExpensePayer.LANDLORD:
                amount = item.annual_amount
            elif item.payer == ExpensePayer.SPLIT:
                amount = item.annual_amount * (item.split_landlord_percent / 100)
            else:
                amount = 0

            if cat in current_expenses_by_category:
                current_expenses_by_category[cat] += amount
            else:
                current_expenses_by_category["other"] += amount

    # ========== PRO FORMA LOOP ==========

    for year in range(1, inputs.hold_years + 1):

        if year > 1:
            current_avg_rent *= (1 + inputs.rent_growth_pct / 100)
            current_other_income *= (1 + inputs.rent_growth_pct / 100)

        current_vacancy_pct = inputs.vacancy_pct

        gpr = inputs.units * current_avg_rent * 12
        other_income = current_other_income * 12
        gross_income = gpr + other_income

        if inputs.apply_vacancy_to_other_income:
            vacancy_loss = gross_income * (current_vacancy_pct / 100)
        else:
            vacancy_loss = gpr * (current_vacancy_pct / 100)

        egi = gross_income - vacancy_loss

        if year > 1:
            for cat in current_expenses_by_category:
                current_expenses_by_category[cat] *= (1 + inputs.expense_growth_pct / 100)

        fixed_expenses = sum(current_expenses_by_category.values())

        management_fee = egi * (inputs.management_pct_of_egi / 100)
        capex_reserve = egi * (inputs.capex_reserve_pct_of_egi / 100)
        total_opex = fixed_expenses + management_fee + capex_reserve
        noi = egi - total_opex

        year_amort_data = get_annual_amort_data(amort_schedule, year)
        debt_service = year_amort_data.annual_debt_service
        principal_paydown = year_amort_data.principal_paydown
        beginning_loan_balance = year_amort_data.beginning_balance
        ending_loan_balance = year_amort_data.ending_balance
        is_io_year = year_amort_data.is_io_year
        io_months_in_year = year_amort_data.io_months_in_year

        operating_cash_flow = noi - debt_service
        cash_on_cash_pct = (operating_cash_flow / equity_invested * 100) if equity_invested > 0 else 0
        property_value = noi / (inputs.exit_cap_rate_pct / 100) if inputs.exit_cap_rate_pct > 0 else 0
        dscr = noi / debt_service if debt_service > 0 else 0

        pro_forma.append(AnnualProForma(
            year=year,
            GPR=round(gpr, 2),
            OtherIncome=round(other_income, 2),
            VacancyLoss=round(vacancy_loss, 2),
            EGI=round(egi, 2),
            OperatingExpenses=round(fixed_expenses, 2),
            ManagementFee=round(management_fee, 2),
            CapexReserve=round(capex_reserve, 2),
            TotalOpEx=round(total_opex, 2),
            NOI=round(noi, 2),
            DebtService=round(debt_service, 2),
            CashFlow=round(operating_cash_flow, 2),
            cashOnCashPct=round(cash_on_cash_pct, 2),
            principalPaydown=round(principal_paydown, 2),
            beginningLoanBalance=round(beginning_loan_balance, 2),
            endingLoanBalance=round(ending_loan_balance, 2),
            propertyValue=round(property_value, 2),
            DSCR=round(dscr, 2),
            isIOYear=is_io_year,
            ioMonthsInYear=io_months_in_year
        ))

        cash_flows_for_irr.append(operating_cash_flow)
        sum_dscr += dscr

    # ========== 4. EXIT CALCULATIONS ==========

    last_year_noi = pro_forma[-1].noi if pro_forma else 0
    next_year_noi = last_year_noi * (1 + inputs.rent_growth_pct / 100)

    sale_price = next_year_noi / (inputs.exit_cap_rate_pct / 100) if inputs.exit_cap_rate_pct > 0 else 0

    selling_costs = sale_price * (inputs.selling_costs_pct / 100)
    net_sale_before_debt = sale_price - selling_costs

    remaining_balance = calculate_remaining_balance(
        loan_amount,
        inputs.interest_rate_pct,
        inputs.amort_years,
        inputs.hold_years
    )

    net_sale_proceeds = net_sale_before_debt - remaining_balance

    if len(cash_flows_for_irr) > inputs.hold_years:
        cash_flows_for_irr[inputs.hold_years] += net_sale_proceeds
    else:
        cash_flows_for_irr.append(net_sale_proceeds)

    # ========== 5. OVERALL METRICS ==========

    year1 = pro_forma[0] if pro_forma else None
    noi_year1 = year1.noi if year1 else 0
    cash_flow_year1 = year1.cash_flow if year1 else 0
    cap_rate_year1 = (noi_year1 / inputs.purchase_price * 100) if inputs.purchase_price > 0 else 0
    cash_on_cash_year1 = (cash_flow_year1 / equity_invested * 100) if equity_invested > 0 else 0
    dscr_year1 = (noi_year1 / annual_debt_service) if annual_debt_service > 0 else 0

    irr = calculate_irr(cash_flows_for_irr)

    total_returned = sum(cash_flows_for_irr[1:])
    equity_multiple = total_returned / equity_invested if equity_invested > 0 else 0

    avg_dscr = sum_dscr / inputs.hold_years if inputs.hold_years > 0 else 0

    # ========== 6. WARNINGS ==========

    warnings: List[str] = []

    if dscr_year1 < 1.20:
        warnings.append("Risk: Year 1 DSCR below 1.20")

    negative_cf_years = [pf.year for pf in pro_forma if pf.cash_flow < 0]
    if negative_cf_years:
        years_str = ", ".join(str(y) for y in negative_cf_years)
        warnings.append(f"Negative operating cash flow in year(s) {years_str}")

    # ========== 7. VERDICT ==========

    targets = inputs.targets
    checks = {
        "irr": VerdictCheck(
            passed=irr >= targets.min_irr,
            value=round(irr, 2),
            target=targets.min_irr
        ),
        "cashOnCash": VerdictCheck(
            passed=cash_on_cash_year1 >= targets.min_cash_on_cash,
            value=round(cash_on_cash_year1, 2),
            target=targets.min_cash_on_cash
        ),
        "dscr": VerdictCheck(
            passed=dscr_year1 >= targets.min_dscr,
            value=round(dscr_year1, 2),
            target=targets.min_dscr
        ),
        "equity": VerdictCheck(
            passed=equity_invested <= targets.max_equity,
            value=round(equity_invested, 2),
            target=targets.max_equity
        )
    }

    passed_count = sum(1 for c in checks.values() if c.passed)

    if passed_count == 4:
        status = "pass"
    elif passed_count >= 3:
        status = "borderline"
    else:
        status = "fail"

    if status == "pass":
        summary = "This deal meets all your investment criteria."
    else:
        failed = []
        if not checks["irr"].passed:
            failed.append(f"IRR ({irr:.2f}% < {targets.min_irr}%)")
        if not checks["cashOnCash"].passed:
            failed.append(f"Year-1 CoC ({cash_on_cash_year1:.2f}% < {targets.min_cash_on_cash}%)")
        if not checks["dscr"].passed:
            failed.append(f"DSCR ({dscr_year1:.2f} < {targets.min_dscr})")
        if not checks["equity"].passed:
            failed.append(f"Equity Req (${equity_invested/1000:.0f}k > ${targets.max_equity/1000:.0f}k)")

        status_text = "is borderline" if status == "borderline" else "fails targets"
        summary = f"This deal {status_text} due to {' and '.join(failed)}."

    verdict = DealVerdict(
        status=status,
        summary=summary,
        checks={k: v.model_dump(by_alias=True) for k, v in checks.items()}
    )

    # ========== 8. OPERATING RATIOS ==========

    year1_data = pro_forma[0] if pro_forma else None
    expense_ratio = (year1_data.total_opex / year1_data.egi * 100) if year1_data and year1_data.egi > 0 else 0

    repairs_amount = sum(
        item.annual_amount for item in inputs.expense_line_items
        if "repair" in item.label.lower() or "maint" in item.label.lower()
    )
    repairs_pct = (repairs_amount / year1_data.egi * 100) if year1_data and year1_data.egi > 0 else 0

    operating_ratios = OperatingRatios(
        expenseRatio=round(expense_ratio, 2),
        managementPct=inputs.management_pct_of_egi,
        repairsPct=round(repairs_pct, 2),
        capexPct=inputs.capex_reserve_pct_of_egi
    )

    # ========== 9. AUDIT DATA ==========

    audit_data = AuditData(
        purchasePrice=inputs.purchase_price,
        downPaymentPct=inputs.down_payment_pct,
        computedLoanAmount=round(loan_amount, 2),
        monthlyPMT=round(monthly_payment, 2),
        annualDebtService=round(annual_debt_service, 2),
        exitCapRatePct=inputs.exit_cap_rate_pct,
        interestOnlyMonths=io_months,
        ioMonthlyPayment=round(io_monthly_payment, 2),
        amortMonthlyPayment=round(amort_monthly_payment, 2)
    )

    # ========== BUILD FINAL RESULTS ==========

    return DealResults(
        totalAcquisitionCost=round(total_acquisition_cost, 2),
        loanAmount=round(loan_amount, 2),
        equityInvested=round(equity_invested, 2),
        NOI_year1=round(noi_year1, 2),
        cashFlow_year1=round(cash_flow_year1, 2),
        capRate_year1=round(cap_rate_year1, 2),
        cashOnCash_year1=round(cash_on_cash_year1, 2),
        DSCR_year1=round(dscr_year1, 2),
        proForma=pro_forma,
        salePrice=round(sale_price, 2),
        netSaleProceeds=round(net_sale_proceeds, 2),
        IRR=round(irr, 2),
        equityMultiple=round(equity_multiple, 2),
        avgDSCR=round(avg_dscr, 2),
        warnings=warnings,
        verdict=verdict,
        operatingRatios=operating_ratios,
        auditData=audit_data
    )
