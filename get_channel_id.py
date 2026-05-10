import os
import asyncio
from balethon import Client
from balethon.handlers import MessageHandler

BOT_TOKEN = os.environ.get("BALE_BOT_TOKEN")

client = Client(BOT_TOKEN)

@client.on(MessageHandler())
async def handle(client, message):
    print(f"Chat ID: {message.chat.id}")
    print(f"Chat Type: {message.chat.type}")
    if message.forward_from_chat:
        print(f"Forwarded from Chat ID: {message.forward_from_chat.id}")
        print(f"Forwarded from Title: {message.forward_from_chat.title}")
    await message.reply(f"Chat ID: {message.chat.id}\nForward Chat ID: {getattr(message.forward_from_chat, 'id', 'N/A')}")

client.run()
