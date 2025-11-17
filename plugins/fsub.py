from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ParseMode, ChatMemberStatus, ChatAction
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from bot import Bot
from config import OWNER_ID, FSUB_SETTINGS_PIC, FSUB_PIC, FSUB_LINK_EXPIRY
from database.database import Seishiro
import logging
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Initialize chat_data_cache
chat_data_cache = {}

async def is_sub(client, user_id, channel_id):
    try:
        member = await client.get_chat_member(channel_id, user_id)
        return member.status in {
            ChatMemberStatus.OWNER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.MEMBER
        }
    except UserNotParticipant:
        mode = await Seishiro.get_channel_mode(channel_id) or await Seishiro.get_channel_mode_all(channel_id)
        if mode == "on":
            exists = await Seishiro.req_user_exist(channel_id, user_id)
            return exists
        return False
    except Exception as e:
        logger.error(f"Error in is_sub(): {e}")
        return False

async def is_subscribed(client, user_id):
    channel_ids = await Seishiro.get_fsub_channels()
    if not channel_ids:
        return True
    if user_id == OWNER_ID:
        return True
    for cid in channel_ids:
        if not await is_sub(client, user_id, cid):
            mode = await Seishiro.get_channel_mode(cid) or await Seishiro.get_channel_mode_all(cid)
            if mode == "on":
                await asyncio.sleep(2)
                if await is_sub(client, user_id, cid):
                    continue
            return False
    return True

async def not_joined(client: Client, message: Message):
    logger.debug(f"not_joined function called for user {message.from_user.id}")
    temp = await message.reply("<b><i>ᴡᴀɪᴛ ᴀ sᴇᴄ..</i></b>")

    user_id = message.from_user.id
    buttons = []
    count = 0

    try:
        all_channels = await Seishiro.get_fsub_channels()
        for chat_id in all_channels:
            await message.reply_chat_action(ChatAction.TYPING)

            is_member = False
            try:
                member = await client.get_chat_member(chat_id, user_id)
                is_member = member.status in {
                    ChatMemberStatus.OWNER,
                    ChatMemberStatus.ADMINISTRATOR,
                    ChatMemberStatus.MEMBER
                }
            except UserNotParticipant:
                is_member = False
            except Exception as e:
                is_member = False
                logger.error(f"Error checking member in not_joined: {e}")

            if not is_member:
                try:
                    if chat_id in chat_data_cache:
                        data = chat_data_cache[chat_id]
                    else:
                        data = await client.get_chat(chat_id)
                        chat_data_cache[chat_id] = data

                    name = data.title
                    mode = await Seishiro.get_channel_mode(chat_id) or await Seishiro.get_channel_mode_all(chat_id)

                    if mode == "on" and not data.username:
                        invite = await client.create_chat_invite_link(
                            chat_id=chat_id,
                            creates_join_request=True,
                            expire_date=datetime.utcnow() + timedelta(seconds=FSUB_LINK_EXPIRY) if FSUB_LINK_EXPIRY else None
                        )
                        link = invite.invite_link
                    else:
                        if data.username:
                            link = f"https://t.me/{data.username}"
                        else:
                            invite = await client.create_chat_invite_link(
                                chat_id=chat_id,
                                expire_date=datetime.utcnow() + timedelta(seconds=FSUB_LINK_EXPIRY) if FSUB_LINK_EXPIRY else None
                            )
                            link = invite.invite_link

                    buttons.append([InlineKeyboardButton(text=name, url=link)])
                    count += 1
                    await temp.edit(f"<b>{'! ' * count}</b>")

                except Exception as e:
                    logger.error(f"Error with chat {chat_id}: {e}")
                    await temp.edit(
                        f"<b><i>! Eʀʀᴏʀ, Cᴏɴᴛᴀᴄᴛ ᴅᴇᴠᴇʟᴏᴘᴇʀ ᴛᴏ sᴏʟᴠᴇ ᴛʜᴇ ɪssᴜᴇs @seishiro_obito</i></b>\n"
                        f"<blockquote expandable><b>Rᴇᴀsᴏɴ:</b> {e}</blockquote>"
                    )
                    return

        try:
            # Get base64_string if exists
            text = message.text
            base64_string = ""
            if len(text) > 7:
                base64_string = text.split(" ", 1)[1]

            # Create deep link with the encoded string
            if base64_string:
                deep_link = f"https://t.me/{client.username}?start={base64_string}"
            else:
                deep_link = f"https://t.me/{client.username}"

            buttons.append([
                InlineKeyboardButton(
                    text='• Jᴏɪɴᴇᴅ •',
                    url=deep_link
                )
            ])
        except Exception as e:
            logger.error(f"Error creating joined button: {e}")
            # Fallback without deep link
            try:
                bot_username = (await client.get_me()).username
                buttons.append([
                    InlineKeyboardButton(
                        text='• Jᴏɪɴᴇᴅ •',
                        url=f"https://t.me/{bot_username}"
                    )
                ])
            except:
                pass

        text = f"<b>Yᴏᴜ {message.from_user.mention} \n\n<blockquote>Jᴏɪɴ ᴍʏ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴜsᴇ ᴍᴇ ᴏᴛʜᴇʀᴡɪsᴇ Yᴏᴜ ᴀʀᴇ ɪɴ ʙɪɢ sʜɪᴛ...!!</blockquote></b>"
        await temp.delete()

        logger.debug(f"Sending final reply photo to user {message.from_user.id}")
        await message.reply_photo(
            photo=FSUB_PIC,
            caption=text,
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    except Exception as e:
        logger.error(f"Final Error in not_joined: {e}")
        await temp.edit(
            f"<b><i>! Eʀʀᴏʀ, Cᴏɴᴛᴀᴄᴛ ᴅᴇᴠᴇʟᴏᴘᴇʀ ᴛᴏ sᴏʟᴠᴇ ᴛʜᴇ ɪssᴜᴇs @seishiro_obito</i></b>\n"
            f"<blockquote expandable><b>Rᴇᴀsᴏɴ:</b> {e}</blockquote>"
        )


@Bot.on_message(filters.command("fsub") & filters.private & filters.user(OWNER_ID))
async def fsub_command(client: Bot, message: Message):
    await message.reply_photo(
        photo=FSUB_SETTINGS_PIC,
        caption="""<b><blockquote expandable>Fsᴜʙ Sᴇᴛᴛɪɴɢs Mᴇɴᴜ:

• Aᴅᴅ Fsᴜʙ Cʜᴀɴɴᴇʟ - Add a channel to fsub list
• Rᴇᴍᴏᴠᴇ Fsᴜʙ Cʜᴀɴɴᴇʟ - Remove a channel from fsub list
• Lɪsᴛ Fsᴜʙ Cʜᴀɴɴᴇʟs - View all channels in fsub list
• Aʟʟ Cʜᴀɴɴᴇʟs - Enable/Disable request fsub for all channels at once
• Pᴀʀᴛɪᴄᴜʟᴀʀʟʏ - Toggle request fsub for specific channels

Sᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ʙᴇʟᴏᴡ:</blockquote></b>""",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("• Aᴅᴅ Fsᴜʙ Cʜᴀɴɴᴇʟ •", callback_data="add_fsub_channel")],
                [InlineKeyboardButton("• Rᴇᴍᴏᴠᴇ Fsᴜʙ Cʜᴀɴɴᴇʟ •", callback_data="remove_fsub_channel")],
                [InlineKeyboardButton("• Lɪsᴛ Fsᴜʙ Cʜᴀɴɴᴇʟs •", callback_data="list_fsub_channels")],
                [InlineKeyboardButton("• Aʟʟ Cʜᴀɴɴᴇʟs •", callback_data="all_channels")],
                [InlineKeyboardButton("• Pᴀʀᴛɪᴄᴜʟᴀʀʟʏ •", callback_data="particularly")],
                [InlineKeyboardButton("• Bᴀᴄᴋ •", callback_data="start")]
            ]
        )
    )

@Bot.on_callback_query(filters.regex("^add_fsub_channel$"))
async def add_fsub_channel_callback(client: Bot, query: CallbackQuery):
    await query.message.edit_text("Send me the ID of the channel you want to add.")

    @Bot.on_message(filters.text & filters.private & filters.user(OWNER_ID))
    async def get_channel_id(client: Bot, message: Message):
        try:
            channel_id = int(message.text)
            await Seishiro.add_fsub_channel(channel_id)
            await message.reply_text(f"Channel {channel_id} has been added to the fsub list.")
        except ValueError:
            await message.reply_text("Invalid channel ID. Please send a valid channel ID.")
        except Exception as e:
            await message.reply_text(f"An error occurred: {e}")
        finally:
            # Unregister the handler to avoid conflicts
            client.remove_handler(get_channel_id)

@Bot.on_callback_query(filters.regex("^remove_fsub_channel$"))
async def remove_fsub_channel_callback(client: Bot, query: CallbackQuery):
    await query.message.edit_text("Send me the ID of the channel you want to remove.")

    @Bot.on_message(filters.text & filters.private & filters.user(OWNER_ID))
    async def get_channel_id(client: Bot, message: Message):
        try:
            channel_id = int(message.text)
            await Seishiro.remove_fsub_channel(channel_id)
            await message.reply_text(f"Channel {channel_id} has been removed from the fsub list.")
        except ValueError:
            await message.reply_text("Invalid channel ID. Please send a valid channel ID.")
        except Exception as e:
            await message.reply_text(f"An error occurred: {e}")
        finally:
            # Unregister the handler to avoid conflicts
            client.remove_handler(get_channel_id)

@Bot.on_callback_query(filters.regex("^list_fsub_channels$"))
async def list_fsub_channels_callback(client: Bot, query: CallbackQuery):
    channels = await Seishiro.get_fsub_channels()
    if not channels:
        await query.answer("There are no fsub channels.", show_alert=True)
        return

    text = "**Fsub Channels:**\n\n"
    for channel in channels:
        text += f"• `{channel}`\n"

    await query.message.edit_text(text)

@Bot.on_callback_query(filters.regex("^all_channels$"))
async def all_channels_callback(client: Bot, query: CallbackQuery):
    await Seishiro.set_channel_mode_all("on" if query.data.endswith("_on") else "off")
    await query.answer("Successfully updated all channels.", show_alert=True)

@Bot.on_callback_query(filters.regex("^particularly$"))
async def particularly_callback(client: Bot, query: CallbackQuery):
    channels = await Seishiro.get_fsub_channels()
    if not channels:
        await query.answer("There are no fsub channels.", show_alert=True)
        return

    buttons = []
    for channel in channels:
        mode = await Seishiro.get_channel_mode(channel)
        buttons.append([InlineKeyboardButton(f"{channel} - {'ON' if mode == 'on' else 'OFF'}", callback_data=f"toggle_{channel}")])

    await query.message.edit_text(
        "**Toggle Fsub for Specific Channels:**",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Bot.on_callback_query(filters.regex("^toggle_"))
async def toggle_channel_callback(client: Bot, query: CallbackQuery):
    channel_id = int(query.data.split("_")[1])
    mode = await Seishiro.get_channel_mode(channel_id)
    new_mode = "off" if mode == "on" else "on"
    await Seishiro.set_channel_mode(channel_id, new_mode)
    await query.answer(f"Successfully toggled fsub for {channel_id} to {new_mode.upper()}", show_alert=True)
    await particularly_callback(client, query)
