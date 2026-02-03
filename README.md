# DealSnap - Real Estate Underwriting Tool

A stateless real estate underwriting calculation API with a clean HTML/CSS frontend and DealSnap Quick Mode.

## Overview

DealSnap is an ultra-minimal validation implementation that provides:

- **Core Financial Metrics**: IRR, DSCR, Cash-on-Cash, Cap Rate, NOI
- **Year-by-Year Pro Forma**: Full cash flow projections
- **Investment Verdict**: Pass/Fail/Borderline based on user-defined targets
- **Stateless API Design**: No database required (V1 scope)
- **OAuth/SSO Ready**: Google OAuth2 integration (optional)

## Project Structure

```
Active-App-Development/
├── backend/
│   ├── main.py           # FastAPI application entry point
│   ├── calculator.py     # Core calculation engine
│   ├── models.py         # Pydantic data models
│   ├── auth.py           # OAuth/JWT authentication
│   ├── config.py         # Environment configuration
│   └── requirements.txt  # Python dependencies
├── frontend/
│   ├── index.html        # Main HTML page
│   └── static/
│       ├── css/styles.css
│       └── js/app.js
├── tests/
│   ├── test_calculator.py
│   └── test_api.py
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## API Endpoints

### Calculation

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/calculate` | POST | Full deal calculation with all parameters |
| `/api/calculate/simple` | POST | Simplified calculation with defaults |
| `/api/dealsnap` | POST | DealSnap Quick Mode calculation |

### Status

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/status` | GET | API status and configuration |

### Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login` | GET | Redirect to Google OAuth |
| `/auth/callback` | GET | OAuth callback handler |
| `/auth/me` | GET | Get current user (requires auth) |
| `/auth/logout` | POST | Logout |

## Core Calculations

### IRR (Internal Rate of Return)
Uses Newton-Raphson method to solve:
```
NPV = Σ(CF_t / (1 + IRR)^t) = 0
```

### DSCR (Debt Service Coverage Ratio)
```
DSCR = NOI / Annual Debt Service
```
Only landlord-paid expenses affect NOI.

### Cash-on-Cash Return
```
CoC = Annual Operating Cash Flow / Total Equity Invested
```

### Cap Rate
```
Purchase Cap Rate = Year 1 NOI / Purchase Price
```

### NOI (Net Operating Income)
```
GPR = Units × Avg Monthly Rent × 12
EGI = GPR × (1 - Vacancy%) + Other Income
Operating Expenses = Sum of Landlord-Paid Expenses
NOI = EGI - Operating Expenses
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Application
APP_NAME=DealSnap
DEBUG=false

# OAuth (optional)
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-secret
OAUTH_REDIRECT_URI=http://localhost:8000/auth/callback

# Security
SECRET_KEY=your-secret-key  # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Testing

Run tests:
```bash
cd tests
pytest -v
```
## PRD Production

"C:\Users\camer\GitHub\Active-App-Development\.claude\PRD.md"

## Technology Stack

- **Backend**: Python 3.11+, FastAPI, Pydantic
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Authentication**: OAuth2 (Google), JWT
- **Deployment**: Docker, Docker Compose

## License

Proprietary - All rights reserved.

## Version History

- **V2.0.0** (2026-01-30): DealSnap rebrand
  - Rebranded from Property King to DealSnap
  - Added DealSnap Quick Mode (`/api/dealsnap`)
  - Updated all configuration and deployment files
- **V1.0.0** (2026-01-27): Initial MVP release
  - Core calculation engine
  - Stateless API
  - HTML/CSS frontend
  - Docker deployment
