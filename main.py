import os
import threading
from flask import Flask
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.messages import ForwardMessagesRequest
from telethon.tl.types import InputReplyToMessage

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

SOURCE_ID = -1001791881265
DEST_ID = -5133982059

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# Maps source message ID -> destination message ID
# so reply threads are preserved in the destination group
msg_id_map = {}

# --- FEATURE 1: AUTO FORWARDER ---
@client.on(events.NewMessage(chats=SOURCE_ID))
async def forwarder_handler(event):
    try:
        reply_to_msg_id = None

        # If this source message is a reply, look up the matching dest message
        if event.message.reply_to and event.message.reply_to.reply_to_msg_id:
            src_reply_id = event.message.reply_to.reply_to_msg_id
            reply_to_msg_id = msg_id_map.get(src_reply_id)

        # Resolve the destination peer
        dest_peer = await client.get_input_entity(DEST_ID)
        src_peer  = await client.get_input_entity(SOURCE_ID)

        # Build optional reply_to header
        reply_to_header = None
        if reply_to_msg_id:
            reply_to_header = InputReplyToMessage(reply_to_msg_id=reply_to_msg_id)

        # Use the raw API so we can attach reply_to on the forwarded message
        result = await client(ForwardMessagesRequest(
            from_peer=src_peer,
            id=[event.message.id],
            to_peer=dest_peer,
            reply_to=reply_to_header,
            drop_author=False,
            silent=False,
        ))

        # Extract the forwarded message ID from the result updates
        sent_id = None
        if hasattr(result, 'updates'):
            for upd in result.updates:
                if hasattr(upd, 'id'):
                    sent_id = upd.id
                    break

        if sent_id:
            msg_id_map[event.message.id] = sent_id

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
