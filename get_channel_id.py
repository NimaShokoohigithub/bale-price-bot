import os
import asyncio
from balethon import Client

BOT_TOKEN = os.environ.get("BALE_BOT_TOKEN")

async def main():
    client = Client(BOT_TOKEN)
    
    async with client:
        try:
            chat = await client.get_chat("nsprice")
            print(f"CHANNEL_ID: {chat.id}")
            print(f"Title: {chat.title}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
