import asyncio
import base64
import re
from datetime import date, datetime, timedelta
from bot import Bot
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, InputMediaPhoto
from pyrogram.errors import UserNotParticipant, FloodWait, ChatAdminRequired, RPCError, PeerIdInvalid
from pyrogram.errors import InviteHashExpired, InviteRequestSent
from database.database import Seishiro
from config import *
from helper_func import *
from pyrogram.enums import ParseMode, ChatMemberStatus

PAGE_SIZE = 6

# Revoke invite link after 5 minutes
async def revoke_invite_after_5_minutes(client: Bot, channel_id: int, link: str, is_request: bool = False):
    await asyncio.sleep(300)
    try:
        await client.revoke_chat_invite_link(channel_id, link)
        print(f"{'Jᴏɪɴ ʀᴇǫᴜᴇsᴛ' if is_request else 'Iɴᴠɪᴛᴇ'} ʟɪɴᴋ ʀᴇᴠᴏᴋᴇᴅ ғᴏʀ ᴄʜᴀɴɴᴇʟ {channel_id}")
    except Exception as e:
        print(f"Fᴀɪʟᴇᴅ ᴛᴏ ʀᴇᴠᴏᴋᴇ ɪɴᴠɪᴛᴇ ғᴏʀ ᴄʜᴀɴɴᴇʟ {channel_id}: {e}")

# Settings command to show the main menu
@Bot.on_message(filters.command('settings') & filters.private & is_owner_or_admin)
async def settings_command(client: Client, message: Message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Aᴅᴅ Cʜᴀɴɴᴇʟ", callback_data="add_channel")],
        [InlineKeyboardButton("Dᴇʟᴇᴛᴇ Cʜᴀɴɴᴇʟ", callback_data="delete_channel")],
        [InlineKeyboardButton("Vɪᴇᴡ Nᴏʀᴍᴀʟ Cʜᴀɴɴᴇʟ Lɪɴᴋs", callback_data="channel_links")],
        [InlineKeyboardButton("Vɪᴇᴡ Rᴇǫᴜᴇsᴛ Cʜᴀɴɴᴇʟ Lɪɴᴋs", callback_data="request_links")],
        [InlineKeyboardButton("Lɪsᴛ Cʜᴀɴɴᴇʟs", callback_data="list_channels")],
        [InlineKeyboardButton("ᴀᴅᴍɪɴ sᴇᴛᴛɪɴɢs", callback_data="admin_bna_system")],
        [InlineKeyboardButton("Bᴀɴ sᴇᴛᴛɪɴɢs", callback_data="ban_menu")],
        [InlineKeyboardButton("Fsᴜʙ sᴇᴛᴛɪɴɢs", callback_data="fsub_settings_menu")],
        [InlineKeyboardButton("• Cʟᴏsᴇ •", callback_data="close")]
    ])
    await message.reply_text(
        "<b>Channel Mᴀɴᴀɢᴇᴍᴇɴᴛ Mᴇɴᴜ:\n\nSᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ʙᴇʟᴏᴡ ᴛᴏ ᴍᴀɴᴀɢᴇ ᴄʜᴀɴɴᴇʟs:</b>",
        reply_markup=keyboard
    )

# Callback query handler for settings
@Bot.on_callback_query()
async def settings_callback(client: Bot, callback_query):
    user_id = callback_query.from_user.id
    cb_data = callback_query.data
    print(f"Callback received: {cb_data} from user {user_id}")

    try:
        is_admin_user = user_id == OWNER_ID or await Seishiro.is_admin(user_id)

        # Main Settings Menu
        if cb_data == "settings_main":
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Aᴅᴅ Cʜᴀɴɴᴇʟ", callback_data="add_channel")],
                [InlineKeyboardButton("Dᴇʟᴇᴛᴇ Cʜᴀɴɴᴇʟ", callback_data="delete_channel")],
                [InlineKeyboardButton("Cʜᴀɴɴᴇʟ Lɪɴᴋs", callback_data="channel_links")],
                [InlineKeyboardButton("Rᴇǫᴜᴇsᴛ Lɪɴᴋs", callback_data="request_links")],
                [InlineKeyboardButton("Lɪsᴛ Cʜᴀɴɴᴇʟs", callback_data="list_channels")],
                [InlineKeyboardButton("ᴀᴅᴍɪɴ sᴇᴛᴛɪɴɢs", callback_data="admin_bna_system")],
                [InlineKeyboardButton("Bᴀɴ sᴇᴛᴛɪɴɢs", callback_data="ban_menu")],
                [InlineKeyboardButton("Fsᴜʙ sᴇᴛᴛɪɴɢs", callback_data="fsub_settings_menu")],
                [InlineKeyboardButton("• Cʟᴏsᴇ •", callback_data="close")]
            ])
            await callback_query.message.edit_text(
                "<b>Channel Mᴀɴᴀɢᴇᴍᴇɴᴛ Mᴇɴᴜ:\n\nSᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ʙᴇʟᴏᴡ ᴛᴏ ᴍᴀɴᴀɢᴇ ᴄʜᴀɴɴᴇʟs:</b>",
                reply_markup=keyboard
            )

        elif cb_data == "close":
            await callback_query.message.delete()
            try:
                await callback_query.message.reply_to_message.delete()
            except:
                pass
        
        elif cb_data == "about":
            user = await client.get_users(OWNER_ID)
            await callback_query.edit_message_media(
                InputMediaPhoto(
                    "https://envs.sh/Wdj.jpg",
                    ABOUT_TXT
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton('• ʙᴀᴄᴋ', callback_data='start'), 
                     InlineKeyboardButton('ᴄʟᴏsᴇ •', callback_data='close')]
                ])
            )

        elif cb_data == "help":
            await callback_query.edit_message_media(
                InputMediaPhoto(
                    "https://envs.sh/Wdj.jpg",
                    HELP_TXT
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton('• ʙᴀᴄᴋ', callback_data='start'), 
                     InlineKeyboardButton('ᴄʟᴏsᴇ •', callback_data='close')]
                ])
            )
        
        elif cb_data == "start":
            inline_buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("• ᴀʙᴏᴜᴛ", callback_data="about"),
                 InlineKeyboardButton("ʜᴇʟᴘ •", callback_data="help")]
            ])
            try:
                await callback_query.edit_message_media(
                    InputMediaPhoto(START_PIC, START_MSG),
                    reply_markup=inline_buttons
                )
            except Exception as e:
                print(f"Error sending start/home photo: {e}")
                await callback_query.edit_message_text(
                    START_MSG,
                    reply_markup=inline_buttons,
                    parse_mode=ParseMode.HTML
                )

        # Ban Menu
        elif cb_data == "ban_menu":
            if not is_admin_user:
                await callback_query.answer("Only admins can access this!", show_alert=True)
                return
            
            btn = [
                [InlineKeyboardButton("Bᴀɴ Usᴇʀ", callback_data="ban_user"), 
                 InlineKeyboardButton("Uɴʙᴀɴ Usᴇʀ", callback_data="unban_user")],
                [InlineKeyboardButton("Bᴀɴɴᴇᴅ Lɪsᴛ", callback_data="banned_list")],
                [InlineKeyboardButton("back", callback_data="settings_main")]
            ]
            await callback_query.message.edit_text(
                "<b>Bᴀɴ Mᴀɴᴀɢᴇᴍᴇɴᴛ Pᴀɴᴇʟ:\n\nSᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ʙᴇʟᴏᴡ:</b>",
                reply_markup=InlineKeyboardMarkup(btn)
            )

        # Ban User
        elif cb_data == "ban_user":
            if not is_admin_user:
                await callback_query.answer("Only admins can ban users!", show_alert=True)
                return
            
            btn = [[InlineKeyboardButton("back", callback_data="ban_menu")]]
            await callback_query.message.edit_text(
                "<b>Sᴇɴᴅ ᴛʜᴇ ᴜsᴇʀ ID ᴡʜɪᴄʜ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ʙᴀɴ (e.g., 123456789):\n\n"
                "Yᴏᴜ ᴄᴀɴ ᴀʟsᴏ ᴘʀᴏᴠɪᴅᴇ ᴀ ʀᴇᴀsᴏɴ:\n"
                "<code>user_id reason</code>\n\n"
                "/cancel ᴛᴏ ᴄᴀɴᴄᴇʟ</b>",
                reply_markup=InlineKeyboardMarkup(btn)
            )
            
            try:
                msg = await client.listen(chat_id=callback_query.message.chat.id, timeout=300)
                await callback_query.message.delete()
                
                if msg.text == '/cancel':
                    await msg.reply("ᴄᴀɴᴄᴇʟʟᴇᴅ!", reply_markup=InlineKeyboardMarkup(btn))
                    return
                
                parts = msg.text.split(maxsplit=1)
                user_id_str = parts[0]
                reason = parts[1] if len(parts) > 1 else "No reason provided"
                
                if not user_id_str.lstrip('-').isdigit():
                    await msg.reply(
                        "<b><blockquote expandable>Iɴᴠᴀʟɪᴅ ᴜsᴇʀ ID. Pʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ.</blockquote></b>",
                        reply_markup=InlineKeyboardMarkup(btn)
                    )
                    return
                
                ban_user_id = int(user_id_str)
                
                await Seishiro.ban_data.update_one(
                    {"_id": ban_user_id},
                    {"$set": {
                        "ban_status.is_banned": True,
                        "ban_status.ban_reason": reason,
                        "ban_status.banned_on": date.today().isoformat()
                    }},
                    upsert=True
                )
                
                await msg.reply(
                    f"<b>Usᴇʀ - `{ban_user_id}` Is sᴜᴄᴄᴇssғᴜʟʟʏ ʙᴀɴɴᴇᴅ. Success\nRᴇᴀsᴏɴ:- {reason}</b>",
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            except asyncio.TimeoutError:
                await callback_query.message.reply(
                    "<b>Tɪᴍᴇᴏᴜᴛ! Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ.</b>",
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            except Exception as e:
                print(f"Error banning user: {e}")
                await msg.reply(f"Uɴᴇxᴘᴇᴄᴛᴇᴅ Eʀʀᴏʀ: {str(e)}", reply_markup=InlineKeyboardMarkup(btn))

        # Unban User
        elif cb_data == "unban_user":
            if not is_admin_user:
                await callback_query.answer("Only admins can unban users!", show_alert=True)
                return
            
            btn = [[InlineKeyboardButton("back", callback_data="ban_menu")]]
            await callback_query.message.edit_text(
                "<b>Sᴇɴᴅ ᴛʜᴇ ᴜsᴇʀ ID ᴛᴏ ᴜɴʙᴀɴ (e.g., 123456789):\n\n/cancel ᴛᴏ ᴄᴀɴᴄᴇʟ</b>",
                reply_markup=InlineKeyboardMarkup(btn)
            )
            
            try:
                msg = await client.listen(chat_id=callback_query.message.chat.id, timeout=300)
                await callback_query.message.delete()
                
                if msg.text == '/cancel':
                    await msg.reply("ᴄᴀɴᴄᴇʟʟᴇᴅ!", reply_markup=InlineKeyboardMarkup(btn))
                    return
                
                if not msg.text.lstrip('-').isdigit():
                    await msg.reply(
                        "<b><blockquote expandable>Iɴᴠᴀʟɪᴅ ᴜsᴇʀ ID. Pʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ.</blockquote></b>",
                        reply_markup=InlineKeyboardMarkup(btn)
                    )
                    return
                
                unban_user_id = int(msg.text)
                
                result = await Seishiro.ban_data.update_one(
                    {"_id": unban_user_id},
                    {"$set": {
                        "ban_status.is_banned": False,
                        "ban_status.ban_reason": "",
                        "ban_status.banned_on": None
                    }}
                )
                
                if result.matched_count == 0:
                    await msg.reply(
                        f"<b>Usᴇʀ - `{unban_user_id}` ɴᴏᴛ ғᴏᴜɴᴅ ɪɴ ᴅᴀᴛᴀʙᴀsᴇ.</b>",
                        reply_markup=InlineKeyboardMarkup(btn)
                    )
                else:
                    await msg.reply(
                        f"<b>Usᴇʀ - `{unban_user_id}` Is sᴜᴄᴄᴇssғᴜʟʟʏ ᴜɴʙᴀɴɴᴇᴅ. Success</b>",
                        reply_markup=InlineKeyboardMarkup(btn)
                    )
            except asyncio.TimeoutError:
                await callback_query.message.reply(
                    "<b>Tɪᴍᴇᴏᴜᴛ! Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ.</b>",
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            except Exception as e:
                print(f"Error unbanning user: {e}")
                await msg.reply(f"Uɴᴇxᴘᴇᴄᴛᴇᴅ Eʀʀᴏʀ: {str(e)}", reply_markup=InlineKeyboardMarkup(btn))

        # Banned List - FIXED: Removed reply_markup from answer()
        elif cb_data == "banned_list":
            if not is_admin_user:
                await callback_query.answer("Only admins can view banned list!", show_alert=True)
                return
            
            await callback_query.answer("Pʟᴇᴀsᴇ ᴡᴀɪᴛ...")
            
            try:
                cursor = Seishiro.ban_data.find({"ban_status.is_banned": True})
                lines = []
                
                async for user in cursor:
                    uid = user['_id']
                    reason = user.get('ban_status', {}).get('ban_reason', 'No reason')
                    try:
                        user_obj = await client.get_users(uid)
                        name = user_obj.mention
                    except PeerIdInvalid:
                        name = f"`{uid}` (Name not found)"
                    except Exception:
                        name = f"`{uid}`"
                    lines.append(f"• {name} - {reason}")
                
                btn = [[InlineKeyboardButton("back", callback_data="ban_menu")]]
                
                if not lines:
                    await callback_query.message.edit_text(
                        "<b>Nᴏ ᴜsᴇʀ(s) ɪs ᴄᴜʀʀᴇɴᴛʟʏ ʙᴀɴɴᴇᴅ</b>",
                        reply_markup=InlineKeyboardMarkup(btn)
                    )
                else:
                    await callback_query.message.edit_text(
                        "Bᴀɴɴᴇᴅ ᴜsᴇʀ(s)\n\n" + "\n".join(lines[:50]),
                        reply_markup=InlineKeyboardMarkup(btn)
                    )
            except Exception as e:
                btn = [[InlineKeyboardButton("back", callback_data="ban_menu")]]
                await callback_query.message.edit_text(
                    f"<b>An error occurred while fetching banned users:</b> `{e}`",
                    reply_markup=InlineKeyboardMarkup(btn)
                )

        # Fsub Settings Menu
        elif cb_data == "fsub_settings_menu":
            if not is_admin_user:
                await callback_query.answer("Only admins can access this!", show_alert=True)
                return
            
            btn = [
                [InlineKeyboardButton("Aᴅᴅ Fsᴜʙ Cʜᴀɴɴᴇʟ", callback_data="add_fsub_channel")],
                [InlineKeyboardButton("Rᴇᴍᴏᴠᴇ Fsᴜʙ Cʜᴀɴɴᴇʟ", callback_data="delete_fsub_channel")],
                [InlineKeyboardButton("Lɪsᴛ Fsᴜʙ Cʜᴀɴɴᴇʟs", callback_data="list_fsub_channels")],
                [InlineKeyboardButton("Aʟʟ Cʜᴀɴɴᴇʟs", callback_data="fsub_all_channels")],
                [InlineKeyboardButton("Pᴀʀᴛɪᴄᴜʟᴀʀʟʏ", callback_data="fsub_particular")],
                [InlineKeyboardButton("back", callback_data="settings_main")]
            ]
            await callback_query.message.edit_text(
                "<b>Fsᴜʙ Sᴇᴛᴛɪɴɢs Mᴇɴᴜ:\n\n"
                "• <b>Aᴅᴅ Fsᴜʙ Cʜᴀɴɴᴇʟ</b> - Add a channel to fsub list\n"
                "• <b>Rᴇᴍᴏᴠᴇ Fsᴜʙ Cʜᴀɴɴᴇʟ</b> - Remove a channel from fsub list\n"
                "• <b>Lɪsᴛ Fsᴜʙ Cʜᴀɴɴᴇʟs</b> - View all channels in fsub list\n"
                "• <b>Aʟʟ Cʜᴀɴɴᴇʟs</b> - Enable/Disable request fsub for all channels at once\n"
                "• <b>Pᴀʀᴛɪᴄᴜʟᴀʀʟʏ</b> - Toggle request fsub for specific channels\n\n"
                "Sᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ʙᴇʟᴏᴡ:</b>",
                reply_markup=InlineKeyboardMarkup(btn)
            )

        # All Channels Toggle
        elif cb_data == "fsub_all_channels":
            if not is_admin_user:
                await callback_query.answer("Only admins can access this!", show_alert=True)
                return
            
            fsub_channels = await Seishiro.get_fsub_channels()
            
            if not fsub_channels:
                await callback_query.answer("No fsub channels found! Add channels first.", show_alert=True)
                return
            
            btn = [
                [InlineKeyboardButton("Eɴᴀʙʟᴇ Aʟʟ", callback_data="fsub_enable_all"),
                 InlineKeyboardButton("Dɪsᴀʙʟᴇ Aʟʟ", callback_data="fsub_disable_all")],
                [InlineKeyboardButton("back", callback_data="fsub_settings_menu")]
            ]
            
            await callback_query.message.edit_text(
                f"<b>Aʟʟ Cʜᴀɴɴᴇʟs Cᴏɴᴛʀᴏʟ\n\n"
                f"Tᴏᴛᴀʟ Fsᴜʙ Cʜᴀɴɴᴇʟs: {len(fsub_channels)}\n\n"
                f"Cʜᴏᴏsᴇ ᴀɴ ᴀᴄᴛɪᴏɴ:</b>",
                reply_markup=InlineKeyboardMarkup(btn)
            )

        # Enable All Channels
        elif cb_data == "fsub_enable_all":
            if not is_admin_user:
                await callback_query.answer("Only admins can perform this action!", show_alert=True)
                return
            
            await callback_query.answer("Enabling request fsub for all channels...")
            
            try:
                result = await Seishiro.set_channel_mode_all("on")
                
                btn = [[InlineKeyboardButton("back", callback_data="fsub_all_channels")]]
                await callback_query.message.edit_text(
                    f"<b>Rᴇǫᴜᴇsᴛ Fsᴜʙ Eɴᴀʙʟᴇᴅ!\n\n{result['message']}</b>",
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            except Exception as e:
                btn = [[InlineKeyboardButton("back", callback_data="fsub_all_channels")]]
                await callback_query.message.edit_text(
                    f"<b>Eʀʀᴏʀ: {str(e)}</b>",
                    reply_markup=InlineKeyboardMarkup(btn)
                )

        # Disable All Channels
        elif cb_data == "fsub_disable_all":
            if not is_admin_user:
                await callback_query.answer("Only admins can perform this action!", show_alert=True)
                return
            
            await callback_query.answer("Disabling request fsub for all channels...")
            
            try:
                result = await Seishiro.set_channel_mode_all("off")
                
                btn = [[InlineKeyboardButton("back", callback_data="fsub_all_channels")]]
                await callback_query.message.edit_text(
                    f"<b>Rᴇǫᴜᴇsᴛ Fsᴜʙ Dɪsᴀʙʟᴇᴅ!\n\n{result['message']}</b>",
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            except Exception as e:
                btn = [[InlineKeyboardButton("back", callback_data="fsub_all_channels")]]
                await callback_query.message.edit_text(
                    f"<b>Eʀʀᴏʀ: {str(e)}</b>",
                    reply_markup=InlineKeyboardMarkup(btn)
                )

        # Particular Fsub Channel Management
        elif cb_data == "fsub_particular":
            if not is_admin_user:
                await callback_query.answer("Only admins can access this!", show_alert=True)
                return
            
            channels = await Seishiro.get_fsub_channels()
            if not channels:
                await callback_query.answer("No fsub channels found!", show_alert=True)
                return
            
            buttons = []
            for cid in channels:
                try:
                    chat = await client.get_chat(cid)
                    mode = await Seishiro.get_channel_mode(cid)
                    status = "ON" if mode == "on" else "OFF"
                    buttons.append([InlineKeyboardButton(
                        f"{status} {chat.title}", 
                        callback_data=f"rfs_ch_{cid}"
                    )])
                except Exception as e:
                    print(f"Error fetching channel {cid}: {e}")
                    continue

            buttons.append([InlineKeyboardButton("back", callback_data="fsub_settings_menu")])
            
            await callback_query.message.edit_text(
                "sᴇʟᴇᴄᴛ ᴀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴛᴏɢɢʟᴇ ɪᴛs ғᴏʀᴄᴇ-sᴜʙ ᴍᴏᴅᴇ:",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        # Handle specific channel fsub toggle
        elif cb_data.startswith("rfs_ch_"):
            cid = int(cb_data.split("_")[2])
            try:
                chat = await client.get_chat(cid)
                mode = await Seishiro.get_channel_mode(cid)
                status = "ON" if mode == "on" else "OFF"
                new_mode = "off" if mode == "on" else "on"
                buttons = [
                    [InlineKeyboardButton(
                        f"ʀᴇǫ ᴍᴏᴅᴇ {'OFF' if mode == 'on' else 'ON'}", 
                        callback_data=f"rfs_toggle_{cid}_{new_mode}"
                    )],
                    [InlineKeyboardButton("back", callback_data="fsub_particular")]
                ]
                await callback_query.message.edit_text(
                    f"Cʜᴀɴɴᴇʟ: {chat.title}\nCᴜʀʀᴇɴᴛ Fᴏʀᴄᴇ-Sᴜʙ Mᴏᴅᴇ: {status}",
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
            except Exception as e:
                await callback_query.answer("Failed to fetch channel info", show_alert=True)

        # Toggle specific channel mode
        elif cb_data.startswith("rfs_toggle_"):
            parts = cb_data.split("_")
            cid = int(parts[2])
            action = parts[3]
            mode = "on" if action == "on" else "off"

            await Seishiro.set_channel_mode(cid, mode)
            await callback_query.answer(f"Force-Sub set to {'ON' if mode == 'on' else 'OFF'}")

            # Refresh the channel's mode view
            chat = await client.get_chat(cid)
            status = "ON" if mode == "on" else "OFF"
            new_mode = "off" if mode == "on" else "on"
            buttons = [
                [InlineKeyboardButton(
                    f"ʀᴇǫ ᴍᴏᴅᴇ {'OFF' if mode == 'on' else 'ON'}", 
                    callback_data=f"rfs_toggle_{cid}_{new_mode}"
                )],
                [InlineKeyboardButton("back", callback_data="fsub_particular")]
            ]
            await callback_query.message.edit_text(
                f"Channel: {chat.title}\nCurrent Force-Sub Mode: {status}",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        # Add Fsub Channel
        elif cb_data == "add_fsub_channel":
            if not is_admin_user:
                await callback_query.answer("Only admins can add channels!", show_alert=True)
                return
            
            btn = [[InlineKeyboardButton("back", callback_data="fsub_settings_menu")]]
            await callback_query.message.edit_text(
                "<b>Sᴇɴᴅ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ID ᴡʜɪᴄʜ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴀᴅᴅ ɪɴ ғsᴜʙ (e.g., -100123456789):\n\n/cancel ᴛᴏ ᴄᴀɴᴄᴇʟ</b>",
                reply_markup=InlineKeyboardMarkup(btn)
            )
            
            try:
                msg = await client.listen(chat_id=callback_query.message.chat.id, timeout=300)
                temp = await msg.reply("<i>Pʟᴇᴀsᴇ ᴡᴀɪᴛ...</i>")
                await callback_query.message.delete()
                
                if msg.text == '/cancel':
                    await temp.edit("ᴄᴀɴᴄᴇʟʟᴇᴅ!", reply_markup=InlineKeyboardMarkup(btn))
                    return
                
                # Validate channel ID format
                if not re.match(r"^-100\d{10,}$", msg.text):
                    await temp.edit(
                        "<b><blockquote expandable>Iɴᴠᴀʟɪᴅ ᴄʜᴀɴɴᴇʟ ID. Mᴜsᴛ ʙᴇ ɪɴ ᴛʜᴇ ғᴏʀᴍᴀᴛ -100XXXXXXXXXX.</blockquote></b>",
                        reply_markup=InlineKeyboardMarkup(btn)
                    )
                    return
                
                channel_id = int(msg.text)
                
                # Check if bot is a member of the channel
                try:
                    chat_member = await client.get_chat_member(channel_id, client.me.id)
                    valid_statuses = [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
                    
                    if chat_member.status not in valid_statuses:
                        await temp.edit(
                            f"<b><blockquote expandable>I ᴀᴍ ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ ᴏғ ᴛʜɪs ᴄʜᴀɴɴᴇʟ. Sᴛᴀᴛᴜs: {chat_member.status}. Pʟᴇᴀsᴇ ᴍᴀᴋᴇ ᴍᴇ ᴀᴅᴍɪɴ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ.</blockquote></b>",
                            reply_markup=InlineKeyboardMarkup(btn)
                        )
                        return
                except UserNotParticipant:
                    await temp.edit(
                        "<b><blockquote expandable>I ᴀᴍ ɴᴏᴛ ᴀ ᴍᴇᴍʙᴇʀ ᴏғ ᴛʜɪs ᴄʜᴀɴɴᴇʟ. Pʟᴇᴀsᴇ ᴀᴅᴅ ᴍᴇ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ.</blockquote></b>",
                        reply_markup=InlineKeyboardMarkup(btn)
                    )
                    return
                except RPCError as e:
                    if "CHANNEL_INVALID" in str(e):
                        await temp.edit(
                            "<b><blockquote expandable>Iɴᴠᴀʟɪᴅ ᴄʜᴀɴɴᴇʟ ID ᴏʀ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ᴅᴏᴇs ɴᴏᴛ ᴇxɪsᴛ. Pʟᴇᴀsᴇ ᴄʜᴇᴄᴋ ᴛʜᴇ ID ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ.</blockquote></b>",
                            reply_markup=InlineKeyboardMarkup(btn)
                        )
                        return
                    print(f"RPC Error checking membership for channel {channel_id}: {e}")
                    await temp.edit(
                        f"<b><blockquote expandable>Fᴀɪʟᴇᴅ ᴛᴏ ᴠᴇʀɪғʏ ᴍᴇᴍʙᴇʀsʜɪᴘ. Eʀʀᴏʀ: {str(e)}.</blockquote></b>",
                        reply_markup=InlineKeyboardMarkup(btn)
                    )
                    return
                
                # Fetch chat details
                try:
                    chat = await client.get_chat(channel_id)
                except RPCError as e:
                    print(f"Error fetching chat {channel_id}: {e}")
                    await temp.edit(
                        f"<b><blockquote expandable>Fᴀɪʟᴇᴅ ᴛᴏ ᴀᴄᴄᴇss ᴄʜᴀɴɴᴇʟ. Eʀʀᴏʀ: {str(e)}.</blockquote></b>",
                        reply_markup=InlineKeyboardMarkup(btn)
                    )
                    return
                
                # Get invite link
                try:
                    link = await client.export_chat_invite_link(chat.id)
                except Exception:
                    link = f"https://t.me/{chat.username}" if chat.username else f"https://t.me/c/{str(chat.id)[4:]}"
                
                # Add to fsub
                await Seishiro.add_fsub_channel(channel_id)
                
                await temp.edit(
                    f"<b>Fᴏʀᴄᴇ-sᴜʙ ᴄʜᴀɴɴᴇʟ ᴀᴅᴅᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!</b>\n\n"
                    f"<b>Nᴀᴍᴇ:</b> <a href='{link}'>{chat.title}</a>\n"
                    f"<b>Iᴅ:</b> <code>{channel_id}</code>",
                    disable_web_page_preview=True,
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            except asyncio.TimeoutError:
                await callback_query.message.reply(
                    "<b>Tɪᴍᴇᴏᴜᴛ! Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ.</b>",
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            except Exception as e:
                print(f"Error adding fsub channel: {e}")
                await temp.edit(
                    f"<b>Failed to add channel:</b>\n<code>{channel_id}</code>\n\n<i>{e}</i>",
                    reply_markup=InlineKeyboardMarkup(btn)
                )

        # Remove Fsub Channel
        elif cb_data == "delete_fsub_channel":
            if not is_admin_user:
                await callback_query.answer("Only admins can delete channels!", show_alert=True)
                return
            
            btn = [[InlineKeyboardButton("back", callback_data="fsub_settings_menu")]]
            await callback_query.message.edit_text(
                "<b>Sᴇɴᴅ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ID ᴛᴏ ʀᴇᴍᴏᴠᴇ ғʀᴏᴍ ғsᴜʙ (e.g., -100123456789):\n\n/cancel ᴛᴏ ᴄᴀɴᴄᴇʟ</b>",
                reply_markup=InlineKeyboardMarkup(btn)
            )
            
            try:
                msg = await client.listen(chat_id=callback_query.message.chat.id, timeout=300)
                await callback_query.message.delete()
                
                if msg.text == '/cancel':
                    await msg.reply("ᴄᴀɴᴄᴇʟʟᴇᴅ!", reply_markup=InlineKeyboardMarkup(btn))
                    return
                
                channel_id = int(msg.text)
                await Seishiro.remove_fsub_channel(channel_id)
                await msg.reply(
                    f"<b><blockquote expandable>Cʜᴀɴɴᴇʟ {channel_id} ʜᴀs ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ.</blockquote></b>",
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            except (ValueError, IndexError):
                await msg.reply(
                    "<b><blockquote expandable>Iɴᴠᴀʟɪᴅ ᴄʜᴀɴɴᴇʟ ID. Pʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ.</blockquote></b>",
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            except Exception as e:
                print(f"Error deleting channel {msg.text}: {e}")
                await msg.reply(f"Unexpected Error: {str(e)}", reply_markup=InlineKeyboardMarkup(btn))

        # List Fsub Channels - NEW FEATURE
        elif cb_data == "list_fsub_channels":
            if not is_admin_user:
                await callback_query.answer("Only admins can view fsub channels!", show_alert=True)
                return
            
            await callback_query.answer("Fᴇᴛᴄʜɪɴɢ ғsᴜʙ ᴄʜᴀɴɴᴇʟs...")
            
            try:
                fsub_channels = await Seishiro.get_fsub_channels()
                
                btn = [[InlineKeyboardButton("back", callback_data="fsub_settings_menu")]]
                
                if not fsub_channels:
                    await callback_query.message.edit_text(
                        "<b>Nᴏ ғsᴜʙ ᴄʜᴀɴɴᴇʟs ғᴏᴜɴᴅ.\n\nPʟᴇᴀsᴇ ᴀᴅᴅ ᴄʜᴀɴɴᴇʟs ᴜsɪɴɢ 'Aᴅᴅ Fsᴜʙ Cʜᴀɴɴᴇʟ' ᴏᴘᴛɪᴏɴ.</b>",
                        reply_markup=InlineKeyboardMarkup(btn)
                    )
                    return
                
                fsub_list = "<b>Fsᴜʙ Cʜᴀɴɴᴇʟs Lɪsᴛ:</b>\n\n"
                
                for idx, channel_id in enumerate(fsub_channels, 1):
                    try:
                        chat = await client.get_chat(channel_id)
                        mode = await Seishiro.get_channel_mode(channel_id)
                        status_emoji = "ON" if mode == "on" else "OFF"
                        status_text = "Rᴇǫᴜᴇsᴛ ON" if mode == "on" else "Rᴇǫᴜᴇsᴛ OFF"
                        
                        # Try to get invite link
                        try:
                            link = await client.export_chat_invite_link(chat.id)
                            fsub_list += f"{idx}. <a href='{link}'>{chat.title}</a> {status_emoji}\n"
                        except:
                            if chat.username:
                                link = f"https://t.me/{chat.username}"
                                fsub_list += f"{idx}. <a href='{link}'>{chat.title}</a> {status_emoji}\n"
                            else:
                                fsub_list += f"{idx}. {chat.title} {status_emoji}\n"
                        
                        fsub_list += f"    <code>{channel_id}</code> - {status_text}\n\n"
                        
                    except Exception as e:
                        print(f"Error fetching channel {channel_id}: {e}")
                        fsub_list += f"{idx}. <code>{channel_id}</code> (Error fetching info)\n\n"
                
                fsub_list += f"<b>Tᴏᴛᴀʟ Fsᴜʙ Cʜᴀɴɴᴇʟs: {len(fsub_channels)}</b>\n"
                fsub_list += "\n<i>ON = Request Mode ON | OFF = Request Mode OFF</i>"
                
                await callback_query.message.edit_text(
                    fsub_list,
                    reply_markup=InlineKeyboardMarkup(btn),
                    disable_web_page_preview=True
                )
            except Exception as e:
                btn = [[InlineKeyboardButton("back", callback_data="fsub_settings_menu")]]
                await callback_query.message.edit_text(
                    f"<b>Eʀʀᴏʀ ғᴇᴛᴄʜɪɴɢ ғsᴜʙ ᴄʜᴀɴɴᴇʟs:</b> {str(e)}",
                    reply_markup=InlineKeyboardMarkup(btn)
                )

        # Admin Panel
        elif cb_data == "admin_bna_system":
            if not is_admin_user:
                await callback_query.answer("Only admins can access this!", show_alert=True)
                return
            
            btn = [
                [InlineKeyboardButton("Aᴅᴅ ᴀᴅᴍɪɴ", callback_data="admin_bna"), 
                 InlineKeyboardButton("Rᴇᴍᴏᴠᴇ Aᴅᴍɪɴ", callback_data="admin_hta")],
                [InlineKeyboardButton("Lɪsᴛ Aᴅᴍɪɴs", callback_data="admin_list")],
                [InlineKeyboardButton("back", callback_data="settings_main")]
            ]
            await callback_query.message.edit_text(
                "<b>Aᴅᴍɪɴ Mᴀɴᴀɢᴇᴍᴇɴᴛ Pᴀɴᴇʟ:\n\nSᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ʙᴇʟᴏᴡ:</b>",
                reply_markup=InlineKeyboardMarkup(btn)
            )

        # List Admins - FIXED: Removed reply_markup from answer()
        elif cb_data == "admin_list":
            if not is_admin_user:
                await callback_query.answer("Only admins can view admin list!", show_alert=True)
                return
            
            await callback_query.answer("Fᴇᴛᴄʜɪɴɢ ᴀᴅᴍɪɴ ʟɪsᴛ...")
            
            try:
                admin_ids = await Seishiro.list_admins()
                
                btn = [[InlineKeyboardButton("back", callback_data="admin_bna_system")]]
                
                if not admin_ids:
                    await callback_query.message.edit_text(
                        "<b>Nᴏ ᴀᴅᴍɪɴs ғᴏᴜɴᴅ.</b>",
                        reply_markup=InlineKeyboardMarkup(btn)
                    )
                    return
                
                admin_list = "<b>Aᴅᴍɪɴ Lɪsᴛ:</b>\n\n"
                for idx, admin_id in enumerate(admin_ids, 1):
                    try:
                        user = await client.get_users(admin_id)
                        admin_list += f"{idx}. {user.mention} (<code>{admin_id}</code>)\n"
                    except Exception:
                        admin_list += f"{idx}. <code>{admin_id}</code>\n"
                
                await callback_query.message.edit_text(
                    admin_list,
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            except Exception as e:
                btn = [[InlineKeyboardButton("back", callback_data="admin_bna_system")]]
                await callback_query.message.edit_text(
                    f"<b>Eʀʀᴏʀ ғᴇᴛᴄʜɪɴɢ ᴀᴅᴍɪɴ ʟɪsᴛ:</b> {str(e)}",
                    reply_markup=InlineKeyboardMarkup(btn)
                )
        
        elif cb_data == "add_channel":
            if not is_admin_user:
                await callback_query.answer("Only admins can add channels!", show_alert=True)
                return
                
            btn = [[InlineKeyboardButton("back", callback_data="settings_main")]]
            await callback_query.message.edit_text(
                "<b>Sᴇɴᴅ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ID ᴛᴏ ᴀᴅᴅ (e.g., -100123456789):\n\n/cancel ᴛᴏ ᴄᴀɴᴄᴇʟ</b>",
                reply_markup=InlineKeyboardMarkup(btn)
            )
                
            try:
                msg = await client.listen(chat_id=callback_query.message.chat.id, timeout=300)
                temp = await msg.reply("<i>Pʀᴏᴄᴇssɪɴɢ...</i>")
                await callback_query.message.delete()
                    
                if msg.text == '/cancel':
                    await temp.edit("ᴄᴀɴᴄᴇʟʟᴇᴅ!", reply_markup=InlineKeyboardMarkup(btn))
                    return
                        
                if not re.match(r"^-100\d{10,}$", msg.text):
                    await temp.edit(
                        "<b><blockquote expandable>Iɴᴠᴀʟɪᴅ ᴄʜᴀɴɴᴇʟ ID. Mᴜsᴛ ʙᴇ ɪɴ ᴛʜᴇ ғᴏʀᴍᴀᴛ -100XXXXXXXXXX.</blockquote></b>",
                        reply_markup=InlineKeyboardMarkup(btn)
                    )
                    return
                            
                channel_id = int(msg.text)
                            
                try:
                    chat_member = await client.get_chat_member(channel_id, client.me.id)
                    valid_statuses = [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
                                
                    if chat_member.status not in valid_statuses:
                        await temp.edit(
                            f"<b><blockquote expandable>I ᴀᴍ ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ ᴏғ ᴛʜɪs ᴄʜᴀɴɴᴇʟ. Pʟᴇᴀsᴇ ᴍᴀᴋᴇ ᴍᴇ ᴀᴅᴍɪɴ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ.</blockquote></b>",
                            reply_markup=InlineKeyboardMarkup(btn)
                        )
                        return
                except UserNotParticipant:
                    await temp.edit(
                        "<b><blockquote expandable>I ᴀᴍ ɴᴏᴛ ᴀ ᴍᴇᴍʙᴇʀ ᴏғ ᴛʜɪs ᴄʜᴀɴɴᴇʟ. Pʟᴇᴀsᴇ ᴀᴅᴅ ᴍᴇ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ.</blockquote></b>",
                        reply_markup=InlineKeyboardMarkup(btn)
                    )
                    return
                except RPCError as e:
                    if "CHANNEL_INVALID" in str(e):
                        await temp.edit(
                            "<b><blockquote expandable>Iɴᴠᴀʟɪᴅ ᴄʜᴀɴɴᴇʟ ID. Pʟᴇᴀsᴇ ᴄʜᴇᴄᴋ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ.</blockquote></b>",
                            reply_markup=InlineKeyboardMarkup(btn)
                        )
                        return
                    await temp.edit(
                        f"<b><blockquote expandable>Eʀʀᴏʀ: {str(e)}</blockquote></b>",
                        reply_markup=InlineKeyboardMarkup(btn)
                    )
                    return
                                    
                try:
                    chat = await client.get_chat(channel_id)
                except RPCError as e:
                    await temp.edit(
                        f"<b><blockquote expandable>Fᴀɪʟᴇᴅ ᴛᴏ ᴀᴄᴄᴇss ᴄʜᴀɴɴᴇʟ: {str(e)}</blockquote></b>",
                        reply_markup=InlineKeyboardMarkup(btn)
                    )
                    return
                                        
                await Seishiro.save_channel(channel_id)
                                        
                base64_invite = await encode(str(channel_id))
                await Seishiro.save_encoded_link(channel_id)
                                        
                base64_request = await encode(str(channel_id))
                await Seishiro.save_encoded_link2(channel_id, base64_request)
                                        
                normal_link = f"https://t.me/{client.username}?start={base64_invite}"
                request_link = f"https://t.me/{client.username}?start=req_{base64_request}"
                reply_text = (
                    f"<b>Cʜᴀɴɴᴇʟ {chat.title} ({channel_id}) ʜᴀs ʙᴇᴇɴ ᴀᴅᴅᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ.</b>\n\n"
                    f"<b>Nᴏʀᴍᴀʟ Lɪɴᴋ:</b>\n<code>{normal_link}</code>\n\n"
                    f"<b>Rᴇǫᴜᴇsᴛ Lɪɴᴋ:</b>\n<code>{request_link}</code>"
                )
                await temp.edit(reply_text, reply_markup=InlineKeyboardMarkup(btn))
                                    
            except asyncio.TimeoutError:
                await callback_query.message.reply(
                    "<b>Tɪᴍᴇᴏᴜᴛ! Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ.</b>",
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            except Exception as e:
                print(f"Unexpected Error adding channel: {e}")
                await temp.edit(f"Unexpected Error: {str(e)}", reply_markup=InlineKeyboardMarkup(btn))
        
        # Delete Channel
        elif cb_data == "delete_channel":
            if not is_admin_user:
                await callback_query.answer("Only admins can delete channels!", show_alert=True)
                return
            
            btn = [[InlineKeyboardButton("back", callback_data="settings_main")]]
            await callback_query.message.edit_text(
                "<b>Sᴇɴᴅ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ID ᴛᴏ ᴅᴇʟᴇᴛᴇ (e.g., -100123456789):\n\n/cancel ᴛᴏ ᴄᴀɴᴄᴇʟ</b>",
                reply_markup=InlineKeyboardMarkup(btn)
            )
            
            try:
                msg = await client.listen(chat_id=callback_query.message.chat.id, timeout=300)
                await callback_query.message.delete()
                
                if msg.text == '/cancel':
                    await msg.reply("ᴄᴀɴᴄᴇʟʟᴇᴅ!", reply_markup=InlineKeyboardMarkup(btn))
                    return
                
                channel_id = int(msg.text)
                await Seishiro.delete_channel(channel_id)
                await msg.reply(
                    f"<b><blockquote expandable>Cʜᴀɴɴᴇʟ {channel_id} ʜᴀs ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ.</blockquote></b>",
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            except (ValueError, IndexError):
                await msg.reply(
                    "<b><blockquote expandable>Iɴᴠᴀʟɪᴅ ᴄʜᴀɴɴᴇʟ ID. Pʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ.</blockquote></b>",
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            except Exception as e:
                print(f"Error deleting channel {msg.text}: {e}")
                await msg.reply(f"Unexpected Error: {str(e)}", reply_markup=InlineKeyboardMarkup(btn))

        # Channel Links
        elif cb_data == "channel_links":
            channels = await Seishiro.get_channels()
            if not channels:
                await callback_query.message.edit_text(
                    "<b><blockquote expandable>Nᴏ ᴄʜᴀɴɴᴇʟs ᴀʀᴇ ᴀᴠᴀɪʟᴀʙʟᴇ. Pʟᴇᴀsᴇ ᴜsᴇ 'Aᴅᴅ Cʜᴀɴɴᴇʟ' ᴛᴏ ᴀᴅᴅ ᴀ ᴄʜᴀɴɴᴇʟ.</blockquote></b>",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("back", callback_data="settings_main")]])
                )
                await callback_query.answer()
                return
            await send_channel_page(client, callback_query.message, channels, page=0)
            await callback_query.answer()

        # Request Links
        elif cb_data == "request_links":
            channels = await Seishiro.get_channels()
            if not channels:
                await callback_query.message.edit_text(
                    "<b><blockquote expandable>Nᴏ ᴄʜᴀɴɴᴇʟs ᴀʀᴇ ᴀᴠᴀɪʟᴀʙʟᴇ. Pʟᴇᴀsᴇ ᴜsᴇ 'Aᴅᴅ Cʜᴀɴɴᴇʟ' ᴛᴏ ᴀᴅᴅ ᴀ ᴄʜᴀɴɴᴇʟ.</blockquote></b>",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("back", callback_data="settings_main")]])
                )
                await callback_query.answer()
                return
            await send_request_page(client, callback_query.message, channels, page=0)
            await callback_query.answer()

        # List Channels
        elif cb_data == "list_channels":
            channels = await Seishiro.get_channels()
            if not channels:
                await callback_query.answer(
                    "Nᴏ ᴄʜᴀɴɴᴇʟs ᴀʀᴇ ᴀᴠᴀɪʟᴀʙʟᴇ. Pʟᴇᴀsᴇ ᴜsᴇ 'Aᴅᴅ Cʜᴀɴɴᴇʟ' ᴛᴏ ᴀᴅᴅ ᴀ ᴄʜᴀɴɴᴇʟ.", show_alert=True
                )
                return
            status_msg = await callback_query.message.reply("<i>Please wait...</i>")
            await send_channel_ids_page(client, callback_query.message, channels, page=0, status_msg=status_msg)

        # Channel Links Pagination
        elif cb_data.startswith("channelpage_"):
            page = int(cb_data.split("_")[1])
            channels = await Seishiro.get_channels()
            await send_channel_page(client, callback_query.message, channels, page, edit=True)
            await callback_query.answer()

        # Request Links Pagination
        elif cb_data.startswith("reqpage_"):
            page = int(cb_data.split("_")[1])
            channels = await Seishiro.get_channels()
            await send_request_page(client, callback_query.message, channels, page, edit=True)
            await callback_query.answer()

        # Channel IDs Pagination
        elif cb_data.startswith("channelids_"):
            page = int(cb_data.split("_")[1])
            channels = await Seishiro.get_channels()
            await send_channel_ids_page(client, callback_query.message, channels, page, edit=True)
            await callback_query.answer()

        # Add Admin
        elif cb_data == "admin_bna":
            if not is_admin_user:
                await callback_query.answer("Only admins can add admins!", show_alert=True)
                return
            
            btn = [[InlineKeyboardButton("back", callback_data="admin_bna_system")]]
            await callback_query.message.edit_text(
                "<b>Sᴇɴᴅ ᴛʜᴇ ᴜsᴇʀ ID ᴡʜɪᴄʜ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴍᴀᴋᴇ ᴀᴅᴍɪɴ (e.g., 123456789):\n\n/cancel ᴛᴏ ᴄᴀɴᴄᴇʟ</b>",
                reply_markup=InlineKeyboardMarkup(btn)
            )
            
            try:
                msg = await client.listen(chat_id=callback_query.message.chat.id, timeout=300)
                await callback_query.message.delete()
                
                if msg.text == '/cancel':
                    await msg.reply("ᴄᴀɴᴄᴇʟʟᴇᴅ!", reply_markup=InlineKeyboardMarkup(btn))
                    return
                
                user_id = int(msg.text)
                await Seishiro.add_admin(user_id)
                await msg.reply(
                    f"<b>Tʜɪs ɪᴅ {user_id} sᴜᴄᴄᴇssғᴜʟʟʏ ᴘʀᴏᴍᴏᴛᴇᴅ ᴛᴏ ᴀᴅᴍɪɴ. Success</b>",
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            except (ValueError, IndexError):
                await msg.reply(
                    "<b><blockquote expandable>Iɴᴠᴀʟɪᴅ ᴜsᴇʀ ID. Pʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ.</blockquote></b>",
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            except Exception as e:
                print(f"Error in promoting admin: {e}")
                await msg.reply(f"Uɴᴇxᴘᴇᴄᴛᴇᴅ Eʀʀᴏʀ: {str(e)}", reply_markup=InlineKeyboardMarkup(btn))

        # Remove Admin
        elif cb_data == "admin_hta":
            if not is_admin_user:
                await callback_query.answer("Only admins can remove admins!", show_alert=True)
                return
            
            btn = [[InlineKeyboardButton("back", callback_data="admin_bna_system")]]
            await callback_query.message.edit_text(
                "<b>Sᴇɴᴅ ᴛʜᴇ ᴜsᴇʀ ID ᴛᴏ ʀᴇᴍᴏᴠᴇ ғʀᴏᴍ ᴀᴅᴍɪɴ (e.g., 123456789):\n\n/cancel ᴛᴏ ᴄᴀɴᴄᴇʟ</b>",
                reply_markup=InlineKeyboardMarkup(btn)
            )
            
            try:
                msg = await client.listen(chat_id=callback_query.message.chat.id, timeout=300)
                await callback_query.message.delete()
                
                if msg.text == '/cancel':
                    await msg.reply("ᴄᴀɴᴄᴇʟʟᴇᴅ!", reply_markup=InlineKeyboardMarkup(btn))
                    return

                user_id = int(msg.text)
                await Seishiro.remove_admin(user_id)
                await msg.reply(
                    f"<b>Tʜɪs ɪᴅ {user_id} sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇᴘʀᴏᴍᴏᴛᴇᴅ ғʀᴏᴍ ᴀᴅᴍɪɴ. Success</b>",
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            except (ValueError, IndexError):
                await msg.reply(
                    "<b><blockquote expandable>Iɴᴠᴀʟɪᴅ ᴜsᴇʀ ID. Pʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ.</blockquote></b>",
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            except Exception as e:
                print(f"Error in depromoting admin: {e}")
                await msg.reply(f"Uɴᴇxᴘᴇᴄᴛᴇᴅ Eʀʀᴏʀ: {str(e)}", reply_markup=InlineKeyboardMarkup(btn))

    except Exception as e:
        print(f"Error in callback: {e}")
        await callback_query.message.edit_text(
            f"Unexpected Error: {str(e)}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("back", callback_data="settings_main")]])
        )


# Helper function: Send channel page with pagination - FIXED
async def send_channel_page(client, message, channels, page, edit=False):
    total_pages = (len(channels) + PAGE_SIZE - 1) // PAGE_SIZE
    start_idx = page * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    buttons = []

    row = []
    for channel_id in channels[start_idx:end_idx]:
        try:
            # Get existing encoded link, don't create new one
            base64_invite = await Seishiro.get_encoded_link(channel_id)
            if not base64_invite:
                base64_invite = await encode(str(channel_id))
                await Seishiro.save_encoded_link(channel_id, base64_invite)
            
            button_link = f"https://t.me/{client.username}?start={base64_invite}"
            chat = await client.get_chat(channel_id)
            
            row.append(InlineKeyboardButton(chat.title, url=button_link))
            
            if len(row) == 2:
                buttons.append(row)
                row = [] 
        except Exception as e:
            print(f"Error for channel {channel_id}: {e}")

    if row: 
        buttons.append(row)

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("• Pʀᴇᴠɪᴏᴜs •", callback_data=f"channelpage_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("• Nᴇxᴛ •", callback_data=f"channelpage_{page+1}"))
    nav_buttons.append(InlineKeyboardButton("back", callback_data="settings_main"))

    if nav_buttons:
        buttons.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(buttons)
    if edit:
        await message.edit_text("Sᴇʟᴇᴄᴛ ᴀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴀᴄᴄᴇss:", reply_markup=reply_markup)
    else:
        await message.reply("Sᴇʟᴇᴄᴛ ᴀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴀᴄᴄᴇss:", reply_markup=reply_markup)


# Helper function: Send request page with pagination - FIXED
async def send_request_page(client, message, channels, page, edit=False):
    total_pages = (len(channels) + PAGE_SIZE - 1) // PAGE_SIZE
    start_idx = page * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    buttons = []

    row = []
    for channel_id in channels[start_idx:end_idx]:
        try:
            # Get existing encoded link, don't create new one
            base64_request = await Seishiro.get_encoded_link2(channel_id)
            if not base64_request:
                base64_request = await encode(str(channel_id))
                await Seishiro.save_encoded_link2(channel_id, base64_request)
            
            button_link = f"https://t.me/{client.username}?start=req_{base64_request}"
            chat = await client.get_chat(channel_id)

            row.append(InlineKeyboardButton(chat.title, url=button_link))

            if len(row) == 2:
                buttons.append(row)
                row = [] 
        except Exception as e:
            print(f"Error generating request link for channel {channel_id}: {e}")

    if row: 
        buttons.append(row)

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("• Pʀᴇᴠɪᴏᴜs •", callback_data=f"reqpage_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("• Nᴇxᴛ •", callback_data=f"reqpage_{page+1}"))
    nav_buttons.append(InlineKeyboardButton("back", callback_data="settings_main"))

    if nav_buttons:
        buttons.append(nav_buttons) 
    reply_markup = InlineKeyboardMarkup(buttons)
    if edit:
        await message.edit_text("Sᴇʟᴇᴄᴛ ᴀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ʀᴇǫᴜᴇsᴛ ᴀᴄᴄᴇss:", reply_markup=reply_markup)
    else:
        await message.reply("Sᴇʟᴇᴄᴛ ᴀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ʀᴇǫᴜᴇsᴛ ᴀᴄᴄᴇss:", reply_markup=reply_markup)


# Helper function: Send channel IDs page with pagination
async def send_channel_ids_page(client, message, channels, page, status_msg=None, edit=False):
    PAGE_SIZE_IDS = 10
    total_pages = (len(channels) + PAGE_SIZE_IDS - 1) // PAGE_SIZE_IDS
    start_idx = page * PAGE_SIZE_IDS
    end_idx = start_idx + PAGE_SIZE_IDS
    text = "<b>Connected Cʜᴀɴɴᴇʟs (ID & Name):</b>\n\n"
    for idx, channel_id in enumerate(channels[start_idx:end_idx], start=start_idx + 1):
        try:
            chat = await client.get_chat(channel_id)
            text += f"<b>{idx}. {chat.title}</b> <code>({channel_id})</code>\n"
        except Exception as e:
            text += f"<b>{idx}. Channel {channel_id}</b> (Error)\n"
    text += f"\n<b>Page {page + 1} ᴏғ {total_pages}</b>"
    buttons = []
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("• Pʀᴇᴠɪᴏᴜs •", callback_data=f"channelids_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("• Nᴇxᴛ •", callback_data=f"channelids_{page+1}"))
    nav_buttons.append(InlineKeyboardButton("back", callback_data="settings_main"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    reply_markup = InlineKeyboardMarkup(buttons)
    if edit:
        await message.edit_text(text, reply_markup=reply_markup)
    else:
        await message.reply(text, reply_markup=reply_markup)
    if status_msg:
        try:
            await status_msg.delete()
        except:
            pass

@Bot.on_message(filters.command('genlink') & filters.private & is_owner_or_admin)
async def gen_link_cmd(client: Bot, message: Message):
    if len(message.command) < 2:
        return await message.reply(
            "<b><blockquote expandable>ᴜsᴀɢᴇ: <code>/genlink -100123456789</code></blockquote></b>"
        )

    try:
        channel_id = int(message.command[1])

        # Check if channel is added
        if not await Seishiro.reqChannel_exist(channel_id):
            return await message.reply(
                "<b><blockquote expandable>ᴄʜᴀɴɴᴇʟ ɴᴏᴛ ғᴏᴜɴᴅ ɪɴ ᴀᴅᴅᴇᴅ ʟɪsᴛ.\n\n"
                "ғɪʀsᴛʟʏ ᴀᴅᴅ ʏᴏᴜʀ ᴄʜᴀɴɴᴇʟ ᴜsɪɴɢ <code>/settings → ᴀᴅᴅ ᴄʜᴀɴɴᴇʟ</code>\n"
                "ᴛʜᴇɴ ʏᴏᴜ ᴡɪʟʟ ʙᴇ ᴀʙʟᴇ ᴛᴏ ᴄʀᴇᴀᴛᴇ ʟɪɴᴋs ғᴏʀ ᴛʜᴀᴛ ɪᴅ.</blockquote></b>"
            )

        chat = await client.get_chat(channel_id)

        # Normal link
        base64_invite = await encode(str(channel_id))
        await Seishiro.save_encoded_link(channel_id)
        normal_link = f"https://t.me/{client.username}?start={base64_invite}"

        # Request link
        base64_request = await encode(str(channel_id))
        await Seishiro.save_encoded_link2(channel_id, base64_request)
        request_link = f"https://t.me/{client.username}?start=req_{base64_request}"

        reply_text = (
            f"<b><u>ʟɪɴᴋs ɢᴇɴᴇʀᴀᴛᴇᴅ:</u></b>\n\n"
            f"<b>ᴄʜᴀɴɴᴇʟ:</b> {chat.title}\n"
            f"<code>{channel_id}</code>\n\n"
            f"<b>ɴᴏʀᴍᴀʟ ʟɪɴᴋ:</b>\n<code>{normal_link}</code>\n\n"
            f"<b>ʀᴇǫᴜᴇsᴛ ʟɪɴᴋ:</b>\n<code>{request_link}</code>"
        )
        await message.reply(reply_text)

    except ValueError:
        await message.reply(
            "<b><blockquote expandable>ɪɴᴠᴀʟɪᴅ ᴄʜᴀɴɴᴇʟ ɪᴅ!\nᴜsᴇ ғᴏʀᴍᴀᴛ: <code>/genlink -100123456789</code></blockquote></b>"
        )
    except Exception as e:
        await message.reply(f"<b>ᴇʀʀᴏʀ:</b> <code>{str(e)}</code>")

@Bot.on_message(filters.command('batch') & is_owner_or_admin)
async def batch(client: Bot, message: Message):
    if len(message.command) < 2:
        return await message.reply(
            "<b><blockquote expandable>ᴜsᴀɢᴇ: <code>/batch -100123456789 -100987654321</code></blockquote></b>"
        )

    ids = message.command[1:]
    reply_text = "<b><u>ʙᴀᴛᴄʜ ʟɪɴᴋ ɢᴇɴᴇʀᴀᴛɪᴏɴ:</u></b>\n\n"

    for idx, id_str in enumerate(ids, start=1):
        try:
            channel_id = int(id_str)

            # Check if channel is added
            if not await Seishiro.reqChannel_exist(channel_id):
                reply_text += (
                    f"<b>{idx}. <code>{channel_id}</code></b>\n"
                    "<blockquote expandable>ᴄʜᴀɴɴᴇʟ ɴᴏᴛ ᴀᴅᴅᴇᴅ!\n"
                    "ᴜsᴇ <code>/settings → ᴀᴅᴅ ᴄʜᴀɴɴᴇʟ</code> ғɪʀsᴛ.</blockquote>\n\n"
                )
                continue

            chat = await client.get_chat(channel_id)

            # Normal link
            base64_invite = await encode(str(channel_id))
            await Seishiro.save_encoded_link(channel_id)
            normal_link = f"https://t.me/{client.username}?start={base64_invite}"

            # Request link
            base64_request = await encode(str(channel_id))
            await Seishiro.save_encoded_link2(channel_id, base64_request)
            request_link = f"https://t.me/{client.username}?start=req_{base64_request}"

            reply_text += (
                f"<b>{idx}. {chat.title}</b>\n"
                f"<code>{channel_id}</code>\n"
                f"<b>ɴᴏʀᴍᴀʟ:</b> <code>{normal_link}</code>\n"
                f"<b>ʀᴇǫᴜᴇsᴛ:</b> <code>{request_link}</code>\n\n"
            )

        except Exception as e:
            reply_text += f"<b>{idx}. {id_str}</b> - ᴇʀʀᴏʀ: <code>{str(e)}</code>\n\n"

    await message.reply(reply_text)
