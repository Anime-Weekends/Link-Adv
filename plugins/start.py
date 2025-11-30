import asyncio
import base64
import time
import logging
from collections import defaultdict
from asyncio import Lock
from pyrogram import Client, filters
from pyrogram.enums import ParseMode, ChatMemberStatus, ChatAction
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid, RPCError
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from functools import wraps

from bot import Bot
from datetime import datetime, timedelta
from config import *
from database.database import Seishiro
from plugins.settings import revoke_invite_after_5_minutes
from helper_func import *

logger = logging.getLogger(__name__)

# Initialize chat_data_cache
chat_data_cache = {}

channel_locks = defaultdict(Lock)

async def check_admin(filter, client, message):
    try:
        user_id = message.from_user.id
        return any([user_id == OWNER_ID, await Seishiro.is_admin(user_id)])
    except Exception as e:
        logger.error(f"Exception in check_admin: {e}")
        return False

admin = filters.create(check_admin)

def check_fsub(func):
    @wraps(func)
    async def wrapper(client, message, *args, **kwargs):
        user_id = message.from_user.id
        logger.debug(f"check_fsub decorator called for user {user_id}")

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
            channel_ids = await Seishiro.show_channels()
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
        
        try:
            is_sub_status = await is_subscribed(client, user_id)
            logger.debug(f"User {user_id} subscribed status: {is_sub_status}")
            
            if not is_sub_status:
                logger.debug(f"User {user_id} is not subscribed, calling not_joined.")
                return await not_joined(client, message)
            
            logger.debug(f"User {user_id} is subscribed, proceeding with function call.")
            return await func(client, message, *args, **kwargs)
        
        except Exception as e:
            logger.error(f"FATAL ERROR in check_fsub: {e}")
            await message.reply_text(f"An unexpected error occurred: {e}. Please contact the developer.")
            return
    return wrapper

async def not_joined(client: Client, message: Message):
    logger.debug(f"not_joined function called for user {message.from_user.id}")
    temp = await message.reply("<b><i>ᴡᴀɪᴛ ᴀ sᴇᴄ..</i></b>")

    # Add a check to ensure temp message exists before proceeding
    if not temp:
        logger.warning("Failed to send temporary message in not_joined")
        return

    user_id = message.from_user.id
    buttons = []
    count = 0

    try:
        all_channels = await Seishiro.show_channels()
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
                    mode = await Seishiro.get_channel_mode(chat_id)

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
                    try:
                        await temp.edit(f"<b>{'! ' * count}</b>")
                    except Exception as e:
                        logger.warning(f"Failed to edit message in not_joined: {e}")


                except Exception as e:
                    logger.error(f"Error with chat {chat_id}: {e}")
                    await temp.edit(
                        f"<b><i>! Eʀʀᴏʀ, Cᴏɴᴛᴀᴄᴛ ᴅᴇᴠᴇʟᴏᴘᴇʀ ᴛᴏ sᴏʟᴠᴇ ᴛʜᴇ ɪssᴜᴇs @seishiro_obito</i></b>\n"
                        f"<blockquote expandable><b>Rᴇᴀsᴏɴ:</b> {e}</blockquote>"
                    )
                    return

        try:
            buttons.append([
                InlineKeyboardButton(
                    text='• Jᴏɪɴᴇᴅ •',
                    url=f"https://t.me/{BOT_USERNAME}?start={message.command[1]}"
                )
            ])
        except IndexError:
            pass

        text = "<b>Yᴏᴜ Bᴀᴋᴋᴀᴀ...!! \n\n<blockquote>Jᴏɪɴ ᴍʏ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴜsᴇ ᴍʏ ᴏᴛʜᴇʀᴡɪsᴇ Yᴏᴜ ᴀʀᴇ ɪɴ ʙɪɢ sʜɪᴛ...!!</blockquote></b>"
        
        logger.debug(f"Sending final reply photo to user {user_id}")
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
    
@Bot.on_message(filters.command('start') & filters.private)
@check_fsub
async def start_command(client: Bot, message: Message):
    user_id = message.from_user.id
    
    # Check if user is banned
    user = await Seishiro.is_user_banned(user_id)
    if user:
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Cᴏɴᴛᴀᴄᴛ ʜᴇʀᴇ", url="https://t.me/RexySama")]]
        )
        return await message.reply_text(
            "<b><blockquote>›› Yᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ ғʀᴏᴍ ᴜsɪɴɢ ᴍᴇ ʙʏ ᴏᴜʀ ᴀᴅᴍɪɴ / ᴏᴡɴᴇʀ . Iғ ʏᴏᴜ ᴛʜɪɴᴋs ɪᴛ's ᴍɪsᴛᴀᴋᴇ ᴄʟɪᴄᴋ ᴏɴ ᴄᴏɴᴛᴀᴄᴛ ʜᴇʀᴇ ..!!<b></blockquote>",
            reply_markup=keyboard
        )
    
    # Add user to database
    await Seishiro.add_user(user_id, message)
    
    try:
        # Handle deep links (encoded links)
        text = message.text
        if len(text) > 7:
            try:
                base64_string = text.split(" ", 1)[1]
                is_request = base64_string.startswith("req_")
                
                logger.info(f"Processing deep link - base64_string: {base64_string}, is_request: {is_request}")
                
                # Decode to get channel_id regardless of database status
                try:
                    if is_request:
                        base64_to_decode = base64_string[4:]  # Remove 'req_' prefix
                    else:
                        base64_to_decode = base64_string
                    
                    # Use the decode function from helper_func.py
                    decoded_string = await decode(base64_to_decode)
                    channel_id = int(decoded_string)
                    logger.info(f"Decoded channel_id from link: {channel_id}")
                    
                except Exception as decode_error:
                    logger.error(f"Failed to decode base64 string '{base64_string}': {decode_error}")
                    return await message.reply_text(
                        "<b><blockquote expandable>›› Iɴᴠᴀʟɪᴅ ᴏʀ ᴇxᴘɪʀᴇᴅ ɪɴᴠɪᴛᴇ ʟɪɴᴋ.</blockquote></b>",
                        parse_mode=ParseMode.HTML
                    )
                
                # Verify channel_id is valid (negative number for channels/groups)
                if not channel_id or (channel_id > 0):
                    logger.error(f"Invalid channel_id decoded: {channel_id}")
                    return await message.reply_text(
                        "<b><blockquote expandable>›› Iɴᴠᴀʟɪᴅ ᴏʀ ᴇxᴘɪʀᴇᴅ ɪɴᴠɪᴛᴇ ʟɪɴᴋ.</blockquote></b>",
                        parse_mode=ParseMode.HTML
                    )
                
                # Ensure channel exists in database
                channel_exists = await Seishiro.channel_data.find_one({"channel_id": channel_id})
                if not channel_exists:
                    logger.info(f"Channel {channel_id} not in database, adding it now")
                    await Seishiro.save_channel(channel_id)
                
                # Update the encoded link in database
                if is_request:
                    await Seishiro.save_encoded_link2(channel_id, base64_to_decode)
                else:
                    await Seishiro.save_encoded_link(channel_id)
                
                # Check if original link exists
                original_link = await Seishiro.get_original_link(channel_id)
                if original_link:
                    button = InlineKeyboardMarkup(
                        [[InlineKeyboardButton("• ᴄʟɪᴄᴋ ʜᴇʀᴇ •", url=original_link)]]
                    )
                    return await message.reply_text(
                        "<b><blockquote expandable>≡ Nᴏᴛᴇ : Hᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ ! ᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ᴛᴏ ᴘʀᴏᴄᴇᴇᴅ</blockquote></b>",
                        reply_markup=button,
                        parse_mode=ParseMode.HTML
                    )

                async with channel_locks[channel_id]:
                    # Check if we already have a valid link
                    old_link_info = await Seishiro.get_current_invite_link(channel_id)
                    current_time = datetime.now()
                    
                    # Initialize variables
                    invite_link = None
                    is_request_link = is_request
                    
                    if old_link_info:
                        # Get link creation time from database
                        channel_data = await Seishiro.channel_data.find_one({"channel_id": channel_id})
                        link_created_time = channel_data.get("invite_link_created_at") if channel_data else None
                        
                        if link_created_time and (current_time - link_created_time).total_seconds() < 240:  # 4 minutes
                            # Use existing link
                            invite_link = old_link_info["invite_link"]
                            is_request_link = old_link_info["is_request"]
                            logger.info(f"Reusing existing link for channel {channel_id}")
                        else:
                            # Revoke old link and create new one
                            try:
                                await client.revoke_chat_invite_link(channel_id, old_link_info["invite_link"])
                                logger.info(f"Revoked old {'request' if old_link_info['is_request'] else 'invite'} link for channel {channel_id}")
                            except Exception as e:
                                logger.warning(f"Failed to revoke old link for channel {channel_id}: {e}")
                    
                    # Create new invite link if needed
                    if not invite_link:
                        try:
                            invite = await client.create_chat_invite_link(
                                chat_id=channel_id,
                                expire_date=datetime.now() + timedelta(minutes=5),
                                creates_join_request=is_request
                            )
                            invite_link = invite.invite_link
                            await Seishiro.save_invite_link(channel_id, invite_link, is_request_link)
                            logger.info(f"Created new {'request' if is_request else 'invite'} link for channel {channel_id}")
                        except Exception as e:
                            logger.error(f"Error creating invite link for channel {channel_id}: {e}")
                            return await message.reply_text(
                                "<b><blockquote expandable>Failed to generate invite link. Please try again later.</blockquote></b>",
                                parse_mode=ParseMode.HTML
                            )
                    
                    button = InlineKeyboardMarkup([[InlineKeyboardButton("• ᴄʟɪᴄᴋ ʜᴇʀᴇ •", url=invite_link)]])
                    
                    wait_msg = await message.reply_text(
                        "<pre>待 っ て</pre>",
                        parse_mode=ParseMode.HTML
                    )
                    
                    await asyncio.sleep(0.5)
                    await wait_msg.delete()
                    
                    link_share_msg = await message.reply_text(
                        "<b><blockquote expandable>≡ Nᴏᴛᴇ : Hᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ ! ᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ᴛᴏ ᴘʀᴏᴄᴇᴇᴅ</blockquote></b>",
                        reply_markup=button,
                        parse_mode=ParseMode.HTML
                    )
                    
                    note_msg = await message.reply_text(
                        "<b><blockquote>◈ Dᴜᴇ ᴛᴏ Cᴏᴘʏʀɪɢʜᴛ ɪssᴜᴇs....</blockquote></b>\n<blockquote><b>›› Tʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ ɪɴ ғᴇᴡ ᴍɪɴᴜᴛᴇs. Iғ ᴛʜᴇ ʟɪɴᴋ ɪs ᴇxᴘɪʀᴇᴅ so ᴛʀʏ ᴀɢᴀɪɴ.</b></blockquote>",
                        parse_mode=ParseMode.HTML
                    )
                    
                    asyncio.create_task(delete_after_delay(note_msg, 300))
                    asyncio.create_task(delete_after_delay(link_share_msg, 900))
                    asyncio.create_task(revoke_invite_after_5_minutes(client, channel_id, invite_link, is_request))
                
            except Exception as e:
                logger.error(f"Error processing deep link: {e}")
                await message.reply_text(
                    "<b><blockquote expandable>›› Iɴᴠᴀʟɪᴅ ᴏʀ ᴇxᴘɪʀᴇᴅ ɪɴᴠɪᴛᴇ ʟɪɴᴋ.</blockquote></b>",
                    parse_mode=ParseMode.HTML
                )
                # Normal /start (no deep link)
        else:
            user_id = message.from_user.id

            # Check if user is owner or admin in database
            is_admin = (user_id == OWNER_ID) or await Seishiro.is_admin(user_id)

            if is_admin:
                # Show Settings button for admins/owner
                inline_buttons = InlineKeyboardMarkup(
                    [
                        [   InlineKeyboardButton("ᴄᴏᴘʏʀɪɢʜᴛ ʟᴀᴡ", callback_data="help")
                        ],
                        [
                            InlineKeyboardButton("ᴀʙᴏᴜᴛ", callback_data="about"),
                            InlineKeyboardButton("ᴅᴇᴠ", user_id=(6266529037))
                        ],
                        [
                            InlineKeyboardButton("Sᴇᴛᴛɪɴɢs", callback_data="settings_main")
                        ]
                    ]
                )
            else:
                # Hide Settings for normal users
                inline_buttons = InlineKeyboardMarkup(
                    [
                        [   InlineKeyboardButton("ᴄᴏᴘʏʀɪɢʜᴛ ʟᴀᴡ", callback_data="help")
                        ],
                        [
                            InlineKeyboardButton("ᴀʙᴏᴜᴛ", callback_data="about"),
                            InlineKeyboardButton("ᴅᴇᴠ", user_id=(6266529037))
                        ]
                    ]
                )

            try:
                await message.reply_photo(
                    photo=START_PIC,
                    caption=START_MSG.format(
                        first=message.from_user.first_name,
                        last=message.from_user.last_name or "",
                        username="@" + message.from_user.username if message.from_user.username else None,
                        mention=message.from_user.mention,
                        id=message.from_user.id,
                        message_effect_id=5104841245755180586 #🔥
                    ),
                    reply_markup=inline_buttons
                )
            except Exception as e:
                logger.warning(f"Failed to send start photo: {e}")
                await message.reply_text(
                    START_MSG.format(
                        first=message.from_user.first_name,
                        last=message.from_user.last_name or "",
                        username="@" + message.from_user.username if message.from_user.username else None,
                        mention=message.from_user.mention,
                        id=message.from_user.id
                    ),
                    reply_markup=inline_buttons
                )

    except Exception as e:
        logger.error(f"FATAL ERROR in start_command: {e}", exc_info=True)
        await message.reply_text(
            f"<b>An unexpected error occurred. Please try again later.</b>\n\n"
            f"<blockquote>If this persists, contact support.</blockquote>",
            parse_mode=ParseMode.HTML
        )
                
@Bot.on_message(filters.command("broadcast") & filters.private & admin)
async def broadcast_handler(bot: Client, m: Message):
    try:
        # Check if command is used as a reply
        if not m.reply_to_message:
            return await m.reply_text(
                "<b>⚠️ Pʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ ɪᴛ!</b>\n\n"
                "<i>Usᴀɢᴇ: Rᴇᴘʟʏ ᴛᴏ ᴀɴʏ ᴍᴇssᴀɢᴇ ᴀɴᴅ ᴜsᴇ /broadcast</i>",
                parse_mode=ParseMode.HTML
            )
        
        try:
            all_users = await Seishiro.get_all_users()
        except Exception as e:
            logger.error(f"Error fetching users from database: {e}")
            return await m.reply_text(
                "<b>❌ Eʀʀᴏʀ ғᴇᴛᴄʜɪɴɢ ᴜsᴇʀs ғʀᴏᴍ ᴅᴀᴛᴀʙᴀsᴇ!</b>",
                parse_mode=ParseMode.HTML
            )
        
        broadcast_msg = m.reply_to_message
        
        try:
            sts_msg = await m.reply_text("Bʀᴏᴀᴅᴄᴀsᴛ Sᴛᴀʀᴛᴇᴅ...!!")
        except Exception as e:
            logger.error(f"Error sending broadcast start message: {e}")
            return
        
        done = 0
        failed = 0
        success = 0
        start_time = time.time()
        
        try:
            total_users = await Seishiro.total_users_count()
        except Exception as e:
            logger.error(f"Error getting total users count: {e}")
            total_users = 0
        
        try:
            async for user in all_users:
                try:
                    sts = await send_msg(user['_id'], broadcast_msg)
                    if sts == 200:
                        success += 1
                    else:
                        failed += 1
                    if sts == 400:
                        try:
                            await Seishiro.delete_user(user['_id'])
                        except Exception as e:
                            logger.error(f"Error deleting user {user['_id']}: {e}")
                    done += 1
                    
                    # Update status every 20 users
                    if done % 20 == 0:
                        try:
                            await sts_msg.edit(
                                f"Broadcast In Progress: \n\n"
                                f"Total Users {total_users} \n"
                                f"Completed : {done} / {total_users}\n"
                                f"Success : {success}\n"
                                f"Failed : {failed}"
                            )
                        except FloodWait as e:
                            logger.warning(f"FloodWait during status update: waiting {e.value}s")
                            await asyncio.sleep(e.value)
                        except Exception as e:
                            logger.error(f"Error updating broadcast status: {e}")
                            
                except Exception as e:
                    logger.error(f"Error processing user {user.get('_id', 'unknown')}: {e}")
                    failed += 1
                    done += 1
                    continue
            
            # Calculate completion time
            completed_in = timedelta(seconds=int(time.time() - start_time))
            
            # Send final status
            try:
                await sts_msg.edit(
                    f"Bʀᴏᴀᴅᴄᴀꜱᴛ Cᴏᴍᴩʟᴇᴛᴇᴅ: \n"
                    f"Cᴏᴍᴩʟᴇᴛᴇᴅ Iɴ {completed_in}.\n\n"
                    f"Total Users {total_users}\n"
                    f"Completed: {done} / {total_users}\n"
                    f"Success: {success}\n"
                    f"Failed: {failed}"
                )
            except Exception as e:
                logger.error(f"Error sending final broadcast status: {e}")
                # Try sending as new message if edit fails
                try:
                    await m.reply_text(
                        f"Bʀᴏᴀᴅᴄᴀꜱᴛ Cᴏᴍᴩʟᴇᴛᴇᴅ: \n"
                        f"Cᴏᴍᴩʟᴇᴛᴇᴅ Iɴ {completed_in}.\n\n"
                        f"Total Users {total_users}\n"
                        f"Completed: {done} / {total_users}\n"
                        f"Success: {success}\n"
                        f"Failed: {failed}"
                    )
                except Exception as e2:
                    logger.error(f"Error sending fallback broadcast status: {e2}")
                    
        except Exception as e:
            logger.error(f"Critical error during broadcast loop: {e}")
            try:
                await sts_msg.edit(
                    f"<b>❌ Bʀᴏᴀᴅᴄᴀsᴛ Fᴀɪʟᴇᴅ!</b>\n\n"
                    f"Completed: {done}\n"
                    f"Success: {success}\n"
                    f"Failed: {failed}\n\n"
                    f"<blockquote expandable><b>Eʀʀᴏʀ:</b> {str(e)}</blockquote>",
                    parse_mode=ParseMode.HTML
                )
            except:
                pass
                
    except Exception as e:
        logger.error(f"Fatal error in broadcast_handler: {e}")
        try:
            await m.reply_text(
                f"<b>❌ Aɴ ᴜɴᴇxᴘᴇᴄᴛᴇᴅ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ! {e}</b>\n\n"
                f"<i>Pʟᴇᴀsᴇ ᴄᴏɴᴛᴀᴄᴛ ᴛʜᴇ ᴅᴇᴠᴇʟᴏᴘᴇʀ.</i>",
                parse_mode=ParseMode.HTML
            )
        except:
            pass

async def send_msg(user_id, message):
    try:
        await message.copy(chat_id=int(user_id))
        return 200
    except FloodWait as e:
        logger.warning(f"FloodWait for user {user_id}: waiting {e.value}s")
        await asyncio.sleep(e.value)
        return await send_msg(user_id, message)
    except InputUserDeactivated:
        logger.info(f"{user_id} : Deactivated")
        return 400
    except UserIsBlocked:
        logger.info(f"{user_id} : Blocked The Bot")
        return 400
    except PeerIdInvalid:
        logger.info(f"{user_id} : User ID Invalid")
        return 400
    except RPCError as e:
        logger.error(f"{user_id} : RPC Error - {e}")
        return 500
    except Exception as e:
        logger.error(f"{user_id} : Unexpected error - {e}")
        return 500

async def delete_after_delay(msg, delay):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except:
        pass
