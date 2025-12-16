# Laser Tag Arena Maps for multiplayer gameplay
# Open spaces, cover obstacles, spawn zones for each team

import SETTINGS
import LEVELS

def load_laser_tag_arenas():
    """Load custom laser tag arena maps into the game"""

    # ARENA 1: "Team Zones" - Compact laser tag arena with anti-spawn-camp design
    arena_grid = LEVELS.Level({
        'lvl_number': 0,
        'name': 'Team Zones',
        'author': 'Laser Tag System',
        'sky_color': (5, 10, 25),  # Dark space-like ceiling
        'ground_color': (35, 35, 40),  # Dark gray floor
        'shade': (True, (0, 255, 255, 20), 800),  # Cyan neon glow
        'player_pos': [18, 8],  # Green team corner spawn (right side)

        # 0 = open space (walkable)
        # 1 = solid wall (outer boundary)
        # 11 = blue brick obstacle walls (mid_walls.png texture)
        'array': [
            # 22x16 compact arena - Shorter distance between spawns, heavy obstacles to prevent camping
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,0,0,0,11,11,11,11,11,11,0,0,0,1,1,1,1,1,1],
            [1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1],
            [1,1,0,0,0,0,11,11,0,0,0,0,11,11,0,0,0,0,0,1,1,1],
            [1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,11,11,0,0,1,1],
            [1,1,0,0,0,11,11,0,0,11,11,0,0,11,11,0,0,0,0,0,1,1],
            [1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1],
            [1,1,0,0,0,0,11,11,11,0,0,11,11,11,0,0,0,0,0,0,1,1],
            [1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1],
            [1,1,0,0,0,0,11,11,11,0,0,11,11,11,0,0,0,0,0,0,1,1],
            [1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1],
            [1,1,0,0,0,11,11,0,0,11,11,0,0,11,11,0,0,0,0,0,1,1],
            [1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,11,11,0,0,1,1],
            [1,1,0,0,0,0,11,11,0,0,0,0,11,11,0,0,0,0,0,1,1,1],
            [1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        ],

        # NPC spawn positions - 10 GREEN team (RIGHT CORNER), 10 ORANGE team (LEFT CORNER)
        'npcs': [
            # GREEN TEAM - Right corner spawn (columns 17-19, rows 7-11)
            ([18, 8], 180, 0),   # Green 1 - right corner, facing left
            ([19, 9], 180, 0),   # Green 2
            ([18, 10], 180, 0),  # Green 3
            ([17, 8], 180, 0),   # Green 4
            ([19, 7], 180, 0),   # Green 5
            ([17, 9], 180, 0),   # Green 6
            ([18, 7], 180, 0),   # Green 7
            ([19, 10], 180, 0),  # Green 8
            ([17, 10], 180, 0),  # Green 9
            ([18, 11], 180, 0),  # Green 10

            # ORANGE TEAM - Left corner spawn (columns 2-4, rows 7-11)
            ([3, 8], 0, 0),      # Orange 1 - left corner, facing right
            ([2, 9], 0, 0),      # Orange 2
            ([3, 10], 0, 0),     # Orange 3
            ([4, 8], 0, 0),      # Orange 4
            ([2, 7], 0, 0),      # Orange 5
            ([4, 9], 0, 0),      # Orange 6
            ([3, 7], 0, 0),      # Orange 7
            ([2, 10], 0, 0),     # Orange 8
            ([4, 10], 0, 0),     # Orange 9
            ([3, 11], 0, 0),     # Orange 10
        ],

        # No items in laser tag mode (unlimited ammo)
        'items': [],
    })

    # Load laser tag arena into tutorial levels list (used when "LASER TAG" button is clicked)
    SETTINGS.tlevels_list = [arena_grid]
    # Also set it to generated levels list so "NEW GAME" uses the same map
    SETTINGS.glevels_list = [arena_grid]
    # Set it to main levels_list for initial game setup
    SETTINGS.levels_list = [arena_grid]
    print("[LASER TAG] Loaded arena: Team Zones (22x16 - Anti-spawn-camp design)")
    return SETTINGS.levels_list