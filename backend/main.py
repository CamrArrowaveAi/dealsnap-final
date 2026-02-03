"""
DealSnap - FastAPI Application
Real estate underwriting calculation API with Quick Mode
"""
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from pydantic import ValidationError

from backend.config import settings
from backend.models import (
    DealInputs, CalculateRequest, CalculateResponse, HealthResponse,
    DealSnapRequest, DealSnapResponse
)
from backend.calculator import calculate_deal, calculate_dealsnap
from backend.auth import (
    get_google_auth_url, exchange_google_code, get_google_user_info,
    create_access_token, get_current_user, require_auth,
    User, AuthToken, is_oauth_configured
)


# ============================================================================
# APP INITIALIZATION
# ============================================================================

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="DealSnap - Real estate underwriting and deal screening API",
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.get("/api/health", response_model=HealthResponse, tags=["Status"])
async def health_check():
    """Health check endpoint for monitoring"""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        message="DealSnap API is running"
    )


@app.get("/api/status", tags=["Status"])
async def api_status():
    """API status with configuration info"""
    return {
        "status": "running",
        "version": settings.app_version,
        "debug": settings.debug,
        "oauth_configured": is_oauth_configured()
    }


# ============================================================================
# DEALSNAP QUICK MODE ENDPOINT
# ============================================================================

@app.post("/api/dealsnap", response_model=DealSnapResponse, tags=["DealSnap"])
async def dealsnap_quick_analysis(request: DealSnapRequest):
    """
    DealSnap Quick Mode - rapid deal screening with minimal inputs.

    Returns:
    - Income analysis (GSR, vacancy, EGI)
    - Expense analysis with smart defaults
    - Value reality check (cap rate valuation ranges)
    - Rent lift sensitivity (optional)
    - Reverse deal engineering
    - Finance reality check (DSCR bands)
    - Deal triage score (Pursue/Watch/Pass)
    - Investor notes
    """
    try:
        results = calculate_dealsnap(request.inputs)
        return DealSnapResponse(
            success=True,
            results=results
        )
    except ValidationError as e:
        return DealSnapResponse(
            success=False,
            error="Validation error",
            details={str(err["loc"]): err["msg"] for err in e.errors()}
        )
    except Exception as e:
        return DealSnapResponse(
            success=False,
            error=str(e)
        )


# ============================================================================
# FULL UNDERWRITE CALCULATION ENDPOINTS
# ============================================================================

@app.post("/api/calculate", response_model=CalculateResponse, tags=["Calculation"])
async def calculate_underwriting(request: CalculateRequest):
    """
    Full underwrite calculation from detailed input parameters.

    Returns:
    - IRR (Internal Rate of Return)
    - DSCR (Debt Service Coverage Ratio)
    - Cash-on-Cash Return
    - Cap Rate
    - Year-by-year Pro Forma
    - Investment verdict (pass/fail/borderline)
    """
    try:
        results = calculate_deal(request.inputs)
        return CalculateResponse(
            success=True,
            results=results
        )
    except ValidationError as e:
        return CalculateResponse(
            success=False,
            error="Validation error",
            details={str(err["loc"]): err["msg"] for err in e.errors()}
        )
    except Exception as e:
        return CalculateResponse(
            success=False,
            error=str(e)
        )


@app.post("/api/calculate/simple", tags=["Calculation"])
async def calculate_simple(
    purchase_price: float,
    units: int,
    avg_monthly_rent: float,
    down_payment_pct: float = 25,
    interest_rate_pct: float = 6.5,
    hold_years: int = 5
):
    """
    Simplified calculation endpoint with minimal inputs.
    Uses default values for most parameters.
    """
    try:
        inputs = DealInputs(
            purchasePrice=purchase_price,
            units=units,
            avgMonthlyRentPerUnit=avg_monthly_rent,
            downPaymentPct=down_payment_pct,
            interestRatePct=interest_rate_pct,
            holdYears=hold_years,
            closingCosts=purchase_price * 0.02,
            expenseLineItems=[
                {"id": "1", "label": "Taxes", "annualAmount": purchase_price * 0.015, "category": "taxes"},
                {"id": "2", "label": "Insurance", "annualAmount": 3000, "category": "insurance"},
                {"id": "3", "label": "Repairs", "annualAmount": 2000, "category": "repairs"}
            ]
        )

        results = calculate_deal(inputs)
        return CalculateResponse(
            success=True,
            results=results
        )
    except Exception as e:
        return CalculateResponse(
            success=False,
            error=str(e)
        )


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.get("/auth/login", tags=["Authentication"])
async def auth_login():
    """Redirect to Google OAuth login"""
    if not is_oauth_configured():
        raise HTTPException(
            status_code=503,
            detail="OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET."
        )

    auth_url = get_google_auth_url()
    return RedirectResponse(url=auth_url)


@app.get("/auth/callback", tags=["Authentication"])
async def auth_callback(code: str = None, error: str = None):
    """OAuth callback handler"""
    if error:
        return RedirectResponse(url=f"/?error={error}")

    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    try:
        tokens = await exchange_google_code(code)
        user = await get_google_user_info(tokens["access_token"])
        access_token = create_access_token(user)

        return RedirectResponse(
            url=f"/?token={access_token}"
        )

    except Exception as e:
        return RedirectResponse(url=f"/?error={str(e)}")


@app.get("/auth/me", response_model=User, tags=["Authentication"])
async def get_me(user: User = Depends(require_auth)):
    """Get current authenticated user"""
    return user


@app.post("/auth/logout", tags=["Authentication"])
async def auth_logout():
    """Logout (client should discard token)"""
    return {"message": "Logged out successfully"}


# ============================================================================
# STATIC FILES & FRONTEND
# ============================================================================

frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path / "static")), name="static")


@app.get("/", response_class=HTMLResponse, tags=["Frontend"])
async def serve_frontend():
    """Serve the main HTML page"""
    index_path = frontend_path / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))

    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>DealSnap</title>
        <style>
            body { font-family: system-ui, sans-serif; padding: 2rem; max-width: 800px; margin: 0 auto; }
            h1 { color: #1a1a2e; }
            .status { padding: 1rem; background: #f0f0f0; border-radius: 8px; }
            code { background: #e0e0e0; padding: 0.2rem 0.4rem; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h1>DealSnap API</h1>
        <div class="status">
            <p><strong>Status:</strong> API is running</p>
            <p><strong>Version:</strong> """ + settings.app_version + """</p>
            <p><strong>Docs:</strong> <a href="/api/docs">/api/docs</a></p>
        </div>
        <p>Frontend files not found. Please build the frontend.</p>
    </body>
    </html>
    """)


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "Validation error",
            "details": {str(err["loc"]): err["msg"] for err in exc.errors()}
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "details": str(exc) if settings.debug else None
        }
    )


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
