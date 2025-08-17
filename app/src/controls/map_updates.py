from app.src.models import map_updates


async def calculate_route(request):
    return await map_updates.calculate_route(request)  # Add await here
