from fastapi import APIRouter

router = APIRouter(prefix="/investigations", tags=["Investigations"])


@router.get("/")
async def list_investigations():
    return {"items": [], "total": 0}
