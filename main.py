import os
import threading
from flask import Flask
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# --- DUMMY WEB SERVER ---
app = Flask(__name__)

@app.route('/')
def hello():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- CONFIGURATION ---
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")

SOURCE_ID = -5044007459
DEST_ID = -5133982059

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# --- FEATURE 1: AUTO FORWARDER ---
@client.on(events.NewMessage(chats=SOURCE_ID))
async def forwarder_handler(event):
    try:
        await event.forward_to(DEST_ID)
    except Exception as e:
        print(f"Forward Error: {e}")

# --- FEATURE 2: STATUS COMMAND ---
# This listens for ".status" sent by YOU in any chat
@client.on(events.NewMessage(pattern=r'\.status', outgoing=True))
async def status_handler(event):
    await event.edit("✅ Bot is Online!\n\nLocation: Koyeb Cloud\nStatus: Forwarding active.")

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    print("Bot is starting...")
    client.start()
    client.run_until_disconnected()
