from contextlib import asynccontextmanager
from datetime import datetime
import os

from fastapi import Depends, FastAPI, HTTPException, Request

from fastapi.responses import FileResponse,RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base, engine, get_db
from app.model import URL
from app.redis import redis_client
from app.utils import encode


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield


app = FastAPI(lifespan=lifespan)
app.mount(
    "/frontend",
    StaticFiles(directory="frontend"),
    name="frontend"
)

RESERVED_CODES = {
    "shorten",
    "stats",
    "docs",
    "redoc",
    "openapi.json"
}
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")#BASE_URL=https://yourdomain.com


class URLRequest(BaseModel):
    long_url: HttpUrl
    expires_at: datetime | None = None
    custom_code: str | None = Field(
        default=None,
        min_length=3,
        max_length=20,
        pattern=r"^[a-zA-Z0-9_-]+$"
    )
class URLResponse(BaseModel):
    long_url: str
    short_code: str
    short_url: str

@app.get("/health")#To check the api is working properly or not.
async def health_check():
    return {"status": "ok"}

@app.get("/")#directly opens the ui.
async def home():
    return FileResponse("frontend/index.html")


@app.post("/shorten",response_model=URLResponse)
async def shorten_url(
    request: URLRequest,
    client_request: Request,
    db: AsyncSession = Depends(get_db)
):
    # Rate limiting - 5 requests per minute
    client_ip = client_request.client.host
    rate_limit_key = f"rate_limit:{client_ip}"

    request_count = await redis_client.incr(rate_limit_key)

    if request_count == 1:
        await redis_client.expire(rate_limit_key, 60)

    if request_count > 5:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Try again later."
        )

    # Get the next ID from PostgreSQL
    result = await db.execute(
        text("SELECT nextval('urls_id_seq')")
    )

    new_id = result.scalar_one()

    # Handle custom code
    if request.custom_code:

        # Check reserved codes
        if request.custom_code.lower() in RESERVED_CODES:
            raise HTTPException(
                status_code=400,
                detail="This custom code is reserved"
            )

        # Check if custom code already exists
        result = await db.execute(
            select(URL).where(
                URL.short_code == request.custom_code
            )
        )

        existing_url = result.scalar_one_or_none()

        if existing_url is not None:
            raise HTTPException(
                status_code=409,
                detail="Custom code already exists"
            )

        short_code = request.custom_code

    else:
        # Generate automatic Base62 code
        short_code = encode(new_id)

    # Create URL record
    url = URL(
        id=new_id,
        long_url=str(request.long_url),
        short_code=short_code,
        expires_at=request.expires_at
    )

    # Add to database
    db.add(url)

    # Save to PostgreSQL
    await db.commit()

    return {
        "long_url": str(request.long_url),
        "short_code": short_code,
        "short_url" : f"{request.base_url}{short_code}"
    }

@app.get("/stats/{short_code}")
async def get_stats(
    short_code: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(URL).where(URL.short_code == short_code)
    )

    url = result.scalar_one_or_none()

    if url is None:
        raise HTTPException(
            status_code=404,
            detail="Short URL not found"
        )

    return {
        "short_code": url.short_code,
        "long_url": url.long_url,
        "click_count": url.click_count,
        "created_at": url.created_at,
        "expires_at": url.expires_at
    }

@app.get("/{short_code}")
async def redirect_url(
    short_code: str,
    db: AsyncSession = Depends(get_db)
):
    # 1. Check Redis
    cached_url = await redis_client.get(short_code)

    if cached_url is not None:

        # URL found in Redis
        result = await db.execute(
            select(URL).where(URL.short_code == short_code)
        )

        url = result.scalar_one_or_none()

        if url is None:
            raise HTTPException(
                status_code=404,
                detail="Short URL not found"
            )

        # Check expiration
        if (
            url.expires_at is not None
            and url.expires_at <= datetime.now(url.expires_at.tzinfo)
        ):
            raise HTTPException(
                status_code=410,
                detail="Short URL has expired"
            )

        # Increase click count
        url.click_count += 1

        await db.commit()

        return RedirectResponse(cached_url)

    # 2. Redis miss → check PostgreSQL
    result = await db.execute(
        select(URL).where(URL.short_code == short_code)
    )

    url = result.scalar_one_or_none()

    if url is None:
        raise HTTPException(
            status_code=404,
            detail="Short URL not found"
        )

    # 3. Check expiration
    if (
        url.expires_at is not None
        and url.expires_at <= datetime.now(url.expires_at.tzinfo)
    ):
        raise HTTPException(
            status_code=410,
            detail="Short URL has expired"
        )

    # 4. Increase click count
    url.click_count += 1

    await db.commit()

    # 5. Put URL into Redis
    await redis_client.set(
        short_code,
        url.long_url
    )

    # 6. Redirect
    return RedirectResponse(url.long_url)