import os
import pygame
import random

# === PROCEDURALLY GENERATED TEXTURES ===

def create_neon_panel(width, height):
    """Create sleek neon panel walls for laser tag arena"""
    surface = pygame.Surface((width, height))

    # Base dark metallic color
    surface.fill((15, 20, 30))

    # Add vertical panels with subtle highlights
    panel_width = width // 3

    for i in range(3):
        x = i * panel_width

        # Dark panel border
        pygame.draw.rect(surface, (8, 12, 20), (x + 2, 2, panel_width - 4, height - 4))

        # Subtle metallic gradient effect
        for j in range(5):
            color = (20 + j * 3, 25 + j * 3, 35 + j * 3)
            pygame.draw.rect(surface, color, (x + 4 + j, 4, panel_width - 8 - j*2, height - 8))

        # Add thin neon accent strips
        accent_color = (57, 255, 20) if i % 2 == 0 else (255, 165, 0)

        # Top accent line
        pygame.draw.line(surface, accent_color, (x + 8, 6), (x + panel_width - 8, 6), 1)
        # Bottom accent line
        pygame.draw.line(surface, accent_color, (x + 8, height - 7), (x + panel_width - 8, height - 7), 1)
        # Vertical accent on side
        pygame.draw.line(surface, accent_color, (x + panel_width - 5, 8), (x + panel_width - 5, height - 8), 1)

    return surface

def create_tech_wall(width, height):
    """Create a high-tech smooth wall texture"""
    surface = pygame.Surface((width, height))

    # Dark base
    surface.fill((12, 15, 22))

    # Add horizontal tech lines
    line_spacing = height // 8

    for i in range(8):
        y = i * line_spacing

        # Main tech line
        color = (25, 30, 40) if i % 2 == 0 else (18, 22, 32)
        pygame.draw.line(surface, color, (0, y), (width, y), 2)

        # Subtle glow accent
        if i % 3 == 0:
            accent = (40, 200, 255, 100)  # Cyan glow
            pygame.draw.line(surface, accent[:3], (0, y + 1), (width, y + 1), 1)

    # Add corner detail
    corner_color = (57, 255, 20)
    pygame.draw.circle(surface, corner_color, (8, 8), 3)
    pygame.draw.circle(surface, corner_color, (width - 8, 8), 3)

    return surface

def create_smooth_metal(width, height):
    """Create a smooth brushed metal texture"""
    surface = pygame.Surface((width, height))

    # Darker base for laser tag atmosphere
    base_color = (20, 25, 35)
    surface.fill(base_color)

    # Add subtle horizontal brushed lines
    for y in range(0, height, 2):
        brightness = 20 + (y % 10)
        color = (brightness, brightness + 5, brightness + 15)
        pygame.draw.line(surface, color, (0, y), (width, y), 1)

    # Add edge highlights
    pygame.draw.line(surface, (40, 45, 60), (0, 0), (width, 0), 2)  # Top
    pygame.draw.line(surface, (15, 18, 25), (0, height-1), (width, height-1), 2)  # Bottom
    pygame.draw.line(surface, (30, 35, 50), (0, 0), (0, height), 2)  # Left
    pygame.draw.line(surface, (30, 35, 50), (width-1, 0), (width-1, height), 2)  # Right

    return surface

def create_tech_floor(width, height):
    """Create a simple gradient floor that looks good when static"""
    surface = pygame.Surface((width, height))

    # Create subtle vertical gradient (darker at bottom)
    for y in range(height):
        # Gradual darkening from top to bottom
        brightness = 35 - int((y / height) * 15)
        color = (brightness - 5, brightness, brightness + 5)
        pygame.draw.line(surface, color, (0, y), (width, y), 1)

    # Add very subtle noise/texture
    random.seed(42)  # Consistent pattern
    for i in range(50):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        noise_brightness = random.randint(-3, 3)
        base = 30
        noise_color = (base + noise_brightness, base + noise_brightness + 5, base + noise_brightness + 10)
        pygame.draw.circle(surface, noise_color, (x, y), 1)

    return surface

def create_tech_ceiling(width, height):
    """Create a black ceiling for laser tag arena atmosphere"""
    surface = pygame.Surface((width, height))
    # Pure black ceiling like a real laser tag arena
    surface.fill((0, 0, 0))
    return surface

def create_obstacle_wall(width, height):
    """Create tactical obstacle walls with neon glow effect"""
    surface = pygame.Surface((width, height))

    # Base color - reinforced concrete/metal look
    surface.fill((25, 30, 40))

    # Add vertical reinforcement plates
    plate_width = width // 4

    for i in range(4):
        x = i * plate_width

        # Darker recessed areas
        if i % 2 == 0:
            pygame.draw.rect(surface, (20, 25, 35), (x + 2, 2, plate_width - 4, height - 4))

        # Plate borders
        pygame.draw.line(surface, (35, 40, 50), (x, 0), (x, height), 2)

        # Rivets/bolts
        for y_pos in [8, height // 2, height - 8]:
            pygame.draw.circle(surface, (40, 45, 55), (x + plate_width // 2, y_pos), 2)
            pygame.draw.circle(surface, (15, 20, 30), (x + plate_width // 2, y_pos), 1)

    # Create neon glow effect with multiple layers
    stripe_height = 3

    # GREEN TEAM STRIPE with glow
    # Outer glow layer (transparent green)
    glow_surface = pygame.Surface((width - 8, stripe_height + 4), pygame.SRCALPHA)
    glow_surface.fill((57, 255, 20, 30))  # Very transparent outer glow
    surface.blit(glow_surface, (4, 0))

    # Middle glow layer
    glow_surface2 = pygame.Surface((width - 8, stripe_height + 2), pygame.SRCALPHA)
    glow_surface2.fill((57, 255, 20, 80))  # Semi-transparent middle glow
    surface.blit(glow_surface2, (4, 1))

    # Bright core
    pygame.draw.rect(surface, (57, 255, 20), (4, 2, width - 8, stripe_height))

    # ORANGE TEAM STRIPE with glow
    # Outer glow layer (transparent orange)
    glow_surface3 = pygame.Surface((width - 8, stripe_height + 4), pygame.SRCALPHA)
    glow_surface3.fill((255, 165, 0, 30))  # Very transparent outer glow
    surface.blit(glow_surface3, (4, height - stripe_height - 4))

    # Middle glow layer
    glow_surface4 = pygame.Surface((width - 8, stripe_height + 2), pygame.SRCALPHA)
    glow_surface4.fill((255, 165, 0, 80))  # Semi-transparent middle glow
    surface.blit(glow_surface4, (4, height - stripe_height - 3))

    # Bright core
    pygame.draw.rect(surface, (255, 165, 0), (4, height - stripe_height - 2, width - 8, stripe_height))

    # Add corner brackets (industrial look)
    bracket_color = (45, 50, 60)
    bracket_size = 6

    # Top-left
    pygame.draw.line(surface, bracket_color, (2, 2), (bracket_size, 2), 2)
    pygame.draw.line(surface, bracket_color, (2, 2), (2, bracket_size), 2)

    # Top-right
    pygame.draw.line(surface, bracket_color, (width - bracket_size, 2), (width - 2, 2), 2)
    pygame.draw.line(surface, bracket_color, (width - 2, 2), (width - 2, bracket_size), 2)

    # Bottom-left
    pygame.draw.line(surface, bracket_color, (2, height - bracket_size), (2, height - 2), 2)
    pygame.draw.line(surface, bracket_color, (2, height - 2), (bracket_size, height - 2), 2)

    # Bottom-right
    pygame.draw.line(surface, bracket_color, (width - 2, height - bracket_size), (width - 2, height - 2), 2)
    pygame.draw.line(surface, bracket_color, (width - bracket_size, height - 2), (width - 2, height - 2), 2)

    return surface

# === LASER TAG TEXTURES ===
all_textures = [
    os.path.join('graphics', 'tiles', 'null.png'), #Air #0

    #-- Laser Tag Arena Theme --
    # Perimeter Walls (Previously "smooth_metal", now upgraded to NEON)
    'PROCEDURAL:neon_panel', #1 - Main Neon Walls
    'PROCEDURAL:neon_panel', #2
    'PROCEDURAL:tech_wall',  #3 - Tech Wall Accent
    'PROCEDURAL:neon_panel', #4
    'PROCEDURAL:neon_panel', #5
    # Doors (Not used but defined)
    'PROCEDURAL:tech_wall',  #6
    'PROCEDURAL:tech_wall',  #7

    # Sprites (obstacles/middle walls)
    os.path.join('graphics', 'tiles', 'sprites', 'pillar.png'), #8
    os.path.join('graphics', 'tiles', 'sprites', 'table.png'), #9
    os.path.join('graphics', 'tiles', 'sprites', 'lysekrone.png'), #10

    #-- Mid-Arena Obstacle Walls (tactical cover) --
    # Walls
    'PROCEDURAL:obstacle_wall', #11 - Tactical obstacle walls with stripes
    'PROCEDURAL:obstacle_wall', #12
    'PROCEDURAL:obstacle_wall', #13
    'PROCEDURAL:obstacle_wall', #14
    'PROCEDURAL:obstacle_wall', #15
    # Sprites
    os.path.join('graphics', 'tiles', 'sprites', 'lysestage.png'), #16
    os.path.join('graphics', 'tiles', 'sprites', 'barrel.png'), #17
    os.path.join('graphics', 'tiles', 'sprites', 'stone_pillar.png'), #18

    #-- Additional Laser Tag Textures --
    # Walls
    'PROCEDURAL:neon_panel', #19
    'PROCEDURAL:tech_wall',  #20
    'PROCEDURAL:neon_panel', #21
    'PROCEDURAL:tech_wall',  #22
    # No doors
    'PROCEDURAL:tech_wall', #23
    'PROCEDURAL:tech_wall', #24
    # Sprites
    os.path.join('graphics', 'tiles', 'sprites', 'fern.png'), #25
    ]