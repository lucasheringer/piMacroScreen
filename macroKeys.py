import os
import pygame
import subprocess

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
os.putenv('SDL_MOUSEDRV', 'TSLIB')
os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')
pygame.display.set_caption('Macro Keys')

screen = pygame.display.set_mode((320, 240))
clock = pygame.time.Clock()
pygame.mouse.set_visible(False)

for x in range(20):
    screen.fill((0, 0, 0))
    pygame.display.flip()
    # clock.tick(1)
    # screen.fill((200, 200, 0))
    # pygame.display.flip()
    for event in pygame.event.get():
        loopCheck = True
        if(event.type == pygame.MOUSEBUTTONDOWN):
            pos = pygame.mouse.get_pos()
            x, y = pos
            if x >= 250 and x <= 290 and y >= 160 and y <= 210:
                while loopCheck == True:
                    #print(str(event.type)+str(pos))
                    pygame.draw.rect(screen,WHITE,(90, 60, 140, 40))
                    pygame.draw.rect(screen,SHADOW,(90, 100, 140, 40))
                    pygame.draw.rect(screen,BLACK,(90, 100, 140, 2))
                    pygame.draw.rect(screen,BLACK,(160, 100, 2, 40))
                    pygame.display.update()
                    clock.tick(5)
                    for event in pygame.event.get():
                        if(event.type == pygame.MOUSEBUTTONDOWN):
                            pos = pygame.mouse.get_pos()
                            x, y = pos
                            if x >= 100 and x <= 140 and y >= 100 and y <= 125:
                                pygame.quit()
                                subprocess.call("sudo shutdown -h now", shell=True)
                                #pygame.quit()
                                quit()
                                #print("Shutting down :( ")
                                loopCheck = False
                            elif x >= 180 and x <= 220 and y >= 100 and y <= 125:
                                #print("Returning to monitor :) ")
                                loopCheck = False
    clock.tick(1)