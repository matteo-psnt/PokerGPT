import os
import dotenv
dotenv.load_dotenv()

API_KEY = str(os.getenv("OPENAI_API_KEY"))

TOKEN = str(os.getenv("DISCORD_TOKEN"))

DEV_TOKEN = str(os.getenv("DISCORD_DEV_TOKEN"))