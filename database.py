import json
import os
import shutil
import time
from typing import Dict, Any, List, Optional
import asyncio
from config import PET_FILE, BACKUP_INTERVAL

# Global data storage
_data = {
    "pets": {},
    "coins": {},
    "inventory": {},
    "daily_rewards": {},
    "last_backup": time.time()
}

def load_data() -> Dict[str, Any]:
    """Load data from the JSON file"""
    if os.path.exists(PET_FILE):
        try:
            with open(PET_FILE, "r") as f:
                loaded_data = json.load(f)
                _data.update(loaded_data)
        except json.JSONDecodeError:
            print(f"Error parsing {PET_FILE}, using default data")
        except Exception as e:
            print(f"Error loading data: {e}")
    return _data

def save_data() -> None:
    """Save data to the JSON file"""
    try:
        with open(PET_FILE, "w") as f:
            json.dump(_data, f, indent=4)
        _data["last_backup"] = time.time()
        
        # Create backup after successful save
        create_backup()
    except Exception as e:
        print(f"Error saving data: {e}")

def create_backup() -> None:
    """Create a backup of the data file"""
    if not os.path.exists(PET_FILE):
        return
        
    try:
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_file = f"{backup_dir}/pets_{timestamp}.json"
        
        # Only keep 5 most recent backups
        existing_backups = sorted([f for f in os.listdir(backup_dir) if f.startswith("pets_")])
        while len(existing_backups) >= 5:
            os.remove(os.path.join(backup_dir, existing_backups[0]))
            existing_backups.pop(0)
            
        shutil.copy2(PET_FILE, backup_file)
    except Exception as e:
        print(f"Error creating backup: {e}")

async def auto_backup_task() -> None:
    """Asynchronous task to automatically backup data"""
    while True:
        await asyncio.sleep(BACKUP_INTERVAL)
        current_time = time.time()
        if current_time - _data.get("last_backup", 0) >= BACKUP_INTERVAL:
            save_data()
            print(f"Auto-backup completed at {time.strftime('%Y-%m-%d %H:%M:%S')}")

# User-related functions
def get_user_pets(user_id: str) -> List[Dict[str, Any]]:
    """Get a user's pets"""
    return _data["pets"].get(user_id, [])

def set_user_pets(user_id: str, pets: List[Dict[str, Any]]) -> None:
    """Set a user's pets"""
    _data["pets"][user_id] = pets
    save_data()

def get_user_coins(user_id: str) -> int:
    """Get a user's coin balance"""
    return _data["coins"].get(user_id, 0)

def set_user_coins(user_id: str, amount: int) -> None:
    """Set a user's coin balance"""
    _data["coins"][user_id] = amount
    save_data()

def add_user_coins(user_id: str, amount: int) -> int:
    """Add coins to a user's balance and return new total"""
    current = get_user_coins(user_id)
    new_amount = current + amount
    set_user_coins(user_id, new_amount)
    return new_amount

# Inventory functions
def get_user_inventory(user_id: str) -> Dict[str, int]:
    """Get a user's inventory"""
    if user_id not in _data["inventory"]:
        _data["inventory"][user_id] = {}
    return _data["inventory"][user_id]

def add_to_inventory(user_id: str, item: str, amount: int = 1) -> None:
    """Add an item to a user's inventory"""
    inventory = get_user_inventory(user_id)
    inventory[item] = inventory.get(item, 0) + amount
    save_data()

def remove_from_inventory(user_id: str, item: str, amount: int = 1) -> bool:
    """Remove an item from a user's inventory. Returns False if not enough items."""
    inventory = get_user_inventory(user_id)
    if item not in inventory or inventory[item] < amount:
        return False
    
    inventory[item] -= amount
    if inventory[item] <= 0:
        del inventory[item]
    
    save_data()
    return True

# Daily rewards functions
def get_last_daily(user_id: str) -> Optional[float]:
    """Get the timestamp of the last daily reward for a user"""
    return _data["daily_rewards"].get(user_id)

def set_last_daily(user_id: str, timestamp: float) -> None:
    """Set the timestamp of the last daily reward for a user"""
    _data["daily_rewards"][user_id] = timestamp
    save_data()

# Initialize database by loading saved data
load_data() 