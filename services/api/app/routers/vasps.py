from fastapi import APIRouter

router = APIRouter(prefix="/vasps", tags=["VASPs"])


@router.get("/")
async def list_vasps():
    return {"items": [], "total": 0}
