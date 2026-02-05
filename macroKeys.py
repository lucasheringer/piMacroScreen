import os
import pygame
screen = pygame.display.set_mode((320, 240))
clock = pygame.time.Clock()

for x in range(20):
    screen.fill((0, 0, 0))
    pygame.display.flip()
    clock.tick(1)
    screen.fill((200, 200, 0))
    pygame.display.flip()
    clock.tick(1)