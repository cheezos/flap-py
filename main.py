import math
import sys
import os
import pygame
import time
import random
from enum import Enum

WINDOW_POSITION = (200, 100)
WINDOW_SIZE = (200, 200)
FPS = 60
PIPE_SPAWN_TIME = 2.0
PIPE_GAP = 20
PIPE_SPEED = 50
GRAVITY = 300

os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % WINDOW_POSITION
pygame.init()
pygame.font.init()
pygame.display.set_caption("Flappy")

_clock = pygame.time.Clock()
_screen = pygame.display.set_mode(WINDOW_SIZE, pygame.SCALED | pygame.RESIZABLE)
_running = True
_paused = False
_last_delta = time.perf_counter()
_pipe_timer = PIPE_SPAWN_TIME
_clicked = False

class LAYER(Enum):
    BACKGROUND = 0
    FOREGROUND = 1
    UI = 2
    SPECIAL = 3

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

# Entities sorted by layer
entities = {
    LAYER.BACKGROUND: [],
    LAYER.FOREGROUND: [],
    LAYER.UI: [],
    LAYER.SPECIAL: []
}

class Vector2:
    def __init__(self, x: int, y: int) -> None:
        self.x: int = x
        self.y: int = y

class Entity:
    def __init__(self, **kwargs) -> None:
        self.position = Vector2(kwargs["x"] if "x" in kwargs else 0, kwargs["y"] if "y" in kwargs else 0)
        self.rect = pygame.Rect(self.position.x, self.position.y, 0, 0)
        self.sprite = self.set_sprite(kwargs["sprite"] if "sprite" in kwargs else None)
        self.layer = kwargs["layer"] if "layer" in kwargs else LAYER.FOREGROUND

    def set_sprite(self, sprite: str | None) -> pygame.Surface | None:
        if sprite is None or sprite not in SPRITES:
            return None
        
        self.sprite = SPRITES[sprite]["surface"].copy()
        self.rect.w = self.sprite.get_width()
        self.rect.h = self.sprite.get_height()
        return self.sprite

    def set_position(self, x, y) -> None:
        self.position.x = x
        self.position.y = y
    
    def translate(self, x, y) -> None:
        self.position.x += x
        self.position.y += y
    
    def draw(self) -> None:
        self.rect.x = self.position.x
        self.rect.y = self.position.y
        
        if self.sprite is not None:
            _screen.blit(self.sprite, (math.floor(self.position.x), math.floor(self.position.y)))
            
        # Debug draw bounds

    def update(self, delta) -> None:
        ...

class Bird(Entity):
    def __init__(self, **kwargs) -> None:
        kwargs["sprite"] = "bird"
        kwargs["layer"] = LAYER.SPECIAL
        super().__init__(**kwargs)
        self.angle = 0
        self.velocity = Vector2(0, 0)
    
    def draw(self, delta) -> None:
        # super().draw()
        self.rect.x = self.position.x
        self.rect.y = self.position.y
        
        if self.sprite is not None:
            angle = math.atan2(self.velocity.y, self.velocity.x) * 180 / math.pi * -1
            self.angle = lerp(self.angle, angle, delta * 2)
            rotated_sprite = pygame.transform.rotate(self.sprite, self.angle)
            new_rect = rotated_sprite.get_rect(center = self.sprite.get_rect(center = (self.position.x + self.sprite.get_width() / 2, self.position.y + self.sprite.get_height() / 2)).center)
            _screen.blit(rotated_sprite, new_rect)
            
        pygame.draw.rect(_screen, (255, 0, 0), self.rect, 1)
        
    def update(self, delta) -> None:
        super().update(delta)
        
        if _clicked:
            self.velocity.y = -100
        
        self.velocity.y += GRAVITY * delta
        self.translate(self.velocity.x * delta, self.velocity.y * delta)
        

class Pipe(Entity):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.top_pipe: Entity = Entity(sprite="pipe_top")
        self.bottom_pipe: Entity = Entity(sprite="pipe_bottom")
        
    def draw(self, delta) -> None:
        super().draw()
        self.top_pipe.draw()
        self.bottom_pipe.draw()
        
    def update(self, delta) -> None:
        super().update(delta)
        self.position.x -= delta * PIPE_SPEED
        self.top_pipe.set_position(self.position.x, self.position.y - self.top_pipe.rect.h - PIPE_GAP)
        self.bottom_pipe.set_position(self.position.x, self.position.y + PIPE_GAP)

def lerp(a, b, t):
    return a + (b - a) * t

def add_entity(entity) -> None:
    entities[entity.layer].append(entity)

def process_entities(delta) -> None:
    for layer in entities.values():
        for entity in layer:
            entity.update(delta)
            entity.draw(delta)

# Create game world
add_entity(Bird(x=20, y=WINDOW_SIZE[1] / 2))

def game_loop(delta) -> None:
    if _paused:
        return
    
    global _pipe_timer
    _pipe_timer -= delta
    
    if _pipe_timer <= 0:
        _pipe_timer = PIPE_SPAWN_TIME
        add_entity(Pipe(x=WINDOW_SIZE[0], y=random.randint(30, WINDOW_SIZE[1] - 30)))

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
    game_loop(delta)
    pygame.display.flip()

pygame.quit()
sys.exit()
