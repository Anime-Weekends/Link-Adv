from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
from bot import Bot
from config import ABOUT_TXT, HELP_TXT, ABOUT_PIC, HELP_PIC

@Bot.on_callback_query(filters.regex("about"))
async def about_callback(client: Bot, query: CallbackQuery):
    await query.message.edit_media(
        media=InputMediaPhoto(
            media=ABOUT_PIC,
            caption=f"""<b><blockquote expandable>{ABOUT_TXT}</blockquote></b>"""
        ),
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("• Bᴀᴄᴋ •", callback_data="start")]
            ]
        )
    )

@Bot.on_callback_query(filters.regex("help"))
async def help_callback(client: Bot, query: CallbackQuery):
    await query.message.edit_media(
        media=InputMediaPhoto(
            media=HELP_PIC,
            caption=f"""<b><blockquote expandable>{HELP_TXT}</blockquote></b>"""
        ),
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("• Bᴀᴄᴋ •", callback_data="start")]
            ]
        )
    )

@Bot.on_callback_query(filters.regex("start"))
async def start_callback(client: Bot, query: CallbackQuery):
    await query.message.edit_text(
        "**Welcome back to the main menu!**",
        reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("• ᴀʙᴏᴜᴛ", callback_data="about"),
                     InlineKeyboardButton("Hᴇʟᴘ •", callback_data="help")],
                    [InlineKeyboardButton("• Fsᴜʙ Sᴇᴛᴛɪɴɢs •", callback_data="fsub")]
                ]
            )
    )
