print("Starting import test...")

try:
    import dotenv
    print("✓ dotenv module imported")
except ImportError as e:
    print(f"✗ Error importing dotenv: {e}")

try:
    from dotenv import load_dotenv
    print("✓ load_dotenv imported")
    load_dotenv()
    print("✓ load_dotenv() called")
except Exception as e:
    print(f"✗ Error with load_dotenv: {e}")

try:
    import os
    print("✓ os module imported")
    token = os.getenv("DISCORD_TOKEN")
    print(f"✓ Discord token from env: {'Present (hidden)' if token else 'Not found'}")
except Exception as e:
    print(f"✗ Error with os: {e}")

try:
    import yaml
    print("✓ yaml module imported")
except ImportError as e:
    print(f"✗ Error importing yaml: {e}")

try:
    import discord
    print("✓ discord module imported")
except ImportError as e:
    print(f"✗ Error importing discord: {e}")

try:
    import config
    print("✓ config module imported")
    print(f"✓ Discord token from config: {'Present (hidden)' if config.DISCORD_TOKEN else 'Not found'}")
except Exception as e:
    print(f"✗ Error importing config: {e}")
    import traceback
    traceback.print_exc()

try:
    import database
    print("✓ database module imported")
except Exception as e:
    print(f"✗ Error importing database: {e}")
    import traceback
    traceback.print_exc()

try:
    import utils
    print("✓ utils module imported")
except Exception as e:
    print(f"✗ Error importing utils: {e}")
    import traceback
    traceback.print_exc()

try:
    import cogs
    print("✓ cogs package imported")
except Exception as e:
    print(f"✗ Error importing cogs: {e}")

print("Import test completed") 