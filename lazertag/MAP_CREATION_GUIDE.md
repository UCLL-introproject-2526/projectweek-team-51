# LASER TAG MAP CREATION GUIDE

## Best Tools for Creating Maps

1. **Excel or Google Sheets** (RECOMMENDED)
   - Set column width to match row height (make square cells)
   - Use cell colors or numbers to design your map
   - Copy the numbers into the code

2. **Notepad++ or VS Code**
   - Use a monospace font
   - Type numbers directly in array format

3. **Graph Paper**
   - Sketch your design first
   - Transfer to code

## Map Dimensions

Your map can be **ANY SIZE** you want! Examples:
- Small arena: 15x15 (225 tiles)
- Medium arena: 25x25 (625 tiles) - Current "The Grid" arena
- Large arena: 40x40 (1600 tiles)
- Rectangle: 30x20, 50x25, etc.

**IMPORTANT:** Maps must be rectangular (all rows same length)

## Tile Numbers Guide

```
0  = Open space (walkable floor)
1  = Solid wall (arena boundary - uses wall_pattern.jpg)
11 = Blue brick walls (mid-arena obstacles - uses mid_walls.png)
12 = Blue brick walls
13 = Blue brick walls
14 = Blue brick walls
15 = Blue brick walls

SPRITES (pass-through obstacles):
8  = Pillar sprite
9  = Table sprite
10 = Chandelier sprite
16 = Lamp sprite
17 = Barrel sprite
18 = Stone pillar sprite
25 = Fern sprite
```

## Example Map Template

Here's a simple 15x15 laser tag arena you can use as a template:

```python
# Copy this into LASERTAG_ARENA.py

arena_simple = LEVELS.Level({
    'lvl_number': 1,
    'name': 'Simple Arena',
    'author': 'Your Name',
    'sky_color': (5, 10, 25),        # Dark ceiling
    'ground_color': (35, 35, 40),    # Dark gray floor
    'shade': (True, (0, 255, 255, 20), 800),  # Cyan glow
    'player_pos': [2, 2],  # Green team spawn position

    'array': [
        # 15x15 simple arena with center obstacles
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        [1,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
        [1,0,8,0,0,0,0,0,0,0,0,0,8,0,1],
        [1,0,0,0,0,11,11,11,11,11,0,0,0,0,1],
        [1,0,0,0,0,11,0,0,0,11,0,0,0,0,1],
        [1,0,0,0,0,11,0,17,0,11,0,0,0,0,1],
        [1,0,0,0,0,11,0,0,0,11,0,0,0,0,1],
        [1,0,0,0,0,11,11,0,11,11,0,0,0,0,1],
        [1,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
        [1,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
        [1,0,8,0,0,0,0,9,0,0,0,0,8,0,1],
        [1,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
        [1,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
        [1,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    ],

    'npcs': [
        # Format: ([x, y], angle, npc_type)
        # Angles: 0=East, 90=North, 180=West, 270=South
        # npc_type is always 0 for laser tag

        # Green team spawns (left side)
        ([3, 3], 90, 0),
        ([3, 5], 90, 0),
        ([3, 7], 90, 0),
        ([3, 9], 90, 0),
        ([3, 11], 90, 0),

        # Orange team spawns (right side)
        ([11, 3], 270, 0),
        ([11, 5], 270, 0),
        ([11, 7], 270, 0),
        ([11, 9], 270, 0),
        ([11, 11], 270, 0),
    ],

    'items': []  # No items in laser tag mode
})

# Add to levels list
SETTINGS.tlevels_list.append(arena_simple)
```

## How to Add Your Map to the Game

1. Open [LASERTAG_ARENA.py](LASERTAG_ARENA.py)

2. Copy the template above and paste it BEFORE the line that says:
   ```python
   SETTINGS.tlevels_list.append(arena_grid)
   ```

3. Customize your map:
   - Change the `'array'` to your design
   - Add NPC spawn points in `'npcs'`
   - Change `'name'` and `'author'`
   - Adjust `'player_pos'` to where green team spawns

4. The map will appear when you click "Laser Tag" in the menu!

## Visual Map Design Tips

**Wall Layouts:**
- Use `1` for outer walls (always surround your map!)
- Use `11-15` for cover/obstacles inside the arena
- Leave lots of `0` (open space) for movement

**Obstacle Ideas:**
```
Center Fort:        Corner Cover:       Hallway:
[11,11,11,11]      [11,11,0]           [0,11,0]
[11,0,0,11]        [11,0,0]            [0,11,0]
[11,0,0,11]        [0,0,0]             [0,11,0]
[11,11,11,11]                          [0,11,0]
```

**Sprite Placement:**
- Place `8, 9, 17, 18` for obstacles you can shoot through
- Don't block spawn points with obstacles!

## Color Customization

Want different colors? Change these values:

```python
'sky_color': (R, G, B),      # Ceiling color (0-255 for each)
'ground_color': (R, G, B),   # Floor color
'shade': (True, (R, G, B, A), distance)  # Glow effect
```

Examples:
- Red arena: `'shade': (True, (255, 0, 0, 20), 800)`
- Green arena: `'shade': (True, (0, 255, 0, 20), 800)`
- Purple arena: `'shade': (True, (200, 0, 255, 20), 800)`
