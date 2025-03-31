import discord
from discord.ext import commands
import time
from typing import Dict, Any, Optional

from config import SHOP_ITEMS, STARTING_COINS
from database import (get_user_pets, set_user_pets, get_user_coins, 
                     set_user_coins, add_user_coins, get_user_inventory,
                     add_to_inventory, remove_from_inventory, get_last_daily,
                     set_last_daily)
from utils import generate_pet, format_pet_info, create_embed, can_claim_daily

class ShopCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="shop")
    async def shop(self, ctx):
        """Display the shop items"""
        user_id = str(ctx.author.id)
        user_coins = get_user_coins(user_id)
        
        # Create shop embed
        embed = create_embed(
            title="Pet Shop",
            description=f"{ctx.author.mention}, welcome to the Pet Shop! You have **{user_coins} PetCoins**.",
            color=0xFFA500
        )
        
        # Add each shop item as a field
        for item_name, details in SHOP_ITEMS.items():
            embed.add_field(
                name=f"{item_name} - {details['cost']} PetCoins",
                value=details['description'],
                inline=False
            )
            
        embed.add_field(
            name="How to Buy",
            value="Use `!buy <item_name>` to purchase an item",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @commands.command(name="buy")
    async def buy_item(self, ctx, *, item_name: str):
        """Buy an item from the shop"""
        user_id = str(ctx.author.id)
        user_coins = get_user_coins(user_id)
        
        # Normalize item name for case-insensitive lookup
        item = item_name.lower()
        item_key = None
        
        # Find matching item (case-insensitive)
        for shop_item in SHOP_ITEMS:
            if shop_item.lower() == item:
                item_key = shop_item
                break
                
        if not item_key:
            await ctx.send(f"{ctx.author.mention}, '{item_name}' isn't in the shop! Use `!shop` to see available items.")
            return
            
        # Check if user has enough coins
        cost = SHOP_ITEMS[item_key]["cost"]
        if user_coins < cost:
            await ctx.send(f"{ctx.author.mention}, you need {cost} PetCoins, but you only have {user_coins}!")
            return
            
        # Process the purchase based on item type
        pets = get_user_pets(user_id)
        
        if item_key in ["SuperPet", "MythicPet"]:
            # If buying a pet, check if user has room
            if len(pets) >= 5:  # Max pets from config
                await ctx.send(f"{ctx.author.mention}, you already have the maximum number of pets! Release or trade one first.")
                return
                
            # Generate pet based on rarity
            new_pet = None
            if item_key == "SuperPet":
                new_pet = generate_pet(rare=True)
            else:  # MythicPet
                new_pet = generate_pet(mythic=True)
                
            # Add the pet and update user data
            pets.append(new_pet)
            set_user_pets(user_id, pets)
            set_user_coins(user_id, user_coins - cost)
            
            # Create success embed
            embed = create_embed(
                title="Pet Purchased!",
                description=f"{ctx.author.mention}, you've purchased a **{new_pet['name']}** for {cost} PetCoins!",
                color=0x00FF00,
                fields=[
                    ("Health", str(new_pet['health']), True),
                    ("Happiness", str(new_pet['happiness']), True),
                    ("Strength", str(new_pet['strength']), True),
                    ("Rarity", new_pet['rarity'].capitalize(), True),
                    ("Remaining Balance", f"{user_coins - cost} PetCoins", False)
                ]
            )
            
            await ctx.send(embed=embed)
        else:
            # For consumable items, add to inventory
            add_to_inventory(user_id, item_key)
            set_user_coins(user_id, user_coins - cost)
            
            # Create success embed
            embed = create_embed(
                title="Item Purchased!",
                description=f"{ctx.author.mention}, you've purchased **{item_key}** for {cost} PetCoins!",
                color=0x00FF00,
                fields=[
                    ("Item", SHOP_ITEMS[item_key]["description"], False),
                    ("Usage", f"Use `!use {item_key} <pet_number>` to use this item", False),
                    ("Remaining Balance", f"{user_coins - cost} PetCoins", False)
                ]
            )
            
            await ctx.send(embed=embed)

    @commands.command(name="inventory", aliases=["inv"])
    async def inventory(self, ctx):
        """View your inventory"""
        user_id = str(ctx.author.id)
        inventory = get_user_inventory(user_id)
        
        if not inventory:
            await ctx.send(f"{ctx.author.mention}, your inventory is empty! Visit `!shop` to buy items.")
            return
            
        # Create inventory embed
        embed = create_embed(
            title="Your Inventory",
            description=f"{ctx.author.mention}, here are your items:",
            color=0x3498db
        )
        
        # Add each inventory item as a field
        for item, quantity in inventory.items():
            if item in SHOP_ITEMS:
                embed.add_field(
                    name=f"{item} (x{quantity})",
                    value=SHOP_ITEMS[item]["description"],
                    inline=False
                )
            else:
                embed.add_field(
                    name=f"{item} (x{quantity})",
                    value="No description available",
                    inline=False
                )
                
        embed.add_field(
            name="How to Use",
            value="Use `!use <item_name> <pet_number>` to use an item on one of your pets",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @commands.command(name="use")
    async def use_item(self, ctx, item_name: str, pet_num: int):
        """Use an item from your inventory on a pet"""
        user_id = str(ctx.author.id)
        inventory = get_user_inventory(user_id)
        pets = get_user_pets(user_id)
        
        # Check if item exists in inventory
        if item_name not in inventory or inventory[item_name] <= 0:
            await ctx.send(f"{ctx.author.mention}, you don't have any **{item_name}** in your inventory!")
            return
            
        # Check if pet number is valid
        if not pets or not 1 <= pet_num <= len(pets):
            await ctx.send(f"{ctx.author.mention}, invalid pet number! Use `!pets` to see your pets.")
            return
            
        # Get the pet to use the item on
        pet = pets[pet_num - 1]
        item_used = False
        result_text = ""
        
        # Apply item effects
        if item_name == "Food":
            pet["health"] = min(100, pet["health"] + 20)
            pet["happiness"] = min(100, pet["happiness"] + 20)
            item_used = True
            result_text = f"You fed your **{pet['name']}**! Health and Happiness +20."
            
        elif item_name == "SuperFood":
            pet["health"] = min(100, pet["health"] + 40)
            pet["happiness"] = min(100, pet["happiness"] + 40)
            item_used = True
            result_text = f"You fed your **{pet['name']}** super food! Health and Happiness +40."
            
        elif item_name == "HealthPotion":
            old_health = pet["health"]
            pet["health"] = 100
            item_used = True
            result_text = f"You gave your **{pet['name']}** a health potion! Health restored from {old_health} to 100."
            
        elif item_name == "HappinessPotion":
            old_happiness = pet["happiness"]
            pet["happiness"] = 100
            item_used = True
            result_text = f"You gave your **{pet['name']}** a happiness potion! Happiness restored from {old_happiness} to 100."
            
        # If item was used successfully
        if item_used:
            # Remove the item from inventory
            remove_from_inventory(user_id, item_name)
            
            # Update the pet
            set_user_pets(user_id, pets)
            
            # Create success embed
            embed = create_embed(
                title="Item Used",
                description=result_text,
                color=0x00FF00,
                fields=[
                    ("Pet", pet['name'], True),
                    ("Health", str(pet['health']), True),
                    ("Happiness", str(pet['happiness']), True)
                ]
            )
            
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{ctx.author.mention}, this item cannot be used on pets.")

    @commands.command(name="balance", aliases=["coins"])
    async def check_balance(self, ctx):
        """Check your PetCoin balance"""
        user_id = str(ctx.author.id)
        coins = get_user_coins(user_id)
        
        embed = create_embed(
            title="Your Balance",
            description=f"{ctx.author.mention}, you have **{coins} PetCoins**.",
            color=0xFFD700
        )
        
        await ctx.send(embed=embed)

    @commands.command(name="daily")
    async def daily_reward(self, ctx):
        """Claim your daily reward"""
        user_id = str(ctx.author.id)
        last_claim = get_last_daily(user_id)
        
        # Check if user can claim daily reward
        can_claim, time_until = can_claim_daily(last_claim)
        
        if not can_claim:
            await ctx.send(f"{ctx.author.mention}, you've already claimed your daily reward! You can claim again in **{time_until}**.")
            return
            
        # Generate random reward
        coins_reward = 50
        add_user_coins(user_id, coins_reward)
        
        # Random bonus item (20% chance)
        got_bonus = False
        bonus_item = None
        
        if time.time() % 5 == 0:  # Simple 20% chance calculation
            got_bonus = True
            # Choose a random consumable item
            consumables = ["Food", "SuperFood"]
            bonus_item = consumables[int(time.time()) % len(consumables)]
            add_to_inventory(user_id, bonus_item)
        
        # Update last claim time
        set_last_daily(user_id, time.time())
        
        # Create embed with daily reward info
        embed = create_embed(
            title="Daily Reward Claimed!",
            description=f"{ctx.author.mention}, you've claimed your daily reward!",
            color=0xFFD700,
            fields=[
                ("Coins", f"+{coins_reward} PetCoins", False)
            ]
        )
        
        if got_bonus:
            embed.add_field(
                name="Bonus Item",
                value=f"You also received a **{bonus_item}**!",
                inline=False
            )
            
        # Add streak info if implemented
            
        await ctx.send(embed=embed)

# Setup function for the cog
async def setup(bot):
    await bot.add_cog(ShopCommands(bot)) 