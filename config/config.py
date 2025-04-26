import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TOKEN = os.getenv("DISCORD_TOKEN")
DEV_TOKEN = os.getenv("DISCORD_DEV_TOKEN")

# Optional DB config
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_DATABASE = os.getenv("DB_NAME")

DATABASE_EXISTS = all([DB_HOST, DB_USER, DB_PASSWORD, DB_DATABASE])
