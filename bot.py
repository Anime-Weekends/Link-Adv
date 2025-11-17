import asyncio
import sys
from datetime import datetime
from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import API_HASH, APP_ID, LOGGER, TG_BOT_TOKEN, TG_BOT_WORKERS, PORT, DATABASE_CHANNEL, OWNER_ID
from plugins import web_server
import pyrogram.utils
from aiohttp import web

name = """
Link share bot started ✨ Credit:- @RexBots_Official
"""

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=APP_ID,
            plugins={"root": "plugins"},
            workers=TG_BOT_WORKERS,
            bot_token=TG_BOT_TOKEN,
        )
        self.LOGGER = LOGGER

    async def start(self, *args, **kwargs):
        await super().start()
        usr_bot_me = await self.get_me()
        self.uptime = datetime.now()

        # Notify bot restart
        try:
            await self.get_chat(DATABASE_CHANNEL)
            await self.send_photo(
                    chat_id=DATABASE_CHANNEL,
                    photo=None,
                    caption=(
                        "**I ʀᴇsᴛᴀʀᴛᴇᴅ ᴀɢᴀɪɴ !**"),
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("ᴜᴘᴅᴀᴛᴇs", url="https://t.me/RexBots_Official")]]
                    )
                )
        except Exception as e:
            self.LOGGER(__name__).warning(f"Failed to send startup notification to DATABASE_CHANNEL ({DATABASE_CHANNEL}). Please make sure the bot is a member of the channel and the channel ID is correct. Error: {e}")

        self.set_parse_mode(ParseMode.HTML)
        self.LOGGER(__name__).info("Wew...Bot is running...⚡  Credit:- @RexBots_Official")
        self.LOGGER(__name__).info(f"{name}")
        self.username = usr_bot_me.username

        # Web-response
        try:
            app = web.AppRunner(await web_server())
            await app.setup()
            bind_address = "0.0.0.0"
            await web.TCPSite(app, bind_address, PORT).start()
            self.LOGGER(__name__).info(f"Web server started on {bind_address}:{PORT}")
        except Exception as e:
            self.LOGGER(__name__).error(f"Failed to start web server: {e}")

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info("Bot stopped...")
        
if __name__ == "__main__":
    Bot().run()
