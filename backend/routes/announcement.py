from fastapi import APIRouter
from datetime import datetime
from zoneinfo import ZoneInfo
from schema import AnnouncementRequest
from database import db

router = APIRouter(prefix="/announcement", tags=["Global Broadcasts"])

@router.post("/send-announcement")
def send_announcement(data: AnnouncementRequest):
    announcement = {
        "title": data.title,
        "message": data.message,
        "created_at": datetime.now(ZoneInfo("Asia/Kolkata"))
    }
    db.announcements_collection.insert_one(announcement)
    return {"status": "success", "message": "Announcement stored successfully."}

@router.get("/announcements")
def get_announcements():
    announcements = db.announcements_collection.find({}, {"_id": 0}).sort("created_at", -1).to_list(length=None)
    
    for ann in announcements:
        if isinstance(ann.get("created_at"), datetime):
            ann["created_at"] = ann["created_at"].isoformat()
            
    return announcements