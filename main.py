from fastapi import FastAPI
from app.routes.support_ticket import router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="SmartHelp API",
    description="Micro-service de support client multimodal (Audio & Vision)"
)

app.include_router(router)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)