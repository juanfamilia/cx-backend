"""
Clips Proxy Router - Proxies clip requests to the Analysis microservice
This allows the frontend to use a single API URL
"""
from fastapi import APIRouter, Depends, Query, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import os

from shared.core.config import settings
from shared.utils.deps import check_company_payment_status, get_auth_user


router = APIRouter(
    prefix="/clips",
    tags=["Clips"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)

# Analysis service URL (internal Railway network)
ANALYSIS_URL = getattr(settings, 'ANALYSIS_SERVICE_URL', 'http://siete-analysis.railway.internal')


async def proxy_to_analysis(path: str, request: Request, method: str = "GET", body: dict = None):
    """Proxy request to analysis service"""
    url = f"{ANALYSIS_URL}/api/v1/clips{path}"
    
    # Forward authorization header
    headers = {}
    if "authorization" in request.headers:
        headers["Authorization"] = request.headers["authorization"]
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            if method == "GET":
                response = await client.get(url, headers=headers, params=dict(request.query_params))
            elif method == "POST":
                response = await client.post(url, headers=headers, json=body)
            else:
                response = await client.request(method, url, headers=headers, json=body)
            
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Analysis service unavailable"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error proxying to analysis service: {str(e)}"
        )


@router.get("/evaluation/{evaluation_id}")
async def get_evaluation_clips(
    request: Request,
    evaluation_id: int,
    delivered_only: bool = Query(default=True),
):
    """Get clips for an evaluation (proxied to analysis service)"""
    return await proxy_to_analysis(f"/evaluation/{evaluation_id}?delivered_only={delivered_only}", request)


@router.get("/evaluation/{evaluation_id}/status")
async def get_clips_status(
    request: Request,
    evaluation_id: int,
):
    """Get processing status of clips (proxied to analysis service)"""
    return await proxy_to_analysis(f"/evaluation/{evaluation_id}/status", request)


@router.get("/{clip_id}")
async def get_single_clip(
    request: Request,
    clip_id: int,
):
    """Get a single clip by ID (proxied to analysis service)"""
    return await proxy_to_analysis(f"/{clip_id}", request)
