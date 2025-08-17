from fastapi import HTTPException
import httpx

# MapTiler API Key
MAPTILER_API_KEY = "OCVJ6l477kLTb0IRr0k5"  
        
async def geocode(q: str):
    """Proxy geocoding requests to MapTiler API"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"https://api.maptiler.com/geocoding/{q}.json",
                params={"key": MAPTILER_API_KEY, "limit": 5}
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
async def reverse_geocode(lng: float, lat: float):
    """Proxy reverse geocoding requests to MapTiler API"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"https://api.maptiler.com/geocoding/{lng},{lat}.json",
                params={"key": MAPTILER_API_KEY}
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=400, detail=str(e))