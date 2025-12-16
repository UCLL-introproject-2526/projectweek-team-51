import SETTINGS
import GUNS
import NPC
import ITEMS

from os import *
import pygame
import copy
import random

#When creating guns, remember to create an item for the gun as well.

def load_guns():
    # === LASER TAG - ONLY 2 WEAPONS ===

    #Laser Gun - 0 (UNLIMITED AMMO, 25 ROUND MAG)
    SETTINGS.gun_list.append(GUNS.Gun(
        {'spritesheet': path.join('graphics', 'weapon', 'weapon_spritesheet.png'),
         'item': path.join('graphics', 'items', 'akitem.png')},
        {'dmg': 2, 'spread': 30, 'hitchance': 95, 'firerate': 0.15,
         'range': 12, 'magsize': 25, 'rlspeed': 1.5, 'zoom': 4,
         'ammotype': None, 'guntype': 'primary', 'name': 'Laser Rifle'},
        {'shot': [pygame.mixer.Sound(path.join('sounds', 'weapons', 'pistol_shot1.ogg'))],
         'click': [pygame.mixer.Sound(path.join('sounds', 'weapons', 'universal_click.ogg'))],
         'magout': [pygame.mixer.Sound(path.join('sounds', 'other', 'none.ogg'))],
         'magin': [pygame.mixer.Sound(path.join('sounds', 'other', 'none.ogg'))]},
        (35,7)))

    #Knife - 1
    SETTINGS.gun_list.append(GUNS.Gun(
        {'spritesheet': path.join('graphics', 'weapon', 'knife_spritesheet.png'),
         'item': path.join('graphics', 'items', 'knifeitem.png')},
        {'dmg': 2, 'spread': 40, 'hitchance': 100, 'firerate': 0.3,
         'range': 1.5, 'magsize': 0, 'rlspeed': 0, 'zoom': 0,
         'ammotype': None, 'guntype': 'melee', 'name': 'Knife'},
        {'shot': [pygame.mixer.Sound(path.join('sounds', 'weapons', 'knife_swing1.ogg'))],
         'click': [pygame.mixer.Sound(path.join('sounds', 'other', 'none.ogg'))],
         'magout': [pygame.mixer.Sound(path.join('sounds', 'other', 'none.ogg'))],
         'magin': [pygame.mixer.Sound(path.join('sounds', 'other', 'none.ogg'))]},
        (37,10)))
def load_npc_types():
    SETTINGS.npc_types = [
        #soldier idle
        {
            'pos': [0,0],
            'face': 0,
            'spf': 0.12,
            'dmg': 2,
            'health': random.randint(12,15),
            'speed': 40,
            'mind': 'hostile',
            'state': 'idle',
            'atcktype': 'hitscan',
            'atckrate': 1,
            'id': 0,
            'filepath' : ('graphics', 'npc', 'green_team_player.png'),
            'name' : 'idle soldier',
            'soundpack' : 'soldier',
            },
        
        #Soldier Patrolling
        {
            'pos' : [0,0],
            'face' : 0,
            'spf': 0.12,
            'dmg': 2,
            'health': random.randint(12,15),
            'speed': 40,
            'mind': 'hostile',
            'state': 'patrolling',
            'atcktype': 'hitscan',
            'atckrate': 1,
            'id': 1,
            'filepath' : ('graphics', 'npc', 'green_team_player.png'),
            'name' : 'patroul soldier',
            'soundpack' : 'soldier',
            },
            
        #Ninja idle
        {
            'pos' : [0,0],
            'face' : 0,
            'spf': 0.10,
            'dmg': 3,
            'health': 11,
            'speed': 60,
            'mind': 'hostile',
            'state': 'idle',
            'atcktype': 'melee',
            'atckrate': 0.8,
            'id': 2,
            'filepath' : ('graphics', 'npc', 'green_team_player.png'),
            'name' : 'idle ninja',
            'soundpack' : 'ninja',
            },

        #Ninja patrolling
        {
            'pos' : [0,0],
            'face' : 0,
            'spf': 0.10,
            'dmg': 3,
            'health': 12,
            'speed': 60,
            'mind': 'hostile',
            'state': 'patrolling',
            'atcktype': 'melee',
            'atckrate': 0.8,
            'id': 3,
            'filepath' : ('graphics', 'npc', 'green_team_player.png'),
            'name' : 'patroul ninja',
            'soundpack' : 'ninja',
            },

        #Zombie patroling hostile (no dmg?)
        {
            'pos' : [0,0],
            'face' : 0,
            'spf': 0.12,
            'dmg': 3.1415, #lol this is used to randomize dmg.
            'health': 6,
            'speed': 70,
            'mind': 'hostile',
            'state': 'patrolling',
            'atcktype': 'melee',
            'atckrate': 0.6,
            'id': 4,
            'filepath' : ('graphics', 'npc', 'green_team_player.png'),
            'name' : 'hostile zombie',
            'soundpack' : 'zombie hostile',
            },

        #Zombie idle shy 
        {
            'pos' : [0,0],
            'face' : 0,
            'spf': 0.12,
            'dmg': 0,
            'health': 6,
            'speed': 50,
            'mind': 'shy',
            'state': 'idle',
            'atcktype': 'melee',
            'atckrate': 0.6,
            'id': 5,
            'filepath' : ('graphics', 'npc', 'green_team_player.png'),
            'name' : 'shy zombie',
            'soundpack' : 'zombie shy',
            },

        #random NPC
        {
            'pos' : [0,0],
            'face' : 0,
            'spf': 0,
            'dmg': 0,
            'health': 0,
            'speed': 0,
            'mind': None,
            'state': None,
            'atcktype': None,
            'atckrate': 0,
            'id': 6,
            'filepath' : ('graphics', 'npc', 'green_team_player.png'),
            'name' : 'random',
            'soundpack' : None,
            },

        #SPECIAL NPCS --------
        #Boss idle
        {
            'pos' : [0,0],
            'face' : 0,
            'spf': 0.10,
            'dmg': 5,
            'health': 40,
            'speed': 20,
            'mind': 'hostile',
            'state': 'idle',
            'atcktype': 'hitscan',
            'atckrate': 3,
            'id': 7,
            'filepath' : ('graphics', 'npc', 'green_team_player.png'),
            'name' : 'idle red',
            'soundpack' : 'red soldier',
            },
        
        #black soldier idle
        {
            'pos': [0,0],
            'face': 0,
            'spf': 0.12,
            'dmg': 2,
            'health': random.randint(15,20),
            'speed': 30,
            'mind': 'hostile',
            'state': 'idle',
            'atcktype': 'hitscan',
            'atckrate': 0.5,
            'id': 8,
            'filepath' : ('graphics', 'npc', 'green_team_player.png'),
            'name' : 'black idle',
            'soundpack' : 'soldier',
            },
        

        #black soldier patroul
        {
            'pos': [0,0],
            'face': 0,
            'spf': 0.12,
            'dmg': 2,
            'health': random.randint(15,20),
            'speed': 30,
            'mind': 'hostile',
            'state': 'patrolling',
            'atcktype': 'hitscan',
            'atckrate': 1.5,
            'id': 9,
            'filepath' : ('graphics', 'npc', 'green_team_player.png'),
            'name' : 'black patroul',
            'soundpack' : 'soldier',
            },

        #green ninja idle
        {
            'pos' : [0,0],
            'face' : 0,
            'spf': 0.12,
            'dmg': 3,
            'health': random.randint(8, 11),
            'speed': 100,
            'mind': 'hostile',
            'state': 'idle',
            'atcktype': 'melee',
            'atckrate': 0.5,
            'id': 10,
            'filepath' : ('graphics', 'npc', 'green_team_player.png'),
            'name' : 'idle green',
            'soundpack' : 'ninja',
            },

        #green ninja patrolling
        {
            'pos' : [0,0],
            'face' : 0,
            'spf': 0.12,
            'dmg': 2,
            'health': random.randint(8, 11),
            'speed': 100,
            'mind': 'hostile',
            'state': 'patrolling',
            'atcktype': 'melee',
            'atckrate': 0.5,
            'id': 11,
            'filepath' : ('graphics', 'npc', 'green_team_player.png'),
            'name' : 'idle green',
            'soundpack' : 'ninja',
            },

        #blue ninja idle
        {
            'pos' : [0,0],
            'face' : 0,
            'spf': 0.1,
            'dmg': 4,
            'health': 14,
            'speed': 35,
            'mind': 'hostile',
            'state': 'patrolling',
            'atcktype': 'melee',
            'atckrate': 1.1,
            'id': 12,
            'filepath' : ('graphics', 'npc', 'green_team_player.png'),
            'name' : 'idle blue',
            'soundpack' : 'ninja',
            },

        #Zombie yellow patrolling
        {
            'pos' : [0,0],
            'face' : 0,
            'spf': 0.18,
            'dmg': 5, 
            'health': 20,
            'speed': 20,
            'mind': 'hostile',
            'state': 'patrolling',
            'atcktype': 'melee',
            'atckrate': 1,
            'id': 13,
            'filepath' : ('graphics', 'npc', 'green_team_player.png'),
            'name' : 'patroul sick',
            'soundpack' : 'zombie hostile',
            },

        #zombie yellow idle
        {
            'pos' : [0,0],
            'face' : 0,
            'spf': 0.18,
            'dmg': 6,
            'health': 20,
            'speed': 20,
            'mind': 'hostile',
            'state': 'idle',
            'atcktype': 'melee',
            'atckrate': 0.8,
            'id': 14,
            'filepath' : ('graphics', 'npc', 'green_team_player.png'),
            'name' : 'idle sick',
            'soundpack' : 'zombie hostile',
            },

        #zombie yellow idle shy
        {
            'pos' : [0,0],
            'face' : 0,
            'spf': 0.18,
            'dmg': 10,
            'health': 35,
            'speed': 20,
            'mind': 'hostile',
            'state': 'idle',
            'atcktype': 'melee',
            'atckrate': 1.2,
            'id': 15,
            'filepath' : ('graphics', 'npc', 'green_team_player.png'),
            'name' : 'shy sick',
            'soundpack' : 'zombie hostile',
            },

        #blurry zombie hostile
        {
            'pos' : [0,0],
            'face' : 0,
            'spf': 0.18,
            'dmg': 8,
            'health': 5,
            'speed': 45,
            'mind': 'hostile',
            'state': 'patrolling',
            'atcktype': 'melee',
            'atckrate': 0.4,
            'id': 16,
            'filepath' : ('graphics', 'npc', 'green_team_player.png'),
            'name' : 'hostile blurry',
            'soundpack' : 'blurry zombie',
            },

        #blurry zombie hostile hitscan??
        {
            'pos' : [0,0],
            'face' : 0,
            'spf': 0.18,
            'dmg': 1,
            'health': 15,
            'speed': 45,
            'mind': 'hostile',
            'state': 'patrolling',
            'atcktype': 'hitscan',
            'atckrate': 0.4,
            'id': 17,
            'filepath' : ('graphics', 'npc', 'green_team_player.png'),
            'name' : 'hostile blurry',
            'soundpack' : 'blurry zombie',
            },
        ]

    load_npc_sounds()

def load_npc_sounds():
    SETTINGS.npc_soundpacks = [
        #Soldier soundpack
        {
            'name' : 'soldier',
            'attack' : pygame.mixer.Sound(path.join('sounds', 'npcs', 'soldier_shoot.ogg')),
            'spot' : pygame.mixer.Sound(path.join('sounds', 'npcs', 'soldier_spot.ogg')),
            'damage' : [pygame.mixer.Sound(path.join('sounds', 'npcs', 'soldier_hurt1.ogg')), pygame.mixer.Sound(path.join('sounds', 'npcs', 'soldier_hurt2.ogg')), pygame.mixer.Sound(path.join('sounds', 'npcs', 'soldier_hurt3.ogg')), pygame.mixer.Sound(path.join('sounds', 'npcs', 'soldier_hurt4.ogg'))],
            'die' : [pygame.mixer.Sound(path.join('sounds', 'npcs', 'soldier_die.ogg')),],
            },
        
        #boss soldier soundpack
        {
            'name' : 'red soldier',
            'attack' : pygame.mixer.Sound(path.join('sounds', 'npcs', 'soldier_shoot_heavy.ogg')),
            'spot' : pygame.mixer.Sound(path.join('sounds', 'npcs', 'soldier_spot.ogg')),
            'damage' : [pygame.mixer.Sound(path.join('sounds', 'npcs', 'soldier_hurt1.ogg')), pygame.mixer.Sound(path.join('sounds', 'npcs', 'soldier_hurt2.ogg')), pygame.mixer.Sound(path.join('sounds', 'npcs', 'soldier_hurt3.ogg')), pygame.mixer.Sound(path.join('sounds', 'npcs', 'soldier_hurt4.ogg'))],
            'die' : [pygame.mixer.Sound(path.join('sounds', 'npcs', 'soldier_die.ogg')),],
            },
        
        #Ninja Soundpack
        {
            'name' : 'ninja',
            'attack' : pygame.mixer.Sound(path.join('sounds', 'npcs', 'ninja_attack.ogg')),
            'spot' : pygame.mixer.Sound(path.join('sounds', 'other', 'none.ogg')),
            'damage' : [pygame.mixer.Sound(path.join('sounds', 'npcs', 'ninja_hurt1.ogg')), pygame.mixer.Sound(path.join('sounds', 'npcs', 'ninja_hurt2.ogg')), pygame.mixer.Sound(path.join('sounds', 'npcs', 'ninja_hurt3.ogg')), pygame.mixer.Sound(path.join('sounds', 'npcs', 'ninja_hurt4.ogg'))],
            'die' : [pygame.mixer.Sound(path.join('sounds', 'npcs', 'ninja_die1.ogg')), pygame.mixer.Sound(path.join('sounds', 'npcs', 'ninja_die2.ogg'))],
            },

        #Zombie shy soundpack
        {
            'name' : 'zombie shy',
            'attack' : pygame.mixer.Sound(path.join('sounds', 'other', 'none.ogg')),
            'spot' : pygame.mixer.Sound(path.join('sounds', 'npcs', 'zombie_spot2.ogg')),
            'damage' : [pygame.mixer.Sound(path.join('sounds', 'npcs', 'zombie_hurt1.ogg')), pygame.mixer.Sound(path.join('sounds', 'npcs', 'zombie_hurt2.ogg')), pygame.mixer.Sound(path.join('sounds', 'npcs', 'zombie_hurt3.ogg'))],
            'die' : [pygame.mixer.Sound(path.join('sounds', 'npcs', 'zombie_die1.ogg')), pygame.mixer.Sound(path.join('sounds', 'npcs', 'zombie_die2.ogg'))],
            },

        #Zombie hostile soundpack
        {
            'name' : 'zombie hostile',
            'attack' : pygame.mixer.Sound(path.join('sounds', 'npcs', 'zombie_attack.ogg')),
            'spot' : pygame.mixer.Sound(path.join('sounds', 'npcs', 'zombie_spot1.ogg')),
            'damage' : [pygame.mixer.Sound(path.join('sounds', 'npcs', 'zombie_hurt1.ogg')), pygame.mixer.Sound(path.join('sounds', 'npcs', 'zombie_hurt2.ogg')), pygame.mixer.Sound(path.join('sounds', 'npcs', 'zombie_hurt3.ogg'))],
            'die' : [pygame.mixer.Sound(path.join('sounds', 'npcs', 'zombie_die1.ogg')), pygame.mixer.Sound(path.join('sounds', 'npcs', 'zombie_die2.ogg'))],
            },

        #Zombie blurry soundpack
        {
            'name' : 'blurry zombie',
            'attack' : pygame.mixer.Sound(path.join('sounds', 'npcs', 'blurry_zombie_attack.ogg')),
            'spot' : pygame.mixer.Sound(path.join('sounds', 'npcs', 'blurry_zombie_spot.ogg')),
            'damage' : [pygame.mixer.Sound(path.join('sounds', 'npcs', 'blurry_zombie_hurt1.ogg')), pygame.mixer.Sound(path.join('sounds', 'npcs', 'blurry_zombie_hurt2.ogg')), pygame.mixer.Sound(path.join('sounds', 'npcs', 'blurry_zombie_hurt3.ogg'))],
            'die' : [pygame.mixer.Sound(path.join('sounds', 'npcs', 'blurry_zombie_die1.ogg')), pygame.mixer.Sound(path.join('sounds', 'npcs', 'blurry_zombie_die2.ogg'))],
            },
        ]


def spawn_npcs():
    seed = SETTINGS.current_level + SETTINGS.seed
    npc_count = 0
    total_npcs = len(SETTINGS.levels_list[SETTINGS.current_level].npcs)

    for npc in SETTINGS.levels_list[SETTINGS.current_level].npcs:
        if [x for x in SETTINGS.npc_types if x['id'] == npc[2]][0]['name'] == 'random':
            random.seed(seed)
            seed += 0.001
            stats = copy.deepcopy(random.choice([x for x in SETTINGS.npc_types if x['name'] != 'random']))
            print(stats['name'])
        else:
            stats = copy.deepcopy([x for x in SETTINGS.npc_types if x['id'] == npc[2]][0])

        try:
            sounds = ([x for x in SETTINGS.npc_soundpacks if x['name'] == stats['soundpack']][0])
        except:
            print("Error loading NPC! No soundpack with name ", stats['soundpack'])
        stats['pos'] = npc[0]
        stats['face'] = npc[1]

        # Team assignment for laser tag gameplay
        # Distribute NPCs evenly between teams (alternating pattern)
        # First half goes to one team, second half to the other
        if npc_count < total_npcs // 2:
            assigned_team = 'green'
        else:
            assigned_team = 'orange'

        # Create NPC with team assignment
        SETTINGS.npc_list.append(NPC.Npc(stats, sounds, path.join(*stats['filepath']), team=assigned_team))
        print(f"[LASER TAG] NPC #{npc_count+1}: {stats['name']} - Team: {assigned_team.upper()}")
        npc_count += 1


def load_item_types():
    # === LASER TAG - NO ITEMS ===
    # Dummy items only for inventory system compatibility (not spawned in game)
    SETTINGS.item_types = [
        {'filepath': ('graphics', 'items', 'bullet.png'), 'type': 'bullet', 'effect': 0, 'id': 2},
        {'filepath': ('graphics', 'items', 'shell.png'), 'type': 'shell', 'effect': 0, 'id': 3},
        {'filepath': ('graphics', 'items', 'ferromag.png'), 'type': 'ferromag', 'effect': 0, 'id': 10},
    ]

def spawn_items():
    # === LASER TAG - NO ITEMS ===
    # No items spawn in laser tag mode
    pass






