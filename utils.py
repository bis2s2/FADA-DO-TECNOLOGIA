
import discord

def create_embed(title: str, description: str, color: discord.Color) -> discord.Embed:
    """Create a Discord embed with the given title, description, and color"""
    embed = discord.Embed(title=title, description=description, color=color)
    return embed

def format_points(points: int) -> str:
    """Format points number with proper formatting"""
    if points >= 1000000:
        return f"{points/1000000:.1f}M pontos"
    elif points >= 1000:
        return f"{points/1000:.1f}K pontos"
    else:
        return f"{points:,} pontos"
