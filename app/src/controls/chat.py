from app.src.models import chat

async def get_chat_history():
    return await chat.get_chat_history()  


async def handle_chat(message):
    return await chat.handle_chat(message)