import discord
from discord.ext import commands
import random
from typing import Dict, Any, Optional
import time

from config import MAX_PETS, SHOP_ITEMS
from database import (get_user_pets, set_user_pets, get_user_coins, 
                     set_user_coins, add_user_coins, get_user_inventory,
                     add_to_inventory, remove_from_inventory)
from utils import generate_pet, format_pet_info, calculate_fight_rewards, create_embed

class PetCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pending_trades = {}  # Store pending trades
        self.pending_fights = {}  # Store pending fights

    @commands.command(name="adopt")
    async def adopt_pet(self, ctx):
        """Adopt a new pet"""
        user_id = str(ctx.author.id)
        pets = get_user_pets(user_id)
        
        if len(pets) >= MAX_PETS:
            await ctx.send(f"You already have {MAX_PETS} pets! Release or trade one first.")
            return
        
        new_pet = generate_pet()
        pets.append(new_pet)
        set_user_pets(user_id, pets)
        
        # Create an embed for the new pet
        embed = create_embed(
            title="New Pet Adopted!",
            description=f"{ctx.author.mention}, you've adopted a new pet!",
            color=0x00FF00,
            fields=[
                ("Pet", new_pet['name'], True),
                ("Health", str(new_pet['health']), True),
                ("Happiness", str(new_pet['happiness']), True),
                ("Strength", str(new_pet['strength']), True),
                ("Rarity", new_pet.get('rarity', 'Common').capitalize(), True)
            ]
        )
        
        await ctx.send(embed=embed)

    @commands.command(name="pets")
    async def list_pets(self, ctx):
        """List your pets"""
        user_id = str(ctx.author.id)
        pets = get_user_pets(user_id)
        
        if not pets:
            await ctx.send("You don't have any pets yet! Use `!adopt` to get one.")
            return
            
        # Create an embed with pet information
        embed = create_embed(
            title="Your Pets",
            description=f"{ctx.author.mention}, here are your pets:",
            color=0x3498db
        )
        
        for i, pet in enumerate(pets):
            embed.add_field(
                name=f"{i+1}. {pet['name']}",
                value=(f"Health: {pet['health']}\n"
                       f"Happiness: {pet['happiness']}\n"
                       f"Strength: {pet['strength']}\n"
                       f"Rarity: {pet.get('rarity', 'Common').capitalize()}"),
                inline=True
            )
            
        await ctx.send(embed=embed)

    @commands.command(name="feed")
    async def feed_pet(self, ctx, pet_num: int):
        """Feed one of your pets"""
        user_id = str(ctx.author.id)
        pets = get_user_pets(user_id)
        
        if not pets:
            await ctx.send("You don't have any pets to feed!")
            return
            
        if not 1 <= pet_num <= len(pets):
            await ctx.send(f"Invalid pet number! You have {len(pets)} pets.")
            return
            
        pet = pets[pet_num - 1]
        
        # Improve both health and happiness
        pet["health"] = min(100, pet["health"] + 20)
        pet["happiness"] = min(100, pet["happiness"] + 20)
        set_user_pets(user_id, pets)
        
        embed = create_embed(
            title="Pet Fed",
            description=f"{ctx.author.mention}, you fed your **{pet['name']}**!",
            color=0x00FF00,
            fields=[
                ("Health", f"+20 (now {pet['health']})", True),
                ("Happiness", f"+20 (now {pet['happiness']})", True)
            ]
        )
        
        await ctx.send(embed=embed)

    @commands.command(name="breed")
    async def breed_pets(self, ctx, pet1: int, pet2: int):
        """Breed two of your pets"""
        user_id = str(ctx.author.id)
        pets = get_user_pets(user_id)
        
        if len(pets) < 2:
            await ctx.send("You need at least 2 pets to breed! Adopt more with `!adopt`.")
            return
            
        if not (1 <= pet1 <= len(pets) and 1 <= pet2 <= len(pets)) or pet1 == pet2:
            await ctx.send(f"Invalid pet numbers! You have {len(pets)} pets.")
            return
            
        parent1 = pets[pet1 - 1]
        parent2 = pets[pet2 - 1]
        
        # Extract traits from pet names
        p1_traits = parent1["name"].split()
        p2_traits = parent2["name"].split()
        
        # Create hybrid pet
        hybrid_color = random.choice([p1_traits[0], p2_traits[0]])
        hybrid_trait = random.choice([p1_traits[1], p2_traits[1]])
        hybrid_species = random.choice([p1_traits[2], p2_traits[2]])
        
        # Determine rarity - chance for upgrade
        rarity1 = parent1.get("rarity", "common")
        rarity2 = parent2.get("rarity", "common")
        rarity_upgrade_chance = 0.2  # 20% chance for rarity upgrade
        
        if rarity1 == "mythic" or rarity2 == "mythic":
            new_rarity = "mythic" if random.random() < 0.4 else "rare"
        elif rarity1 == "rare" and rarity2 == "rare":
            new_rarity = "mythic" if random.random() < rarity_upgrade_chance else "rare"
        elif rarity1 == "rare" or rarity2 == "rare":
            new_rarity = "rare" if random.random() < 0.6 else "common"
        else:
            new_rarity = "rare" if random.random() < rarity_upgrade_chance else "common"
            
        # Create new pet with averaged stats and possible bonus
        new_pet = {
            "name": f"{hybrid_color} {hybrid_trait} {hybrid_species}",
            "health": min(100, (parent1["health"] + parent2["health"]) // 2 + random.randint(0, 10)),
            "happiness": min(100, (parent1["happiness"] + parent2["happiness"]) // 2 + random.randint(0, 10)),
            "strength": min(50, (parent1["strength"] + parent2["strength"]) // 2 + random.randint(0, 5)),
            "rarity": new_rarity,
            "created_at": time.time()
        }
        
        # Check if at max pets capacity
        if len(pets) >= MAX_PETS:
            # If at max capacity, replace one parent with the child
            pets.pop(pet1 - 1)
            pets.append(new_pet)
            set_user_pets(user_id, pets)
            
            embed = create_embed(
                title="Pets Bred (Parent Replaced)",
                description=f"{ctx.author.mention}, your **{parent1['name']}** was replaced by its child!",
                color=0xFFA500
            )
        else:
            # If under capacity, just add the child
            pets.append(new_pet)
            set_user_pets(user_id, pets)
            
            embed = create_embed(
                title="Pets Bred",
                description=f"{ctx.author.mention}, your pets had a child!",
                color=0xFFA500
            )
            
        # Add fields with parent and child info
        embed.add_field(name="Parent 1", value=parent1['name'], inline=True)
        embed.add_field(name="Parent 2", value=parent2['name'], inline=True)
        embed.add_field(name="Child", value=new_pet['name'], inline=True)
        
        embed.add_field(name="Health", value=str(new_pet['health']), inline=True)
        embed.add_field(name="Happiness", value=str(new_pet['happiness']), inline=True)
        embed.add_field(name="Strength", value=str(new_pet['strength']), inline=True)
        embed.add_field(name="Rarity", value=new_pet['rarity'].capitalize(), inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="release")
    async def release_pet(self, ctx, pet_num: int):
        """Release a pet into the wild"""
        user_id = str(ctx.author.id)
        pets = get_user_pets(user_id)
        
        if not pets:
            await ctx.send("You don't have any pets to release!")
            return
            
        if not 1 <= pet_num <= len(pets):
            await ctx.send(f"Invalid pet number! You have {len(pets)} pets.")
            return
            
        released_pet = pets.pop(pet_num - 1)
        set_user_pets(user_id, pets)
        
        # Give coins based on pet's rarity
        reward = 0
        if "rarity" in released_pet:
            if released_pet["rarity"] == "rare":
                reward = random.randint(30, 50)
            elif released_pet["rarity"] == "mythic":
                reward = random.randint(80, 120)
            else:  # common
                reward = random.randint(10, 30)
        else:
            reward = random.randint(10, 30)
            
        if reward > 0:
            add_user_coins(user_id, reward)
        
        embed = create_embed(
            title="Pet Released",
            description=f"{ctx.author.mention}, you've released your **{released_pet['name']}** into the wild!",
            color=0xFF0000,
            fields=[("Reward", f"You received {reward} PetCoins", False)] if reward > 0 else None
        )
        
        await ctx.send(embed=embed)

    @commands.command(name="fight")
    async def fight_pet(self, ctx, pet_num: int, target: discord.Member):
        """Challenge another user to a pet battle"""
        if target.bot:
            await ctx.send("You can't challenge a bot to a pet battle!")
            return
            
        if target.id == ctx.author.id:
            await ctx.send("You can't challenge yourself to a pet battle!")
            return
            
        user_id = str(ctx.author.id)
        target_id = str(target.id)
        
        # Get pets for both users
        pets = get_user_pets(user_id)
        target_pets = get_user_pets(target_id)
        
        if not pets:
            await ctx.send("You don't have any pets to fight with!")
            return
            
        if not target_pets:
            await ctx.send(f"{target.mention} doesn't have any pets to fight!")
            return
            
        if not 1 <= pet_num <= len(pets):
            await ctx.send(f"Invalid pet number! You have {len(pets)} pets.")
            return
            
        # Get the attacker's pet
        attacker_pet = pets[pet_num - 1]
        
        # Store the fight in pending fights
        self.pending_fights[target_id] = {
            "challenger": ctx.author,
            "challenger_pet": attacker_pet,
            "challenger_pet_idx": pet_num - 1,
            "channel": ctx.channel
        }
        
        # Create an embed for the challenge
        embed = create_embed(
            title="Pet Battle Challenge!",
            description=f"{target.mention}, {ctx.author.mention} challenges you to a pet battle!",
            color=0xFF0000,
            fields=[
                ("Challenger Pet", format_pet_info(attacker_pet), False),
                ("Instructions", "Reply with `!accept <pet_number>` to accept or `!decline` to decline", False)
            ]
        )
        
        await ctx.send(embed=embed)
        
    @commands.command(name="accept")
    async def accept_fight(self, ctx, pet_num: int):
        """Accept a pet battle challenge"""
        user_id = str(ctx.author.id)
        
        if user_id not in self.pending_fights:
            await ctx.send("You don't have any pending fight challenges!")
            return
            
        pets = get_user_pets(user_id)
        
        if not 1 <= pet_num <= len(pets):
            await ctx.send(f"Invalid pet number! You have {len(pets)} pets.")
            return
            
        # Get fight info
        fight = self.pending_fights[user_id]
        challenger = fight["challenger"]
        challenger_pet = fight["challenger_pet"]
        challenger_pet_idx = fight["challenger_pet_idx"]
        
        # Get defender pet
        defender_pet = pets[pet_num - 1]
        
        # Battle logic
        challenger_roll = random.randint(1, challenger_pet["strength"])
        defender_roll = random.randint(1, defender_pet["strength"])
        
        # Update pet stats
        challenger_pets = get_user_pets(str(challenger.id))
        if challenger_pet_idx < len(challenger_pets):
            challenger_pet = challenger_pets[challenger_pet_idx]  # Make sure we have current stats
            
        # Pet takes damage
        challenger_pet["health"] = max(1, challenger_pet["health"] - random.randint(5, 15))
        defender_pet["health"] = max(1, defender_pet["health"] - random.randint(5, 15))
        
        # Determine winner
        if challenger_roll > defender_roll:
            winner = challenger
            loser = ctx.author
            winner_pet = challenger_pet
            loser_pet = defender_pet
            
            # Calculate reward
            prize = calculate_fight_rewards(winner_pet, loser_pet)
            
            # Award coins
            add_user_coins(str(winner.id), prize)
            
            # Update pets
            challenger_pets[challenger_pet_idx] = challenger_pet
            set_user_pets(str(challenger.id), challenger_pets)
            
            pets[pet_num - 1] = defender_pet
            set_user_pets(user_id, pets)
            
            result_description = f"{winner.mention} wins! They earn {prize} PetCoins."
        else:
            winner = ctx.author
            loser = challenger
            winner_pet = defender_pet
            loser_pet = challenger_pet
            
            # Calculate reward
            prize = calculate_fight_rewards(winner_pet, loser_pet)
            
            # Award coins
            add_user_coins(str(winner.id), prize)
            
            # Update pets
            challenger_pets[challenger_pet_idx] = challenger_pet
            set_user_pets(str(challenger.id), challenger_pets)
            
            pets[pet_num - 1] = defender_pet
            set_user_pets(user_id, pets)
            
            result_description = f"{winner.mention} wins! They earn {prize} PetCoins."
            
        # Remove pending fight
        del self.pending_fights[user_id]
        
        # Send results
        embed = create_embed(
            title="Battle Results",
            description=result_description,
            color=0xFF9900,
            fields=[
                (f"{challenger.name}'s Pet", f"{challenger_pet['name']} (Roll: {challenger_roll}, Health: {challenger_pet['health']})", True),
                (f"{ctx.author.name}'s Pet", f"{defender_pet['name']} (Roll: {defender_roll}, Health: {defender_pet['health']})", True),
                ("Winner", winner.mention, False)
            ]
        )
        
        await ctx.send(embed=embed)
        
    @commands.command(name="decline")
    async def decline_fight(self, ctx):
        """Decline a pet battle challenge"""
        user_id = str(ctx.author.id)
        
        if user_id not in self.pending_fights:
            await ctx.send("You don't have any pending fight challenges!")
            return
            
        # Get challenger
        challenger = self.pending_fights[user_id]["challenger"]
        
        # Remove pending fight
        del self.pending_fights[user_id]
        
        await ctx.send(f"{ctx.author.mention} declined {challenger.mention}'s battle challenge.")

    @commands.command(name="trade")
    async def trade_pet(self, ctx, pet_num: int, target: discord.Member):
        """Offer to trade a pet with another user"""
        if target.bot:
            await ctx.send("You can't trade with a bot!")
            return
            
        if target.id == ctx.author.id:
            await ctx.send("You can't trade with yourself!")
            return
            
        user_id = str(ctx.author.id)
        target_id = str(target.id)
        
        # Get pets
        pets = get_user_pets(user_id)
        target_pets = get_user_pets(target_id)
        
        if not pets:
            await ctx.send("You don't have any pets to trade!")
            return
            
        if not 1 <= pet_num <= len(pets):
            await ctx.send(f"Invalid pet number! You have {len(pets)} pets.")
            return
            
        if len(target_pets) >= MAX_PETS:
            await ctx.send(f"{target.mention} already has the maximum number of pets!")
            return
            
        # Get the offered pet
        offered_pet = pets[pet_num - 1]
        
        # Store the trade offer
        self.pending_trades[target_id] = {
            "offerer": ctx.author,
            "offerer_pet": offered_pet,
            "offerer_pet_idx": pet_num - 1,
            "channel": ctx.channel
        }
        
        # Create an embed for the trade offer
        embed = create_embed(
            title="Pet Trade Offer",
            description=f"{target.mention}, {ctx.author.mention} wants to trade a pet with you!",
            color=0x00FF00,
            fields=[
                ("Offered Pet", format_pet_info(offered_pet), False),
                ("Instructions", "Reply with `!tradeaccept <your_pet_number>` to accept the trade or `!tradedecline` to decline", False)
            ]
        )
        
        await ctx.send(embed=embed)
        
    @commands.command(name="tradeaccept")
    async def accept_trade(self, ctx, pet_num: int):
        """Accept a pet trade offer"""
        user_id = str(ctx.author.id)
        
        if user_id not in self.pending_trades:
            await ctx.send("You don't have any pending trade offers!")
            return
            
        # Get trade info
        trade = self.pending_trades[user_id]
        offerer = trade["offerer"]
        offerer_pet = trade["offerer_pet"]
        offerer_pet_idx = trade["offerer_pet_idx"]
        
        # Get pets
        offerer_pets = get_user_pets(str(offerer.id))
        acceptor_pets = get_user_pets(user_id)
        
        # Validate pet numbers
        if offerer_pet_idx >= len(offerer_pets):
            await ctx.send("The offered pet is no longer available.")
            del self.pending_trades[user_id]
            return
            
        if not 1 <= pet_num <= len(acceptor_pets):
            await ctx.send(f"Invalid pet number! You have {len(acceptor_pets)} pets.")
            return
            
        # Get the pets to trade
        acceptor_pet = acceptor_pets[pet_num - 1]
        
        # Execute the trade
        acceptor_pets[pet_num - 1] = offerer_pet
        offerer_pets[offerer_pet_idx] = acceptor_pet
        
        # Update the database
        set_user_pets(user_id, acceptor_pets)
        set_user_pets(str(offerer.id), offerer_pets)
        
        # Remove the pending trade
        del self.pending_trades[user_id]
        
        # Create an embed for the trade result
        embed = create_embed(
            title="Trade Completed!",
            description=f"{ctx.author.mention} and {offerer.mention} have completed a pet trade!",
            color=0x00FF00,
            fields=[
                (f"{offerer.name} Traded", format_pet_info(offerer_pet), True),
                (f"{ctx.author.name} Traded", format_pet_info(acceptor_pet), True)
            ]
        )
        
        await ctx.send(embed=embed)
        
    @commands.command(name="tradedecline")
    async def decline_trade(self, ctx):
        """Decline a pet trade offer"""
        user_id = str(ctx.author.id)
        
        if user_id not in self.pending_trades:
            await ctx.send("You don't have any pending trade offers!")
            return
            
        # Get offerer
        offerer = self.pending_trades[user_id]["offerer"]
        
        # Remove pending trade
        del self.pending_trades[user_id]
        
        await ctx.send(f"{ctx.author.mention} declined {offerer.mention}'s trade offer.")

# Setup function for the cog
async def setup(bot):
    await bot.add_cog(PetCommands(bot)) 