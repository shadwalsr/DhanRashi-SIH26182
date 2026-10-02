from fastapi import APIRouter

router = APIRouter(prefix="/sahyog", tags=["SAHYOG"])


@router.get("/")
async def list_sahyog_requests():
    return {"items": [], "total": 0}
