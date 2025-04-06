import logging
import os
from pyrogram import Client, filters
from pyrogram.errors import RPCError
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

logging.basicConfig(
    filename="error.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

client = Client("forward-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
mongo = MongoClient(MONGO_URI)
db = mongo["forward_bot"]["users"]

@client.on_message(filters.command("start"))
async def start_handler(_, message):
    await message.reply_text(
        "**Welcome to Channel Forwarder Bot!**\n\nUse:\n/setsource -100xxxxxx\n/setdestination -100yyyyyy"
    )

@client.on_message(filters.command("setsource"))
async def set_source(_, message):
    user_id = message.from_user.id
    try:
        source = message.text.split()[1]
        db.update_one({"user_id": user_id}, {"$set": {"source": source}}, upsert=True)
        await message.reply_text(f"✅ Source channel set to `{source}`", quote=True)
    except IndexError:
        await message.reply_text("Usage: /setsource -100xxxxxxxx")

@client.on_message(filters.command("setdestination"))
async def set_destination(_, message):
    user_id = message.from_user.id
    try:
        destination = message.text.split()[1]
        db.update_one({"user_id": user_id}, {"$set": {"destination": destination}}, upsert=True)
        await message.reply_text(f"✅ Destination channel set to `{destination}`", quote=True)
    except IndexError:
        await message.reply_text("Usage: /setdestination -100xxxxxxxx")

@client.on_message(filters.forwarded & filters.private)
async def forward_handler(_, message):
    user_id = message.from_user.id
    data = db.find_one({"user_id": user_id})
    if data and "source" in data and "destination" in data:
        try:
            if str(message.forward_from_chat.id) == str(data["source"]):
                await client.forward_messages(
                    chat_id=data["destination"],
                    from_chat_id=message.chat.id,
                    message_ids=message.message_id
                )
        except RPCError as e:
            logging.error(f"Forward Error for user {user_id}: {e}")
            await message.reply_text("❌ Error during forwarding. Please check logs or your channel permissions.")

client.run()
