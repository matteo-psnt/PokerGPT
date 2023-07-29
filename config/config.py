import os
import dotenv
dotenv.load_dotenv()

API_KEY = str(os.getenv("OPENAI_API_KEY"))

TOKEN = str(os.getenv("DISCORD_TOKEN"))

DEV_TOKEN = str(os.getenv("DISCORD_DEV_TOKEN"))

try:
    DB_HOST = os.getenv('DB_HOST')

    DB_USER = os.getenv('DB_USER')

    DB_PASSWORD = os.getenv('DB_PASSWORD')

    DB_DATABASE = os.getenv('DB_NAME')
except:
    DB_HOST, DB_USER, DB_PASSWORD, DB_DATABASE = None, None, None, None