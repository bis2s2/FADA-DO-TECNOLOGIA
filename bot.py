
import discord
from discord.ext import commands
import logging
import json
import os
import time
from bot.database import Database
from bot.commands import setup_commands

logger = logging.getLogger(__name__)

class PointsBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        
        super().__init__(command_prefix='/', intents=intents)
        
        # Load config
        self.config = self.load_config()
        
        # Initialize database
        self.db = Database()
        
        # User cooldowns
        self.user_cooldowns = {}
        
    def load_config(self):
        """Load configuration from config.json"""
        try:
            with open('config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Default config
            return {
                "points": {
                    "message": 1
                },
                "cooldowns": {
                    "message_points_cooldown": 60
                },
                "permissions": {
                    "admin_users": ["gabis2s2"],
                    "moderator_roles": ["Moderador", "Admin"]
                }
            }
    
    async def setup_hook(self):
        """Called when the bot is starting"""
        await self.db.init_database()
        setup_commands(self)
        logger.info("Bot setup completed")
    
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Set bot status
        activity = discord.Game(name="/ajuda para comandos")
        await self.change_presence(status=discord.Status.online, activity=activity)
    
    async def on_message(self, message):
        """Handle incoming messages"""
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Process commands first
        await self.process_commands(message)
        
        # Award points for messages
        await self.award_message_points(message)
    
    async def award_message_points(self, message):
        """Award points for sending a message"""
        user_id = message.author.id
        current_time = time.time()
        cooldown = self.config.get('cooldowns', {}).get('message_points_cooldown', 60)
        
        # Check cooldown
        if user_id in self.user_cooldowns:
            if current_time - self.user_cooldowns[user_id] < cooldown:
                return
        
        # Update cooldown
        self.user_cooldowns[user_id] = current_time
        
        # Award points
        points = self.config.get('points', {}).get('message', 1)
        await self.db.update_user_points(
            user_id, 
            message.author.display_name, 
            points, 
            "message"
        )
