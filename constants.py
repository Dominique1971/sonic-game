# Screen
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE = "Kitsune Adventure"

# Physics
GRAVITY = 0.55
JUMP_FORCE = -14.0
MAX_FALL_SPEED = 18.0
PLAYER_SPEED = 5

# World
GROUND_Y = SCREEN_HEIGHT - 90  # y of ground surface

# Player
MAX_LIVES = 3
INVINCIBILITY_DURATION = 120  # frames

# Weapons cycle
WEAPON_NAMES = ['Normal', 'Spread', 'Bounce', 'Homing', 'Laser', 'Bomb']

# Ten levels – background palette + difficulty params
LEVELS = [
    dict(id=1,  name='Green Meadow',      sky=(135,206,235), sky2=(180,230,180), ground=(87,160,50),   ground2=(60,120,30),  theme='meadow',     speed=1.0, enemy_speed=1.0, enemies=5,  length=6000),
    dict(id=2,  name='Enchanted Forest',  sky=(60,120,60),   sky2=(90,150,70),   ground=(50,100,30),   ground2=(40,80,20),   theme='forest',     speed=1.1, enemy_speed=1.1, enemies=7,  length=7000),
    dict(id=3,  name='Desert Dunes',      sky=(255,180,80),  sky2=(255,220,140), ground=(210,180,100), ground2=(180,150,70), theme='desert',     speed=1.2, enemy_speed=1.2, enemies=8,  length=7500),
    dict(id=4,  name='Twilight Valley',   sky=(80,40,120),   sky2=(180,90,70),   ground=(80,55,90),    ground2=(60,35,70),   theme='twilight',   speed=1.3, enemy_speed=1.3, enemies=10, length=8000),
    dict(id=5,  name='Ice Kingdom',       sky=(170,210,255), sky2=(220,240,255), ground=(190,220,255), ground2=(160,190,230),theme='ice',        speed=1.4, enemy_speed=1.4, enemies=11, length=8500),
    dict(id=6,  name='Underwater Realm',  sky=(0,50,140),    sky2=(0,90,190),    ground=(0,70,110),    ground2=(0,50,90),    theme='underwater', speed=0.9, enemy_speed=1.3, enemies=12, length=9000),
    dict(id=7,  name='Volcanic Wasteland',sky=(170,55,20),   sky2=(240,110,40),  ground=(110,35,15),   ground2=(85,25,8),    theme='volcano',    speed=1.5, enemy_speed=1.5, enemies=14, length=9500),
    dict(id=8,  name='Sky Kingdom',       sky=(90,150,255),  sky2=(170,205,255), ground=(255,255,255), ground2=(210,215,255),theme='sky',        speed=1.6, enemy_speed=1.6, enemies=16, length=10000),
    dict(id=9,  name='Crystal Cavern',    sky=(25,0,55),     sky2=(55,15,95),    ground=(75,35,115),   ground2=(55,15,95),   theme='cave',       speed=1.7, enemy_speed=1.8, enemies=18, length=10500),
    dict(id=10, name='Final Fortress',    sky=(8,8,25),      sky2=(35,15,55),    ground=(55,35,75),    ground2=(35,15,55),   theme='castle',     speed=1.8, enemy_speed=2.0, enemies=22, length=12000),
]
