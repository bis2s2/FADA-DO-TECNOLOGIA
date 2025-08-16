import os
import logging
from bot.bot import PointsBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    # Get Discord token from environment variable
    token = os.getenv('DISCORD_TOKEN')

    if not token:
        logger.error("DISCORD_TOKEN environment variable not found!")
        logger.error("Please add your Discord bot token to the Secrets in Replit.")
        return

    # Create and run bot
    bot = PointsBot()

    try:
        bot.run(token)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

if __name__ == "__main__":
    main()
