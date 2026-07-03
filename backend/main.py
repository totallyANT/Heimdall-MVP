from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import db

# Existing routes
from routes.auth import router as auth_router
from routes.visitor import router as visitor_router
from routes.qr import router as qr_router
from routes.resident import router as resident_router
from routes.security_guard import router as security_guard_router
from routes.announcement import router as announcement_router
from routes.community_directory import router as community_router
from routes import profile
from routes.alerts import router as alerts_router

# Security Dashboard routes
from routes.security import router as security_router
from routes.blacklist import router as blacklist_router
from routes.delivery import router as delivery_router

app = FastAPI()

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

# ---------------- Authentication ----------------
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

# ---------------- Visitor ----------------
app.include_router(visitor_router, prefix="/visitor", tags=["Visitor"])

# ---------------- QR ----------------
app.include_router(qr_router, prefix="/qr", tags=["QR"])

# ---------------- Resident ----------------
app.include_router(resident_router, prefix="/resident", tags=["Resident"])

app.include_router(alerts_router)

# ---------------- Security Guard ----------------
app.include_router(
    security_guard_router,
    prefix="/security",
    tags=["Security Guard"]
)

# ---------------- Security Dashboard ----------------
app.include_router(
    security_router,
    prefix="/security",
    tags=["Security Dashboard"]
)

app.include_router(
    blacklist_router,
    prefix="/blacklist",
    tags=["Blacklist"]
)


app.include_router(
    delivery_router,
    prefix="/delivery",
    tags=["Delivery"]
)

# ---------------- Announcements ----------------
app.include_router(
    announcement_router,
    prefix="/announcement",
    tags=["Announcement"]
)

# ---------------- Community Directory ----------------
app.include_router(
    community_router,
    prefix="/community",
    tags=["Community"]
)

app.include_router(profile.router)

@app.get("/")
def root():
    resident_count =  db.residents.count_documents({})

    return {
        "message": "Heimdall FastAPI Server Running",
        "resident_count": resident_count
    }