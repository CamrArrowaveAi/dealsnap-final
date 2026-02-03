

\### Two Parallel Modes (Not Tiered, Not Dumbed Down)



DealSnap (Quick Mode)



\- Fast screening  

&nbsp;     

&nbsp;   

\- Minimal inputs  

&nbsp;     

&nbsp;   

\- Directional, reality-checked outputs  

&nbsp;     

&nbsp;   

\- Designed for speed and triage  

&nbsp;     

&nbsp;   



Full Underwriting Mode



\- Deep modeling  

&nbsp;     

&nbsp;   

\- Line-item detail  

&nbsp;     

&nbsp;   



Decision-ready analysis  



\#### Core Design Rule



Outputs generate must remain FAIR when managing all data and information. 



\### Core purpose of DealSnap



DealSnap allows users to evaluate whether a property is worth deeper analysis in under 60 seconds by modeling income potential, operating reality, valuation ranges, and financing viability using conservative, market-tested assumptions.



This tool is not about precision.  

It answers:



\- Is this deal even in the universe of investable opportunities?  

&nbsp;     

&nbsp;   

\- What variable matters most if it is close?  

&nbsp;     

&nbsp;   

\- Is this likely dead on arrival?  

&nbsp;     

&nbsp;   

\## DealSnap Inputs \& Calculation Logic



\### A. Core Property Inputs (Required)



\- Number of Units  

&nbsp;     

&nbsp;   

\- Average Current Rent (per unit)  

&nbsp;     

&nbsp;   

\- Vacancy Assumption (default 8%, editable)  

&nbsp;     

&nbsp;   

\- Property Age / Condition:  

&nbsp;     

&nbsp;   



\- Newer / Well-Maintained  

&nbsp;     

&nbsp;   

\- Average  

&nbsp;     

&nbsp;   

\- Older / Heavy Maintenance  

&nbsp;     

&nbsp;   



\### Logic



\- Property age drives expense ratio ranges  

&nbsp;     

&nbsp;   

\- Vacancy is prefilled but user-editable  

&nbsp;     

&nbsp;   



---



\### B. Income Engine (Base Case Output)



Calculations



\- Gross Scheduled Rent (GSR)  

&nbsp;   Units × Average Rent × 12  

&nbsp;     

&nbsp;   

\- Vacancy Loss  

&nbsp;   GSR × Vacancy %  

&nbsp;     

&nbsp;   

\- Effective Gross Income (EGI)  

&nbsp;   GSR − Vacancy  

&nbsp;     

&nbsp;   



---



\### C. Operating Expense Engine (Smart Defaults)



\#### Expense Ratio Defaults



Defaults vary by property type and condition:



Single-Family



\- Newer: 45–50%  

&nbsp;     

&nbsp;   

\- Average: 50–55%  

&nbsp;     

&nbsp;   

\- Older: 55–60%  

&nbsp;     

&nbsp;   



Multifamily



\- Newer: 35–40%  

&nbsp;     

&nbsp;   

\- Average: 40–45%  

&nbsp;     

&nbsp;   

\- Older: 45–50%  

&nbsp;     

&nbsp;   



\#### Expense Responsibility Toggle



\- Mostly Owner-Paid  

&nbsp;     

&nbsp;   

\- Mixed  

&nbsp;     

&nbsp;   

\- Mostly Tenant-Paid  

&nbsp;     

&nbsp;   



This adjusts:



\- Expense ratio  

&nbsp;     

&nbsp;   

\- Risk flags  

&nbsp;     

&nbsp;   

\- Investor notes  

&nbsp;     

&nbsp;   



Calculation



\- Operating Expenses = EGI × Expense Ratio  

&nbsp;     

&nbsp;   

\- NOI (Pre-Debt) = EGI − Operating Expenses  

&nbsp;     

&nbsp;   



Explicit Label  

NOI excludes debt service.



\## Valuation \& Sensitivity Outputs



\### Output Set 1: Value Reality Check



Auto-generated valuation ranges:



\- Value at 8.5% cap  

&nbsp;     

&nbsp;   

\- Value at 8.0% cap (default)  

&nbsp;     

&nbsp;   

\- Value at 7.5% cap  

&nbsp;     

&nbsp;   

\- Value at 7.0% cap  

&nbsp;     

&nbsp;   



Formula  

NOI ÷ Cap Rate



Visual Guidance



\- Below value: Green  

&nbsp;     

&nbsp;   

\- Near value: Orange  

&nbsp;     

&nbsp;   

\- Above value: Red  

&nbsp;     

&nbsp;   



\### Output Set 2: Rent Lift Sensitivity



User can adjust rent by:



\- Dollar amount per unit, or  

&nbsp;     

&nbsp;   

\- Percentage  

&nbsp;     

&nbsp;   



Live recalculation of:



\- GSR  

&nbsp;     

&nbsp;   

\- NOI  

&nbsp;     

&nbsp;   

\- Value range  

&nbsp;     

&nbsp;   



Purpose:  

“This deal only works if rent moves by X.”



\### Output Set 3: Reverse Deal Engineering



Purpose  

What must be true for this deal to justify the price?



Inputs



\- Purchase Price  

&nbsp;     

&nbsp;   

\- Target Cap Rate (default 8%)  

&nbsp;     

&nbsp;   

\- Expense Ratio  

&nbsp;     

&nbsp;   



Outputs



\- Required NOI  

&nbsp;     

&nbsp;   

\- Required EGI  

&nbsp;     

&nbsp;   

\- Required Average Rent per Unit  

&nbsp;     

&nbsp;   



This is a core differentiation feature.



\## Finance Reality Check



\### Inputs (Editable Defaults)



\- Purchase Price  

&nbsp;     

&nbsp;   

\- Down Payment: 25%  

&nbsp;     

&nbsp;   

\- Interest Rate: 7.0%  

&nbsp;     

&nbsp;   

\- Amortization: 25 years  

&nbsp;     

&nbsp;   



\### Outputs



\- Cash Required  

&nbsp;     

&nbsp;   

\- Loan Amount  

&nbsp;     

&nbsp;   

\- Annual Debt Service  

&nbsp;     

&nbsp;   

\- DSCR  

&nbsp;     

&nbsp;   



\### DSCR Bands



\- Green: ≥ 1.25 (likely financeable)  

&nbsp;     

&nbsp;   

\- Orange: 1.10–1.24 (tight)  

&nbsp;     

&nbsp;   

\- Red: < 1.10 (challenging)  

&nbsp;     

&nbsp;   



Note  

DSCR below 1.2 may limit lender options.



\## Capital Expenditures, Taxes, and Insurance (Explicit Risk Treatment)



\### Capital Expenditures (Separate from OpEx)



CapEx is not included in NOI but must be surfaced as a risk.



Default CapEx Reserves



\- Single-Family: 8–12% of EGI  

&nbsp;     

&nbsp;   

\- Multifamily: 5–8% of EGI  

&nbsp;     

&nbsp;   



Displayed in Investor Notes and optional cash flow views.



\### Taxes



\- Allow entry as annual amount or % of value  

&nbsp;     

&nbsp;   

\- Default ranges:  

&nbsp;     

&nbsp;   



\- SFR: 1.2–2.5%  

&nbsp;     

&nbsp;   

\- MF: 0.9–1.8%  

&nbsp;     

&nbsp;   



Trigger tax risk notes when taxes materially impact NOI.



\### Insurance



Insurance risk selector:



\- Low  

&nbsp;     

&nbsp;   

\- Moderate  

&nbsp;     

&nbsp;   

\- High  

&nbsp;     

&nbsp;   



Adjusts expense ratio and investor notes to reflect volatility.



\## Game-Changer Capabilities



\### Deal Triage Score



Outputs:



\- Pursue  

&nbsp;     

&nbsp;   

\- Watch  

&nbsp;     

&nbsp;   

\- Pass  

&nbsp;     

&nbsp;   



Based on:



\- NOI margin  

&nbsp;     

&nbsp;   

\- Expense realism  

&nbsp;     

&nbsp;   

\- Rent lift dependency  

&nbsp;     

&nbsp;   

\- DSCR strength  

&nbsp;     

&nbsp;   

\- Price vs value band  

&nbsp;     

&nbsp;   







\# Core Requirements 



\- Must Use UV as the Python package

\- Must use PostgreSQL 18

\- Python FastAPI calculation engine (stateless, no database)

&nbsp; 

\### Operates in two parallel modes — not tiered, not simplified:



\*\*DealSnap (Quick Mode)\*\*:

\- Rapid deal screening in under 60 seconds

\- Minimal required inputs (property type, units, rent, purchase price, basic financing)

\- Smart defaults by property type and condition

\- Outputs: NOI, DSCR, Cap Rate, valuation range, financeability signal, deal triage score (Pursue / Watch / Pass)

\- Investor notes: auto-generated risk flags

\- One-click promotion to Full Underwrite without re-entry



\*\*Full Underwrite (Detailed Mode)\*\*:

\- Complete control over all assumptions

\- Line-item expense modeling with landlord/tenant/split payer logic

\- Multi-tranche financing (senior debt, seller notes, hard money, HELOC)

\- Year-by-year pro forma with growth assumptions

\- Sensitivity analysis (2D parametric tables)

\- Refinance modeling

\- Tax optimization (depreciation, cost segregation)

\- Professional PDF/Excel export



\*\*Core Design Rule\*\*: DealSnap outputs must be saveable, exportable, and convertible to Full Underwrite with one click. DealSnap is a gatekeeper, not a shortcut.

