"""
market.py — Market data endpoints (NAV, benchmarks).
"""

from fastapi import APIRouter, Depends

from app.auth.role_guard import get_current_user, CurrentUser
from app.core.base_response import success_response, APIResponse

router = APIRouter(prefix="/api/market", tags=["market"])

# Stub market data — Phase 2 will populate from DB
STUB_NAV = [
    {"symbol": "NIFTY50", "name": "Nifty 50", "nav": 24850.25, "change_pct": 0.42},
    {"symbol": "SENSEX", "name": "BSE Sensex", "nav": 81500.75, "change_pct": 0.38},
    {"symbol": "NIFTY_MID", "name": "Nifty Midcap 100", "nav": 57230.10, "change_pct": 0.61},
]


@router.get("/nav")
async def get_nav(
    current_user: CurrentUser = Depends(get_current_user),
) -> APIResponse:
    return success_response(data=STUB_NAV)


@router.get("/nav/{symbol}")
async def get_nav_by_symbol(
    symbol: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> APIResponse:
    item = next((n for n in STUB_NAV if n["symbol"] == symbol.upper()), None)
    if not item:
        return success_response(data=None, message=f"Symbol {symbol} not found")
    return success_response(data=item)
