import pygame
import pickle
import os
import copy
import random
import math
import SETTINGS
import TEXT
import SOUND

SETTINGS.menu_showing = True

class Controller:

    def __init__(self, canvas):
        self.current_menu = 'main'
        self.current_type = 'main'
        self.canvas = canvas
        self.shut_up = False

        self.load_settings()
        self.esc_pressed = False
        self.new_pressed = False

        self.mainMenu = MainMenu()
        self.newMenu = NewMenu(self.current_settings)
        self.optionsMenu = OptionsMenu(self.current_settings)
        self.creditsMenu = CreditsMenu()
        self.gMainMenu = GMainMenu()
        self.supportSplash = SupportSplash()
        self.scoreMenu = ScoreMenu()

    def load_settings(self):
        #This script does not change the settings themselves, but only the settings.dat
        with open(os.path.join('data', 'settings.dat'), 'rb') as file1:
            settings = pickle.load(file1)

        self.current_settings = settings

        #self.current_settings = {'fov': 60, 'fullscreen': False, 'sensitivity': 0.25, 'graphics': (140, 12), 'volume': 0.5, 'music volume' : 0, 'shut up' : False}

        self.shut_up = self.current_settings['shut up']        
        
    def save_settings(self):
        current_settings = self.optionsMenu.current_settings
        current_settings['shut up'] = self.shut_up
        
        with open(os.path.join('data', 'settings.dat'), 'wb') as file2:
            pickle.dump(current_settings, file2)
            

    def check_mouse(self):
        pygame.event.set_grab(False)
        pygame.mouse.set_visible(True)

    def control(self):
        self.check_mouse()
        if self.current_type == 'main':
            if self.current_menu == 'main':
                self.mainMenu.draw(self.canvas)
                if self.mainMenu.new_button.get_clicked():
                    self.current_menu = 'new'
                elif self.mainMenu.options_button.get_clicked():
                    self.current_menu = 'options'
                elif self.mainMenu.score_button.get_clicked():
                    self.current_menu = 'score'
                elif self.mainMenu.quit_button.get_clicked():
                    SETTINGS.quit_game = True
                #Splash screen
                if SETTINGS.statistics['playtime'] >= 120 and not self.shut_up:
                    self.supportSplash.draw(self.canvas)
                    if self.supportSplash.button.get_clicked():
                        self.shut_up = True
                        self.save_settings()
                
            elif self.current_menu == 'new':
                self.newMenu.draw(self.canvas)
                if self.newMenu.back_button.get_clicked():
                    self.current_menu = 'main'

                # Multiplayer button - placeholder for future implementation
                elif self.newMenu.new_button.get_clicked():
                    pass  # TODO: Implement multiplayer functionality

                # Play laser tag
                elif self.newMenu.tutorial_button.get_clicked():
                    self.newMenu.reset_inventory()
                    SETTINGS.playing_tutorial = True
                elif SETTINGS.playing_tutorial:
                    self.current_type = 'game'
                    self.current_menu = 'main'
                    SETTINGS.current_level = 0
                    SETTINGS.menu_showing = False
                    SETTINGS.playing_tutorial = False                    

            elif self.current_menu == 'options':
                self.optionsMenu.draw(self.canvas)
                if self.optionsMenu.back_button.get_clicked():
                    self.current_menu = 'main'
                if self.optionsMenu.save:
                    self.save_settings()
                    self.optionsMenu.save = False

            elif self.current_menu == 'score':
                self.scoreMenu.draw(self.canvas)
                if self.scoreMenu.back_button.get_clicked():
                    self.current_menu = 'main'

        #Show menu in game 
        elif self.current_type == 'game':
            key = pygame.key.get_pressed()
            if self.current_menu == 'main':
                self.gMainMenu.draw(self.canvas)
                if self.gMainMenu.resume_button.get_clicked() or (self.esc_pressed and not key[pygame.K_ESCAPE]):
                    SETTINGS.menu_showing = False
                    self.esc_pressed = False
                elif self.gMainMenu.exit_button.get_clicked():
                    self.current_type = 'main'

            if key[pygame.K_ESCAPE]:
                self.esc_pressed = True
                

class Menu:

    def __init__(self, title):
        self.title = TEXT.Text(0,0, title, SETTINGS.BLACK, "DUGAFONT.ttf", 120)
        self.title.update_pos((SETTINGS.canvas_actual_width/2)-(self.title.layout.get_width()/2)+8, 20)

        self.background_image = None


class Particle:
    def __init__(self, x, y, color, speed_x, speed_y):
        self.x = x
        self.y = y
        self.color = color
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.size = random.randint(1, 3)
        self.lifetime = random.randint(60, 120)
        self.age = 0

    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.age += 1
        return self.age < self.lifetime

    def draw(self, canvas):
        alpha = int(255 * (1 - self.age / self.lifetime))
        surf = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color, alpha), (self.size, self.size), self.size)
        canvas.blit(surf, (int(self.x), int(self.y)))


class LaserBeam:
    def __init__(self, start_x, start_y, end_x, end_y, color):
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.color = color
        self.lifetime = random.randint(15, 40)  # Last longer
        self.age = 0
        self.width = random.randint(3, 5)  # Thicker beams

    def update(self):
        self.age += 1
        return self.age < self.lifetime

    def draw(self, canvas):
        alpha = int(200 * (1 - self.age / self.lifetime))
        # Calculate bounding box for the line
        min_x = int(min(self.start_x, self.end_x))
        max_x = int(max(self.start_x, self.end_x))
        min_y = int(min(self.start_y, self.end_y))
        max_y = int(max(self.start_y, self.end_y))
        width = max(max_x - min_x + 20, 20)
        height = max(max_y - min_y + 20, 20)

        # Create smaller surface just for this beam
        beam_surf = pygame.Surface((width, height), pygame.SRCALPHA)

        # Adjust coordinates relative to surface
        start_x_rel = int(self.start_x - min_x + 10)
        start_y_rel = int(self.start_y - min_y + 10)
        end_x_rel = int(self.end_x - min_x + 10)
        end_y_rel = int(self.end_y - min_y + 10)

        # Draw glow layers
        for i in range(3, 0, -1):
            glow_alpha = alpha // (4 - i)
            pygame.draw.line(beam_surf, (*self.color, min(255, glow_alpha)),
                           (start_x_rel, start_y_rel),
                           (end_x_rel, end_y_rel),
                           self.width + i * 2)
        # Draw core beam
        pygame.draw.line(beam_surf, (*self.color, min(255, alpha)),
                       (start_x_rel, start_y_rel),
                       (end_x_rel, end_y_rel),
                       self.width)

        # Blit to canvas
        canvas.blit(beam_surf, (min_x - 10, min_y - 10))


class MainMenu(Menu):

    def __init__(self):
        Menu.__init__(self, '')
        self.new_button = Button((SETTINGS.canvas_actual_width/2, 320, 200, 60), "NEW GAME")
        self.options_button = Button((SETTINGS.canvas_actual_width/2, 410, 200, 60), "OPTIONS")
        self.score_button = Button((SETTINGS.canvas_actual_width/2, 500, 200, 60), "STATISTICS")
        self.quit_button = Button((SETTINGS.canvas_actual_width/2, 590, 200, 60), "QUIT")

        self.logo = pygame.image.load(os.path.join('graphics', 'logo_cutout.png')).convert_alpha()
        self.logo_rect = self.logo.get_rect()

        self.logo_surface = pygame.Surface(self.logo.get_size()).convert_alpha()
        self.logo_surface_rect = self.logo_surface.get_rect()
        self.logo_surface_rect.center = (SETTINGS.canvas_actual_width/2, 90)

        # Load NPC sprites for animation
        try:
            self.green_npc = pygame.image.load(os.path.join('graphics', 'npc', 'green_team_player.png')).convert_alpha()
            self.orange_npc = pygame.image.load(os.path.join('graphics', 'npc', 'orange_team_player.png')).convert_alpha()
            # Scale NPCs to appropriate size
            npc_size = 120
            self.green_npc = pygame.transform.scale(self.green_npc, (npc_size, npc_size))
            self.orange_npc = pygame.transform.scale(self.orange_npc, (npc_size, npc_size))
        except:
            self.green_npc = None
            self.orange_npc = None

        # NPC animation positions
        self.npc_timer = 0
        self.green_npc_pos = [50, SETTINGS.canvas_target_height - 150]
        self.orange_npc_pos = [SETTINGS.canvas_actual_width - 170, SETTINGS.canvas_target_height - 150]

        # Particle system - laser beams
        self.particles = []
        self.particle_spawn_timer = 0

        # Laser beams shooting across screen
        self.laser_beams = []
        self.laser_spawn_timer = 0

        # Animated background - grid lines for laser tag arena feel
        self.bg_offset = 0
        self.grid_offset_x = 0
        self.grid_offset_y = 0

        # "LASER TAG ARENA" subtitle
        self.subtitle = TEXT.Text(0, 0, "ARENA  MODE", SETTINGS.team_colors['green'], "DUGAFONT.ttf", 32)
        self.subtitle.update_pos((SETTINGS.canvas_actual_width/2) - (self.subtitle.layout.get_width()/2), 180)

    def draw(self, canvas):
        # Solid black background - clean and simple
        canvas.fill((0, 0, 0))

        # Spawn laser beams shooting from logo center outward
        self.laser_spawn_timer += 1
        if self.laser_spawn_timer > 30:  # Moderate spawn rate
            if random.random() > 0.5:  # 50% chance
                color = SETTINGS.team_colors['green'] if random.random() > 0.5 else SETTINGS.team_colors['orange']
                # Start from logo center
                start_x = SETTINGS.canvas_actual_width // 2
                start_y = 140  # Logo center height

                # Random direction outward
                angle = random.uniform(0, 360)
                distance = random.randint(300, 600)
                end_x = start_x + int(distance * math.cos(math.radians(angle)))
                end_y = start_y + int(distance * math.sin(math.radians(angle)))

                # Keep end points on screen
                end_x = max(0, min(SETTINGS.canvas_actual_width, end_x))
                end_y = max(0, min(SETTINGS.canvas_target_height, end_y))

                self.laser_beams.append(LaserBeam(start_x, start_y, end_x, end_y, color))
            self.laser_spawn_timer = 0

        # Update and draw laser beams
        self.laser_beams = [beam for beam in self.laser_beams if beam.update()]
        for beam in self.laser_beams:
            beam.draw(canvas)

        # Clean design - no particles, NPCs, or subtitle

        self.logo_animation(canvas)

        self.new_button.draw(canvas)
        self.options_button.draw(canvas)
        self.score_button.draw(canvas)
        self.quit_button.draw(canvas)

    def logo_animation(self, canvas):
        # Subtle glowing logo effect - laser tag style
        glow_pulse = abs(pygame.math.Vector2(1, 0).rotate(pygame.time.get_ticks() * 0.08).x)
        glow_size = int(glow_pulse * 10 + 8)

        # Subtle background glow - only 3 layers
        for i in range(3):
            glow_radius = glow_size * (3 - i) + i * 5
            glow_surface = pygame.Surface((self.logo.get_width() + glow_radius * 2, self.logo.get_height() + glow_radius * 2), pygame.SRCALPHA)

            # Alternate between green and orange glow layers - subtler
            if i % 2 == 0:
                color = (0, 255, 0, 60 - i * 15)
            else:
                color = (255, 140, 0, 60 - i * 15)

            # Draw filled rectangle glow
            pygame.draw.rect(glow_surface, color, glow_surface.get_rect(), border_radius=20)

            glow_rect = glow_surface.get_rect()
            glow_rect.center = self.logo_surface_rect.center
            canvas.blit(glow_surface, glow_rect)

        # Draw main logo
        canvas.blit(self.logo, self.logo_surface_rect)

        # Add subtle scan line effect across logo
        scan_y = int((pygame.time.get_ticks() * 0.3) % self.logo.get_height())
        scan_surf = pygame.Surface((self.logo.get_width(), 2), pygame.SRCALPHA)
        scan_surf.fill((255, 255, 255, 60))
        canvas.blit(scan_surf, (self.logo_surface_rect.x, self.logo_surface_rect.y + scan_y))
        
        

class NewMenu(Menu):

    def __init__(self, settings):
        Menu.__init__(self, 'NEW GAME')
        self.new_button = Button((SETTINGS.canvas_actual_width/2, 320, 200, 60), "MULTIPLAYER")
        self.tutorial_button = Button((SETTINGS.canvas_actual_width/2, 410, 200, 60), "LASER  TAG")
        self.back_button = Button((SETTINGS.canvas_actual_width/2, 590, 200, 60), "BACK")

        self.loading = TEXT.Text(0,0, "LOADING...", SETTINGS.BLACK, "DUGAFONT.ttf", 74)
        self.loading.update_pos((SETTINGS.canvas_actual_width/2)-(self.loading.layout.get_width()/2)+8, (SETTINGS.canvas_target_height/2)-(self.loading.layout.get_height()/2))

        self.nolevels = TEXT.Text(0,0, "NO  CUSTOM  LEVELS", SETTINGS.RED, "DUGAFONT.ttf", 50)
        self.nolevels.update_pos((SETTINGS.canvas_actual_width/2)-(self.nolevels.layout.get_width()/2)+8, (SETTINGS.canvas_target_height/2)-(self.nolevels.layout.get_height()/2))
        self.timer = 0
        self.no_levels_on = False
        self.settings = settings

    def draw(self, canvas):
        # Dark arena background with grid
        canvas.fill((5, 5, 15))

        # Animated grid effect
        grid_offset = (pygame.time.get_ticks() * 0.02) % 40
        grid_surf = pygame.Surface((SETTINGS.canvas_actual_width, SETTINGS.canvas_target_height), pygame.SRCALPHA)

        # Grid lines
        for i in range(0, SETTINGS.canvas_target_height, 40):
            y_pos = int((i + grid_offset) % SETTINGS.canvas_target_height)
            pygame.draw.line(grid_surf, (0, 100, 0, 40), (0, y_pos), (SETTINGS.canvas_actual_width, y_pos), 1)

        for i in range(0, SETTINGS.canvas_actual_width, 40):
            pygame.draw.line(grid_surf, (100, 50, 0, 30), (i, 0), (i, SETTINGS.canvas_target_height), 1)

        canvas.blit(grid_surf, (0, 0))

        # Add animated accent lines (laser sweep effect)
        line_offset = (pygame.time.get_ticks() * 0.05) % SETTINGS.canvas_target_height
        for i in range(3):
            y_pos = int((line_offset + i * (SETTINGS.canvas_target_height / 3)) % SETTINGS.canvas_target_height)
            alpha_surf = pygame.Surface((SETTINGS.canvas_actual_width, 3), pygame.SRCALPHA)
            color = SETTINGS.team_colors['green'] if i % 2 == 0 else SETTINGS.team_colors['orange']
            # Draw glow
            for j in range(3, 0, -1):
                pygame.draw.line(alpha_surf, (*color, 60 // j), (0, 1), (SETTINGS.canvas_actual_width, 1), j)
            canvas.blit(alpha_surf, (0, y_pos))

        self.new_button.draw(canvas)
        self.tutorial_button.draw(canvas)
        self.back_button.draw(canvas)

        # Draw title with glow effect
        title_glow = pygame.Surface((self.title.layout.get_width() + 40, self.title.layout.get_height() + 20), pygame.SRCALPHA)
        pulse = abs(pygame.math.Vector2(1, 0).rotate(pygame.time.get_ticks() * 0.1).x)
        for i in range(3):
            pygame.draw.rect(title_glow, (0, 200, 0, int(40 * pulse) // (i + 1)),
                           title_glow.get_rect(), border_radius=8)
        canvas.blit(title_glow, (self.title.posx - 20, self.title.posy - 10))
        self.title.draw(canvas)

        if self.no_levels_on:
            self.draw_no_levels(canvas)
        else:
            self.timer = 0

    def reset_inventory(self):
        for i in SETTINGS.inventory:
            SETTINGS.inventory[i] = None

        for i in SETTINGS.held_ammo:
            SETTINGS.held_ammo[i] = 0

        for i in SETTINGS.gun_list:
            i.current_mag = 0

        # LASER TAG - Give player laser rifle and melee
        SETTINGS.gun_list[0].current_mag = 25  # Laser rifle starts with full mag
        SETTINGS.gun_list[1].current_mag = 0   # Knife doesn't use ammo
        SETTINGS.inventory['primary'] = SETTINGS.gun_list[0]  # Laser rifle
        SETTINGS.inventory['melee'] = SETTINGS.gun_list[1]     # Knife
        SETTINGS.current_gun = SETTINGS.gun_list[0]  # Start with laser rifle equipped
        SETTINGS.next_gun = SETTINGS.gun_list[0]

        SETTINGS.player_health = SETTINGS.og_player_health
        SETTINGS.player_armor = SETTINGS.og_player_armor
        SETTINGS.current_level = 0

        SETTINGS.player_states['dead'] = False
        SETTINGS.player_states['invopen'] = False
        SETTINGS.player_states['heal'] = False
        SETTINGS.player_states['armor'] = False
        SETTINGS.player_states['cspeed'] = 0

        SETTINGS.statistics['last enemies'] = 0
        SETTINGS.statistics['last dtaken'] = 0
        SETTINGS.statistics['last ddealt'] = 0
        SETTINGS.statistics['last shots'] = 0
        SETTINGS.statistics['last levels'] = 0

        SETTINGS.fov = self.settings['fov']
        SETTINGS.player_states['cspeed'] = SETTINGS.player_speed
        SETTINGS.aiming = False
        SETTINGS.player.update_collide_list = True

    def draw_no_levels(self, canvas):
        if self.timer <= 1.2:
            self.nolevels.draw(canvas)
        else:
            self.no_levels_on = False
            
        self.timer += SETTINGS.dt
        

class OptionsMenu(Menu):
    
    def __init__(self, settings):
        Menu.__init__(self, 'OPTIONS')
        self.save = False

        self.strings = ['LOW', 'MED', 'HIGH']
        self.music_strings = ['OFF', 'MED', 'HIGH']
        self.degrees = ['50', '60', '70']
        self.onoff = ['ON', 'OFF']
        
        self.strings_to_data = {
            #'graphics' : [(resolution, render), (), ()]
            'graphics' : [(100, 10), (140, 12), (175, 14)],
            'fov' : [50, 60, 70],
            'sensitivity' : [0.15, 0.25, 0.35], #Tjek den her
            'volume' : [0.1, 0.5, 1],
            'music volume' : [0, 0.5, 1],
            'fullscreen' : [True, False],}

        self.graphics_index = self.strings_to_data['graphics'].index(settings['graphics'])
        self.fov_index = self.strings_to_data['fov'].index(settings['fov'])
        self.sens_index = self.strings_to_data['sensitivity'].index(settings['sensitivity'])
        self.vol_index = self.strings_to_data['volume'].index(settings['volume'])
        self.music_index = self.strings_to_data['music volume'].index(settings['music volume'])
        self.fs_index = self.strings_to_data['fullscreen'].index(settings['fullscreen'])

        self.update_strings()


    def update_strings(self):
        
        self.graphics_button = Button((SETTINGS.canvas_actual_width/2, 150, 300, 30), "GRAPHICS: %s" % self.strings[self.graphics_index])
        self.fov_button = Button((SETTINGS.canvas_actual_width/2, 200, 300, 30), "FOV: %s" % self.degrees[self.fov_index])
        self.sensitivity_button = Button((SETTINGS.canvas_actual_width/2, 250, 300, 30), "SENSITIVITY: %s" % self.strings[self.sens_index])
        self.volume_button = Button((SETTINGS.canvas_actual_width/2, 300, 300, 30), "MASTER  VOLUME: %s" % self.strings[self.vol_index])
        self.music_button = Button((SETTINGS.canvas_actual_width/2, 350, 300, 30), "MUSIC  VOLUME: %s" % self.music_strings[self.music_index])
        self.fullscreen_button = Button((SETTINGS.canvas_actual_width/2, 400, 300, 30), "FULLSCREEN: %s" % self.onoff[self.fs_index])
        self.back_button = Button((SETTINGS.canvas_actual_width/2, 500, 200, 60), "BACK")

        self.restart = TEXT.Text(0,0, 'RESTART GAME TO APPLY CHANGES', SETTINGS.LIGHTGRAY, "DUGAFONT.ttf", 20)
        self.restart.update_pos((SETTINGS.canvas_actual_width/2)-(self.restart.layout.get_width()/2), 580)

        self.current_settings = {
            'graphics' : self.strings_to_data['graphics'][self.graphics_index],
            'fov' : self.strings_to_data['fov'][self.fov_index],
            'sensitivity' : self.strings_to_data['sensitivity'][self.sens_index],
            'volume' : self.strings_to_data['volume'][self.vol_index],
            'music volume' : self.strings_to_data['music volume'][self.music_index],
            'fullscreen' : self.strings_to_data['fullscreen'][self.fs_index],}

        self.save = True

    def control_options(self):
        if self.graphics_button.get_clicked():
            self.graphics_index += 1
            if self.graphics_index >= len(self.strings):
                self.graphics_index = 0
            self.update_strings()

        elif self.fov_button.get_clicked():
            self.fov_index += 1
            if self.fov_index >= len(self.degrees):
                self.fov_index = 0
            self.update_strings()

        elif self.sensitivity_button.get_clicked():
            self.sens_index += 1
            if self.sens_index >= len(self.strings):
                self.sens_index = 0
            self.update_strings()

        elif self.volume_button.get_clicked():
            self.vol_index += 1
            if self.vol_index >= len(self.strings):
                self.vol_index = 0
            self.update_strings()

        elif self.music_button.get_clicked():
            self.music_index += 1
            if self.music_index >= len(self.music_strings):
                self.music_index = 0
            self.update_strings()

        elif self.fullscreen_button.get_clicked():
            self.fs_index += 1
            if self.fs_index >= len(self.onoff):
                self.fs_index = 0
            self.update_strings()
            

    def draw(self, canvas):
        # Dark arena background with subtle grid
        canvas.fill((5, 5, 15))

        # Subtle grid pattern
        grid_surf = pygame.Surface((SETTINGS.canvas_actual_width, SETTINGS.canvas_target_height), pygame.SRCALPHA)
        for i in range(0, SETTINGS.canvas_target_height, 50):
            pygame.draw.line(grid_surf, (0, 80, 0, 20), (0, i), (SETTINGS.canvas_actual_width, i), 1)
        for i in range(0, SETTINGS.canvas_actual_width, 50):
            pygame.draw.line(grid_surf, (80, 40, 0, 15), (i, 0), (i, SETTINGS.canvas_target_height), 1)
        canvas.blit(grid_surf, (0, 0))

        self.graphics_button.draw(canvas)
        self.fov_button.draw(canvas)
        self.sensitivity_button.draw(canvas)
        self.volume_button.draw(canvas)
        self.music_button.draw(canvas)
        self.fullscreen_button.draw(canvas)
        self.back_button.draw(canvas)

        # Draw title with glow
        title_glow = pygame.Surface((self.title.layout.get_width() + 40, self.title.layout.get_height() + 20), pygame.SRCALPHA)
        for i in range(3):
            pygame.draw.rect(title_glow, (0, 150, 0, 30 // (i + 1)), title_glow.get_rect(), border_radius=8)
        canvas.blit(title_glow, (self.title.posx - 20, self.title.posy - 10))
        self.title.draw(canvas)
        self.restart.draw(canvas)

        self.control_options()
        

class ScoreMenu(Menu):

    def __init__(self):
        Menu.__init__(self, 'STATISTICS')

        self.area = pygame.Surface((600, 300))
        self.area_rect = self.area.get_rect()
        self.area_rect.center = (SETTINGS.canvas_actual_width / 2, SETTINGS.canvas_target_height / 2)
        self.area.fill((200,200,200))

        self.middle_area = pygame.Surface((200, 300))
        self.middle_area.fill((180,180,180))

        self.back_button = Button((SETTINGS.canvas_actual_width/2, 500, 200, 60), "BACK")
        self.score_testing = copy.copy(SETTINGS.statistics)

        self.highlights = []
        for i in range(6):
            if i == 0:
                self.highlights.append(pygame.Surface((600, 35)).convert_alpha())
            else:
                self.highlights.append(pygame.Surface((600, 30)).convert_alpha())
            self.highlights[i].fill((0,0,0,20))

        #High scores
        self.best_scores = ['HIGHEST SCORES',
                        'ENEMIES  KILLED : %s' % SETTINGS.statistics['best enemies'],
                        'DAMAGE  DEALT : %s' % SETTINGS.statistics['best ddealt'],
                        'DAMAGE  TAKEN : %s' % SETTINGS.statistics['best dtaken'],
                        'SHOTS  FIRED : %s' % SETTINGS.statistics['best shots'],
                        'LEVEL  STREAK : %s' % SETTINGS.statistics['best levels']]

        self.texts = []
        self.pos = 10

        for i in range(len(self.best_scores)):
            if i == 0:
                self.texts.append(TEXT.Text(0, 0, self.best_scores[i], SETTINGS.DARKGRAY, "DUGAFONT.ttf", 18))
            else:
                self.texts.append(TEXT.Text(0, 0, self.best_scores[i], SETTINGS.WHITE, "DUGAFONT.ttf", 18))
            self.texts[i].update_pos(10, self.pos)
            self.pos += 30

        #Last play scores
        self.last_scores = ['LAST PLAY',
                        'ENEMIES  KILLED : %s' % SETTINGS.statistics['last enemies'],
                        'DAMAGE  DEALT : %s' % SETTINGS.statistics['last ddealt'],
                        'DAMAGE  TAKEN : %s' % SETTINGS.statistics['last dtaken'],
                        'SHOTS  FIRED : %s' % SETTINGS.statistics['last shots'],
                        'LEVEL  STREAK : %s' % SETTINGS.statistics['last levels']]
        self.last_texts = []
        self.pos = 10

        for i in range(len(self.last_scores)):
            if i == 0:
                self.last_texts.append(TEXT.Text(0, 0, self.last_scores[i], SETTINGS.DARKGRAY, "DUGAFONT.ttf", 18))
            else:
                if self.last_scores[i] == self.best_scores[i] and self.last_scores[i].find(' 0') == -1:
                    self.last_texts.append(TEXT.Text(0, 0, self.last_scores[i], (100,100,200), "DUGAFONT.ttf", 18))
                else:
                    self.last_texts.append(TEXT.Text(0, 0, self.last_scores[i], SETTINGS.WHITE, "DUGAFONT.ttf", 18))
            self.last_texts[i].update_pos(210, self.pos)
            self.pos += 30

        #all time statistics
        #format play time
            
        self.all_scores = ['ALL TIME',
                        'ENEMIES  KILLED : %s' % SETTINGS.statistics['all enemies'],
                        'DAMAGE  DEALT : %s' % SETTINGS.statistics['all ddealt'],
                        'DAMAGE  TAKEN : %s' % SETTINGS.statistics['all dtaken'],
                        'SHOTS  FIRED : %s' % SETTINGS.statistics['all shots'],
                        'LEVEL  STREAK : %s' % SETTINGS.statistics['all levels'],
                        'TIME PLAYED : {:02d}h {:02d}m'.format(*divmod(SETTINGS.statistics['playtime'], 60))]
        self.all_texts = []
        self.pos = 10

        for i in range(len(self.all_scores)):
            if i == 0:
                self.all_texts.append(TEXT.Text(0, 0, self.all_scores[i], SETTINGS.DARKGRAY, "DUGAFONT.ttf", 18))
            else:
                self.all_texts.append(TEXT.Text(0, 0, self.all_scores[i], SETTINGS.WHITE, "DUGAFONT.ttf", 18))
            self.all_texts[i].update_pos(410, self.pos)
            self.pos += 30

    def draw(self, canvas):
        if self.score_testing != SETTINGS.statistics:
            self.__init__()

        # Dark arena background with subtle grid
        canvas.fill((5, 5, 15))

        # Subtle grid pattern
        grid_surf = pygame.Surface((SETTINGS.canvas_actual_width, SETTINGS.canvas_target_height), pygame.SRCALPHA)
        for i in range(0, SETTINGS.canvas_target_height, 50):
            pygame.draw.line(grid_surf, (0, 80, 0, 20), (0, i), (SETTINGS.canvas_actual_width, i), 1)
        for i in range(0, SETTINGS.canvas_actual_width, 50):
            pygame.draw.line(grid_surf, (80, 40, 0, 15), (i, 0), (i, SETTINGS.canvas_target_height), 1)
        canvas.blit(grid_surf, (0, 0))

        # Draw title with glow
        title_glow = pygame.Surface((self.title.layout.get_width() + 40, self.title.layout.get_height() + 20), pygame.SRCALPHA)
        for i in range(3):
            pygame.draw.rect(title_glow, (0, 150, 0, 30 // (i + 1)), title_glow.get_rect(), border_radius=8)
        canvas.blit(title_glow, (self.title.posx - 20, self.title.posy - 10))
        self.title.draw(canvas)
        self.back_button.draw(canvas)

        self.area.fill((200,200,200))
        self.area.blit(self.middle_area, (200,0))

        pos = 0
        for i in self.highlights:
            self.area.blit(i, (0, pos))
            if pos == 0:
                pos = 5
            pos += 60

        for i in self.texts:
            i.draw(self.area)

        for i in self.last_texts:
            i.draw(self.area)

        for i in self.all_texts:
            i.draw(self.area)

        canvas.blit(self.area, self.area_rect)

            
class CreditsMenu(Menu):
    
    def __init__(self):
        Menu.__init__(self, 'CREDITS')
        self.back_button = Button((SETTINGS.canvas_actual_width/2, 500, 200, 60), "BACK")

        #Created by
        self.createdby = TEXT.Text(0,0, 'CREATED  BY', SETTINGS.LIGHTGRAY, "DUGAFONT.ttf", 24)
        self.createdby.update_pos((SETTINGS.canvas_actual_width/2)-(self.createdby.layout.get_width()/2)+8, 130)

        self.creators = TEXT.Text(0,0, 'LAMA, ATAY, VOLODYMYR, AHMED, YARO', SETTINGS.DARKGRAY, "DUGAFONT.ttf", 38)
        self.creators.update_pos((SETTINGS.canvas_actual_width/2)-(self.creators.layout.get_width()/2)+8, 160)

        self.and_you = TEXT.Text(0,0, 'THANKS  TO  YOU  FOR  PLAYING!' , SETTINGS.GREEN, "DUGAFONT.ttf", 22)
        self.and_you.update_pos((SETTINGS.canvas_actual_width/2)-(self.and_you.layout.get_width()/2)+8, 410)


    def draw(self, canvas, show):
        # LASER TAG - Add dark background with gradient effect
        canvas.fill((20, 20, 25))  # Very dark blue-gray background

        self.back_button.draw(canvas)
        self.title.draw(canvas)
        self.createdby.draw(canvas)
        self.creators.draw(canvas)

        if show or SETTINGS.statistics['playtime'] >= 120:
            self.and_you.draw(canvas)
        

class SupportSplash:

    def __init__(self):
        self.area = pygame.Surface((200, 300)).convert()
        self.rect = self.area.get_rect()
        self.rect.topleft = SETTINGS.canvas_actual_width - 220, SETTINGS.canvas_target_height - 280
        self.area.fill((200,200,200))

        self.title = TEXT.Text(0,0, 'THANKS   FOR   PLAYING', SETTINGS.DARKGRAY, "DUGAFONT.ttf", 19)
        self.title.update_pos((self.rect.width/2) - (self.title.layout.get_width()/2)+2, 5)

        self.pleas = ['You  have  been  playing  DUGA', 'for  over  two  hours  now.  I', 'really  hope  you  enjoy  it.',
                      'If  you  do,  please  consider', 'buying  it.  If  you  have  al-', 'ready  bought  it,  thank  you', 'very  much!  If  you  don\'t  think',
                      'it  is  worth  money,  please  let', 'me  know  what  to  improve.', 'Well,  I\'m  happy  to  have  you',
                      'playing,  so  I  added  you  to',  'the  credits!']
        self.texts = []

        self.pos = 30

        self.button = Button((SETTINGS.canvas_actual_width - 120, SETTINGS.canvas_target_height - 15, 192, 40), "LEAVE ME ALONE!")

        for i in range(len(self.pleas)):
            self.texts.append(TEXT.Text(0, 0, self.pleas[i], SETTINGS.WHITE, "DUGAFONT.ttf", 15))
            self.texts[i].update_pos((self.rect.width/2) - (self.texts[i].layout.get_width()/2)+2, self.pos)
            self.pos += 17
        

    def draw(self, canvas):
        self.title.draw(self.area)

        for text in self.texts:
            text.draw(self.area)        

        canvas.blit(self.area, self.rect)

        self.button.draw(canvas)



        
        

#---------------------------------------- IN-GAME MENUS ----------------------------------------------------------------------------

class GMainMenu(Menu):

    def __init__(self):
        Menu.__init__(self, 'PAUSED')
        self.resume_button = Button((SETTINGS.canvas_actual_width/2, 200, 200, 60), "RESUME")
        self.exit_button = Button((SETTINGS.canvas_actual_width/2, 500, 200, 60), "EXIT GAME")

        self.background = pygame.Surface((SETTINGS.canvas_actual_width, SETTINGS.canvas_target_height)).convert_alpha()
        self.background.fill((5, 5, 15, 200))  # Semi-transparent dark overlay

        # Team scores display
        self.green_score_text = TEXT.Text(0, 0, "", SETTINGS.team_colors['green'], "DUGAFONT.ttf", 36)
        self.orange_score_text = TEXT.Text(0, 0, "", SETTINGS.team_colors['orange'], "DUGAFONT.ttf", 36)

    def draw(self, canvas):
        canvas.blit(self.background, (0, 0))

        # Draw grid overlay effect
        grid_surf = pygame.Surface((SETTINGS.canvas_actual_width, SETTINGS.canvas_target_height), pygame.SRCALPHA)
        for i in range(0, SETTINGS.canvas_target_height, 60):
            pygame.draw.line(grid_surf, (0, 100, 0, 40), (0, i), (SETTINGS.canvas_actual_width, i), 1)
        for i in range(0, SETTINGS.canvas_actual_width, 60):
            pygame.draw.line(grid_surf, (100, 50, 0, 30), (i, 0), (i, SETTINGS.canvas_target_height), 1)
        canvas.blit(grid_surf, (0, 0))

        # Update and draw team scores
        green_score = SETTINGS.team_kills['green']
        orange_score = SETTINGS.team_kills['orange']
        self.green_score_text.update_string(f"GREEN: {green_score}")
        self.orange_score_text.update_string(f"ORANGE: {orange_score}")

        # Position scores at top
        self.green_score_text.update_pos(50, 300)
        self.orange_score_text.update_pos(SETTINGS.canvas_actual_width - self.orange_score_text.layout.get_width() - 50, 300)

        # Draw score with glow
        for text in [self.green_score_text, self.orange_score_text]:
            glow_surf = pygame.Surface((text.layout.get_width() + 20, text.layout.get_height() + 10), pygame.SRCALPHA)
            color = SETTINGS.team_colors['green'] if text == self.green_score_text else SETTINGS.team_colors['orange']
            for i in range(3):
                pygame.draw.rect(glow_surf, (*color, 60 // (i + 1)), glow_surf.get_rect(), border_radius=5)
            canvas.blit(glow_surf, (text.posx - 10, text.posy - 5))
            text.draw(canvas)

        self.resume_button.draw(canvas)
        self.exit_button.draw(canvas)

        # Draw title with glow
        title_glow = pygame.Surface((self.title.layout.get_width() + 40, self.title.layout.get_height() + 20), pygame.SRCALPHA)
        for i in range(3):
            pygame.draw.rect(title_glow, (0, 200, 0, 50 // (i + 1)), title_glow.get_rect(), border_radius=8)
        canvas.blit(title_glow, (self.title.posx - 20, self.title.posy - 10))
        self.title.draw(canvas)


class Button:

    def __init__(self, xywh, text):
        #ADD CLICK SOUND
        self.surface = pygame.Surface((xywh[2], xywh[3]), pygame.SRCALPHA)
        self.glow_surface = pygame.Surface((xywh[2] + 20, xywh[3] + 20), pygame.SRCALPHA)
        self.rect = self.surface.get_rect()
        self.rect.center = (xywh[0], xywh[1])
        self.glow_rect = self.glow_surface.get_rect()
        self.glow_rect.center = (xywh[0], xywh[1])
        self.clicked = False
        self.hover_scale = 1.0
        self.glow_alpha = 0
        self.pulse_timer = 0

        self.text = TEXT.Text(0,0, text, SETTINGS.WHITE, "DUGAFONT.ttf", 24)
        self.text.update_pos(xywh[0] - self.text.layout.get_width()/2, xywh[1] - (self.text.layout.get_height() / 2)+2)

        # LASER TAG - Enhanced colors
        self.base_color = (30, 30, 35)
        self.border_color = (0, 200, 0)  # Green
        self.hover_border_color = (255, 140, 0)  # Orange
        self.glow_color = (0, 255, 0, 80)  # Green glow
        self.hover_glow_color = (255, 140, 0, 120)  # Orange glow
        self.sound = pygame.mixer.Sound(os.path.join('sounds', 'other', 'button.ogg'))


    def draw(self, canvas):
        # Get scaled mouse position for accurate collision detection
        if hasattr(SETTINGS, 'game_canvas') and hasattr(SETTINGS.game_canvas, 'get_scaled_mouse_pos'):
            mouse_pos = SETTINGS.game_canvas.get_scaled_mouse_pos()
        else:
            mouse_pos = pygame.mouse.get_pos()
        is_hovering = self.rect.collidepoint(mouse_pos)

        # Update pulse animation
        self.pulse_timer += 0.05
        pulse = abs(pygame.math.Vector2(1, 0).rotate(self.pulse_timer * 50).x) * 0.15 + 0.85

        # Smooth hover transitions
        if is_hovering:
            self.hover_scale = min(1.05, self.hover_scale + 0.03)
            self.glow_alpha = min(255, self.glow_alpha + 15)
        else:
            self.hover_scale = max(1.0, self.hover_scale - 0.03)
            self.glow_alpha = max(0, self.glow_alpha - 15)

        # Draw glow effect when hovering
        if self.glow_alpha > 0:
            self.glow_surface.fill((0, 0, 0, 0))
            glow_color = self.hover_glow_color if is_hovering else self.glow_color
            # Multiple glow layers for better effect
            for i in range(3):
                alpha = int(self.glow_alpha * (1 - i * 0.3))
                glow_rect = pygame.Rect(10 - i * 3, 10 - i * 3,
                                       self.surface.get_width() + i * 6,
                                       self.surface.get_height() + i * 6)
                pygame.draw.rect(self.glow_surface, (*glow_color[:3], alpha), glow_rect, border_radius=8)
            canvas.blit(self.glow_surface, self.glow_rect)

        # Draw button with gradient
        self.surface.fill((0, 0, 0, 0))

        # Create gradient effect
        for y in range(self.surface.get_height()):
            gradient_factor = y / self.surface.get_height()
            color = tuple(int(self.base_color[i] * (1 + gradient_factor * 0.3)) for i in range(3))
            pygame.draw.line(self.surface, color, (4, y), (self.surface.get_width() - 4, y))

        # Draw border with current color
        border_color = self.hover_border_color if is_hovering else self.border_color
        border_width = 4 if is_hovering else 3

        # Animated border glow
        if is_hovering:
            for i in range(2):
                alpha = int(80 * pulse * (1 - i * 0.5))
                temp_surface = pygame.Surface((self.surface.get_width(), self.surface.get_height()), pygame.SRCALPHA)
                pygame.draw.rect(temp_surface, (*border_color, alpha),
                               temp_surface.get_rect(), border_width + i * 2, border_radius=6)
                self.surface.blit(temp_surface, (0, 0))

        pygame.draw.rect(self.surface, border_color,
                        (0, 0, self.surface.get_width(), self.surface.get_height()),
                        border_width, border_radius=6)

        canvas.blit(self.surface, self.rect)
        self.text.draw(canvas)

    def get_clicked(self):
        # Get scaled mouse position for accurate collision detection
        if hasattr(SETTINGS, 'game_canvas') and hasattr(SETTINGS.game_canvas, 'get_scaled_mouse_pos'):
            mouse_pos = SETTINGS.game_canvas.get_scaled_mouse_pos()
        else:
            mouse_pos = pygame.mouse.get_pos()

        if self.rect.collidepoint(mouse_pos):
            if pygame.mouse.get_pressed()[0]:
                self.clicked = True
            if not pygame.mouse.get_pressed()[0] and self.clicked:
                self.clicked = False
                SOUND.play_sound(self.sound, 0)
                return True
            else:
                return False
        else:
            return False
