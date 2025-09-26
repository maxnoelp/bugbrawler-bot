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

REPO_NAME_FRONTEND = os.getenv("REPO_NAME_FRONTEND")

TICKET_TODO_CHANNEL_ID = os.getenv("TICKET_TODO_CHANNEL_ID")

DONE_CHANNEL_ID = os.getenv("DONE_CHANNEL_ID")

# Role IDs for ticket channel permissions
STAFF_ROLE_ID = int(os.getenv("STAFF_ROLE_ID")) if os.getenv("STAFF_ROLE_ID") else None
ADMIN_ROLE_ID = int(os.getenv("ADMIN_ROLE_ID")) if os.getenv("ADMIN_ROLE_ID") else None
OWNER_ROLE_ID = int(os.getenv("OWNER_ROLE_ID")) if os.getenv("OWNER_ROLE_ID") else None
HEAD_STAFF_ID = int(os.getenv("HEAD_STAFF_ID")) if os.getenv("HEAD_STAFF_ID") else None
HEAD_MOD_ID = int(os.getenv("HEAD_MOD_ID")) if os.getenv("HEAD_MOD_ID") else None
TRIAL_MOD_ID = int(os.getenv("TRIAL_MOD_ID")) if os.getenv("TRIAL_MOD_ID") else None
DESIGNER_ROLE_ID = int(os.getenv("DESIGNER_ROLE_ID")) if os.getenv("DESIGNER_ROLE_ID") else None

TICKET_CREATE_CHANNEL_ID = os.getenv("TICKET_CREATE_CHANNEL_ID")