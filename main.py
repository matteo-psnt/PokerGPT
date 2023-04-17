
import os
import openai


# Get the API key from the environment variable
API_KEY = os.getenv('API_KEY')
openai.api_key = API_KEY


def play_poker(hand1, hand2, flop1, flop2, flop3):
    response = openai.Completion.create(
        engine="gpt-3.5-turbo",
        prompt="Hey ChatGPT, let's play a game of Texas Hold'em poker! I'll be the dealer, and you'll be a player. Your starting hand is {hand1} and {hand2}. The community cards are {flop1}, {flop2}, and {flop3}. What move do you want to make? Will you fold, call, raise, or go all-in?",
        temperature=0.9,
        max_tokens=150,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0.6,
    )
    return response


# print (response)


if __name__ == "__main__":
    play_poker(prompt):
