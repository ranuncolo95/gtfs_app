from fastapi import APIRouter
from src.web.geocode import router as geocode_router
from src.web.calculate_route import router as calc_route_router


api_router = APIRouter()
api_router.include_router(geocode_router, tags=["geocode"])
api_router.include_router(calc_route_router, tags=["calculate_route"])
