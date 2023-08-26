from faker import Faker
from db.db_injector import DatabaseInjector
import random
import numpy as np

# Initialize the Faker library
faker = Faker()

db_injector = DatabaseInjector()


discord_server_names = [
    "Gamer's Galaxy",
    "Manga Masters Meet",
    "Film Fanatics Fort",
    "Literary Lounge",
    "Wellness Warriors",
    "Tune Town Collective",
    "Wisdom Warehouse",
    "Endless Dialogues",
    "Knowledge Nexus",
    "Code & Circuit Club"
]

# Generate and print 200 sets of fake statistics for servers
try:
    for _ in range(10):
        # Generate fake server details
        server_name = discord_server_names[_]
        host_id = _ + 1 # Using UUID for unique host_id values

        # Generate random statistics
        total_players = random.randint(4, 8)  # Averaging around 6
        total_hands = random.randint(200, 400)  # Averaging around 300

        # Generate random number of wins, losses, and draws
        total_losses = random.randint(total_hands//3, total_hands//2)
        temp = total_hands - total_losses - 20
        if temp < 0:
            temp = 0
        total_wins = random.randint(temp, total_hands - total_losses)
        total_draws = total_hands - total_wins - total_losses
        if total_draws < 0:
            total_draws = 0  # Ensure total_draws is not negative

        # Generate positive random net big blind statistics partially based on total_hands
        net_bb_wins = round(random.uniform(2 * total_hands, 4 * total_hands), 3)
        net_bb_losses = round(random.uniform(1 * total_hands, 3 * total_hands), 3)

        # Ensure about 95% of Net BB Wins and Net BB Losses are whole numbers
        if random.random() < 0.40:
            net_bb_wins = round(net_bb_wins, 1)
            net_bb_losses = round(net_bb_losses, 1)
        
        # Ensure about 95% of Net BB Wins and Net BB Losses are whole numbers
        if random.random() < 0.90:
            net_bb_wins = round(net_bb_wins)
            
        if random.random() < 0.90:
            net_bb_losses = round(net_bb_losses)

        # Calculate net_bb_total as the difference between net_bb_wins and net_bb_losses
        net_bb_total = round(net_bb_wins - net_bb_losses, 3)

        # Print the fake statistics
        print(f"Server Name: {server_name}")
        print(f"Host ID: {host_id}")
        print(f"Total Players: {total_players}")
        print(f"Total Hands: {total_hands}")
        print(f"Total Wins: {total_wins}")
        print(f"Total Losses: {total_losses}")
        print(f"Total Draws: {total_draws}")
        print(f"Net BB Wins: {net_bb_wins}")
        print(f"Net BB Losses: {net_bb_losses}")
        print(f"Net BB Total: {net_bb_total}")
        print("=" * 40)  # Separation line between servers
        
        
        db_injector.add_fake_server(host_id, server_name)
        db_injector.update_fake_server(host_id, **{
            'total_players': total_players,
            'total_hands': total_hands,
            'total_wins': total_wins,
            'total_losses': total_losses,
            'total_draws': total_draws,
            'net_bb_wins': net_bb_wins,
            'net_bb_losses': net_bb_losses,
            'net_bb_total': net_bb_total
        })
finally:
    db_injector.close()
