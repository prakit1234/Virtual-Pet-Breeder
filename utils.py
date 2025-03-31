import random
import discord
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional
import pytz
from config import SPECIES, TRAITS, COLORS, BASE_PRIZE_COINS

def generate_pet(rare: bool = False, mythic: bool = False) -> Dict[str, Any]:
    """Generate a random pet with specified rarity"""
    # For mythic pets, use a special prefix
    if mythic:
        pet_name = f"Mythic {random.choice(COLORS)} {random.choice(TRAITS)} {random.choice(SPECIES)}"
        return {
            "name": pet_name,
            "health": random.randint(85, 100),
            "happiness": random.randint(85, 100),
            "strength": random.randint(40, 50),
            "rarity": "mythic",
            "created_at": time.time()
        }
    # For rare pets
    elif rare:
        pet_name = f"{random.choice(COLORS)} {random.choice(TRAITS)} {random.choice(SPECIES)}"
        return {
            "name": pet_name,
            "health": random.randint(70, 95),
            "happiness": random.randint(70, 95),
            "strength": random.randint(25, 35),
            "rarity": "rare",
            "created_at": time.time()
        }
    # For regular pets
    else:
        pet_name = f"{random.choice(COLORS)} {random.choice(TRAITS)} {random.choice(SPECIES)}"
        return {
            "name": pet_name,
            "health": random.randint(50, 80),
            "happiness": random.randint(50, 80),
            "strength": random.randint(10, 25),
            "rarity": "common",
            "created_at": time.time()
        }

def format_pet_info(pet: Dict[str, Any]) -> str:
    """Format pet information for display"""
    created_date = ""
    if "created_at" in pet:
        created_date = f", Age: {format_time_ago(pet['created_at'])}"
    
    rarity_str = ""
    if "rarity" in pet:
        rarity_str = f", Rarity: {pet['rarity'].capitalize()}"
        
    return (f"{pet['name']} (Health: {pet['health']}, "
            f"Happiness: {pet['happiness']}, Strength: {pet['strength']}{rarity_str}{created_date})")

def calculate_fight_rewards(winner_pet: Dict[str, Any], loser_pet: Dict[str, Any]) -> int:
    """Calculate the reward for winning a fight"""
    base_reward = BASE_PRIZE_COINS
    
    # Bonus for strength difference
    str_diff = abs(winner_pet["strength"] - loser_pet["strength"])
    bonus = 0
    
    # If underdog won (lower strength), give bigger bonus
    if winner_pet["strength"] < loser_pet["strength"]:
        bonus = int(str_diff * 2.5)
    else:
        bonus = int(str_diff * 0.5)
    
    # Rarity bonus
    rarity_bonus = 0
    if "rarity" in loser_pet:
        if loser_pet["rarity"] == "rare":
            rarity_bonus = 20
        elif loser_pet["rarity"] == "mythic":
            rarity_bonus = 50
            
    total_reward = base_reward + bonus + rarity_bonus
    
    # Randomize slightly
    return max(10, int(total_reward * random.uniform(0.8, 1.2)))

def create_embed(title: str, description: str, color: int = 0x3498db, fields: List[Tuple[str, str, bool]] = None) -> discord.Embed:
    """Create a Discord embed with given parameters"""
    embed = discord.Embed(title=title, description=description, color=color)
    
    if fields:
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
            
    return embed

def can_claim_daily(last_claim_time: Optional[float]) -> Tuple[bool, Optional[str]]:
    """Check if user can claim daily reward and return time until next claim if not"""
    if last_claim_time is None:
        return True, None
        
    now = time.time()
    utc_now = datetime.fromtimestamp(now, tz=pytz.UTC)
    last_claim = datetime.fromtimestamp(last_claim_time, tz=pytz.UTC)
    
    # Reset at midnight UTC
    next_reset = last_claim.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    
    if utc_now >= next_reset:
        return True, None
    
    # Calculate time until next reset
    time_until = next_reset - utc_now
    hours, remainder = divmod(time_until.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    time_str = f"{hours}h {minutes}m {seconds}s"
    return False, time_str

def format_time_ago(timestamp: float) -> str:
    """Format a timestamp as a human-readable time ago string"""
    now = time.time()
    diff = now - timestamp
    
    if diff < 60:
        return "Just now"
    elif diff < 3600:
        minutes = int(diff / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff < 86400:
        hours = int(diff / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff < 604800:
        days = int(diff / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        weeks = int(diff / 604800)
        return f"{weeks} week{'s' if weeks != 1 else ''} ago" 