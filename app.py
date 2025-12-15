import pygame

def create_main_surface():
    # Tuple representing width and height in pixels
    screen_size = (1024, 768)

    # Create window with given size
    return pygame.display.set_mode(screen_size)

def main():
    # Initialize Pygame
    pygame.init()

    # Create the main surface
    screen = create_main_surface()

    # Main loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

    pygame.quit()

# Explicitly call main
main()