from discord.ext import commands
from utils import create_embed, generate_pet_image, generate_battle_image, generate_pet
import asyncio
import discord
import random
from datetime import datetime, timedelta
from typing import Optional
from config import ADMIN_IDS
from database import (get_user_pets, set_user_pets, get_user_coins, 
                     set_user_coins, add_user_coins, get_user_inventory,
                     add_to_inventory, remove_from_inventory, _data)

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pranks_active = {}  # Store active pranks
        self.bot.start_time = datetime.utcnow()

    async def cog_check(self, ctx):
        """Check if user is an admin"""
        return str(ctx.author.id) in ADMIN_IDS

    @commands.command(name="adminhelp")
    async def admin_help(self, ctx):
        """Show all admin commands"""
        embed = create_embed(
            title="Admin Commands",
            description="Here are all available admin commands:",
            color=0xFF0000,
            fields=[
                ("User Management", "`!listusers` - List all users\n`!viewuser <user>` - View user details\n`!resetuser <user>` - Reset user data", False),
                ("Economy", "`!givecoins <user> <amount>` - Give coins to user\n`!giveitem <user> <item> <amount>` - Give item to user", False),
                ("Pet Management", "`!givepet <user> <rarity>` - Give pet to user\n`!setlevel <user> <pet_num> <level>` - Set pet level\n`!heal <user> <pet_num>` - Heal pet", False),
                ("System", "`!broadcast <message>` - Broadcast message\n`!stats` - View bot statistics", False)
            ]
        )
        await ctx.send(embed=embed)

    @commands.command(name="givecoins")
    async def give_coins(self, ctx, user: discord.Member, amount: int):
        """Give coins to a user"""
        if amount <= 0:
            await ctx.send("Amount must be positive!")
            return
            
        user_id = str(user.id)
        current_coins = get_user_coins(user_id)
        add_user_coins(user_id, amount)
        
        embed = create_embed(
            title="Coins Given!",
            description=f"Gave {amount} PetCoins to {user.mention}!",
            color=0xFFD700,
            fields=[
                ("Previous Balance", str(current_coins), True),
                ("Amount Added", str(amount), True),
                ("New Balance", str(current_coins + amount), True)
            ]
        )
        await ctx.send(embed=embed)

    @commands.command(name="givepet")
    async def give_pet(self, ctx, user: discord.Member, rarity: str = "common"):
        """Give a pet to a user"""
        rarity = rarity.lower()
        if rarity not in ["common", "rare", "mythic"]:
            await ctx.send("Invalid rarity! Use common, rare, or mythic.")
            return
            
        user_id = str(user.id)
        pets = get_user_pets(user_id)
        
        # Generate pet based on rarity
        new_pet = generate_pet(rare=(rarity == "rare"), mythic=(rarity == "mythic"))
        new_pet["level"] = 1
        new_pet["xp"] = 0
        
        pets.append(new_pet)
        set_user_pets(user_id, pets)
        
        # Generate and send pet image
        pet_image = await generate_pet_image(new_pet)
        
        embed = create_embed(
            title="Pet Given!",
            description=f"Gave a {rarity.capitalize()} pet to {user.mention}!",
            color=0x00FF00,
            fields=[
                ("Pet", new_pet['name'], True),
                ("Health", str(new_pet['health']), True),
                ("Happiness", str(new_pet['happiness']), True),
                ("Strength", str(new_pet['strength']), True),
                ("Level", "1", True),
                ("Rarity", new_pet['rarity'].capitalize(), True)
            ]
        )
        
        if pet_image:
            embed.set_image(url="attachment://pet.png")
            await ctx.send(embed=embed, file=pet_image)
        else:
            await ctx.send(embed=embed)

    @commands.command(name="giveitem")
    async def give_item(self, ctx, user: discord.Member, item: str, amount: int = 1):
        """Give an item to a user"""
        if amount <= 0:
            await ctx.send("Amount must be positive!")
            return
            
        user_id = str(user.id)
        add_to_inventory(user_id, item, amount)
        
        embed = create_embed(
            title="Item Given!",
            description=f"Gave {amount}x {item} to {user.mention}!",
            color=0xFFA500
        )
        await ctx.send(embed=embed)

    @commands.command(name="setlevel")
    async def set_level(self, ctx, user: discord.Member, pet_num: int, level: int):
        """Set a pet's level"""
        if level < 1 or level > 50:
            await ctx.send("Level must be between 1 and 50!")
            return
            
        user_id = str(user.id)
        pets = get_user_pets(user_id)
        
        if not pets or not 1 <= pet_num <= len(pets):
            await ctx.send("Invalid pet number!")
            return
            
        pet = pets[pet_num - 1]
        old_level = pet.get("level", 1)
        
        # Update pet stats based on level difference
        level_diff = level - old_level
        if level_diff > 0:
            pet["health"] = min(100, pet["health"] + level_diff * 2)
            pet["strength"] = min(50, pet["strength"] + level_diff)
            
        pet["level"] = level
        pet["xp"] = 0
        
        set_user_pets(user_id, pets)
        
        embed = create_embed(
            title="Level Updated!",
            description=f"Set {pet['name']}'s level to {level}!",
            color=0x00FF00
        )
        await ctx.send(embed=embed)

    @commands.command(name="heal")
    async def heal_pet(self, ctx, user: discord.Member, pet_num: int):
        """Fully heal a pet"""
        user_id = str(user.id)
        pets = get_user_pets(user_id)
        
        if not pets or not 1 <= pet_num <= len(pets):
            await ctx.send("Invalid pet number!")
            return
            
        pet = pets[pet_num - 1]
        old_health = pet["health"]
        pet["health"] = 100
        pet["happiness"] = 100
        
        set_user_pets(user_id, pets)
        
        embed = create_embed(
            title="Pet Healed!",
            description=f"Healed {pet['name']}!",
            color=0x00FF00,
            fields=[
                ("Previous Health", str(old_health), True),
                ("Current Health", "100", True),
                ("Happiness", "100", True)
            ]
        )
        await ctx.send(embed=embed)

    @commands.command(name="broadcast")
    async def broadcast(self, ctx, *, message: str):
        """Send a message to all servers"""
        if not message:
            await ctx.send("Cannot send an empty message!")
            return
            
        # Ask for confirmation
        guild_count = len(self.bot.guilds)
        embed = create_embed(
            title="Confirm Broadcast",
            description=f"Are you sure you want to send this message to all {guild_count} servers?",
            color=0xFF0000,
            fields=[
                ("Message", message, False)
            ]
        )
        confirm_msg = await ctx.send(embed=embed)
        
        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❌")
        
        def check(reaction, reactor):
            return (reactor == ctx.author and 
                    reaction.message.id == confirm_msg.id and 
                    str(reaction.emoji) in ["✅", "❌"])
                    
        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
            
            if str(reaction.emoji) == "✅":
                broadcast_embed = create_embed(
                    title="Announcement",
                    description=message,
                    color=0x9B59B6
                )
                
                successful = 0
                failed = 0
                
                for guild in self.bot.guilds:
                    try:
                        # Try to find system channel or general
                        channel = guild.system_channel or discord.utils.get(guild.text_channels, name="general")
                        if channel and channel.permissions_for(guild.me).send_messages:
                            await channel.send(embed=broadcast_embed)
                            successful += 1
                        else:
                            failed += 1
                    except:
                        failed += 1
                        
                await ctx.send(f"Broadcast complete! Sent to {successful} servers. Failed: {failed}")
            else:
                await ctx.send("Broadcast canceled.")
                
        except asyncio.TimeoutError:
            await ctx.send("Broadcast canceled due to timeout.")

    @commands.command(name="stats")
    async def stats(self, ctx):
        """View bot statistics"""
        guild_count = len(self.bot.guilds)
        total_members = sum(g.member_count for g in self.bot.guilds)
        
        # Get pet statistics
        total_pets = sum(len(pets) for pets in _data["pets"].values())
        total_coins = sum(_data["coins"].values())
        
        embed = create_embed(
            title="Bot Statistics",
            description="Current bot statistics",
            color=0x3498db,
            fields=[
                ("Servers", str(guild_count), True),
                ("Total Users", str(total_members), True),
                ("Total Pets", str(total_pets), True),
                ("Total Coins", str(total_coins), True),
                ("Active Users", str(len(_data["pets"])), True)
            ]
        )
        
        await ctx.send(embed=embed)

# Setup function for the cog
async def setup(bot):
    await bot.add_cog(AdminCommands(bot)) 