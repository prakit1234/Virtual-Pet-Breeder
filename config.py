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
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PET_FILE = os.getenv("PET_FILE", "pets.json")
BACKUP_INTERVAL = int(os.getenv("BACKUP_INTERVAL", 3600))

# Game settings
STARTING_COINS = int(os.getenv("STARTING_COINS", 100))
MAX_PETS = int(os.getenv("MAX_PETS", 5))
BASE_PRIZE_COINS = int(os.getenv("BASE_PRIZE_COINS", 30))

# Feature flags
ENABLE_TRADING = os.getenv("ENABLE_TRADING", "true").lower() == "true"
ENABLE_DAILY_REWARDS = os.getenv("ENABLE_DAILY_REWARDS", "true").lower() == "true"

# Pet traits
SPECIES = ["Dragon", "Cactus", "Toaster", "Penguin", "Cloud", "Robot", "Phoenix", "Jellyfish", "Unicorn"]
TRAITS = ["Winged", "Singing", "Glowy", "Spiky", "Fluffy", "Invisible", "Psychic", "Metallic", "Mystic"]
COLORS = ["Crimson", "Neon", "Golden", "Icy", "Shadow", "Rainbow", "Emerald", "Azure", "Violet"]

# Shop items
SHOP_ITEMS = {
    "Food": {"cost": 50, "description": "Restores 20 Health and Happiness"},
    "SuperFood": {"cost": 100, "description": "Restores 40 Health and Happiness"},
    "SuperPet": {"cost": 200, "description": "A rare pet with boosted stats"},
    "MythicPet": {"cost": 500, "description": "An extremely rare pet with exceptional stats"},
    "HealthPotion": {"cost": 75, "description": "Fully restores a pet's health"},
    "HappinessPotion": {"cost": 75, "description": "Fully restores a pet's happiness"}
}

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

def validate_config() -> bool:
    """Validate that the configuration is valid"""
    if not DISCORD_TOKEN:
        print("ERROR: Discord token missing! Please add it to your .env file.")
        return False
    return True 