import os
import dotenv
dotenv.load_dotenv()

API_KEY = str(os.getenv("OPENAI_API_KEY"))

token = str(os.getenv("DISCORD_TOKEN"))