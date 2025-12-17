import pickle
import os

# Create default statistics with all required fields
statistics = {
    'playtime': 0,
    'kills': 0,
    'deaths': 0,
    'shots_fired': 0,
    'shots_hit': 0,
    'damage_dealt': 0,
    'damage_taken': 0,
    'distance_walked': 0,
    'levels_completed': 0,
    'games_played': 0,
    'wins': 0,
    'losses': 0,
    'green_kills': 0,
    'orange_kills': 0,
    'team_wins_green': 0,
    'team_wins_orange': 0,
    'best enemies': 0,  # Best enemies killed in a single game
    'best score': 0,    # Best score achieved
    'best accuracy': 0, # Best accuracy percentage
    'total_distance': 0, # Total distance walked
    'best ddealt': 0,   # Best damage dealt in a single game
    'best dtaken': 0,   # Best damage taken in a single game
    'best shots': 0,    # Best shots fired in a single game
    'best levels': 0,   # Best level streak
    'last enemies': 0,  # Last game enemies killed
    'last ddealt': 0,   # Last game damage dealt
    'last dtaken': 0,   # Last game damage taken
    'last shots': 0,    # Last game shots fired
    'last levels': 0,   # Last game level streak
    'all enemies': 0,   # All-time enemies killed
    'all ddealt': 0,    # All-time damage dealt
    'all dtaken': 0,    # All-time damage taken
    'all shots': 0,     # All-time shots fired
    'all levels': 0     # All-time level streak
}

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

# Save to file
with open('data/statistics.dat', 'wb') as f:
    pickle.dump(statistics, f)

print('statistics.dat created successfully with all required fields')
