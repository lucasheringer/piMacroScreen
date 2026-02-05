import os
import pygame
import subprocess

# Set environment variables BEFORE pygame initializes
os.putenv('SDL_FBDEV', '/dev/fb0')
os.putenv('SDL_MOUSEDRV', 'TSLIB')
os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')

pygame.init()

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

pygame.display.set_caption('Macro Keys')


screen = pygame.display.set_mode((320, 240))
clock = pygame.time.Clock()
pygame.mouse.set_visible(False)

for x in range(20):
    screen.fill((255, 255, 255))
    pygame.display.flip()
    for event in pygame.event.get():
        if(event.type == pygame.MOUSEBUTTONDOWN):
            pos = pygame.mouse.get_pos()
            x, y = pos
            print(f"[TOUCHSCREEN] Button DOWN - Position: X={x}, Y={y}")
        elif(event.type == pygame.MOUSEBUTTONUP):
            pos = pygame.mouse.get_pos()
            x, y = pos
            print(f"[TOUCHSCREEN] Button UP - Position: X={x}, Y={y}")
        elif(event.type == pygame.MOUSEMOTION):
            pos = pygame.mouse.get_pos()
            x, y = pos
            print(f"[TOUCHSCREEN] Motion - Position: X={x}, Y={y}")

    clock.tick(1)