import discord
from discord.ext import commands
import os
import asyncio
import random
import logging
from datetime import datetime

# Import our custom modules
from config import DISCORD_TOKEN, validate_config
from database import load_data, auto_backup_task
from utils import create_embed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("petbot")

# Bot setup with all intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Cogs to load
COGS = [
    "cogs.pet_commands",
    "cogs.shop_commands"
]

@bot.event
async def on_ready():
    """Event: Bot is ready"""
    logger.info(f"{bot.user} has connected to Discord!")
    
    # Set bot activity
    await bot.change_presence(activity=discord.Game(name="!help | Virtual Pet Breeder"))
    
    # Load data
    load_data()
    
    # Start auto-backup task
    bot.loop.create_task(auto_backup_task())
    
    # Print info
    logger.info(f"Connected to {len(bot.guilds)} servers")
    logger.info(f"Bot is ready at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

@bot.event
async def on_guild_join(guild):
    """Event: Bot joins a new server"""
    logger.info(f"Joined new guild: {guild.name} (ID: {guild.id})")
    
    # Try to send welcome message
    try:
        # Find a suitable channel to send the welcome message
        general_channels = [channel for channel in guild.text_channels 
                          if channel.name.lower() in ["general", "main", "chat", "lobby"]]
        
        if general_channels:
            channel = general_channels[0]
        else:
            # If no suitable channel found, use the first text channel
            channel = guild.text_channels[0]
            
        # Create welcome embed
        embed = create_embed(
            title="Virtual Pet Breeder Bot",
            description="Thanks for adding me to your server!",
            color=0x00FF00,
            fields=[
                ("Getting Started", "Type `!adopt` to get your first pet!", False),
                ("Commands", "Type `!help` to see all available commands", False),
                ("Support", "For more help, join our support server: [Link]", False)
            ]
        )
        
        await channel.send(embed=embed)
    except Exception as e:
        logger.error(f"Error sending welcome message: {e}")

@bot.event
async def on_command_error(ctx, error):
    """Event: Command error handler"""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"Command not found. Use `!help` to see available commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing required argument: {error.param.name}. Use `!help {ctx.command.name}` for proper usage.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"Invalid argument provided. Use `!help {ctx.command.name}` for proper usage.")
    else:
        logger.error(f"Unhandled command error: {error}")
        await ctx.send(f"An error occurred: {error}")

@bot.command(name="help")
async def custom_help(ctx, command_name=None):
    """Custom help command with better formatting"""
    if command_name:
        # Help for a specific command
        command = bot.get_command(command_name)
        if command:
            embed = create_embed(
                title=f"Help: !{command.name}",
                description=command.help or "No description available",
                color=0x3498db
            )
            
            # Add usage if available
            usage = f"!{command.name}"
            if command.signature:
                usage = f"!{command.name} {command.signature}"
            embed.add_field(name="Usage", value=f"`{usage}`", inline=False)
            
            # Add aliases if available
            if command.aliases:
                aliases = ", ".join([f"!{alias}" for alias in command.aliases])
                embed.add_field(name="Aliases", value=aliases, inline=False)
                
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"Command `{command_name}` not found.")
    else:
        # General help - list all commands by category
        embed = create_embed(
            title="Virtual Pet Breeder Bot Commands",
            description="Here are all available commands. Use `!help <command>` for more info on a command.",
            color=0x3498db
        )
        
        # Group commands by cog (category)
        cogs = {}
        for command in bot.commands:
            cog_name = command.cog_name or "No Category"
            if cog_name not in cogs:
                cogs[cog_name] = []
            cogs[cog_name].append(command)
        
        # Add each category to the embed
        for cog_name, commands_list in cogs.items():
            # Format command list
            commands_text = ", ".join([f"`!{cmd.name}`" for cmd in commands_list])
            embed.add_field(name=cog_name, value=commands_text, inline=False)
            
        embed.set_footer(text="For more details on a command, use !help <command>")
        await ctx.send(embed=embed)

async def load_cogs():
    """Load all cogs"""
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            logger.info(f"Loaded cog: {cog}")
        except Exception as e:
            logger.error(f"Error loading cog {cog}: {e}")
            # Print more detailed error information
            import traceback
            logger.error(traceback.format_exc())

async def main():
    """Main function to run the bot"""
    # Validate configuration
    if not validate_config():
        logger.error("Invalid configuration. Check your .env file.")
        return
        
    
        
    # Create cogs directory if it doesn't exist
    os.makedirs("cogs", exist_ok=True)
    
    # Create __init__.py in cogs directory if it doesn't exist
    if not os.path.exists("cogs/__init__.py"):
        with open("cogs/__init__.py", "w") as f:
            f.write("# This file is required to make the cogs directory a Python package")
    
    # Load cogs
    logger.info("Loading cogs...")
    await load_cogs()
    
    # Run the bot
    logger.info("Starting bot...")
    try:
        async with bot:
            await bot.start(DISCORD_TOKEN)
    except discord.errors.LoginFailure:
        logger.error("Invalid Discord token. Please check your .env file.")
        print("ERROR: Invalid Discord token. Please check your .env file.")
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main()) 