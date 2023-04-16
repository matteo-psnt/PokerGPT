
import os
import openai


# Get the API key from the environment variable
API_KEY = os.getenv('API_KEY')

openai.api_key = os.getenv(API_KEY)
openai.Model.list()