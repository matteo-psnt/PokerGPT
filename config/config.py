import os
from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = str(os.getenv("OPENAI_API_KEY"))

TOKEN = str(os.getenv("DISCORD_TOKEN"))

try:
    DEV_TOKEN = str(os.getenv("DISCORD_DEV_TOKEN"))
except:
    DEV_TOKEN = None

try:
    DB_HOST = os.getenv('DB_HOST')

    DB_USER = os.getenv('DB_USER')

    DB_PASSWORD = os.getenv('DB_PASSWORD')

    DB_DATABASE = os.getenv('DB_NAME')
    DATABASE_EXISTS = True
except:
    DB_HOST, DB_USER, DB_PASSWORD, DB_DATABASE = None, None, None, None
    DATABASE_EXISTS = False