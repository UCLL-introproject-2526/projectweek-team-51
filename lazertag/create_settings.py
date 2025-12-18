import pickle
import os

# Create default settings with all required fields
settings = {
    'graphics': (100, 10),  # Graphics settings tuple (resolution, render distance)
    'fov': 50,              # Field of view
    'sensitivity': 0.25,    # Mouse sensitivity
    'volume': 0.1,          # Sound effects volume
    'music volume': 0,      # Music volume
    'fullscreen': True,     # Fullscreen mode
    'shut up': True         # Disable certain audio notifications
}

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

# Save to file
with open('data/settings.dat', 'wb') as f:
    pickle.dump(settings, f)

print('settings.dat created successfully with all required fields')
