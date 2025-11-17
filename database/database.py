import motor.motor_asyncio
import base64
import logging
from datetime import datetime, date
from typing import List, Optional
from config import * 

logging.basicConfig(level=logging.INFO)


class Master:
    def __init__(self, DB_URL, DB_NAME):
        self.dbclient = motor.motor_asyncio.AsyncIOMotorClient(DB_URL)
        self.database = self.dbclient[DB_NAME]

        # Initialize all collections
        self.user_data = self.database['users']
        self.channel_data = self.database['channels']
        self.admins_data = self.database['admins']
        self.del_timer_data = self.database['del_timer']
        self.ban_data = self.database['ban_data']
        self.fsub_data = self.database['fsub']
        self.rqst_fsub_data = self.database['request_forcesub']
        self.rqst_fsub_Channel_data = self.database['request_forcesub_channel']

        # Main collection reference (for backward compatibility)
        self.col = self.user_data

    def new_user(self, id, username=None):
        return dict(
            _id=int(id),
            username=username.lower() if username else None,
            join_date=date.today().isoformat(),
            ban_status=dict(
                is_banned=False,
                ban_duration=0,
                banned_on=date.max.isoformat(),
                ban_reason='',
            )
        )

    async def add_user(self, b, m):
        u = m.from_user
        if not await self.is_user_exist(u.id):
            user = self.new_user(u.id, u.username)
            try:
                await self.user_data.insert_one(user)
                logging.info(f"New user added: {u.id}")
                # Uncomment if send_log function exists
                # await send_log(b, u)
            except Exception as e:
                logging.error(f"Error adding user {u.id}: {e}")
        else:
            logging.info(f"User {u.id} already exists")

    async def is_user_exist(self, id):
        try:
            user = await self.user_data.find_one({"_id": int(id)})
            return bool(user)
        except Exception as e:
            logging.error(f"Error checking if user {id} exists: {e}")
            return False

    async def get_all_users(self):
        try:
            all_users = self.user_data.find({})
            return all_users
        except Exception as e:
            logging.error(f"Error getting all users: {e}")
            return None

    async def total_users_count(self):
        try:
            count = await self.user_data.count_documents({})
            return count
        except Exception as e:
            logging.error(f"Error counting users: {e}")
            return 0

    async def delete_user(self, user_id):
        try:
            await self.user_data.delete_many({"_id": int(user_id)})
        except Exception as e:
            logging.error(f"Error deleting user {user_id}: {e}")

    async def is_user_banned(self, user_id):
        try:
            user = await self.ban_data.find_one({"_id": user_id})
            if user and user.get("ban_status", {}).get("is_banned", False):
                return user
        except Exception as e:
            logging.error(f"Error in checking ban status {user_id}: {e}")

    async def is_admin(self, user_id: int) -> bool:
        """Check if a user is an admin."""
        try:
            user_id = int(user_id)
            return bool(await self.admins_data.find_one({"_id": user_id}))
        except Exception as e:
            logging.error(f"Error checking admin status for {user_id}: {e}")
            return False

    async def add_admin(self, user_id: int) -> bool:
        """Add a user as admin."""
        try:
            user_id = int(user_id)
            await self.admins_data.update_one(
                {"user_id": user_id},
                {"$set": {"_id": user_id, "added_at": datetime.utcnow()}},
                upsert=True
            )
            return True
        except Exception as e:
            logging.error(f"Error adding admin {user_id}: {e}")
            return False

    async def remove_admin(self, user_id: int) -> bool:
        """Remove a user from admins."""
        try:
            result = await self.admins_data.delete_one({"_id": user_id})
            return result.deleted_count > 0
        except Exception as e:
            logging.error(f"Error removing admin {user_id}: {e}")
            return False

    async def list_admins(self) -> list:
        """List all admin user IDs."""
        try:
            admins = await self.admins_data.find({}).to_list(None)
            return [admin["user_id"] for admin in admins]
        except Exception as e:
            logging.error(f"Error listing admins: {e}")
            return []

    async def save_channel(self, channel_id: int) -> bool:
        """Save a channel to the database with invite link expiration."""
        if not isinstance(channel_id, int):
            logging.error(f"Invalid channel_id: {channel_id}")
            return False

        try:
            await self.channel_data.update_one(
                {"channel_id": channel_id},
                {
                    "$set": {
                        "invite_link_expiry": None,
                        "created_at": datetime.utcnow(),
                        "status": "active"
                    }
                },
                upsert=True
            )
            return True
        except Exception as e:
            logging.error(f"Error saving channel {channel_id}: {e}")
            return False

    async def get_channels(self) -> List[int]:
        """Get all active channel IDs from the database."""
        try:
            channels = await self.channel_data.find({"status": "active"}).to_list(None)
            valid_channels = [ch["channel_id"] for ch in channels if "channel_id" in ch]
            if not valid_channels:
                logging.info(f"No valid channels found in database. Total documents checked: {len(channels)}")
            return valid_channels
        except Exception as e:
            logging.error(f"Error fetching channels: {e}")
            return []

    async def show_channels(self) -> List[int]:
        """Alias for get_channels - used by reqChannel_exist."""
        return await self.get_channels()

    async def delete_channel(self, channel_id: int) -> bool:
        """Delete a channel from the database."""
        try:
            result = await self.channel_data.delete_one({"_id": channel_id})
            return result.deleted_count > 0
        except Exception as e:
            logging.error(f"Error deleting channel {channel_id}: {e}")
            return False

    async def save_encoded_link(self, channel_id: int) -> Optional[str]:
        """Save an encoded link for a channel and return it."""
        if not isinstance(channel_id, int):
            logging.error(f"Invalid channel_id: {channel_id}")
            return None

        try:
            encoded_link = base64.urlsafe_b64encode(str(channel_id).encode()).decode()
            await self.channel_data.update_one(
                {"channel_id": channel_id},
                {
                    "$set": {
                        "encoded_link": encoded_link,
                        "status": "active",
                        "updated_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            return encoded_link
        except Exception as e:
            logging.error(f"Error saving encoded link for channel {channel_id}: {e}")
            return None

    async def get_channel_by_encoded_link(self, encoded_link: str) -> Optional[int]:
        """Get a channel ID by its encoded link."""
        if not isinstance(encoded_link, str):
            return None

        try:
            channel = await self.channel_data.find_one({"encoded_link": encoded_link, "status": "active"})
            return channel["channel_id"] if channel and "channel_id" in channel else None
        except Exception as e:
            logging.error(f"Error fetching channel by encoded link {encoded_link}: {e}")
            return None

    async def save_encoded_link2(self, channel_id: int, encoded_link: str) -> Optional[str]:
        """Save a secondary encoded link for a channel."""
        if not isinstance(channel_id, int) or not isinstance(encoded_link, str):
            logging.error(f"Invalid input: channel_id={channel_id}, encoded_link={encoded_link}")
            return None

        try:
            await self.channel_data.update_one(
                {"channel_id": channel_id},
                {
                    "$set": {
                        "req_encoded_link": encoded_link,
                        "status": "active",
                        "updated_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            return encoded_link
        except Exception as e:
            logging.error(f"Error saving secondary encoded link for channel {channel_id}: {e}")
            return None

    async def get_channel_by_encoded_link2(self, encoded_link: str) -> Optional[int]:
        """Get a channel ID by its secondary encoded link."""
        if not isinstance(encoded_link, str):
            return None

        try:
            channel = await self.channel_data.find_one({"req_encoded_link": encoded_link, "status": "active"})
            return channel["channel_id"] if channel and "channel_id" in channel else None
        except Exception as e:
            logging.error(f"Error fetching channel by secondary encoded link {encoded_link}: {e}")
            return None

    async def save_invite_link(self, channel_id: int, invite_link: str, is_request: bool) -> bool:
        """Save the current invite link for a channel and its type."""
        if not isinstance(channel_id, int) or not isinstance(invite_link, str):
            logging.error(f"Invalid input: channel_id={channel_id}, invite_link={invite_link}")
            return False

        try:
            await self.channel_data.update_one(
                {"channel_id": channel_id},
                {
                    "$set": {
                        "current_invite_link": invite_link,
                        "is_request_link": is_request,
                        "invite_link_created_at": datetime.utcnow(),
                        "status": "active"
                    }
                },
                upsert=True
            )
            return True
        except Exception as e:
            logging.error(f"Error saving invite link for channel {channel_id}: {e}")
            return False

    async def get_current_invite_link(self, channel_id: int) -> Optional[dict]:
        """Get the current invite link and its type for a channel."""
        if not isinstance(channel_id, int):
            return None

        try:
            channel = await self.channel_data.find_one({"_id": channel_id, "status": "active"})
            if channel and "current_invite_link" in channel:
                return {
                    "invite_link": channel["current_invite_link"],
                    "is_request": channel.get("is_request_link", False)
                }
            return None
        except Exception as e:
            logging.error(f"Error fetching current invite link for channel {channel_id}: {e}")
            return None

    async def add_fsub_channel(self, channel_id: int) -> bool:
        """Add a channel to the FSub list."""
        if not isinstance(channel_id, int):
            logging.error(f"Invalid channel_id: {channel_id}")
            return False

        try:
            result = await self.fsub_data.update_one(
                {"channel_id": channel_id},
                {
                    "$set": {
                        "channel_id": channel_id,
                        "created_at": datetime.utcnow(),
                        "status": "active",
                        "mode": "off"
                    }
                },
                upsert=True
            )
            return result.matched_count == 0
        except Exception as e:
            logging.error(f"Error adding FSub channel {channel_id}: {e}")
            return False

    async def remove_fsub_channel(self, channel_id: int) -> bool:
        """Remove a channel from the FSub list."""
        try:
            result = await self.fsub_data.delete_one({"_id": channel_id})
            return result.deleted_count > 0
        except Exception as e:
            logging.error(f"Error removing FSub channel {channel_id}: {e}")
            return False

    async def get_fsub_channels(self) -> List[int]:
        """Get all active FSub channel IDs."""
        try:
            channels = await self.fsub_data.find({"status": "active"}).to_list(None)
            return [channel["channel_id"] for channel in channels if "channel_id" in channel]
        except Exception as e:
            logging.error(f"Error fetching FSub channels: {e}")
            return []

    async def get_channel_mode(self, channel_id: int):
        """Get current mode of a channel."""
        data = await self.fsub_data.find_one({'_id': channel_id})
        return data.get("mode", "off") if data else "off"

    async def set_channel_mode(self, channel_id: int, mode: str):
        """Set mode of a channel."""
        await self.fsub_data.update_one(
            {'channel_id': channel_id},
            {'$set': {'mode': mode}},
            upsert=True
        )

    async def set_channel_mode_all(self, mode: str) -> dict:
        """
        Set mode for all FSub channels at once.

        Args:
            mode: The mode to set ('on' or 'off')

        Returns:
            dict: Result with success status and count of updated channels
        """
        try:
            # Validate mode
            if mode not in ['on', 'off']:
                logging.error(f"Invalid mode: {mode}. Must be 'on' or 'off'")
                return {
                    "success": False,
                    "updated_count": 0,
                    "message": "Invalid mode. Must be 'on' or 'off'"
                }

            # Update all active FSub channels
            result = await self.fsub_data.update_many(
                {"status": "active"},
                {
                    "$set": {
                        "channel_id": channel_id,
                        "mode": mode,
                        "mode_updated_at": datetime.utcnow()
                    }
                }
            )

            logging.info(f"Bulk mode update: Set {result.modified_count} channels to '{mode}' mode")

            return {
                "success": True,
                "updated_count": result.modified_count,
                "matched_count": result.matched_count,
                "message": f"Successfully set {result.modified_count} channel(s) to '{mode}' mode"
            }

        except Exception as e:
            logging.error(f"Error setting mode for all channels: {e}")
            return {
                "success": False,
                "updated_count": 0,
                "message": f"Error: {str(e)}"
            }

    async def get_channel_mode_all(self) -> dict:
        """
        Get the mode status of all FSub channels.

        Returns:
            dict: Contains mode statistics and list of channels with their modes
        """
        try:
            channels = await self.fsub_data.find({"status": "active"}).to_list(None)

            if not channels:
                return {
                    "success": True,
                    "total_channels": 0,
                    "on_count": 0,
                    "off_count": 0,
                    "channels": [],
                    "message": "No FSub channels found"
                }

            channel_modes = []
            on_count = 0
            off_count = 0

            for channel in channels:
                channel_id = channel.get("channel_id") or channel.get("_id")
                mode = channel.get("mode", "off")

                if mode == "on":
                    on_count += 1
                else:
                    off_count += 1

                channel_modes.append({
                    "channel_id": channel_id,
                    "mode": mode
                })

            return {
                "success": True,
                "total_channels": len(channels),
                "on_count": on_count,
                "off_count": off_count,
                "channels": channel_modes,
                "message": f"Found {len(channels)} channel(s): {on_count} ON, {off_count} OFF"
            }

        except Exception as e:
            logging.error(f"Error getting mode for all channels: {e}")
            return {
                "success": False,
                "total_channels": 0,
                "on_count": 0,
                "off_count": 0,
                "channels": [],
                "message": f"Error: {str(e)}"
            }

    async def req_user(self, channel_id: int, user_id: int):
        """Add the user to the set of users for a specific channel."""
        try:
            await self.rqst_fsub_Channel_data.update_one(
                {'channel_id': int(channel_id)},
                {'$addToSet': {'user_ids': int(user_id)}},
                upsert=True
            )
        except Exception as e:
            logging.error(f"[DB ERROR] Failed to add user to request list: {e}")

    async def del_req_user(self, channel_id: int, user_id: int):
        """Remove a user from the channel set."""
        await self.rqst_fsub_Channel_data.update_one(
            {'channel_id': channel_id},
            {'$pull': {'user_ids': user_id}}
        )

    async def req_user_exist(self, channel_id: int, user_id: int):
        """Check if the user exists in the set of the channel's users."""
        try:
            found = await self.rqst_fsub_Channel_data.find_one({
                'channel_id': int(channel_id),
                'user_ids': int(user_id)
            })
            return bool(found)
        except Exception as e:
            logging.error(f"[DB ERROR] Failed to check request list: {e}")
            return False

    async def reqChannel_exist(self, channel_id: int):
        """Check if a channel exists using show_channels."""
        channel_ids = await self.show_channels()
        return channel_id in channel_ids

    async def get_original_link(self, channel_id: int) -> Optional[str]:
        """Get the original link stored for a channel (used by /genlink)."""
        if not isinstance(channel_id, int):
            return None
        try:
            channel = await self.channel_data.find_one({"channel_id": channel_id, "status": "active"})
            return channel.get("original_link") if channel else None
        except Exception as e:
            logging.error(f"Error fetching original link for channel {channel_id}: {e}")
            return None

Seishiro = Master(DB_URL, DB_NAME)
