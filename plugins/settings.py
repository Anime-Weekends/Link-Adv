import os
import sys
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot import Bot
from config import OWNER_ID, DB_NAME
from database.database import Seishiro
import logging

logger = logging.getLogger(__name__)

@Bot.on_message(filters.command("settings") & filters.private & filters.user(OWNER_ID))
async def settings_command(client: Bot, message: Message):
    await message.reply_text(
        "**Bot Settings:**",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("• Set MongoDB URL •", callback_data="set_db_url")],
                [InlineKeyboardButton("• Set Sticker ID •", callback_data="set_sticker_id")],
                [InlineKeyboardButton("• Bᴀᴄᴋ •", callback_data="start")]
            ]
        )
    )

@Bot.on_callback_query(filters.regex("^set_db_url$"))
async def set_db_url_callback(client: Bot, query: CallbackQuery):
    try:
        db_url = await client.ask(
            chat_id=query.from_user.id,
            text="Send me the MongoDB URL.",
            timeout=30
        )
        await Seishiro.set_setting("DB_URI", db_url.text)
        Seishiro.re_init(db_url.text, DB_NAME)
        await query.message.reply_text("MongoDB URL has been updated. The bot will now restart.")
        # Restart the bot
        os.execl(sys.executable, sys.executable, "-m", "bot")
    except Exception as e:
        await query.message.reply_text(f"An error occurred: {e}")


@Bot.on_callback_query(filters.regex("^set_sticker_id$"))
async def set_sticker_id_callback(client: Bot, query: CallbackQuery):
    try:
        sticker_id = await client.ask(
            chat_id=query.from_user.id,
            text="Send me the Sticker ID.",
            timeout=30
        )
        await Seishiro.set_setting("STICKER_ID", sticker_id.text)
        await query.message.reply_text("Sticker ID has been updated.")
    except Exception as e:
        await query.message.reply_text(f"An error occurred: {e}")
