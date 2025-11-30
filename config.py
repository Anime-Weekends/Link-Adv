from ast import pattern
import os
from os import environ
import logging
from logging.handlers import RotatingFileHandler

TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "7463031242:AAF38Y2RBxx2XhDlDUur1YhQzZrhMU8x2x8")
BOT_USERNAME = 'AnimeWeekendLinkBot'

APP_ID = int(os.environ.get("APP_ID", "28744454"))
API_HASH = os.environ.get("API_HASH", "debd37cef0ad1a1ce45d0be8e8c3c5e7")

OWNER_ID = int(os.environ.get("OWNER_ID", "6266529037"))

PORT = os.environ.get("PORT", "8080")
DB_URL = os.environ.get("DB_URI", "mongodb+srv://Rexybecomenice:Rexybecomenice@cluster0.4oosu31.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DB_NAME = os.environ.get("DB_NAME", "AnimeWeekendsLinkBot")
TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "40"))

COMMAND_PHOTO = os.environ.get("COMMAND_PHOTO", "https://i.ibb.co/Y7xZr9zd/photo-2025-11-30-09-21-11-7578446111342329860.jpg")  # Replace with your photo URL
START_PIC = os.environ.get("START_PIC", "https://i.ibb.co/Y7xZr9zd/photo-2025-11-30-09-21-11-7578446111342329860.jpg")
START_MSG = os.environ.get("START_MESSAGE", "<b><blockquote>›› Hᴇʏ {mention} ×</blockquote>\n<blockquote>›› ʟᴏᴠᴇ ᴀɴɪᴍᴇ ? ɪ ᴀᴍ ᴍᴀᴅᴇ ᴛᴏ ʜᴇʟᴘ ʏᴏᴜ ᴛᴏ ғɪɴᴅ ᴡʜᴀᴛ ʏᴏᴜ'ʀᴇ ʟᴏᴏᴋɪɴɢ ꜰᴏʀ.</blockquote></b>")
ABOUT_TXT = os.environ.get("HELP_MESSAGE", "<b><blockquote>Mʏ ɴᴀᴍᴇ :</blockquote>\n<blockquote>◈ Oᴡɴᴇʀ : <a href=https://t.me/AckerManFreak>R x ʏ</a>\n◈ Dᴇᴠᴇʟᴏᴘᴇʀ : <a href=https://t.me/RexySama>ᴄʟɪᴄᴋ ʜᴇʀᴇ</a>\n◈ Mᴀɪɴ Cʜᴀɴɴᴇʟ : <a href='https://t.me/Anime_Weekends'>ᴄʟɪᴄᴋ ʜᴇʀᴇ</a>\n◈ Kᴅʀᴀᴍᴀ Cʜᴀɴɴᴇʟ : <a href='https://t.me/Kdrama_Weekends'>ᴄʟɪᴄᴋ ʜᴇʀᴇ</a>\n◈ Eᴍɪɴᴇɴᴄᴇ Sᴏᴄɪᴇᴛʏ : <a href='https://t.me/Eminence_Society'>ᴄʟɪᴄᴋ ʜᴇʀᴇ</a></blockquote></b></i>")
HELP_TXT =  os.environ.get("HELP_MESSAGE", "<b><blockquote>◈ 𝗖𝗢𝗣𝗬𝗥𝗜𝗚𝗛𝗧 𝗟𝗔𝗪</blockquote>\n<blockquote expandable>≡ Cᴏᴘʏʀɪɢʜᴛ ᴅɪsᴄʟᴀɪᴍᴇʀ: - ᴜɴᴅᴇʀ sᴇᴄᴛɪᴏɴ 107 ᴏғ ᴛʜᴇ ᴄᴏᴘʏʀɪɢʜᴛ ᴀᴄᴛ 1976, ᴀʟʟᴏᴡᴀɴᴄᴇ ɪs ᴍᴀᴅ ғᴏʀ ғᴀɪʀ ᴜsᴇ ғᴏʀ ᴘᴜʀᴘᴏsᴇ sᴜᴄʜ ᴀ ᴀs ᴄʀɪᴛɪᴄɪsᴍ, ᴄᴏᴍᴍᴇɴᴛ, ɴᴇᴡs ʀᴇᴘᴏʀᴛɪɴɢ, ᴛᴇᴀᴄʜɪɴɢ, sᴄʜᴏʟᴀʀsʜɪᴘ ᴀɴᴅ ʀᴇsᴇᴀʀᴄʜ. ғᴀɪʀ ᴜsᴇ ɪs ᴀ ᴜsᴇ ᴘᴇʀᴍɪᴛᴛᴇᴅ ʙʏ ᴄᴏᴘʏʀɪɢʜᴛ sᴛᴀᴛᴜᴇs ᴛʜᴀᴛ ᴍɪɢʜᴛ ᴏᴛʜᴇʀᴡɪsᴇ ʙᴇ ɪɴғʀɪɴɢɪɴɢ. ɴᴏɴ- ᴘʀᴏғɪᴛ, ᴇᴅᴜᴄᴀᴛɪᴏɴᴀʟ ᴏʀ ᴘᴇʀsᴏɴᴀʟ ᴜsᴇ ᴛɪᴘs ᴛʜᴇ ʙᴀʟᴀɴᴄᴇ ɪɴ ғᴀᴠᴏʀ ᴏғ ғᴀɪʀ ᴜsᴇ.</blockquote>")
FSUB_PIC = os.environ.get("FSUB_PIC", "https://i.ibb.co/Y7xZr9zd/photo-2025-11-30-09-21-11-7578446111342329860.jpg")
FSUB_LINK_EXPIRY = 300
LOG_FILE_NAME = "Rexbots.txt"
DATABASE_CHANNEL = int(os.environ.get("DATABASE_CHANNEL", "-1003415022924"))

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
