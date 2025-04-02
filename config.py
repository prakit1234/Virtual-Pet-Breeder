import os
import json
from dotenv import load_dotenv
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    print("YAML module not available - custom config from YAML won't be loaded")
from typing import Dict, Any, Optional

# Load environment variables from .env file
load_dotenv()

# Bot Configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "YOUR_TOKEN_HERE")
PET_FILE = os.getenv("PET_FILE", "pets.json")
BACKUP_INTERVAL = int(os.getenv("BACKUP_INTERVAL", 3600))

# Game settings
STARTING_COINS = int(os.getenv("STARTING_COINS", 100))
MAX_PETS = int(os.getenv("MAX_PETS", 5))
BASE_PRIZE_COINS = int(os.getenv("BASE_PRIZE_COINS", 50))

# Feature flags
ENABLE_TRADING = os.getenv("ENABLE_TRADING", "true").lower() == "true"
ENABLE_DAILY_REWARDS = os.getenv("ENABLE_DAILY_REWARDS", "true").lower() == "true"

# Domain Expansion Moves for Mythic Pets
DOMAIN_EXPANSIONS = {
    "Dragon": {
        "name": "Infernal Void: Eternal Flame Prison",
        "power": 150,
        "description": "Creates a domain of endless flames where time and space burn away",
        "animation_frames": ["🔥", "🌋", "⚡", "🐉", "💥"]
    },
    "Phoenix": {
        "name": "Solar Eclipse: Immortal Rebirth",
        "power": 140,
        "description": "A domain where life and death cycle endlessly in burning light",
        "animation_frames": ["🌞", "🌑", "✨", "🦅", "🌟"]
    },
    "Unicorn": {
        "name": "Celestial Dream: Mystic Starfall",
        "power": 130,
        "description": "Creates a realm where cosmic energy rains from an endless starlit sky",
        "animation_frames": ["⭐", "🌠", "🦄", "💫", "✨"]
    },
    "Griffin": {
        "name": "Storm Lord's Domain: Sky Rending Tempest",
        "power": 135,
        "description": "A domain of raging storms and lightning where gravity holds no meaning",
        "animation_frames": ["⚡", "🌪️", "🦅", "☈", "💨"]
    }
}

# Available Pet Species (based on your image files)
SPECIES = [
    "Dragon",
    "Phoenix",
    "Unicorn",
    "Griffin",
    "Wolf",
    "Cat",
    "Dog",
    "Rabbit",
    "Hamster",
    "Bird"
]

# Pet Colors
COLORS = [
    "Crimson", "Neon", "Golden", "Icy", "Shadow",
    "Rainbow", "Emerald", "Azure", "Violet", "Platinum"
]

# Pet Traits
TRAITS = [
    "Mystic", "Fierce", "Swift", "Clever", "Brave",
    "Mighty", "Agile", "Wise", "Noble", "Royal"
]

# Shop items
SHOP_ITEMS = {
    "health_potion": {"price": 100, "description": "Restores 50 HP"},
    "happiness_treat": {"price": 75, "description": "Increases happiness by 30"},
    "training_weight": {"price": 150, "description": "Increases strength by 5"},
    "rare_candy": {"price": 300, "description": "Increases level by 1"}
}

# Admin IDs (Discord user IDs with admin access)
ADMIN_IDS = os.getenv("ADMIN_IDS", "").split(",")

# Load custom items if available
def load_custom_config(file_path: str = "custom_config.yaml") -> Dict[str, Any]:
    """Load custom configuration from YAML file if it exists"""
    if not YAML_AVAILABLE:
        print(f"Warning: YAML module not available, can't load {file_path}")
        return {}
    
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            print(f"Error loading custom config: {e}")
    return {}

# Try to load custom configuration
try:
    custom_config = load_custom_config()
    
    # Update shop items if defined in custom config
    if 'shop_items' in custom_config:
        SHOP_ITEMS.update(custom_config['shop_items'])
        
    # Update species, traits, colors if defined
    if 'species' in custom_config:
        SPECIES.extend(custom_config['species'])
    if 'traits' in custom_config:
        TRAITS.extend(custom_config['traits'])
    if 'colors' in custom_config:
        COLORS.extend(custom_config['colors'])
        
except Exception as e:
    print(f"Error loading custom config: {e}")
    # Continue with default configuration

# Battle Moves Configuration
BASIC_MOVES = {
    "Tackle": {"power": 20, "accuracy": 95, "description": "A basic tackle attack"},
    "Scratch": {"power": 25, "accuracy": 90, "description": "Sharp claws scratch the opponent"}
}

ADVANCED_MOVES = {
    "Fire Blast": {"power": 40, "accuracy": 85, "description": "A powerful blast of fire"},
    "Ice Beam": {"power": 35, "accuracy": 90, "description": "A freezing beam of ice"},
    "Thunder Strike": {"power": 45, "accuracy": 80, "description": "A shocking electric attack"},
    "Nature's Fury": {"power": 38, "accuracy": 88, "description": "Harness the power of nature"},
    "Shadow Claw": {"power": 42, "accuracy": 82, "description": "Attack with shadowy claws"},
    "Mystic Wave": {"power": 37, "accuracy": 87, "description": "A wave of mystic energy"}
}

# Moves unlocked by level
MOVES_BY_LEVEL = {
    1: ["Tackle", "Scratch"],  # Starting moves
    5: ["Fire Blast"],
    10: ["Ice Beam"],
    15: ["Thunder Strike"],
    20: ["Nature's Fury"],
    25: ["Shadow Claw"],
    30: ["Mystic Wave"]
}

# Economy Settings
DAILY_REWARD = 100

# Pet Settings
MAX_HEALTH = 100
MAX_HAPPINESS = 100
MAX_LEVEL = 50
XP_PER_LEVEL = 100  # XP needed to level up = level * XP_PER_LEVEL

def validate_config() -> bool:
    """Validate that the configuration is valid"""
    if not DISCORD_TOKEN:
        print("ERROR: Discord token missing! Please add it to your .env file.")
        return False
    return True 