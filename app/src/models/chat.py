from transformers import pipeline
from fastapi.responses import RedirectResponse
from fastapi import Form


chat_history = []

async def get_chat_history():

    """Endpoint that returns JUST the chat messages (loaded in iframe)"""
    messages_html = "".join([
        f'<div class="chat-message {msg["type"]}-message">{msg["text"]}</div>'
        for msg in chat_history
    ])
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            .chat-message {{ 
                margin-bottom: 10px;
                padding: 8px 12px;
                border-radius: 5px;
            }}
            .user-message {{ background-color: #e3f2fd; margin-left: 20%; }}
            .bot-message {{ background-color: #f8f9fa; margin-right: 20%; }}
        </style>
    </head>
    <body>{messages_html}</body>
    </html>
    """

async def handle_chat(message: str = Form(...)):
    """Process chat form submission"""
    global chat_history
    chat_history = []

    # Add user message to history
    chat_history.append({"type": "user", "text": message})
    
    # Generate bot response (using your existing pipeline)
    generator = pipeline('text-generation', model='gpt2')
    response = generator(message, max_length=100, num_return_sequences=1)[0]['generated_text']
    
    chat_history.append({"type": "bot", "text": response})
    # Redirect back to chat history (which will refresh the iframe)
    return RedirectResponse(url="/chat-history", status_code=303)