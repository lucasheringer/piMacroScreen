# import os
# import pygame
# import subprocess

# # Set environment variables BEFORE pygame initializes
# os.putenv('SDL_FBDEV', '/dev/fb0')
# os.putenv('SDL_MOUSEDRV', 'TSLIB')
# os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')

# pygame.init()

# # Define basic colors
# SHADOW = (192, 192, 192)
# WHITE = (255, 255, 255)
# LIGHTGREEN = (0, 255, 0 )
# GREEN = (0, 200, 0 )
# BLUE = (0, 0, 128)
# LIGHTBLUE = (0, 0, 255)
# RED = (200, 0, 0 )
# LIGHTRED = (255, 100, 100)
# PURPLE = (102, 0, 102)
# LIGHTPURPLE = (153, 0, 153)
# BLACK = (0, 0, 0)

# pygame.display.set_caption('Macro Keys')


# screen = pygame.display.set_mode((320, 240))
# clock = pygame.time.Clock()
# pygame.mouse.set_visible(False)
# screen.fill((255, 255, 255))
# pygame.display.flip()
# while True:
#     for event in pygame.event.get():
#         if(event.type == pygame.MOUSEBUTTONDOWN):
#             pos = pygame.mouse.get_pos()
#             x, y = pos
#             print(f"[TOUCHSCREEN] Button DOWN - Position: X={x}, Y={y}")
#         elif(event.type == pygame.MOUSEBUTTONUP):
#             pos = pygame.mouse.get_pos()
#             x, y = pos
#             print(f"[TOUCHSCREEN] Button UP - Position: X={x}, Y={y}")
#         elif(event.type == pygame.MOUSEMOTION):
#             pos = pygame.mouse.get_pos()
#             x, y = pos
#             print(f"[TOUCHSCREEN] Motion - Position: X={x}, Y={y}")

#     clock.tick(1)

#!/usr/bin/python3

##
# Prerequisites:
# A Touchscreen properly installed on your system:
# - a device to output to it, e.g. /dev/fb1
# - a device to get input from it, e.g. /dev/input/touchscreen
##

import pygame, time, evdev, select, math, subprocess
from usbHidKeyboard import send, KEYS_ALLOWED, DEFAULT_HID
from io import BytesIO
import cairosvg
#subprocess.call("fbtest", shell=True)
time.sleep(2)

# Very important: the exact pixel size of the TFT screen must be known so we can build graphics at this exact format
surfaceSize = (320, 240)

# Note that we don't instantiate any display!
pygame.init()

# The pygame surface we are going to draw onto. 
# /!\ It must be the exact same size of the target display /!\
lcd = pygame.Surface(surfaceSize)

# This is the important bit
def refresh():
    # We open the TFT screen's framebuffer as a binary file. Note that we will write bytes into it, hence the "wb" operator
    f = open("/dev/fb0","wb")
    # According to the TFT screen specs, it supports only 16bits pixels depth
    # Pygame surfaces use 24bits pixels depth by default, but the surface itself provides a very handy method to convert it.
    # once converted, we write the full byte buffer of the pygame surface into the TFT screen framebuffer like we would in a plain file:
    f.write(lcd.get_buffer())
    # We can then close our access to the framebuffer
    f.close()
    time.sleep(0.1)

# Now we've got a function that can get the bytes from a pygame surface to the TFT framebuffer, 
# we can use the usual pygame primitives to draw on our surface before calling the refresh function.

# Here we just blink the screen background in a few colors with the "Hello World!" text
pygame.font.init()
pygame.mouse.set_visible(False)
defaultFont = pygame.font.SysFont(None,30)

# lcd.fill((255,0,0))
# lcd.blit(defaultFont.render("Hello World!", False, (0, 0, 0)),(0, 0))
# refresh()

# lcd.fill((0, 255, 0))
# lcd.blit(defaultFont.render("Hello World!", False, (0, 0, 0)),(0, 0))
# refresh()

# lcd.fill((0,0,255))
# lcd.blit(defaultFont.render("Hello World!", False, (0, 0, 0)),(0, 0))
# refresh()

lcd.fill((128, 128, 128))
lcd.blit(defaultFont.render("Hello World!", False, (0, 0, 0)),(0, 0))

refresh()

##
# Everything that follows is for handling the touchscreen touch events via evdev
##

# Used to map touch event from the screen hardware to the pygame surface pixels. 
# (Those values have been found empirically, but I'm working on a simple interactive calibration tool
tftOrig = (3750, 180)
tftEnd = (150, 3750)
tftDelta = (tftEnd [0] - tftOrig [0], tftEnd [1] - tftOrig [1])
tftAbsDelta = (abs(tftEnd [0] - tftOrig [0]), abs(tftEnd [1] - tftOrig [1]))

# We use evdev to read events from our touchscreen
# (The device must exist and be properly installed for this to work)
touch = evdev.InputDevice('/dev/input/touchscreen')

# We make sure the events from the touchscreen will be handled only by this program
# (so the mouse pointer won't move on X when we touch the TFT screen)
touch.grab()
# Prints some info on how evdev sees our input device
print(touch)
# Even more info for curious people
#print(touch.capabilities())

# Here we convert the evdev "hardware" touch coordinates into pygame surface pixel coordinates
def getPixelsFromCoordinates(coords):
    # TODO check divide by 0!
    if tftDelta [0] < 0:
        x = float(tftAbsDelta [0] - coords [0] + tftEnd [0]) / float(tftAbsDelta [0]) * float(surfaceSize [0])
    else:    
        x = float(coords [0] - tftOrig [0]) / float(tftAbsDelta [0]) * float(surfaceSize [0])
    if tftDelta [1] < 0:
        y = float(tftAbsDelta [1] - coords [1] + tftEnd [1]) / float(tftAbsDelta [1]) * float(surfaceSize [1])
    else:        
        y = float(coords [1] - tftOrig [1]) / float(tftAbsDelta [1]) * float(surfaceSize [1])
    return (int(x), int(y))

# Function to load SVG icon and convert to pygame surface
def load_svg_icon(svg_path, size=60):
    try:
        # Convert SVG to PNG in memory with transparent background
        png_data = BytesIO()
        cairosvg.svg2png(url=svg_path, write_to=png_data, output_width=size, output_height=size)
        png_data.seek(0)
        icon = pygame.image.load(png_data)
        return icon
    except Exception as e:
        print(f"Error loading SVG {svg_path}: {e}")
        return None

# Was useful to see what pieces I would need from the evdev events
def printEvent(event):
    print(evdev.categorize(event))
    print("Value: {0}".format(event.value))
    print("Type: {0}".format(event.type))
    print("Code: {0}".format(event.code))

# Define 6 buttons in a 2x3 grid (2 rows, 3 columns)
BUTTON_COLS = 3
BUTTON_ROWS = 2
BUTTON_WIDTH = surfaceSize[0] // BUTTON_COLS  # 106 pixels
BUTTON_HEIGHT = surfaceSize[1] // BUTTON_ROWS  # 120 pixels

# Load SVG icon for button 1
pause_icon = load_svg_icon('/usr/share/icons/Adwaita/symbolic/actions/media-playback-pause-symbolic.svg', size=50)

# Create button rectangles
buttons = []
button_id = 1
for row in range(BUTTON_ROWS):
    for col in range(BUTTON_COLS):
        x = col * BUTTON_WIDTH
        y = row * BUTTON_HEIGHT
        btn_data = {
            'id': button_id,
            'rect': pygame.Rect(x, y, BUTTON_WIDTH, BUTTON_HEIGHT),
            'color': (100, 100, 100),
            'pressed_color': (255, 0, 0),
            'icon': pause_icon if button_id == 1 else None
        }
        buttons.append(btn_data)
        button_id += 1

# Function to draw all buttons
def drawButtons():
    lcd.fill((128, 128, 128))  # Background
    for btn in buttons:
        pygame.draw.rect(lcd, btn['color'], btn['rect'], 3)  # Draw border
        # Draw icon or button number in center
        if btn['icon'] is not None:
            icon_rect = btn['icon'].get_rect(center=btn['rect'].center)
            lcd.blit(btn['icon'], icon_rect)
        else:
            text = defaultFont.render(str(btn['id']), False, (255, 255, 255))
            text_rect = text.get_rect(center=btn['rect'].center)
            lcd.blit(text, text_rect)

# Initial draw
drawButtons()
refresh()

# Main event loop
while True:
    # TODO get the right ecodes instead of int
    r,w,x = select.select([touch], [], [])
    for event in touch.read():
        if event.type == evdev.ecodes.EV_ABS:
            if event.code == 1:
                X = event.value
            elif event.code == 0:
                Y = event.value
        elif event.type == evdev.ecodes.EV_KEY:
            if event.code == 330 and event.value == 1:  # Touch press
                p = getPixelsFromCoordinates((X, Y))
                print("Touch detected at Pixels: {0}:{1}".format(p[0], p[1]))
                
                # Check which button was touched
                for btn in buttons:
                    if btn['rect'].collidepoint(p):
                        print("==> BUTTON {0} PRESSED! <==".format(btn['id']))
                        # Highlight the pressed button
                        if btn['id'] == 1:
                            send('PAUSE_UNPAUSE', '/dev/hidg0')
                        drawButtons()
                        pygame.draw.rect(lcd, btn['pressed_color'], btn['rect'], 3)
                        text = defaultFont.render(str(btn['id']), False, (255, 255, 255))
                        text_rect = text.get_rect(center=btn['rect'].center)
                        lcd.blit(text, text_rect)
                        refresh()
                        time.sleep(0.3)
                        drawButtons()
                        refresh()
                        break

exit()