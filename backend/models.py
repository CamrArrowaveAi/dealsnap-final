"""
DealSnap - Pydantic Data Models
Real estate underwriting data models for Quick Mode (DealSnap) and Full Underwrite
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Literal, Any
from enum import Enum


# ============================================================================
# ENUMS AND TYPE DEFINITIONS
# ============================================================================

class ExpenseCategory(str, Enum):
    TAXES = "taxes"
    INSURANCE = "insurance"
    UTILITIES = "utilities"
    REPAIRS = "repairs"
    ADMIN = "admin"
    MANAGEMENT = "management"
    LANDSCAPING = "landscaping"
    CLEANING = "cleaning"
    PEST = "pest"
    CONTRACTED = "contracted"
    OTHER = "other"


class ExpensePayer(str, Enum):
    LANDLORD = "landlord"
    TENANT = "tenant"
    SPLIT = "split"


class PropertyType(str, Enum):
    SINGLE_FAMILY = "single_family"
    MULTIFAMILY = "multifamily"
    APARTMENT = "apartment"


class PropertyCondition(str, Enum):
    NEWER = "newer"
    AVERAGE = "average"
    OLDER = "older"


class ExpenseResponsibility(str, Enum):
    MOSTLY_OWNER = "mostly_owner"
    MIXED = "mixed"
    MOSTLY_TENANT = "mostly_tenant"


class InsuranceRisk(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class TriageScore(str, Enum):
    PURSUE = "pursue"
    WATCH = "watch"
    PASS_DEAL = "pass"


# ============================================================================
# INPUT MODELS
# ============================================================================

class ExpenseItem(BaseModel):
    """Individual expense line item"""
    id: str
    label: str
    annual_amount: float = Field(..., alias="annualAmount", ge=0)
    category: ExpenseCategory = ExpenseCategory.OTHER
    payer: ExpensePayer = ExpensePayer.LANDLORD
    split_landlord_percent: float = Field(100.0, alias="splitLandlordPercent", ge=0, le=100)

    model_config = ConfigDict(populate_by_name=True)


class OtherIncomeLineItem(BaseModel):
    """Other income source (laundry, parking, etc.)"""
    id: str
    name: str
    monthly_amount: float = Field(..., alias="monthlyAmount", ge=0)

    model_config = ConfigDict(populate_by_name=True)


class DealTargets(BaseModel):
    """Investment target thresholds for pass/fail verdict"""
    min_irr: float = Field(12.0, alias="minIRR", description="Minimum required IRR (%)")
    min_cash_on_cash: float = Field(6.0, alias="minCashOnCash", description="Minimum Year 1 CoC (%)")
    min_dscr: float = Field(1.25, alias="minDSCR", description="Minimum DSCR")
    max_equity: float = Field(500000, alias="maxEquity", description="Maximum equity investment ($)")

    model_config = ConfigDict(populate_by_name=True)


class DealInputs(BaseModel):
    """
    Complete deal input parameters for underwriting calculation.
    V1 scope: Core metrics only (no stabilization, value-add, tax optimization)
    """
    # ========== Purchase & Financing ==========
    purchase_price: float = Field(..., alias="purchasePrice", gt=0)
    closing_costs: float = Field(0, alias="closingCosts", ge=0)
    renovation_budget: float = Field(0, alias="renovationBudget", ge=0)
    down_payment_pct: float = Field(25.0, alias="downPaymentPct", ge=0, le=100)
    interest_rate_pct: float = Field(6.5, alias="interestRatePct", ge=0, le=30)
    amort_years: int = Field(30, alias="amortYears", ge=1, le=40)
    loan_term_years: int = Field(30, alias="loanTermYears", ge=1, le=40)
    loan_fees_pct: float = Field(0, alias="loanFeesPct", ge=0, le=10)
    interest_only_months: int = Field(0, alias="interestOnlyMonths", ge=0, le=120)
    entire_loan_interest_only: bool = Field(False, alias="entireLoanInterestOnly")

    # ========== Property & Operations ==========
    units: int = Field(..., ge=1)
    avg_monthly_rent_per_unit: float = Field(..., alias="avgMonthlyRentPerUnit", gt=0)
    other_monthly_income: float = Field(0, alias="otherMonthlyIncome", ge=0)
    other_income_line_items: List[OtherIncomeLineItem] = Field(
        default_factory=list, alias="otherIncomeLineItems"
    )
    apply_vacancy_to_other_income: bool = Field(False, alias="applyVacancyToOtherIncome")
    vacancy_pct: float = Field(5.0, alias="vacancyPct", ge=0, le=100)
    rent_growth_pct: float = Field(3.0, alias="rentGrowthPct", ge=-10, le=20)
    expense_growth_pct: float = Field(3.0, alias="expenseGrowthPct", ge=-10, le=20)
    management_pct_of_egi: float = Field(8.0, alias="managementPctOfEGI", ge=0, le=30)
    capex_reserve_pct_of_egi: float = Field(5.0, alias="capexReservePctOfEGI", ge=0, le=20)

    # ========== Property Classification (DealSnap) ==========
    property_type: PropertyType = Field(PropertyType.MULTIFAMILY, alias="propertyType")
    property_condition: PropertyCondition = Field(PropertyCondition.AVERAGE, alias="propertyCondition")
    expense_responsibility: ExpenseResponsibility = Field(
        ExpenseResponsibility.MOSTLY_OWNER, alias="expenseResponsibility"
    )
    insurance_risk: InsuranceRisk = Field(InsuranceRisk.MODERATE, alias="insuranceRisk")

    # ========== Expenses ==========
    expense_line_items: List[ExpenseItem] = Field(
        default_factory=list, alias="expenseLineItems"
    )

    # ========== Exit Strategy ==========
    hold_years: int = Field(5, alias="holdYears", ge=1, le=30)
    exit_cap_rate_pct: float = Field(6.0, alias="exitCapRatePct", gt=0, le=20)
    selling_costs_pct: float = Field(6.0, alias="sellingCostsPct", ge=0, le=15)

    # ========== Investment Targets ==========
    targets: DealTargets = Field(default_factory=DealTargets)

    model_config = ConfigDict(populate_by_name=True)


# ============================================================================
# DEALSNAP INPUT MODELS (Quick Mode)
# ============================================================================

class DealSnapInputs(BaseModel):
    """
    DealSnap Quick Mode inputs - minimal required fields for rapid deal screening.
    All other parameters use smart defaults derived from property type and condition.
    """
    # Required
    units: int = Field(..., ge=1, description="Number of units")
    avg_monthly_rent: float = Field(..., alias="avgMonthlyRent", gt=0, description="Average current rent per unit")
    purchase_price: float = Field(..., alias="purchasePrice", gt=0, description="Asking or offer price")

    # Smart defaults
    property_type: PropertyType = Field(PropertyType.MULTIFAMILY, alias="propertyType")
    property_condition: PropertyCondition = Field(PropertyCondition.AVERAGE, alias="propertyCondition")
    vacancy_pct: float = Field(8.0, alias="vacancyPct", ge=0, le=100, description="Vacancy assumption (default 8%)")

    # Expense controls
    expense_responsibility: ExpenseResponsibility = Field(
        ExpenseResponsibility.MOSTLY_OWNER, alias="expenseResponsibility"
    )
    insurance_risk: InsuranceRisk = Field(InsuranceRisk.MODERATE, alias="insuranceRisk")

    # Financing (editable defaults)
    down_payment_pct: float = Field(25.0, alias="downPaymentPct", ge=0, le=100)
    interest_rate_pct: float = Field(7.0, alias="interestRatePct", ge=0, le=30)
    amort_years: int = Field(25, alias="amortYears", ge=1, le=40)

    # Tax input (optional)
    annual_taxes: Optional[float] = Field(None, alias="annualTaxes", ge=0, description="Annual property taxes ($)")
    tax_rate_pct: Optional[float] = Field(None, alias="taxRatePct", ge=0, le=10, description="Tax rate as % of value")

    # Rent lift sensitivity (optional)
    rent_lift_amount: Optional[float] = Field(None, alias="rentLiftAmount", description="Rent increase $ per unit")
    rent_lift_pct: Optional[float] = Field(None, alias="rentLiftPct", description="Rent increase %")

    # Reverse engineering target cap (optional)
    target_cap_rate_pct: float = Field(8.0, alias="targetCapRatePct", gt=0, le=20)

    model_config = ConfigDict(populate_by_name=True)


# ============================================================================
# DEALSNAP OUTPUT MODELS
# ============================================================================

class IncomeAnalysis(BaseModel):
    """Income engine output"""
    gross_scheduled_rent: float = Field(..., alias="grossScheduledRent")
    vacancy_loss: float = Field(..., alias="vacancyLoss")
    effective_gross_income: float = Field(..., alias="effectiveGrossIncome")

    model_config = ConfigDict(populate_by_name=True)


class ExpenseAnalysis(BaseModel):
    """Operating expense engine output"""
    expense_ratio_pct: float = Field(..., alias="expenseRatioPct")
    operating_expenses: float = Field(..., alias="operatingExpenses")
    noi: float = Field(..., alias="NOI")
    capex_reserve: float = Field(..., alias="capexReserve")
    capex_reserve_pct: float = Field(..., alias="capexReservePct")

    model_config = ConfigDict(populate_by_name=True)


class ValuationRange(BaseModel):
    """Single cap rate valuation point"""
    cap_rate_pct: float = Field(..., alias="capRatePct")
    implied_value: float = Field(..., alias="impliedValue")
    signal: Literal["green", "orange", "red"] = Field(...)

    model_config = ConfigDict(populate_by_name=True)


class ValueRealityCheck(BaseModel):
    """Valuation range output across cap rates"""
    purchase_price: float = Field(..., alias="purchasePrice")
    valuations: List[ValuationRange] = Field(...)

    model_config = ConfigDict(populate_by_name=True)


class RentLiftSensitivity(BaseModel):
    """Rent lift sensitivity output"""
    current_rent: float = Field(..., alias="currentRent")
    lifted_rent: float = Field(..., alias="liftedRent")
    lift_amount: float = Field(..., alias="liftAmount")
    lift_pct: float = Field(..., alias="liftPct")
    new_gsr: float = Field(..., alias="newGSR")
    new_noi: float = Field(..., alias="newNOI")
    new_value_range: List[ValuationRange] = Field(..., alias="newValueRange")

    model_config = ConfigDict(populate_by_name=True)


class ReverseDealEngineering(BaseModel):
    """Reverse engineering output - what must be true"""
    purchase_price: float = Field(..., alias="purchasePrice")
    target_cap_rate_pct: float = Field(..., alias="targetCapRatePct")
    expense_ratio_pct: float = Field(..., alias="expenseRatioPct")
    required_noi: float = Field(..., alias="requiredNOI")
    required_egi: float = Field(..., alias="requiredEGI")
    required_avg_rent: float = Field(..., alias="requiredAvgRent")

    model_config = ConfigDict(populate_by_name=True)


class FinanceRealityCheck(BaseModel):
    """Financing viability output"""
    cash_required: float = Field(..., alias="cashRequired")
    loan_amount: float = Field(..., alias="loanAmount")
    annual_debt_service: float = Field(..., alias="annualDebtService")
    monthly_payment: float = Field(..., alias="monthlyPayment")
    dscr: float = Field(..., alias="DSCR")
    dscr_signal: Literal["green", "orange", "red"] = Field(..., alias="dscrSignal")
    dscr_note: str = Field(..., alias="dscrNote")

    model_config = ConfigDict(populate_by_name=True)


class DealTriageResult(BaseModel):
    """Deal triage score output"""
    score: TriageScore
    factors: Dict[str, Any]
    investor_notes: List[str] = Field(..., alias="investorNotes")

    model_config = ConfigDict(populate_by_name=True)


class DealSnapResults(BaseModel):
    """Complete DealSnap Quick Mode results"""
    # Income
    income: IncomeAnalysis

    # Expenses
    expenses: ExpenseAnalysis

    # Valuation
    value_check: ValueRealityCheck = Field(..., alias="valueCheck")

    # Rent sensitivity (if requested)
    rent_sensitivity: Optional[RentLiftSensitivity] = Field(None, alias="rentSensitivity")

    # Reverse engineering
    reverse_engineering: ReverseDealEngineering = Field(..., alias="reverseEngineering")

    # Finance
    finance_check: FinanceRealityCheck = Field(..., alias="financeCheck")

    # Triage
    triage: DealTriageResult

    # Investor notes
    investor_notes: List[str] = Field(..., alias="investorNotes")

    # Cap rate at purchase
    purchase_cap_rate_pct: float = Field(..., alias="purchaseCapRatePct")

    model_config = ConfigDict(populate_by_name=True)


# ============================================================================
# OUTPUT MODELS (Full Underwrite)
# ============================================================================

class AnnualProForma(BaseModel):
    """Year-by-year pro forma projection"""
    year: int
    gpr: float = Field(..., alias="GPR", description="Gross Potential Rent")
    other_income: float = Field(..., alias="OtherIncome")
    vacancy_loss: float = Field(..., alias="VacancyLoss")
    egi: float = Field(..., alias="EGI", description="Effective Gross Income")
    operating_expenses: float = Field(..., alias="OperatingExpenses")
    management_fee: float = Field(..., alias="ManagementFee")
    capex_reserve: float = Field(..., alias="CapexReserve")
    total_opex: float = Field(..., alias="TotalOpEx")
    noi: float = Field(..., alias="NOI", description="Net Operating Income")
    debt_service: float = Field(..., alias="DebtService")
    cash_flow: float = Field(..., alias="CashFlow", description="Operating Cash Flow")
    cash_on_cash_pct: float = Field(..., alias="cashOnCashPct")
    principal_paydown: float = Field(..., alias="principalPaydown")
    beginning_loan_balance: float = Field(..., alias="beginningLoanBalance")
    ending_loan_balance: float = Field(..., alias="endingLoanBalance")
    property_value: float = Field(..., alias="propertyValue")
    dscr: float = Field(..., alias="DSCR")
    is_io_year: bool = Field(..., alias="isIOYear")
    io_months_in_year: int = Field(..., alias="ioMonthsInYear")

    model_config = ConfigDict(populate_by_name=True)


class VerdictCheck(BaseModel):
    """Individual metric check result"""
    passed: bool = Field(..., alias="pass")
    value: float
    target: float

    model_config = ConfigDict(populate_by_name=True)


class DealVerdict(BaseModel):
    """Investment decision verdict"""
    status: Literal["pass", "fail", "borderline"]
    summary: str
    checks: Dict[str, Any]  # Serialized VerdictCheck objects


class OperatingRatios(BaseModel):
    """Operating performance ratios"""
    expense_ratio: float = Field(..., alias="expenseRatio")
    management_pct: float = Field(..., alias="managementPct")
    repairs_pct: float = Field(..., alias="repairsPct")
    capex_pct: float = Field(..., alias="capexPct")

    model_config = ConfigDict(populate_by_name=True)


class AuditData(BaseModel):
    """Debug/audit data for calculation verification"""
    purchase_price: float = Field(..., alias="purchasePrice")
    down_payment_pct: float = Field(..., alias="downPaymentPct")
    computed_loan_amount: float = Field(..., alias="computedLoanAmount")
    monthly_pmt: float = Field(..., alias="monthlyPMT")
    annual_debt_service: float = Field(..., alias="annualDebtService")
    exit_cap_rate_pct: float = Field(..., alias="exitCapRatePct")
    interest_only_months: int = Field(..., alias="interestOnlyMonths")
    io_monthly_payment: float = Field(..., alias="ioMonthlyPayment")
    amort_monthly_payment: float = Field(..., alias="amortMonthlyPayment")

    model_config = ConfigDict(populate_by_name=True)


class DealResults(BaseModel):
    """Complete calculation results"""
    # ========== Upfront ==========
    total_acquisition_cost: float = Field(..., alias="totalAcquisitionCost")
    loan_amount: float = Field(..., alias="loanAmount")
    equity_invested: float = Field(..., alias="equityInvested")

    # ========== Year 1 Metrics ==========
    noi_year1: float = Field(..., alias="NOI_year1")
    cash_flow_year1: float = Field(..., alias="cashFlow_year1")
    cap_rate_year1: float = Field(..., alias="capRate_year1")
    cash_on_cash_year1: float = Field(..., alias="cashOnCash_year1")
    dscr_year1: float = Field(..., alias="DSCR_year1")

    # ========== Pro Forma ==========
    pro_forma: List[AnnualProForma] = Field(..., alias="proForma")

    # ========== Exit & Overall ==========
    sale_price: float = Field(..., alias="salePrice")
    net_sale_proceeds: float = Field(..., alias="netSaleProceeds")
    irr: float = Field(..., alias="IRR")
    equity_multiple: float = Field(..., alias="equityMultiple")
    avg_dscr: float = Field(..., alias="avgDSCR")

    # ========== Warnings ==========
    warnings: List[str] = Field(default_factory=list)

    # ========== Verdict ==========
    verdict: DealVerdict

    # ========== Ratios ==========
    operating_ratios: OperatingRatios = Field(..., alias="operatingRatios")

    # ========== Audit ==========
    audit_data: AuditData = Field(..., alias="auditData")

    model_config = ConfigDict(populate_by_name=True)


# ============================================================================
# API REQUEST/RESPONSE MODELS
# ============================================================================

class CalculateRequest(BaseModel):
    """API request for deal calculation"""
    inputs: DealInputs


class CalculateResponse(BaseModel):
    """API response for deal calculation"""
    success: bool
    results: Optional[DealResults] = None
    error: Optional[str] = None
    details: Optional[Dict[str, str]] = None


class DealSnapRequest(BaseModel):
    """API request for DealSnap quick analysis"""
    inputs: DealSnapInputs


class DealSnapResponse(BaseModel):
    """API response for DealSnap quick analysis"""
    success: bool
    results: Optional[DealSnapResults] = None
    error: Optional[str] = None
    details: Optional[Dict[str, str]] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    message: str
