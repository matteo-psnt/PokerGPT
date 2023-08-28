import logging

# Set up a logger
logger = logging.getLogger('my_app')
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('bot.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Set up a separate logger for the Discord library
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.INFO)
discord_file_handler = logging.FileHandler('discord.log')
discord_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
discord_logger.addHandler(discord_file_handler)