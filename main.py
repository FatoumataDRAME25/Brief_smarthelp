from fastapi import FastAPI
from app.routes.support_ticket import router

app = FastAPI(
    title="SmartHelp API",
    description="Micro-service de support client multimodal (Audio & Vision)"
)

app.include_router(router)