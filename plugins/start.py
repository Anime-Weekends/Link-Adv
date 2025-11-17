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

from bot import Bot
from datetime import datetime, timedelta
from config import *
from database.database import Seishiro
from plugins.newpost import revoke_invite_after_5_minutes
from helper_func import *

logger = logging.getLogger(__name__)

# Initialize chat_data_cache
chat_data_cache = {}

channel_locks = defaultdict(Lock)

async def check_admin(filter, client, update):
    try:
        user_id = update.from_user.id
        return any([user_id == OWNER_ID, await is_admin_filter(user_id)])
    except Exception as e:
        logger.error(f"Exception in check_admin: {e}")
        return False

admin = filters.create(check_admin)

# Admin filter
is_owner_or_admin = admin

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
    
@Bot.on_message(filters.command('start') & filters.private)
async def start_command(client: Bot, message: Message):
    user_id = message.from_user.id
    
    # Check if user is banned
    user = await Seishiro.is_user_banned(user_id)
    if user:
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Cᴏɴᴛᴀᴄᴛ ʜᴇʀᴇ...!!", url="https://t.me/rexbots_official")]]
        )
        return await message.reply_text(
            "Wᴛғ ʏᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ ғʀᴏᴍ ᴜsɪɴɢ ᴍᴇ ʙʏ ᴏᴜʀ ᴀᴅᴍɪɴ/ᴏᴡɴᴇʀ . Iғ ʏᴏᴜ ᴛʜɪɴᴋs ɪᴛ's ᴍɪsᴛᴀᴋᴇ ᴄʟɪᴄᴋ ᴏɴ ᴄᴏɴᴛᴀᴄᴛ ʜᴇʀᴇ...!!",
            reply_markup=keyboard
        )
    
    # Add user to database
    await Seishiro.add_user(user_id, message)
    
    try:
        # Check subscription status
        is_sub_status = await is_subscribed(client, user_id)
        logger.debug(f"User {user_id} subscribed status: {is_sub_status}")
        
        if not is_sub_status:
            logger.debug(f"User {user_id} is not subscribed, calling not_joined.")
            return await not_joined(client, message)
        
        logger.debug(f"User {user_id} is subscribed, proceeding with start message.")
        
        # Handle deep links (encoded links)
        text = message.text
        if len(text) > 7:
            try:
                base64_string = text.split(" ", 1)[1]
                is_request = base64_string.startswith("req_")
                
                if is_request:
                    base64_string = base64_string[4:]
                    channel_id = await Seishiro.get_channel_by_encoded_link2(base64_string)
                else:
                    channel_id = await Seishiro.get_channel_by_encoded_link(base64_string)
                
                if not channel_id:
                    return await message.reply_text(
                        "<b><blockquote expandable>Invalid or expired invite link.</blockquote></b>",
                        parse_mode=ParseMode.HTML
                    )
                
                # Check if original link exists
                original_link = await Seishiro.get_original_link(channel_id)
                if original_link:
                    button = InlineKeyboardMarkup(
                        [[InlineKeyboardButton("• ᴄʟɪᴄᴋ ʜᴇʀᴇ •", url=original_link)]]
                    )
                    return await message.reply_text(
                        "<b><blockquote expandable>ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ! ᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ᴛᴏ ᴘʀᴏᴄᴇᴇᴅ</blockquote></b>",
                        reply_markup=button,
                        parse_mode=ParseMode.HTML
                    )

                async with channel_locks[channel_id]:
                    # Check if we already have a valid link
                    old_link_info = await get_current_invite_link(channel_id)
                    current_time = datetime.now()
                    
                    if old_link_info:
                        link_created_time = await get_link_creation_time(channel_id)
                        if link_created_time and (current_time - link_created_time).total_seconds() < 240:  # 4 minutes
                            # Use existing link
                            invite_link = old_link_info["invite_link"]
                            is_request_link = old_link_info["is_request"]
                        else:
                            # Revoke old link and create new one
                            try:
                                await client.revoke_chat_invite_link(channel_id, old_link_info["invite_link"])
                                print(f"Revoked old {'request' if old_link_info['is_request'] else 'invite'} link for channel {channel_id}")
                            except Exception as e:
                                print(f"Failed to revoke old link for channel {channel_id}: {e}")
                    
                    # Create new invite link
                    invite = await client.create_chat_invite_link(
                        chat_id=channel_id,
                        expire_date=datetime.now() + timedelta(minutes=5),
                        creates_join_request=is_request
                    )
                    invite_link = invite.invite_link
                    is_request_link = is_request
                    await Seishiro.save_invite_link(channel_id, invite.invite_link, is_request)
                    
                    button = InlineKeyboardMarkup([[InlineKeyboardButton("• ᴄʟɪᴄᴋ ʜᴇʀᴇ •", url=invite.invite_link)]])
                    
                    wait_msg = await message.reply_text(
                        "<b>ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ...</b>",
                        parse_mode=ParseMode.HTML
                    )
                    
                    await asyncio.sleep(0.5)
                    await wait_msg.delete()
                    
                    link_share_msg = await message.reply_text(
                        "<b><blockquote expandable>ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ! ᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ᴛᴏ ᴘʀᴏᴄᴇᴇᴅ</blockquote></b>",
                        reply_markup=button,
                        parse_mode=ParseMode.HTML
                    )
                    
                    note_msg = await message.reply_text(
                        "<b><u>ɴᴏᴛᴇ</u>:-</b>\n\n<blockquote><b>Iғ ᴛʜᴇ ʟɪɴᴋ ɪs ᴇxᴘɪʀᴇᴅ so ᴛʀʏ ᴀɢᴀɪɴ.Tʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ ɪɴ ғᴇᴡ ᴍɪɴᴜᴛᴇs</b></blockquote>",
                        parse_mode=ParseMode.HTML
                    )
                    
                    asyncio.create_task(delete_after_delay(note_msg, 300))
                    asyncio.create_task(delete_after_delay(link_share_msg, 900))
                    asyncio.create_task(revoke_invite_after_5_minutes(client, channel_id, invite.invite_link, is_request))
                
            except Exception as e:
                await message.reply_text(
                    "<b><blockquote expandable>Invalid or expired invite link.</blockquote></b>",
                    parse_mode=ParseMode.HTML
                )
                print(f"Decoding error: {e}")
        else:
            # Show start menu
            inline_buttons = InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("• ᴀʙᴏᴜᴛ", callback_data="about"),
                     InlineKeyboardButton("Hᴇʟᴘ •", callback_data="help")]
                ]
            )
            
            try:
                await message.reply_photo(
                    photo=START_PIC,
                    caption=START_MSG,
                    reply_markup=inline_buttons,
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                print(f"Error sending start picture: {e}")
                await message.reply_text(
                    START_MSG,
                    reply_markup=inline_buttons,
                    parse_mode=ParseMode.HTML
                )
    
    except Exception as e:
        logger.error(f"FATAL ERROR in start_command: {e}")
        await message.reply_text(f"An unexpected error occurred: {e}. Please contact the developer.")

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
