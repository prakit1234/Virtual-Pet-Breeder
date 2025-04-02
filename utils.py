import random
import discord
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional
import pytz
from config import SPECIES, TRAITS, COLORS, BASE_PRIZE_COINS, MAX_HEALTH, MAX_HAPPINESS
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import io
import math
import colorsys

def generate_pet(rare: bool = False, mythic: bool = False) -> Dict[str, Any]:
    """Generate a new pet with random attributes"""
    # Select species based on rarity
    if mythic:
        species_pool = ["Dragon", "Phoenix", "Unicorn", "Griffin"]  # Mythic species
    elif rare:
        species_pool = ["Wolf", "Cat", "Dog"]  # Rare species
    else:
        species_pool = ["Rabbit", "Hamster", "Bird"]  # Common species
        
    species = random.choice(species_pool)
    color = random.choice(COLORS)
    trait = random.choice(TRAITS)
    
    # Set rarity
    rarity = "mythic" if mythic else "rare" if rare else "common"
    
    # Generate base stats - higher for rare/mythic pets
    base_health = random.randint(60, 80) if rare else random.randint(80, 100) if mythic else random.randint(40, 60)
    base_happiness = random.randint(60, 80) if rare else random.randint(80, 100) if mythic else random.randint(40, 60)
    base_strength = random.randint(15, 25) if rare else random.randint(25, 35) if mythic else random.randint(5, 15)
    
    # Create pet data
    pet = {
        "name": f"{color} {trait} {species}",
        "species": species,
        "color": color,
        "trait": trait,
        "health": min(base_health, MAX_HEALTH),
        "happiness": min(base_happiness, MAX_HAPPINESS),
        "strength": base_strength,
        "rarity": rarity,
        "level": 1,
        "xp": 0
    }
    
    return pet

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
    """Calculate coins reward for winning a fight"""
    base_reward = 50
    
    # Bonus for beating stronger pets
    level_difference = (loser_pet.get("level", 1) - winner_pet.get("level", 1))
    level_bonus = max(0, level_difference * 10)
    
    # Rarity bonus
    rarity_bonus = {
        "common": 0,
        "rare": 25,
        "mythic": 50
    }.get(loser_pet.get("rarity", "common"), 0)
    
    return base_reward + level_bonus + rarity_bonus

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

# Directory for pet assets
ASSETS_DIR = "assets"
PET_IMAGES_DIR = os.path.join(ASSETS_DIR, "pets")
BACKGROUNDS_DIR = os.path.join(ASSETS_DIR, "backgrounds")
ACCESSORIES_DIR = os.path.join(ASSETS_DIR, "accessories")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")

def ensure_assets_dirs():
    """Ensure all required asset directories exist"""
    dirs = [
        "assets/pets",
        "assets/backgrounds",
        "assets/accessories",
        "assets/fonts",
        "assets/pets/idle",
        "assets/pets/attack",
        "assets/pets/victory",
        "assets/effects"
    ]
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)

def find_matching_image(category: str, name: str, pose: str = "idle") -> Optional[str]:
    """Find a matching image in the assets directory"""
    # Define search paths based on category
    if category == "pet":
        search_dir = f"assets/pets/{pose}"
    elif category == "accessory":
        search_dir = "assets/accessories"
    elif category == "background":
        search_dir = "assets/backgrounds"
    elif category == "effect":
        search_dir = "assets/effects"
    else:
        return None
        
    # Try exact match first
    for ext in ['.png', '.jpg', '.gif']:
        path = os.path.join(search_dir, f"{name.lower()}{ext}")
        if os.path.exists(path):
            return path
            
    # Try partial matches
    try:
        files = os.listdir(search_dir)
        for file in files:
            if name.lower() in file.lower():
                return os.path.join(search_dir, file)
    except:
        pass
        
    return None

def get_random_color():
    """Generate a random vibrant color"""
    hue = random.random()  # Random hue
    saturation = random.uniform(0.7, 1.0)  # High saturation for vibrant colors
    value = random.uniform(0.8, 1.0)  # High value for brightness
    rgb = colorsys.hsv_to_rgb(hue, saturation, value)
    return tuple(int(x * 255) for x in rgb)

def generate_random_shape(draw, x, y, size, color):
    """Generate a random shape for body parts"""
    shape_type = random.choice(['circle', 'oval', 'polygon'])
    
    if shape_type == 'circle':
        draw.ellipse([x, y, x + size, y + size], fill=color)
    elif shape_type == 'oval':
        stretch = random.uniform(0.5, 1.5)
        draw.ellipse([x, y, x + size, y + size * stretch], fill=color)
    else:
        points = []
        num_points = random.randint(3, 7)
        for i in range(num_points):
            angle = (2 * math.pi * i) / num_points
            px = x + size/2 + math.cos(angle) * size/2
            py = y + size/2 + math.sin(angle) * size/2
            points.append((px, py))
        draw.polygon(points, fill=color)

def add_details(draw, x, y, size, color):
    """Add details like eyes, patterns, etc."""
    # Add eyes
    eye_size = size // 8
    draw.ellipse([x + size//3, y + size//3, x + size//3 + eye_size, y + size//3 + eye_size], fill='white')
    draw.ellipse([x + 2*size//3, y + size//3, x + 2*size//3 + eye_size, y + size//3 + eye_size], fill='white')
    
    # Add pupils
    pupil_size = eye_size // 2
    draw.ellipse([x + size//3 + eye_size//4, y + size//3 + eye_size//4, 
                  x + size//3 + eye_size//4 + pupil_size, y + size//3 + eye_size//4 + pupil_size], fill='black')
    draw.ellipse([x + 2*size//3 + eye_size//4, y + size//3 + eye_size//4,
                  x + 2*size//3 + eye_size//4 + pupil_size, y + size//3 + eye_size//4 + pupil_size], fill='black')
    
    # Add patterns based on rarity
    if random.random() < 0.7:  # 70% chance for patterns
        pattern_type = random.choice(['spots', 'stripes', 'stars'])
        pattern_color = (color[0] ^ 255, color[1] ^ 255, color[2] ^ 255)  # Complementary color
        
        if pattern_type == 'spots':
            for _ in range(random.randint(3, 7)):
                spot_x = x + random.randint(0, size)
                spot_y = y + random.randint(0, size)
                spot_size = size // random.randint(8, 12)
                draw.ellipse([spot_x, spot_y, spot_x + spot_size, spot_y + spot_size], fill=pattern_color)
        elif pattern_type == 'stripes':
            for i in range(random.randint(2, 5)):
                stripe_y = y + (size * i) // 4
                draw.line([x, stripe_y, x + size, stripe_y], fill=pattern_color, width=size//20)
        else:  # stars
            for _ in range(random.randint(2, 4)):
                star_x = x + random.randint(0, size)
                star_y = y + random.randint(0, size)
                points = []
                for i in range(5):
                    angle = (2 * math.pi * i) / 5 - math.pi/2
                    px = star_x + math.cos(angle) * (size//12)
                    py = star_y + math.sin(angle) * (size//12)
                    points.append((px, py))
                draw.polygon(points, fill=pattern_color)

async def generate_pet_image(pet):
    """Generate a pet image based on its attributes"""
    try:
        # Get the base image path based on species
        base_path = f"assets/pets/idle/{pet['species'].lower()}_idle.png"
        
        if not os.path.exists(base_path):
            print(f"Warning: Image not found for {pet['species']}")
            return None
            
        # Open and convert the image
        img = Image.open(base_path).convert('RGBA')
        
        # Apply color tint based on pet's color
        tint = get_color_tint(pet['color'])
        if tint:
            tinted = Image.new('RGBA', img.size, tint + (100,))  # Add alpha for transparency
            img = Image.alpha_composite(img, tinted)
        
        # Add rarity effects
        if pet['rarity'] == 'mythic':
            # Add golden glow
            glow = Image.new('RGBA', img.size, (255, 215, 0, 50))  # Golden color
            img = Image.alpha_composite(img, glow)
        elif pet['rarity'] == 'rare':
            # Add blue shimmer
            shimmer = Image.new('RGBA', img.size, (0, 191, 255, 30))  # Blue color
            img = Image.alpha_composite(img, shimmer)
        
        # Save to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        return discord.File(img_byte_arr, filename='pet.png')
        
    except Exception as e:
        print(f"Error generating pet image: {e}")
        return None

def get_color_tint(color):
    """Get RGB values for color tinting"""
    color_map = {
        "Crimson": (220, 20, 60),
        "Neon": (57, 255, 20),
        "Golden": (255, 215, 0),
        "Icy": (135, 206, 235),
        "Shadow": (47, 79, 79),
        "Rainbow": None,  # Special case - no tint
        "Emerald": (46, 204, 113),
        "Azure": (0, 127, 255),
        "Violet": (138, 43, 226),
        "Platinum": (229, 228, 226)
    }
    return color_map.get(color)

async def generate_battle_image(pet1, pet2):
    """Generate a battle scene with two pets"""
    try:
        # Create battle background
        width = 800
        height = 400
        background = Image.new('RGBA', (width, height), (200, 200, 255, 255))
        
        # Load pet images
        pet1_path = f"assets/pets/attack/{pet1['species'].lower()}_idle.png"  # Using idle for now, can add attack poses later
        pet2_path = f"assets/pets/attack/{pet2['species'].lower()}_idle.png"
        
        if not os.path.exists(pet1_path) or not os.path.exists(pet2_path):
            return None
            
        pet1_img = Image.open(pet1_path).convert('RGBA')
        pet2_img = Image.open(pet2_path).convert('RGBA')
        
        # Resize pet images if needed
        pet_size = (300, 300)
        pet1_img = pet1_img.resize(pet_size)
        pet2_img = pet2_img.resize(pet_size)
        
        # Apply color tints
        tint1 = get_color_tint(pet1['color'])
        tint2 = get_color_tint(pet2['color'])
        
        if tint1:
            tinted1 = Image.new('RGBA', pet1_img.size, tint1 + (100,))
            pet1_img = Image.alpha_composite(pet1_img, tinted1)
        if tint2:
            tinted2 = Image.new('RGBA', pet2_img.size, tint2 + (100,))
            pet2_img = Image.alpha_composite(pet2_img, tinted2)
        
        # Position pets
        background.paste(pet1_img, (50, 50), pet1_img)
        background.paste(pet2_img, (450, 50), pet2_img)
        
        # Add VS text
        draw = ImageDraw.Draw(background)
        try:
            font = ImageFont.truetype("arial.ttf", 60)
        except:
            font = ImageFont.load_default()
            
        draw.text((width//2, height//2), "VS", fill=(255, 0, 0), font=font, anchor="mm")
        
        # Save to bytes
        img_byte_arr = io.BytesIO()
        background.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        return discord.File(img_byte_arr, filename='battle.png')
        
    except Exception as e:
        print(f"Error generating battle image: {e}")
        return None

async def load_pet_image(pet: Dict[str, Any], pose: str = "idle") -> Optional[Image.Image]:
    """Load or create a pet image with accessories"""
    try:
        # Get base pet image
        species = pet["name"].split()[-1].lower()
        base_image_path = find_matching_image("pet", species, pose)
        
        if base_image_path and os.path.exists(base_image_path):
            img = Image.open(base_image_path).convert("RGBA")
        else:
            img = create_default_pet_image(species, pet["name"].split()[0].lower())
            
        # Apply color tint
        color_name = pet["name"].split()[0].lower()
        img = apply_color_tint(img, color_name)
        
        # Add accessories based on rarity
        if "rarity" in pet:
            if pet["rarity"] == "rare":
                accessory = find_matching_image("accessory", "rare")
                if accessory:
                    acc_img = Image.open(accessory).convert("RGBA")
                    acc_img = acc_img.resize(img.size, Image.LANCZOS)
                    img = Image.alpha_composite(img, acc_img)
            elif pet["rarity"] == "mythic":
                accessory = find_matching_image("accessory", "mythic")
                if accessory:
                    acc_img = Image.open(accessory).convert("RGBA")
                    acc_img = acc_img.resize(img.size, Image.LANCZOS)
                    img = Image.alpha_composite(img, acc_img)
                    
        # Add visual effects based on stats
        if pet["health"] < 30:
            img = add_effect(img, "wounded")
        if pet["happiness"] > 80:
            img = add_effect(img, "happy")
            
        return img
        
    except Exception as e:
        print(f"Error loading pet image: {e}")
        return None

def add_effect(img: Image.Image, effect_name: str) -> Image.Image:
    """Add a visual effect to an image"""
    effect_path = find_matching_image("effect", effect_name)
    if effect_path:
        try:
            effect = Image.open(effect_path).convert("RGBA")
            effect = effect.resize(img.size, Image.LANCZOS)
            return Image.alpha_composite(img, effect)
        except:
            pass
    return img

def create_default_pet_image(species: str, color_name: str) -> Image.Image:
    """Create a default pet image with the given species name"""
    img = Image.new("RGBA", (300, 300), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw a simple shape
    draw.ellipse((50, 50, 250, 250), fill=(200, 200, 200, 255))
    
    # Try to load a font
    font_path = os.path.join(FONTS_DIR, "default.ttf")
    try:
        font = ImageFont.truetype(font_path, 24)
    except Exception:
        font = ImageFont.load_default()
    
    # Add species name
    draw.text((150, 150), species.upper(), fill=(0, 0, 0, 255), font=font, anchor="mm")
    
    return img

def apply_color_tint(img: Image.Image, color_name: str) -> Image.Image:
    """Apply a color tint to the image based on color name"""
    # Define color tints for different colors
    color_map = {
        "crimson": (220, 20, 60, 128),
        "neon": (57, 255, 20, 128),
        "golden": (255, 215, 0, 128),
        "icy": (0, 255, 255, 128),
        "shadow": (47, 79, 79, 128),
        "rainbow": None,  # Special case
        "emerald": (80, 200, 120, 128),
        "azure": (0, 127, 255, 128),
        "violet": (238, 130, 238, 128),
        "platinum": (229, 228, 226, 128),
        "obsidian": (66, 66, 66, 128),
        "celestial": (135, 206, 250, 128),
        "nebula": (123, 104, 238, 128),
        "sunset": (250, 214, 165, 128)
    }
    
    # Get the color or use a default gray
    tint_color = color_map.get(color_name.lower(), (150, 150, 150, 128))
    
    # Special case for rainbow
    if color_name.lower() == "rainbow":
        return apply_rainbow_effect(img)
    
    # Create a tinted overlay
    overlay = Image.new("RGBA", img.size, tint_color)
    
    # Composite the overlay with the original image
    return Image.alpha_composite(img, overlay)

def apply_rainbow_effect(img: Image.Image) -> Image.Image:
    """Apply a rainbow effect to the image"""
    # Create a gradient image
    gradient = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(gradient)
    
    # Rainbow colors
    rainbow_colors = [
        (255, 0, 0, 100),      # Red
        (255, 127, 0, 100),    # Orange
        (255, 255, 0, 100),    # Yellow
        (0, 255, 0, 100),      # Green
        (0, 0, 255, 100),      # Blue
        (75, 0, 130, 100),     # Indigo
        (148, 0, 211, 100)     # Violet
    ]
    
    # Draw rainbow stripes
    height = img.height
    stripe_height = height / len(rainbow_colors)
    
    for i, color in enumerate(rainbow_colors):
        y0 = i * stripe_height
        y1 = (i + 1) * stripe_height
        draw.rectangle([(0, y0), (img.width, y1)], fill=color)
    
    # Composite the gradient with the original image
    return Image.alpha_composite(img, gradient)

def apply_trait_effect(img: Image.Image, trait: str) -> Image.Image:
    """Apply effects based on the pet's trait"""
    trait_effects = {
        "winged": add_wings,
        "singing": add_music_notes,
        "glowy": add_glow_effect,
        "spiky": add_spikes,
        "fluffy": add_fluff,
        "invisible": make_partially_transparent,
        "psychic": add_psychic_effect,
        "metallic": add_metallic_effect,
        "mystic": add_mystic_effect,
        "electric": add_electric_effect,
        "hypnotic": add_hypnotic_effect,
        "venomous": add_venom_effect,
        "musical": add_music_notes,
        "magical": add_magic_effect
    }
    
    effect_func = trait_effects.get(trait.lower())
    if effect_func:
        return effect_func(img)
    return img

# Trait effect functions
def add_wings(img: Image.Image) -> Image.Image:
    # Look for wings accessory or just add simple wings
    wings_path = os.path.join(ACCESSORIES_DIR, "wings.png")
    if os.path.exists(wings_path):
        wings = Image.open(wings_path).convert("RGBA")
        wings = wings.resize(img.size, Image.LANCZOS)
        return Image.alpha_composite(img, wings)
    
    # Simple wings if no image
    result = img.copy()
    draw = ImageDraw.Draw(result)
    w, h = img.size
    draw.ellipse((w//4, h//3, w//2, h*2//3), fill=(255, 255, 255, 100))
    draw.ellipse((w//2, h//3, w*3//4, h*2//3), fill=(255, 255, 255, 100))
    return result

def add_music_notes(img: Image.Image) -> Image.Image:
    result = img.copy()
    draw = ImageDraw.Draw(result)
    w, h = img.size
    
    notes = [
        (w*3//4, h//4),
        (w*2//3, h//3),
        (w*4//5, h//2)
    ]
    
    for x, y in notes:
        # Draw music note (simple version)
        draw.ellipse((x-5, y-5, x+5, y+5), fill=(0, 0, 0, 200))
        draw.line([(x, y), (x, y-20)], fill=(0, 0, 0, 200), width=2)
    
    return result

def add_glow_effect(img: Image.Image) -> Image.Image:
    # Create a glowing overlay
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)
    
    w, h = img.size
    center = (w//2, h//2)
    for radius in range(min(w, h)//2, 0, -5):
        alpha = max(0, 150 - radius * 3)
        draw.ellipse(
            (center[0] - radius, center[1] - radius, 
             center[0] + radius, center[1] + radius), 
            fill=(255, 255, 200, alpha)
        )
    
    # Composite images
    return Image.alpha_composite(img, glow)

def add_spikes(img: Image.Image) -> Image.Image:
    result = img.copy()
    draw = ImageDraw.Draw(result)
    w, h = img.size
    
    # Draw spikes around the edge
    center = (w//2, h//2)
    radius = min(w, h) // 3
    spikes = 12
    
    for i in range(spikes):
        angle = i * (360 / spikes)
        angle_rad = angle * (3.14159 / 180)
        
        x1 = center[0] + int(radius * 0.8 * math.cos(angle_rad))
        y1 = center[1] + int(radius * 0.8 * math.sin(angle_rad))
        
        x2 = center[0] + int(radius * 1.5 * math.cos(angle_rad))
        y2 = center[1] + int(radius * 1.5 * math.sin(angle_rad))
        
        draw.line([(x1, y1), (x2, y2)], fill=(100, 100, 100, 200), width=5)
    
    return result

def add_fluff(img: Image.Image) -> Image.Image:
    result = img.copy()
    draw = ImageDraw.Draw(result)
    w, h = img.size
    
    # Draw fluffy dots around the edge
    center = (w//2, h//2)
    radius = min(w, h) // 3
    fluffs = 30
    
    for i in range(fluffs):
        angle = random.uniform(0, 360)
        angle_rad = angle * (3.14159 / 180)
        
        dist = random.uniform(radius * 0.8, radius * 1.2)
        x = center[0] + int(dist * math.cos(angle_rad))
        y = center[1] + int(dist * math.sin(angle_rad))
        
        size = random.randint(5, 15)
        draw.ellipse(
            (x - size, y - size, x + size, y + size), 
            fill=(255, 255, 255, 150)
        )
    
    return result

def make_partially_transparent(img: Image.Image) -> Image.Image:
    # Make the image semi-transparent
    result = img.copy()
    pixels = result.load()
    
    for i in range(result.width):
        for j in range(result.height):
            r, g, b, a = pixels[i, j]
            pixels[i, j] = (r, g, b, a // 2)
    
    return result

def add_psychic_effect(img: Image.Image) -> Image.Image:
    # Add purple swirls
    result = img.copy()
    draw = ImageDraw.Draw(result)
    w, h = img.size
    
    center = (w//2, h//2)
    for i in range(0, 360, 30):
        angle_rad = i * (3.14159 / 180)
        
        for radius in range(20, min(w, h)//2, 20):
            x1 = center[0] + int(radius * math.cos(angle_rad))
            y1 = center[1] + int(radius * math.sin(angle_rad))
            
            x2 = center[0] + int(radius * math.cos(angle_rad + 0.5))
            y2 = center[1] + int(radius * math.sin(angle_rad + 0.5))
            
            draw.line([(x1, y1), (x2, y2)], fill=(128, 0, 128, 100), width=3)
    
    return result

def add_metallic_effect(img: Image.Image) -> Image.Image:
    # Create a metallic overlay
    metallic = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(metallic)
    
    w, h = img.size
    for y in range(0, h, 5):
        alpha = 100 + 50 * math.sin(y / 10)
        draw.line([(0, y), (w, y)], fill=(200, 200, 220, int(alpha)), width=2)
    
    # Composite images
    return Image.alpha_composite(img, metallic)

def add_mystic_effect(img: Image.Image) -> Image.Image:
    # Add stars and sparkles
    result = img.copy()
    draw = ImageDraw.Draw(result)
    w, h = img.size
    
    for _ in range(20):
        x = random.randint(0, w)
        y = random.randint(0, h)
        size = random.randint(2, 6)
        alpha = random.randint(150, 250)
        
        draw.ellipse(
            (x - size, y - size, x + size, y + size), 
            fill=(255, 255, 220, alpha)
        )
        
        # Draw star rays
        for i in range(4):
            angle = i * (3.14159 / 2)
            x1 = x + int((size + 2) * math.cos(angle))
            y1 = y + int((size + 2) * math.sin(angle))
            x2 = x + int((size + 8) * math.cos(angle))
            y2 = y + int((size + 8) * math.sin(angle))
            
            draw.line([(x1, y1), (x2, y2)], fill=(255, 255, 220, alpha), width=1)
    
    return result

def add_electric_effect(img: Image.Image) -> Image.Image:
    # Add lightning bolts
    result = img.copy()
    draw = ImageDraw.Draw(result)
    w, h = img.size
    
    for _ in range(5):
        x1 = random.randint(w//4, w*3//4)
        y1 = 20
        
        points = [(x1, y1)]
        x, y = x1, y1
        
        # Create a jagged path
        while y < h - 20:
            x += random.randint(-15, 15)
            y += random.randint(10, 30)
            
            x = max(10, min(w-10, x))
            points.append((x, y))
        
        # Draw the lightning
        for i in range(len(points) - 1):
            draw.line([points[i], points[i+1]], fill=(255, 255, 0, 180), width=3)
    
    return result

def add_hypnotic_effect(img: Image.Image) -> Image.Image:
    # Add hypnotic circles
    result = img.copy()
    draw = ImageDraw.Draw(result)
    w, h = img.size
    
    center = (w//2, h//2)
    for radius in range(10, min(w, h)//2, 15):
        alpha = 150 - radius
        if alpha < 30:
            alpha = 30
            
        draw.ellipse(
            (center[0] - radius, center[1] - radius, 
             center[0] + radius, center[1] + radius), 
            outline=(128, 0, 128, alpha), width=3
        )
    
    return result

def add_venom_effect(img: Image.Image) -> Image.Image:
    # Add green drips
    result = img.copy()
    draw = ImageDraw.Draw(result)
    w, h = img.size
    
    for _ in range(8):
        x = random.randint(w//4, w*3//4)
        y1 = random.randint(h//4, h*3//4)
        
        # Draw drip
        drip_length = random.randint(20, 50)
        y2 = y1 + drip_length
        
        # Draw the drip with gradient
        for y in range(y1, y2):
            alpha = 200 - int(((y - y1) / drip_length) * 150)
            draw.ellipse(
                (x-3, y-3, x+3, y+3), 
                fill=(0, 200, 0, alpha)
            )
    
    return result

def add_magic_effect(img: Image.Image) -> Image.Image:
    # Combine mystic and glowy effects
    glowy = add_glow_effect(img)
    return add_mystic_effect(glowy)

def add_pet_stats(img: Image.Image, pet: Dict[str, Any]) -> Image.Image:
    """Add pet stats to the image"""
    result = img.copy()
    draw = ImageDraw.Draw(result)
    w, h = img.size
    
    # Try to load a font
    font_path = os.path.join(FONTS_DIR, "default.ttf")
    try:
        name_font = ImageFont.truetype(font_path, 24)
        stats_font = ImageFont.truetype(font_path, 14)
    except Exception:
        name_font = ImageFont.load_default()
        stats_font = ImageFont.load_default()
    
    # Add a semi-transparent background for text
    draw.rectangle([(0, h-80), (w, h)], fill=(0, 0, 0, 128))
    
    # Add pet name
    draw.text((w//2, h-65), pet["name"], fill=(255, 255, 255, 255), font=name_font, anchor="mm")
    
    # Add pet stats
    stats_text = f"HP: {pet['health']}  Happiness: {pet['happiness']}  STR: {pet['strength']}"
    draw.text((w//2, h-30), stats_text, fill=(255, 255, 255, 255), font=stats_font, anchor="mm")
    
    # Add rarity
    if "rarity" in pet:
        rarity_colors = {
            "common": (200, 200, 200),
            "rare": (30, 144, 255),
            "mythic": (255, 215, 0)
        }
        color = rarity_colors.get(pet["rarity"].lower(), (200, 200, 200))
        draw.text((w//2, h-15), pet["rarity"].upper(), fill=color + (255,), font=stats_font, anchor="mm")
    
    return result 