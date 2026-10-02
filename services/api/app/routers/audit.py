from fastapi import APIRouter

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/")
async def list_audit_logs():
    return {"items": [], "total": 0}
