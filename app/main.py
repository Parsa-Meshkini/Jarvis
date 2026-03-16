from fastapi import FastAPI
from app.api.routes import router
from app.core.config import settings

app = FastAPI(title=settings.APP_NAME)

app.include_router(router)


@app.get("/")
async def root():
    return {"message": f"{settings.APP_NAME} is running"}


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME}