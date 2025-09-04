import os
from dotenv import load_dotenv

load_dotenv()

GUILD_ID = os.getenv("GUILD_ID")

DC_TOKEN = os.getenv("DISCORD_TOKEN")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

REPO_OWNER = os.getenv("REPO_OWNER")

REPO_NAME = os.getenv("REPO_NAME")

DEV_ROLE_ID = int(os.getenv("DEV_ROLE_ID"))

TICKET_CHANNEL_ID = os.getenv("TICKET_CHANNEL_ID")
