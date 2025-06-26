from fastapi import APIRouter, Depends, Header, Response
import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.utils.deps import get_auth_user


router = APIRouter(
    prefix="/cloudflare",
    tags=["Cloudflare"],
    dependencies=[Depends(get_auth_user)],
)


class UploadTokenResponse(BaseModel):
    upload_url: str
    uid: str


@router.post("/stream", response_model=UploadTokenResponse)
async def upload_cloudflare_stream(
    upload_length: str = Header(..., alias="Upload-Length"),
    upload_metadata: str = Header(..., alias="Upload-Metadata"),
):
    url = f"https://api.cloudflare.com/client/v4/accounts/{settings.CLOUDFLARE_ACCOUNT_ID}/stream?direct_user=true"

    headers = {
        "Authorization": f"Bearer {settings.CLOUDFLARE_STREAM_KEY}",
        "Tus-Resumable": "1.0.0",
        "Upload-Length": upload_length,
        "Upload-Metadata": upload_metadata,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers)
        response.raise_for_status()
        location = response.headers.get("Location")

        return Response(
            status_code=201,
            headers={
                "Access-Control-Expose-Headers": "Location",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Origin": "*",
                "Location": location,
            },
        )
