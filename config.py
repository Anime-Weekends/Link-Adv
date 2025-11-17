from ast import pattern
import os
from os import environ
import logging
from logging.handlers import RotatingFileHandler
import asyncio

# Check for required environment variables
required_vars = ["TG_BOT_TOKEN", "API_HASH", "APP_ID", "DB_URI"]
for var in required_vars:
    if not environ.get(var):
        raise ValueError(f"Missing required environment variable: {var}")

DB_URL = environ.get("DB_URI")
DB_NAME = os.environ.get("DB_NAME", "link_1_bro")

from database.database import Seishiro

async def load_settings():
    DB_URL_DB = await Seishiro.get_setting("DB_URI")
    STICKER_ID_DB = await Seishiro.get_setting("STICKER_ID")
    return DB_URL_DB, STICKER_ID_DB

# Load settings from database
loop = asyncio.get_event_loop()
DB_URL_DB, STICKER_ID_DB = loop.run_until_complete(load_settings())

DB_URL = DB_URL_DB or DB_URL
STICKER_ID = STICKER_ID_DB or environ.get("STICKER_ID")


TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
BOT_USERNAME = 'LinkkShare_bot'
APP_ID = int(os.environ.get("APP_ID"))
API_HASH = os.environ.get("API_HASH")
OWNER_ID = int(os.environ.get("OWNER_ID"))
PORT = os.environ.get("PORT", "8080")
TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "40"))
COMMAND_PHOTO = os.environ.get("COMMAND_PHOTO")
START_PIC = os.environ.get("START_PIC")
START_MSG = os.environ.get("START_MESSAGE")
ABOUT_TXT = os.environ.get("HELP_MESSAGE")
HELP_TXT =  os.environ.get("HELP_MESSAGE")
BOT_STATS_TEXT = "<i><b><blockquote>ʙᴏᴛ ᴜᴘᴛɪᴍᴇ\n{uptime}</blockquote></b></i>"
USER_REPLY_TEXT = "<i><b><blockquote>⚠️ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴍʏ ᴍᴀsᴛᴇʀ.</blockquote></b></i>"
LOG_FILE_NAME = "links-sharingbot.txt"
DATABASE_CHANNEL = int(os.environ.get("DATABASE_CHANNEL"))
FSUB_SETTINGS_PIC = os.environ.get("FSUB_SETTINGS_PIC")
ABOUT_PIC = os.environ.get("ABOUT_PIC")
HELP_PIC = os.environ.get("HELP_PIC")
FSUB_PIC = os.environ.get("FSUB_PIC")
FSUB_LINK_EXPIRY = int(os.environ.get("FSUB_LINK_EXPIRY", "300"))

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            LOG_FILE_NAME,
            maxBytes=50000000,
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)
