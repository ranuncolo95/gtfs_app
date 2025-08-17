from app.src.models import coordinates

async def geocode(q: str):
    return await coordinates.geocode(q)  # Add await here
                
async def reverse_geocode(lng: float, lat: float):
    return await coordinates.reverse_geocode(lng, lat)  # Add await here