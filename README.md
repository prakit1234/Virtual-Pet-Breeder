# Virtual Pet Breeder Discord Bot

A Discord bot that allows users to adopt, breed, and battle virtual pets with unique traits and abilities.

## Features

- **Pet Management**: Adopt, breed, and release virtual pets
- **Battling System**: Challenge other users' pets to battles
- **Shop System**: Buy items and special pets with in-game currency
- **Inventory System**: Store and use items
- **Daily Rewards**: Claim daily rewards for consistent play
- **Pet Stats**: Each pet has health, happiness, and strength stats
- **Pet Rarities**: Common, Rare, and Mythic pets with varying stats
- **Data Persistence**: All pet data is saved and loaded automatically
- **Auto Backups**: Your pet data is backed up regularly

## Setup

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory with the following content:
   ```
   DISCORD_TOKEN=TOKEN_HERE
   ```
4. Run the bot:
   ```
   python bot.py
   ```

## Commands

- `!adopt` - Adopt a new pet
- `!pets` - View your current pets
- `!feed <pet_number>` - Feed one of your pets
- `!shop` - View available items in the shop
- `!buy <item_name>` - Purchase an item from the shop
- `!balance` - Check your PetCoin balance
- `!inventory` - View your inventory
- `!use <item_name> <pet_number>` - Use an item on one of your pets
- `!breed <pet1_number> <pet2_number>` - Breed two of your pets
- `!fight <pet_number> <@user>` - Challenge another user to a pet battle
- `!release <pet_number>` - Release a pet into the wild
- `!daily` - Claim your daily reward
- `!trade <pet_number> <@user>` - Offer to trade a pet with another user
- `!help` - View all available commands

## Customization

You can create a `custom_config.yaml` file to add custom species, traits, colors, and shop items.

Example:
```yaml
species:
  - "Fox"
  - "Slime"
  - "Ghost"
traits:
  - "Electric"
  - "Hypnotic"
  - "Venomous"
colors:
  - "Platinum"
  - "Obsidian"
  - "Celestial"
shop_items:
  "RarityPotion": 
    cost: 300
    description: "Increases the rarity of a pet by one level"
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 