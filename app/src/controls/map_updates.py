from app.src.models import map_updates

async def read_root(request):
    return await map_updates.read_root(request)


async def calculate_route(request):
    return await map_updates.calculate_route(request)  
