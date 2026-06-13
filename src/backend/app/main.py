from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router
from app.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "Backend scaffold for Longevity-assistant with profile, guidance, "
        "source-scope and future genetics/evidence orchestration."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
