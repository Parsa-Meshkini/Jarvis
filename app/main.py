import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from app.api.routes import router
from app.api.voice  import router as voice_router
from app.api.auth   import router as auth_router
from app.core.config import settings
from app.database import engine, Base
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan, redirect_slashes=False)

# Trust proxy headers from ngrok so HTTPS requests are handled correctly
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(voice_router)
app.include_router(auth_router)


@app.get("/voice/audio/{filename}")
async def serve_audio(filename: str):
    filepath = f"/tmp/{filename}"
    if not os.path.exists(filepath):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Audio not found")
    return FileResponse(filepath, media_type="audio/mpeg")


@app.get("/")
async def root():
    return {"message": f"{settings.APP_NAME} is running"}


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME}