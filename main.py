import math
import sys
import os
import time
import pygame
import random
from enum import Enum

WINDOW_POSITION = (30, 30)
WINDOW_SIZE = (100, 140)
FPS = 60
PIPE_SPAWN_TIME = 2.0
PIPE_GAP = 18
PIPE_SPEED = 50
GRAVITY = 300
GAME_OVER_COOLDOWN = 1.0

pygame.init()
pygame.font.init()
pygame.display.set_caption("FlapPy Bird")

_clock = pygame.time.Clock()
_screen = pygame.display.set_mode(WINDOW_SIZE, pygame.SCALED | pygame.RESIZABLE)
_font = pygame.font.Font(f"{os.path.dirname(os.path.abspath(__file__))}/resources/fonts/ThaleahFat.ttf", 15)
_debug = False
_running = True
_game_over = True
_clicked = False
_pipe_timer = PIPE_SPAWN_TIME
_last_delta = time.perf_counter()
_game_over_cooldown = 0.0
_score = 0.0
_player = None
_ground_1 = None
_ground_2 = None

SPRITES = {
    "bird": {
        "path": "resources/sprites/bird.png",
        "surface": None
    },
    "pipe_top": {
        "path": "resources/sprites/pipe_top.png",
        "surface": None
    },
    "pipe_bottom": {
        "path": "resources/sprites/pipe_bottom.png",
        "surface": None
    },
    "ground": {
        "path": "resources/sprites/ground.png",
        "surface": None
    }
}

# Preload sprites
for sprite in SPRITES:
    if os.path.exists(SPRITES[sprite]["path"]):
        path = SPRITES[sprite]["path"]
        img = pygame.image.load(path).convert_alpha()
        img.set_colorkey((0, 0, 0))
        SPRITES[sprite]["surface"] = img
        print(f"Loaded sprite from '{path}'")
        
class LAYER(Enum):
    BACKGROUND = 0
    FOREGROUND = 1
    PLAYER = 2

# Entities sorted by layer
entities = {
    LAYER.BACKGROUND: [],
    LAYER.FOREGROUND: [],
    LAYER.PLAYER: []
}

class Vector2:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Entity:
    def __init__(self, **kwargs):
        self.position = Vector2(kwargs["x"] if "x" in kwargs else 0, kwargs["y"] if "y" in kwargs else 0)
        self.rect = pygame.Rect(self.position.x, self.position.y, 0, 0)
        self.sprite = self.set_sprite(kwargs["sprite"] if "sprite" in kwargs else None)
        self.layer = kwargs["layer"] if "layer" in kwargs else LAYER.FOREGROUND
        self.lifetime = kwargs["lifetime"] if "lifetime" in kwargs else 0

    def destroy(self):
        entities[self.layer].remove(self)

    def set_sprite(self, sprite: str | None):
        if sprite is None or sprite not in SPRITES:
            return None
        
        self.sprite = SPRITES[sprite]["surface"].copy()
        self.rect.w = self.sprite.get_width()
        self.rect.h = self.sprite.get_height()
        return self.sprite

    def set_position(self, x, y):
        self.position.x = x
        self.position.y = y
    
    def translate(self, x, y):
        self.position.x += x
        self.position.y += y
    
    def draw(self, delta):
        if self.sprite is not None:
            _screen.blit(self.sprite, (self.position.x, self.position.y))
            
        if _debug:
            pygame.draw.rect(_screen, (255, 0, 0), self.rect, 1)

    def update(self, delta):
        self.rect.x = self.position.x
        self.rect.y = self.position.y
        
        if self.lifetime > 0:
            self.lifetime -= delta
            
            if self.lifetime <= 0:
                self.destroy()


class Bird(Entity):
    def __init__(self, **kwargs):
        kwargs["sprite"] = "bird"
        kwargs["layer"] = LAYER.PLAYER
        super().__init__(**kwargs)
        self.angle = 0
        self.velocity = Vector2(0, 0)
    
    def draw(self, delta):
        self.rect.x = self.position.x
        self.rect.y = self.position.y
        
        if self.sprite is not None:
            angle = math.atan2(self.velocity.y, self.velocity.x) * 180 / math.pi * -1
            self.angle = lerp(self.angle, angle, delta * 2)
            rotated_sprite = pygame.transform.rotate(self.sprite, self.angle)
            new_rect = rotated_sprite.get_rect(center=self.sprite.get_rect(center=(self.position.x + self.sprite.get_width() / 2, self.position.y + self.sprite.get_height() / 2)).center)
            _screen.blit(rotated_sprite, new_rect)
        
        if _debug:
            pygame.draw.rect(_screen, (255, 0, 0), self.rect, 1)
        
    def update(self, delta):
        super().update(delta)
        global _game_over
        
        if _clicked and not _game_over:
            self.velocity.y = -100
        
        self.velocity.y += GRAVITY * delta
        self.translate(self.velocity.x * delta, self.velocity.y * delta)
        
        if self.position.y <= 0:
            _game_over = True


class Pipe(Entity):
    def __init__(self, **kwargs):
        kwargs["lifetime"] = 5.0
        super().__init__(**kwargs)
    
    def update(self, delta):
        super().update(delta)
        global _game_over
        self.position.x -= delta * PIPE_SPEED
        
        if _player is not None and not _game_over:
            if self.rect.colliderect(_player.rect):
                _game_over = True


class Ground(Entity):
    def __init__(self, **kwargs):
        kwargs["sprite"] = "ground"
        super().__init__(**kwargs)
    
    def update(self, delta):
        super().update(delta)
        global _game_over
        self.position.x -= delta * PIPE_SPEED
        
        if _player is not None and not _game_over:
            if self.rect.colliderect(_player.rect):
                _game_over = True

def lerp(a, b, t):
    return a + (b - a) * t

def add_entity(entity):
    entities[entity.layer].append(entity)
    return entity

def process_entities(delta):
    for layer in entities.values():
        for entity in layer:
            entity.update(delta)
            entity.draw(delta)

def handle_environment(delta):
    global _ground_1, _ground_2, _pipe_timer
    
    if _ground_1.position.x <= -_ground_1.sprite.get_width():  # type: ignore
        _ground_1.position.x = _ground_2.position.x + _ground_2.sprite.get_width()  # type: ignore
    
    if _ground_2.position.x <= -_ground_2.sprite.get_width():  # type: ignore
        _ground_2.position.x = _ground_1.position.x + _ground_1.sprite.get_width()  # type: ignore
    
    if not _game_over:
        _pipe_timer -= delta
        
        if _pipe_timer <= 0:
            _pipe_timer = PIPE_SPAWN_TIME
            y_pos = random.randint(30, WINDOW_SIZE[1] - 40)
            top_pipe = add_entity(Pipe(sprite="pipe_top"))
            top_pipe.set_position(WINDOW_SIZE[0], y_pos - top_pipe.sprite.get_height() - PIPE_GAP)
            bottom_pipe = add_entity(Pipe(sprite="pipe_bottom"))
            bottom_pipe.set_position(WINDOW_SIZE[0], y_pos + PIPE_GAP)

def handle_game(delta):
    global _score, _font, _game_over_font, _game_over_cooldown
    
    if not _game_over:
        _score += delta
    else:
        surface = _font.render("Click To Start", False, (255, 255, 255))
        _screen.blit(surface, (WINDOW_SIZE[0] / 2 - surface.get_width() / 2, WINDOW_SIZE[1] / 2 - surface.get_height() / 2))
        _game_over_cooldown -= delta
        
        if _clicked and _game_over_cooldown <= 0:
            create_world()
            reset()
            start()
    
    surface = _font.render(str(math.floor(_score)), False, (255, 255, 255))
    _screen.blit(surface, (WINDOW_SIZE[0] / 2 - surface.get_width() / 2, 2))

def create_world():
    global _ground_1, _ground_2, _player, entities
    
    if _player is not None:
        _player.destroy()
        
    entities[LAYER.FOREGROUND] = []
    _ground_1 = add_entity(Ground())
    _ground_1.set_position(0, WINDOW_SIZE[1] - _ground_1.sprite.get_height() / 4)
    _ground_2 = add_entity(Ground())
    _ground_2.set_position(_ground_1.sprite.get_width(), WINDOW_SIZE[1] - _ground_2.sprite.get_height() / 4)

def reset():
    global _score, _game_over, _pipe_timer, _game_over_cooldown
    _game_over_cooldown = GAME_OVER_COOLDOWN
    _pipe_timer = PIPE_SPAWN_TIME
    _score = 0

def start():
    global _game_over, _player
    _game_over = False
    _player = add_entity(Bird(x=20, y=WINDOW_SIZE[1] / 2))

create_world()

while _running:
    _clock.tick(FPS)
    _clicked = False
    events = pygame.event.get()

    for event in events:
        if event.type == pygame.QUIT:
            _running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            _clicked = True
            
    now = time.perf_counter()
    delta = now - _last_delta
    _last_delta = now
    _screen.fill((10, 10, 30))
    process_entities(delta)
    handle_environment(delta)
    handle_game(delta)
    pygame.display.flip()

pygame.quit()
sys.exit()
