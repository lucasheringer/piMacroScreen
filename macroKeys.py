import os
import pygame

# Define basic colors
SHADOW = (192, 192, 192)
WHITE = (255, 255, 255)
LIGHTGREEN = (0, 255, 0 )
GREEN = (0, 200, 0 )
BLUE = (0, 0, 128)
LIGHTBLUE = (0, 0, 255)
RED = (200, 0, 0 )
LIGHTRED = (255, 100, 100)
PURPLE = (102, 0, 102)
LIGHTPURPLE = (153, 0, 153)
BLACK = (0, 0, 0)

os.putenv('SDL_FBDEV', '/dev/fb0')
# os.putenv('SDL_MOUSEDRV', 'TSLIB')
os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')
pygame.display.set_caption('Macro Keys')
pygame.mouse.set_visible(False)

screen = pygame.display.set_mode((320, 240))
clock = pygame.time.Clock()

for x in range(20):
    screen.fill((0, 0, 0))
    pygame.display.flip()
    clock.tick(1)
    screen.fill((200, 200, 0))
    pygame.display.flip()
    clock.tick(1)