import discord
from discord.ext import commands
import random
from typing import Dict, Any, Optional, List
import time
import asyncio
import io
from datetime import datetime, timedelta

from config import MAX_PETS, SHOP_ITEMS, MAX_HEALTH, MAX_LEVEL, XP_PER_LEVEL, BASIC_MOVES, ADVANCED_MOVES, MOVES_BY_LEVEL, DOMAIN_EXPANSIONS
from database import (get_user_pets, set_user_pets, get_user_coins, 
                     set_user_coins, add_user_coins, get_user_inventory,
                     add_to_inventory, remove_from_inventory, _data)
from utils import generate_pet, format_pet_info, calculate_fight_rewards, create_embed, generate_pet_image, generate_battle_image, load_pet_image

class PetCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pending_trades = {}  # Store pending trades
        self.pending_fights = {}  # Store pending fights
        self.domain_cooldowns = {}  # Store cooldowns for domain expansion

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
        
        # Generate and attach pet image
        try:
            pet_image = await generate_pet_image(new_pet)
            if pet_image:
                embed.set_image(url="attachment://pet.png")
                await ctx.send(embed=embed, file=pet_image)
            else:
                await ctx.send(embed=embed)
        except Exception as e:
            print(f"Error generating pet image: {e}")
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
            
        # Send initial list without images
        await ctx.send(embed=embed)
        
        # Ask if user wants to see pet images
        if len(pets) > 0:
            view_msg = await ctx.send("Would you like to see your pet images? React with 🖼️ to view.")
            await view_msg.add_reaction("🖼️")
            
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) == "🖼️" and reaction.message.id == view_msg.id
                
            try:
                await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
                
                # User wants to see pet images
                for i, pet in enumerate(pets):
                    try:
                        pet_image = await generate_pet_image(pet)
                        if pet_image:
                            pet_embed = create_embed(
                                title=f"Pet #{i+1}: {pet['name']}",
                                description=f"Health: {pet['health']}, Happiness: {pet['happiness']}, Strength: {pet['strength']}\nRarity: {pet.get('rarity', 'Common').capitalize()}",
                                color=0x3498db
                            )
                            pet_embed.set_image(url="attachment://pet.png")
                            await ctx.send(embed=pet_embed, file=pet_image)
                        else:
                            await ctx.send(f"Could not generate image for {pet['name']}")
                    except Exception as e:
                        print(f"Error generating pet image: {e}")
                        await ctx.send(f"Error showing image for {pet['name']}")
                        
            except asyncio.TimeoutError:
                await view_msg.edit(content="Image view request timed out.")
                await view_msg.clear_reactions()

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

    async def animate_domain_expansion(self, ctx, pet, domain_data):
        """Create an enhanced animated sequence for domain expansion"""
        # Initial power-up animation
        power_up_frames = [
            "```\n   ⚡   \n  ⚡⚡  \n ⚡🔮⚡ \n  ⚡⚡  \n   ⚡   ```",
            "```\n   💫   \n  💫💫  \n 💫🔮💫 \n  💫💫  \n   💫   ```",
            "```\n   ✨   \n  ✨✨  \n ✨🔮✨ \n  ✨✨  \n   ✨   ```"
        ]
        
        msg = await ctx.send(f"**{pet['name']}** begins to channel immense power...")
        for frame in power_up_frames:
            await msg.edit(content=f"**{pet['name']}** channels their power...\n{frame}")
            await asyncio.sleep(0.7)
        
        # Domain announcement with dramatic effect
        announcement = [
            "```\n╔══════════════╗\n║ D O M A I N ║\n║              ║\n║ EXPANSION!! ║\n╚══════════════╝```",
            "```\n╔══════════════╗\n║⚡D O M A I N⚡║\n║   ══════    ║\n║⚡EXPANSION!!⚡║\n╚══════════════╝```",
            "```\n╔══════════════╗\n║💫D O M A I N💫║\n║   ══════    ║\n║💫EXPANSION!!💫║\n╚══════════════╝```"
        ]
        
        for frame in announcement:
            await msg.edit(content=frame)
            await asyncio.sleep(0.8)
        
        # Domain specific animation
        domain_frames = []
        if pet['species'] == "Dragon":
            domain_frames = [
                "```\n🔥  🐉  🔥\n 🔥🔥🔥 \n  🌋🌋  ```",
                "```\n🌋  🐉  🌋\n 🔥🐉🔥 \n  🌋🌋  ```",
                "```\n💥  🐉  💥\n 🌋🐉🌋 \n  💥💥  ```"
            ]
        elif pet['species'] == "Phoenix":
            domain_frames = [
                "```\n☀️  🦅  ☀️\n ✨✨✨ \n  🌟🌟  ```",
                "```\n🌟  🦅  🌟\n ☀️🦅☀️ \n  ✨✨  ```",
                "```\n✨  🦅  ✨\n 🌟🦅🌟 \n  ☀️☀️  ```"
            ]
        elif pet['species'] == "Unicorn":
            domain_frames = [
                "```\n⭐  🦄  ⭐\n 💫💫💫 \n  ✨✨  ```",
                "```\n💫  🦄  💫\n ⭐🦄⭐ \n  💫💫  ```",
                "```\n✨  🦄  ✨\n 💫🦄💫 \n  ⭐⭐  ```"
            ]
        elif pet['species'] == "Griffin":
            domain_frames = [
                "```\n⚡  🦅  ⚡\n 🌪️🌪️🌪️ \n  ⛈️⛈️  ```",
                "```\n🌪️  🦅  🌪️\n ⚡🦅⚡ \n  🌪️🌪️  ```",
                "```\n⛈️  🦅  ⛈️\n 🌪️🦅🌪️ \n  ⚡⚡  ```"
            ]
        
        # Animate domain frames
        await msg.edit(content=f"**{domain_data['name']}**")
        for _ in range(2):
            for frame in domain_frames:
                await msg.edit(content=f"**{domain_data['name']}**\n{frame}")
                await asyncio.sleep(0.6)
        
        # Final impact animation
        impact_frames = [
            "```\n  💥💥💥  \n 💥💥💥💥 \n💥💥💥💥💥\n 💥💥💥💥 \n  💥💥💥  ```",
            "```\n  ⚡⚡⚡  \n ⚡⚡⚡⚡ \n⚡⚡⚡⚡⚡\n ⚡⚡⚡⚡ \n  ⚡⚡⚡  ```",
            "```\n  ✨✨✨  \n ✨✨✨✨ \n✨✨✨✨✨\n ✨✨✨✨ \n  ✨✨✨  ```"
        ]
        
        for frame in impact_frames:
            await msg.edit(content=f"**{domain_data['name']}**\n{frame}\n{domain_data['description']}")
            await asyncio.sleep(0.5)
        
        return msg

    async def can_use_domain_expansion(self, user_id: str, pet: Dict[str, Any]) -> bool:
        """Check if a pet can use domain expansion"""
        if pet['rarity'] != 'mythic':
            return False
            
        cooldown_key = f"{user_id}_{pet['name']}"
        last_used = self.domain_cooldowns.get(cooldown_key)
        
        if last_used:
            # Check if 24 hours have passed
            time_diff = datetime.now() - last_used
            if time_diff < timedelta(days=1):
                return False
                
        return True

    @commands.command(name="fight")
    async def fight(self, ctx, opponent: discord.Member, pet_num: int = 1):
        """Start a battle with another user's pet"""
        if opponent.bot:
            await ctx.send("You can't fight with a bot!")
            return
            
        if opponent == ctx.author:
            await ctx.send("You can't fight with yourself!")
            return
            
        challenger_id = str(ctx.author.id)
        opponent_id = str(opponent.id)
        
        # Get pets
        challenger_pets = get_user_pets(challenger_id)
        opponent_pets = get_user_pets(opponent_id)
        
        if not challenger_pets or not opponent_pets:
            await ctx.send("Both users need to have pets to fight!")
            return
            
        if pet_num < 1 or pet_num > len(challenger_pets):
            await ctx.send("Invalid pet number!")
            return
            
        challenger_pet = challenger_pets[pet_num - 1]
        
        # Send challenge
        embed = create_embed(
            title="Pet Battle Challenge!",
            description=f"{ctx.author.mention} challenges {opponent.mention} to a battle!\n"
                       f"Pet: {challenger_pet['name']}\n\n"
                       f"{opponent.mention}, choose your pet number to accept, or type 'decline' to refuse.",
            color=0xFF0000
        )
        
        challenge_msg = await ctx.send(embed=embed)
        
        def check(m):
            if m.author != opponent:
                return False
            if m.channel != ctx.channel:
                return False
            return m.content.lower() == 'decline' or m.content.isdigit()
            
        try:
            response = await self.bot.wait_for('message', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(f"{opponent.mention} didn't respond in time. Challenge expired!")
            return
            
        if response.content.lower() == 'decline':
            await ctx.send(f"{opponent.mention} declined the challenge!")
            return
            
        try:
            opponent_pet_num = int(response.content)
            if opponent_pet_num < 1 or opponent_pet_num > len(opponent_pets):
                await ctx.send("Invalid pet number!")
                return
                
            opponent_pet = opponent_pets[opponent_pet_num - 1]
        except ValueError:
            await ctx.send("Invalid response!")
            return
            
        # Start battle
        battle = await self.start_battle(ctx, challenger_pet, opponent_pet, ctx.author, opponent)
        
        # Update pets after battle
        challenger_pets[pet_num - 1] = challenger_pet
        opponent_pets[opponent_pet_num - 1] = opponent_pet
        
        set_user_pets(challenger_id, challenger_pets)
        set_user_pets(opponent_id, opponent_pets)
        
        # Give rewards
        if battle["winner"] == "challenger":
            reward = calculate_fight_rewards(challenger_pet, opponent_pet)
            add_user_coins(challenger_id, reward)
            await ctx.send(f"{ctx.author.mention} won {reward} coins!")
        elif battle["winner"] == "opponent":
            reward = calculate_fight_rewards(opponent_pet, challenger_pet)
            add_user_coins(opponent_id, reward)
            await ctx.send(f"{opponent.mention} won {reward} coins!")

    async def start_battle(self, ctx, pet1, pet2, owner1, owner2):
        """Handle the battle between two pets"""
        # Get available moves for each pet based on level
        pet1_level = pet1.get("level", 1)
        pet2_level = pet2.get("level", 1)
        
        pet1_moves = self.get_available_moves(pet1_level)
        pet2_moves = self.get_available_moves(pet2_level)
        
        # Add domain expansion if available
        can_use_domain1 = await self.can_use_domain_expansion(str(owner1.id), pet1)
        can_use_domain2 = await self.can_use_domain_expansion(str(owner2.id), pet2)
        
        if can_use_domain1 and pet1['species'] in DOMAIN_EXPANSIONS:
            pet1_moves.append("DOMAIN EXPANSION")
        if can_use_domain2 and pet2['species'] in DOMAIN_EXPANSIONS:
            pet2_moves.append("DOMAIN EXPANSION")
        
        # Generate battle image
        battle_image = await generate_battle_image(pet1, pet2)
        
        # Initial battle state
        current_hp1 = pet1["health"]
        current_hp2 = pet2["health"]
        
        # Battle loop
        current_turn = "challenger"
        turn_count = 0
        
        # Battle start animation
        vs_animation = [
            "```\n╔═══════ VS ═══════╗\n║                  ║\n║    🆚 BATTLE    ║\n║                  ║\n╚══════════════════╝```",
            "```\n╔═══════⚡VS⚡═══════╗\n║     PREPARE     ║\n║    🆚 BATTLE    ║\n║    TO FIGHT!    ║\n╚══════════════════╝```",
            "```\n╔═══════💥VS💥═══════╗\n║    BATTLE!!!    ║\n║    🆚 START     ║\n║     NOW!!!      ║\n╚══════════════════╝```"
        ]
        
        for frame in vs_animation:
            await ctx.send(frame)
            await asyncio.sleep(1)
        
        while current_hp1 > 0 and current_hp2 > 0:
            # Show battle status with ASCII art arena
            arena_frame = f"```\n╔══════════════════════╗\n║ {pet1['name'][:10]:^10} VS {pet2['name'][:10]:^10} ║\n║ HP: {current_hp1:^3}/{pet1['health']:^3}  {current_hp2:^3}/{pet2['health']:^3} ║\n╚══════════════════════╝```"
            
            status_embed = create_embed(
                title="⚔️ Battle Arena ⚔️",
                description=arena_frame,
                color=0xFF0000
            )
            
            if battle_image:
                status_embed.set_image(url="attachment://battle.png")
                await ctx.send(embed=status_embed, file=battle_image)
            else:
                await ctx.send(embed=status_embed)
            
            # Get current player and moves
            current_player = owner1 if current_turn == "challenger" else owner2
            current_pet = pet1 if current_turn == "challenger" else pet2
            current_moves = pet1_moves if current_turn == "challenger" else pet2_moves
            
            # Show available moves with fancy formatting
            moves_text = "\n".join([
                f"{i+1}. {'🌟 ' if move == 'DOMAIN EXPANSION' else ''}{move}" + 
                (" - 🌈 DOMAIN EXPANSION! 🌈" if move == "DOMAIN EXPANSION" else 
                f" - ⚔️ Power: {BASIC_MOVES.get(move, ADVANCED_MOVES.get(move))['power']}, "
                f"🎯 Accuracy: {BASIC_MOVES.get(move, ADVANCED_MOVES.get(move))['accuracy']}")
                for i, move in enumerate(current_moves)
            ])
            
            move_embed = create_embed(
                title=f"🎮 {current_player.name}'s turn!",
                description=f"Choose your move (type the number):\n{moves_text}",
                color=0x00FF00
            )
            await ctx.send(embed=move_embed)
            
            # Wait for move selection
            def check(m):
                return (m.author == current_player and 
                        m.channel == ctx.channel and 
                        m.content.isdigit() and 
                        1 <= int(m.content) <= len(current_moves))
                        
            try:
                move_msg = await self.bot.wait_for('message', timeout=30.0, check=check)
                selected_move = current_moves[int(move_msg.content) - 1]
                
                # Handle Domain Expansion
                if selected_move == "DOMAIN EXPANSION":
                    current_species = current_pet['species']
                    domain_data = DOMAIN_EXPANSIONS[current_species]
                    
                    # Animate domain expansion
                    await self.animate_domain_expansion(ctx, current_pet, domain_data)
                    
                    # Apply massive damage
                    damage = domain_data['power'] * (current_pet['strength'] / 20)
                    
                    if current_turn == "challenger":
                        current_hp2 = max(0, current_hp2 - damage)
                        # Set cooldown
                        self.domain_cooldowns[f"{str(owner1.id)}_{pet1['name']}"] = datetime.now()
                    else:
                        current_hp1 = max(0, current_hp1 - damage)
                        # Set cooldown
                        self.domain_cooldowns[f"{str(owner2.id)}_{pet2['name']}"] = datetime.now()
                        
                    await ctx.send(f"💥 The domain expansion dealt **{damage}** damage!")
                    
                else:
                    # Normal move handling with animation
                    move_data = BASIC_MOVES.get(selected_move, ADVANCED_MOVES.get(selected_move))
                    
                    # Attack animation frames
                    attack_frames = [
                        f"```\n  {current_pet['name']} prepares...\n     ⚡     \n    ⚡⚡    \n   ⚡⚡⚡   ```",
                        f"```\n  {selected_move} charging...\n     💫     \n    💫💫    \n   💫💫💫   ```",
                        f"```\n  ATTACK!!!\n     ⭐     \n    ⭐⭐    \n   ⭐⭐⭐   ```"
                    ]
                    
                    # Show attack animation
                    attack_msg = await ctx.send(attack_frames[0])
                    for frame in attack_frames[1:]:
                        await attack_msg.edit(content=frame)
                        await asyncio.sleep(0.7)
                    
                    # Calculate damage
                    accuracy_roll = random.randint(1, 100)
                    if accuracy_roll <= move_data["accuracy"]:
                        # Hit!
                        attacker_strength = pet1["strength"] if current_turn == "challenger" else pet2["strength"]
                        base_damage = move_data["power"]
                        damage = int(base_damage * (attacker_strength / 20))
                        
                        # Hit animation
                        hit_frames = [
                            "```\n   💥   \n  💥💥  \n 💥💥💥 \n  DIRECT  \n   HIT!   ```",
                            "```\n   ⚡   \n  ⚡⚡  \n ⚡⚡⚡ \n  SUPER  \n EFFECTIVE```",
                            "```\n   ✨   \n  ✨✨  \n ✨✨✨ \n  GREAT  \n  STRIKE! ```"
                        ]
                        
                        for frame in hit_frames:
                            await attack_msg.edit(content=frame)
                            await asyncio.sleep(0.5)
                        
                        # Apply damage
                        if current_turn == "challenger":
                            current_hp2 = max(0, current_hp2 - damage)
                            await ctx.send(f"💥 {pet1['name']} used {selected_move}! Dealt {damage} damage!")
                        else:
                            current_hp1 = max(0, current_hp1 - damage)
                            await ctx.send(f"💥 {pet2['name']} used {selected_move}! Dealt {damage} damage!")
                    else:
                        # Miss animation
                        miss_frames = [
                            "```\n  MISSED!  \n   💨💨   \n  💨💨💨  ```",
                            "```\n  DODGED!  \n   ✨✨   \n  ✨✨✨  ```",
                            "```\n  EVADED!  \n   ⭐⭐   \n  ⭐⭐⭐  ```"
                        ]
                        
                        for frame in miss_frames:
                            await attack_msg.edit(content=frame)
                            await asyncio.sleep(0.5)
                        
                        await ctx.send("❌ The attack missed!")
                
            except asyncio.TimeoutError:
                await ctx.send(f"⏰ {current_player.mention} took too long! Turn skipped!")
            
            # Switch turns
            current_turn = "opponent" if current_turn == "challenger" else "challenger"
            turn_count += 1
            
            # Add a short delay between turns
            await asyncio.sleep(2)
        
        # Battle end animation
        end_frames = [
            "```\n╔════════════════╗\n║  BATTLE OVER!  ║\n╚════════════════╝```",
            "```\n╔════════════════╗\n║⚡BATTLE OVER!⚡║\n╚════════════════╝```",
            "```\n╔════════════════╗\n║💫BATTLE OVER!💫║\n╚════════════════╝```"
        ]
        
        for frame in end_frames:
            await ctx.send(frame)
            await asyncio.sleep(0.7)
        
        # Determine winner with victory animation
        if current_hp1 <= 0:
            winner = "opponent"
            victory_frames = [
                f"```\n🏆 VICTORY! 🏆\n\n{owner2.name}'s\n{pet2['name']}\nWINS!```",
                f"```\n✨ VICTORY! ✨\n\n{owner2.name}'s\n{pet2['name']}\nTRIUMPHS!```",
                f"```\n⭐ VICTORY! ⭐\n\n{owner2.name}'s\n{pet2['name']}\nCONQUERS!```"
            ]
        else:
            winner = "challenger"
            victory_frames = [
                f"```\n🏆 VICTORY! 🏆\n\n{owner1.name}'s\n{pet1['name']}\nWINS!```",
                f"```\n✨ VICTORY! ✨\n\n{owner1.name}'s\n{pet1['name']}\nTRIUMPHS!```",
                f"```\n⭐ VICTORY! ⭐\n\n{owner1.name}'s\n{pet1['name']}\nCONQUERS!```"
            ]
        
        victory_msg = await ctx.send(victory_frames[0])
        for frame in victory_frames[1:]:
            await victory_msg.edit(content=frame)
            await asyncio.sleep(1)
        
        # Update pet stats
        pet1["health"] = max(1, current_hp1)  # Ensure pet doesn't faint completely
        pet2["health"] = max(1, current_hp2)
        
        # Add experience
        self.add_experience(pet1, 50 if winner == "challenger" else 25)
        self.add_experience(pet2, 50 if winner == "opponent" else 25)
        
        return {"winner": winner, "turns": turn_count}

    def get_available_moves(self, level: int) -> List[str]:
        """Get available moves for the given level"""
        moves = []
        for req_level, level_moves in MOVES_BY_LEVEL.items():
            if level >= req_level:
                moves.extend(level_moves)
        return moves

    def add_experience(self, pet: Dict[str, Any], xp: int):
        """Add experience to a pet and handle leveling up"""
        current_level = pet.get("level", 1)
        current_xp = pet.get("xp", 0)
        
        # Add XP
        new_xp = current_xp + xp
        xp_needed = current_level * XP_PER_LEVEL
        
        # Check for level up
        while new_xp >= xp_needed and current_level < MAX_LEVEL:
            new_xp -= xp_needed
            current_level += 1
            xp_needed = current_level * XP_PER_LEVEL
            
            # Increase stats on level up
            pet["health"] = min(MAX_HEALTH, pet["health"] + random.randint(5, 10))
            pet["strength"] = min(50, pet["strength"] + random.randint(2, 5))
        
        # Update pet
        pet["level"] = current_level
        pet["xp"] = new_xp

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

    async def create_battle_animation(self, move_name: str) -> List[str]:
        """Create cinematic battle animations for different moves"""
        animations = {
            "Tackle": [
                "```\n     🔄     \n    ⚡ ⚡    \n  ➡️  ⭐  ➡️  \n    ⚡ ⚡    \n     🔄     ```",
                "```\n    💨💨    \n   💨💨💨   \n ➡️  ⭐  ➡️ \n   💨💨💨   \n    💨💨    ```",
                "```\n   💥💥💥   \n  💥💥💥💥  \n 💥  ⭐  💥 \n  💥💥💥💥  \n   💥💥💥   ```"
            ],
            "Scratch": [
                "```\n   ✨  ✨   \n  ／  ＼  \n ／    ＼ \n✨      ✨```",
                "```\n   ⚔️  ⚔️   \n  ／╲╱＼  \n ／    ＼ \n⚔️      ⚔️```",
                "```\n   💢  💢   \n  ／╳╳＼  \n ／╳╳╳╳＼ \n💢      💢```"
            ],
            "Fire Blast": [
                "```\n    🔥    \n   🔥🔥   \n  🔥🔥🔥  \n 🔥🔥🔥🔥 ```",
                "```\n  🌋🌋🌋  \n 🌋🔥🔥🌋 \n🌋🔥🔥🔥🌋\n 🌋🔥🔥🌋 \n  🌋🌋🌋  ```",
                "```\n💥💥💥💥💥\n💥🔥🔥🔥💥\n💥🔥💫🔥💥\n💥🔥🔥🔥💥\n💥💥💥💥💥```"
            ],
            "Ice Beam": [
                "```\n    ❄️    \n   ❄️❄️   \n  ❄️❄️❄️  \n ❄️❄️❄️❄️ ```",
                "```\n  ❄️➡️❄️  \n ❄️⚡⚡❄️ \n❄️⚡❄️⚡❄️\n ❄️⚡⚡❄️ \n  ❄️➡️❄️  ```",
                "```\n❄️❄️❄️❄️❄️\n❄️💠💠💠❄️\n❄️💠⚡💠❄️\n❄️💠💠💠❄️\n❄️❄️❄️❄️❄️```"
            ],
            "Thunder Strike": [
                "```\n    ⚡    \n   ⚡⚡   \n  ⚡⚡⚡  \n ⚡⚡⚡⚡ ```",
                "```\n⚡  ⚡  ⚡\n ⚡⚡⚡⚡ \n⚡⚡✨⚡⚡\n ⚡⚡⚡⚡ \n⚡  ⚡  ⚡```",
                "```\n⚡⚡⚡⚡⚡\n⚡💫💫💫⚡\n⚡💫⚡💫⚡\n⚡💫💫💫⚡\n⚡⚡⚡⚡⚡```"
            ]
        }
        
        # Default animation for moves without specific animations
        default_animation = [
            "```\n  ✨  ✨  \n ✨✨✨✨ \n✨  ⚡  ✨\n ✨✨✨✨ \n  ✨  ✨  ```",
            "```\n  💫  💫  \n 💫💫💫💫 \n💫  ⚡  💫\n 💫💫💫💫 \n  💫  💫  ```",
            "```\n  ⭐  ⭐  \n ⭐⭐⭐⭐ \n⭐  💥  ⭐\n ⭐⭐⭐⭐ \n  ⭐  ⭐  ```"
        ]
        
        return animations.get(move_name, default_animation)

# Setup function for the cog
async def setup(bot):
    await bot.add_cog(PetCommands(bot)) 