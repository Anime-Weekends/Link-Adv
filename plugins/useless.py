from bot import Bot
from pyrogram.types import Message, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import filters
from config import BOT_STATS_TEXT, USER_REPLY_TEXT, STICKER_ID, COMMAND_PHOTO
from datetime import datetime
from helper_func import *
import asyncio

async def check_admin(filter, client, update):
    try:
        user_id = update.from_user.id
        return any([user_id == OWNER_ID, await is_admin_filter(user_id)])
    except Exception as e:
        logger.error(f"Exception in check_admin: {e}")
        return False

admin = filters.create(check_admin)

is_owner_or_admin = admin

@Bot.on_message(filters.command('stats') & admin)
async def stats(bot: Bot, message: Message):
    await bot.send_sticker(message.chat.id, STICKER_ID)
    await asyncio.sleep(0.5)
    
    now = datetime.now()
    delta = now - bot.uptime
    time = get_readable_time(delta.seconds)
    caption = f"<i><b><blockquote expandable>{BOT_STATS_TEXT.format(uptime=time)}\n\n📜 <b>ʜᴏᴡ ɪᴛ ᴡᴏʀᴋs</b>: ᴅɪsᴘʟᴀʏs ᴛʜᴇ ʙᴏᴛ’s ᴜᴘᴛɪᴍᴇ. ᴏɴʟʏ ᴛʜᴇ ᴏᴡɴᴇʀ ᴄᴀɴ ᴜsᴇ ᴛʜɪs.</blockquote></b></i>"
    buttons = [
        [InlineKeyboardButton("• ʀᴇғʀᴇsʜ •", callback_data="refresh_stats")]
    ]
    await bot.send_photo(
        chat_id=message.chat.id,
        photo=COMMAND_PHOTO,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Bot.on_callback_query(filters.regex(r"refresh_stats"))
async def refresh_stats_callback(client, callback_query):
    now = datetime.now()
    delta = now - client.uptime
    time = get_readable_time(delta.seconds)
    caption = f"<i><b><blockquote expandable>{BOT_STATS_TEXT.format(uptime=time)}\n\n📜 <b>ʜᴏᴡ ɪᴛ ᴡᴏʀᴋs</b>: ᴅɪsᴘʟᴀʏs ᴛʜᴇ ʙᴏᴛ’s ᴜᴘᴛɪᴍᴇ. ᴏɴʟʏ ᴛʜᴇ ᴏᴡɴᴇʀ ᴄᴀɴ ᴜsᴇ ᴛʜɪs.</blockquote></b></i>"
    await client.send_sticker(callback_query.message.chat.id, STICKER_ID)
    await asyncio.sleep(0.5)
    await callback_query.message.edit_media(
        media=InputMediaPhoto(
            media=COMMAND_PHOTO,
            caption=caption
        ),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("• ʀᴇғʀᴇsʜ •", callback_data="refresh_stats")]])
    )
