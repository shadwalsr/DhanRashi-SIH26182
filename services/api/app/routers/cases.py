from fastapi import APIRouter

router = APIRouter(prefix="/cases", tags=["Cases"])


@router.get("/")
async def list_cases():
    return {"items": [], "total": 0}
