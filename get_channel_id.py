from balethon import Client
from balethon.handlers import MessageHandler

BOT_TOKEN = "توکن_بات_خودت"

client = Client(BOT_TOKEN)

@client.on(MessageHandler())
async def handle(client, message):
    text = f"Chat ID: {message.chat.id}"
    if message.forward_from_chat:
        text += f"\nForward from: {message.forward_from_chat.id}"
    await message.reply(text)

client.run()
