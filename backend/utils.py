from database import db
from datetime import datetime


async def log_scan(
    pass_id,
    pass_type,
    action,
    status,
    reason=None,
    current_status=None
):
    log = {
        "passId": pass_id,
        "passType": pass_type,
        "action": action,
        "status": status,
        "timestamp": datetime.utcnow()
    }

    if reason:
        log["reason"] = reason

    await db.scan_logs.insert_one(log)
