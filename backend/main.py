from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import db

from routes.auth import router as auth_router
from routes.visitor import router as visitor_router
from routes.qr import router as qr_router
from routes.resident import router as resident_router
from routes.admin_provisioning import router as admin_provisioning_router
from routes.announcement import router as announcement_router
from routes.community_directory import router as community_router
from routes.profile import router as profile_router
from routes.alerts import router as alerts_router
from routes.security import router as security_router
from routes.delivery import router as delivery_router

app = FastAPI(
    title="Heimdall Security Management System API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(visitor_router)
app.include_router(qr_router)
app.include_router(resident_router)
app.include_router(alerts_router)
app.include_router(admin_provisioning_router)
app.include_router(security_router)
app.include_router(delivery_router)
app.include_router(announcement_router)
app.include_router(community_router)
app.include_router(profile_router)


@app.get("/", tags=["System Health"])
def root():
    resident_count = db.residents.count_documents({})
    return {
        "message": "Heimdall FastAPI Server Running",
        "resident_count": resident_count
    }