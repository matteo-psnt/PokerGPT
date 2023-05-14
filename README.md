# Poker Discord Bot - ChatGPT

Welcome to the Poker Discord Bot powered by ChatGPT! This bot allows you to play a virtual game of Texas Hold'em poker with your friends right in your Discord server. The bot utilizes the powerful ChatGPT-3.5 language model developed by OpenAI to provide an interactive and dynamic poker experience.

## Features

- **Multiplayer Poker**: Play Texas Hold'em poker with multiple players in your Discord server.
- **Intelligent Chat**: Interact with the ChatGPT-3.5 language model to have realistic conversations and gameplay guidance.
- **Dynamic Gameplay**: The bot handles all aspects of the game, including dealing cards, managing bets, and determining winners.
- **Easy-to-Use Command**: Start a game of Texas Hold'em using the `play_poker` command.
- **Customizable Settings**: Adjust various game settings such as starting chips, blind levels, and move timeout.
- **Error Handling**: The bot incorporates error handling to ensure a smooth user experience and provide informative error messages when necessary.

## Command

To start a game of Texas Hold'em poker, use the following command:

/play_poker [buy-in] [small-blind] [big-blind] [timeout]


- `buy-in` (optional): Set the starting chips for each player (default: 1000, minimum: 10).
- `small-blind` (optional): Set the small blind amount (default: 5, minimum: 1).
- `big-blind` (optional): Set the big blind amount (default: 10, minimum: 2).
- `timeout` (optional): Set the number of seconds allowed to make a move (default: 30, minimum: 5, maximum: 180).

## Setup

To set up the Poker Discord Bot in your Discord server, follow these steps:

1. Create a new Discord application on the Discord Developer Portal.
2. Generate a bot token for your application.
3. Invite the bot to your server using the generated invite link.
4. Create a `.env` file in the project directory.
5. In the `.env` file, add the following line:

```plaintext
DISCORD_TOKEN=your_discord_bot_token
OPENAI_API_KEY=your_openai_api_key
```

6. Replace your_discord_bot_token with your Discord bot token.
7. Replace your_openai_api_key with your OpenAI API key.
8. Configure any other settings in the code as needed.
9. Run the bot script on your preferred hosting environment.

## Contributions

Contributions to the Poker Discord Bot are welcome! If you have any suggestions, bug reports, or feature requests, please open an issue or submit a pull request on the GitHub repository.

## Disclaimer

This Poker Discord Bot is provided as-is without any warranty. The developers and contributors are not responsible for any loss of virtual currency or damages resulting from the use of this bot.

## License

The Poker Discord Bot is released under the [MIT License](https://opensource.org/licenses/MIT).
