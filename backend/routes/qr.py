from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from database import db
import qrcode
import io
import json

router = APIRouter()


@router.get("/{pass_id}")
def get_qr(pass_id: str):

    qr_data = None

    # ---------- Guest Pass ----------
    if pass_id.startswith("VIS-"):
        guest =  db.guest_passes.find_one({
            "passId": pass_id
        })

        if not guest:
            raise HTTPException(
                status_code=404,
                detail="Guest pass not found"
            )

        qr_data = {
            "passId": pass_id,
            "type": "guest"
        }

    # ---------- Group Pass ----------
    elif pass_id.startswith("GRP-"):
        group =  db.group_passes.find_one({
            "passId": pass_id
        })

        if not group:
            raise HTTPException(
                status_code=404,
                detail="Group pass not found"
            )

        qr_data = {
            "passId": pass_id,
            "type": "group"
        }

    # ---------- Worker Pass ----------
    elif pass_id.startswith("WRK-"):
        worker = db.worker_passes.find_one({
            "worker_id": pass_id
        })

        if not worker:
            raise HTTPException(
                status_code=404,
                detail="Worker pass not found"
            )

        qr_data = {
            "workerId": pass_id,
            "type": "worker"
        }

    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid pass format"
        )

    qr = qrcode.make(json.dumps(qr_data))

    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="image/png"
    )
