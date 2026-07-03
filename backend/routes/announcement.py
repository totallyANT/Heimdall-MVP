from fastapi import APIRouter
from datetime import datetime
from zoneinfo import ZoneInfo

from schema import AnnouncementRequest
from database import db

router = APIRouter()


@router.post("/send-announcement")
def send_announcement(data: AnnouncementRequest):

    print("Received:", data)

    announcement = {
        "title": data.title,
        "message": data.message,
        "created_at": datetime.now(ZoneInfo("Asia/Kolkata"))
    }

    result = db.announcements_collection.insert_one(announcement)

    print("Inserted ID:", result.inserted_id)

    return {
        "status": "success",
        "message": "Announcement stored successfully."
    }

@router.get("/announcements")
def get_announcements():

    announcements = db.announcements_collection.find(
        {},
        {"_id": 0}
    ).to_list(length=None)

    return announcements