from fastapi import APIRouter


router = APIRouter()


@router.get("")
def health_check():
    return {
        "status": "healthy",
        "message": "WayFinder backend is running",
    }


@router.get("/")
def health_check_slash():
    return {
        "status": "healthy",
        "message": "WayFinder backend is running",
    }