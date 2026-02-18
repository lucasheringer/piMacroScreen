#!/usr/bin/python3

##
# Prerequisites:
# A Touchscreen properly installed on your system:
# - a device to output to it, e.g. /dev/fb1
# - a device to get input from it, e.g. /dev/input/touchscreen
##

import pygame, time, evdev, select, math, subprocess, random
import sys
import json
from usbHidKeyboard import send, KEYS_ALLOWED, DEFAULT_HID
from io import BytesIO
import cairosvg
import glob
import os
#subprocess.call("fbtest", shell=True)
time.sleep(2)
NULL_CHAR = chr(0)

# Load configuration from JSON file
def load_config(config_file='config.json'):
    """Load configuration from JSON file"""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        # Return default configuration
        return {
            'background': 'bg.png',
            'buttons': []
        }

# Load the configuration
CONFIG = load_config()

def detect_framebuffer_device(width=320, height=240):
    """
    Auto-detect the correct framebuffer device (/dev/fb0, /dev/fb1, etc.)
    by checking resolution or trying to open each device.
    """
    # First, try to find by checking /sys/class/graphics for matching resolution
    fb_devices = sorted(glob.glob('/sys/class/graphics/fb*'))
    
    for fb_path in fb_devices:
        try:
            mode_path = os.path.join(fb_path, 'modes')
            if os.path.exists(mode_path):
                with open(mode_path, 'r') as f:
                    modes = f.read()
                    if f"{width}x{height}" in modes:
                        fb_num = os.path.basename(fb_path)
                        device = f"/dev/{fb_num}"
                        print(f"Found framebuffer device: {device}")
                        return device
        except Exception as e:
            pass
    
    # Fallback: try to open each device
    for i in range(5):
        fb_device = f"/dev/fb{i}"
        try:
            with open(fb_device, 'rb+') as f:
                print(f"Detected framebuffer device: {fb_device}")
                return fb_device
        except Exception:
            pass
    
    # Default fallback
    print("Warning: Could not auto-detect framebuffer device, using /dev/fb0")
    return "/dev/fb0"

# Auto-detect framebuffer device
FB_DEVICE = detect_framebuffer_device(320, 240)

def write_report(report):
    with open('/dev/hidg0', 'rb+') as fd:
        fd.write(report.encode())

# Very important: the exact pixel size of the TFT screen must be known so we can build graphics at this exact format
surfaceSize = (320, 240)

# Hide TTY cursor on Raspberry Pi
subprocess.call("setterm -cursor off", shell=True)

# Note that we don't instantiate any display!
pygame.init()
#load image - from configuration
bg = pygame.image.load(CONFIG.get('background', 'bg.png'))

# The pygame surface we are going to draw onto. 
# /!\ It must be the exact same size of the target display /!\
lcd = pygame.Surface(surfaceSize)
lcd.blit(bg, (0, 0))

# This is the important bit
def refresh():
    # We open the TFT screen's framebuffer as a binary file. Note that we will write bytes into it, hence the "wb" operator
    f = open(FB_DEVICE,"wb")
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

# Create buttons from configuration
buttons = []
for button_config in CONFIG.get('buttons', []):
    button_id = button_config['id']
    row = (button_id - 1) // BUTTON_COLS
    col = (button_id - 1) % BUTTON_COLS
    x = col * BUTTON_WIDTH
    y = row * BUTTON_HEIGHT
    
    # Load icon if specified
    icon = None
    if 'icon' in button_config and button_config['icon']:
        icon = load_svg_icon(button_config['icon'], size=50)
    
    btn_data = {
        'id': button_id,
        'rect': pygame.Rect(x, y, BUTTON_WIDTH, BUTTON_HEIGHT),
        'color': tuple(button_config.get('color', [100, 100, 100])),
        'pressed_color': tuple(button_config.get('pressed_color', [255, 0, 0])),
        'icon': icon,
        'action_type': button_config.get('action_type', 'media'),
        'action_value': button_config.get('action_value', '')
    }
    buttons.append(btn_data)

# Function to draw all buttons
def drawButtons():
    lcd.blit(bg, (0, 0))
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

# Screensaver / inactivity configuration
SCREENSAVER_DELAY = 300  # seconds (5 minutes)
SCREENSAVER_FRAME_DELAY = 0.05  # seconds between animation frames

last_activity = time.time()
screensaver_active = False

# Simple screensaver: bouncing ball
def run_screensaver():
    global screensaver_active, last_activity
    screensaver_active = True
    x = surfaceSize[0] // 2
    y = surfaceSize[1] // 2
    vx = 3
    vy = 2
    radius = random.randint(8, 20)
    color_hue = 0

    import colorsys

    while True:
        # Poll for touch; exit screensaver on any touch press
        r, w, xsel = select.select([touch], [], [], SCREENSAVER_FRAME_DELAY)
        if r:
            for event in touch.read():
                last_activity = time.time()
                if event.type == evdev.ecodes.EV_KEY and event.code == 330 and event.value == 1:
                    screensaver_active = False
                    drawButtons()
                    refresh()
                    return

        # Update animation
        x += vx
        y += vy
        if x - radius < 0 or x + radius > surfaceSize[0]:
            vx = -vx
            x += vx
        if y - radius < 0 or y + radius > surfaceSize[1]:
            vy = -vy
            y += vy

        color_hue = (color_hue + 3) % 360
        rgb = colorsys.hsv_to_rgb(color_hue / 360.0, 0.8, 0.9)
        color = tuple(int(c * 255) for c in rgb)

        lcd.fill((0, 0, 0))
        pygame.draw.circle(lcd, color, (int(x), int(y)), radius)
        pygame.draw.circle(lcd, (255,255,255), (int(x), int(y)), 3)
        refresh()

# Non-blocking main loop with inactivity check
while True:
    # Small timeout so we can detect inactivity
    r, w, xsel = select.select([touch], [], [], 0.1)
    if r:
        for event in touch.read():
            last_activity = time.time()
            if event.type == evdev.ecodes.EV_ABS:
                if event.code == 1:
                    X = event.value
                elif event.code == 0:
                    Y = event.value
            elif event.type == evdev.ecodes.EV_KEY:
                if event.code == 330 and event.value == 1:  # Touch press
                    try:
                        p = getPixelsFromCoordinates((X, Y))
                    except Exception:
                        continue
                    print("Touch detected at Pixels: {0}:{1}".format(p[0], p[1]))

                    # Check which button was touched
                    for btn in buttons:
                        if btn['rect'].collidepoint(p):
                            print("==> BUTTON {0} PRESSED! <==".format(btn['id']))
                            
                            # Execute action based on configuration
                            action_type = btn.get('action_type', 'media')
                            action_value = btn.get('action_value', '')
                            
                            if action_type == 'media':
                                # Send media key command
                                send(action_value, '/dev/hidg0')
                            elif action_type == 'hid':
                                # Send raw HID report
                                # Convert hex string format "01:0D:00:10:..." to bytes
                                hex_values = action_value.split(':')
                                report = ''.join([chr(int(h, 16)) for h in hex_values])
                                write_report(report)
                                # Send null report to release
                                write_report(chr(1) + NULL_CHAR*8)
                            elif action_type == 'shell':
                                # Execute shell command
                                try:
                                    subprocess.call(action_value, shell=True)
                                except Exception as e:
                                    print(f"Error executing shell command: {e}")

                            drawButtons()
                            pygame.draw.rect(lcd, btn['pressed_color'], btn['rect'], 3)
                            if btn['icon'] is not None:
                                icon_rect = btn['icon'].get_rect(center=btn['rect'].center)
                                lcd.blit(btn['icon'], icon_rect)
                            else:
                                text = defaultFont.render(str(btn['id']), False, (255, 255, 255))
                                text_rect = text.get_rect(center=btn['rect'].center)
                                lcd.blit(text, text_rect)
                            refresh()
                            time.sleep(0.3)
                            drawButtons()
                            refresh()
                            break

    # Start screensaver if idle
    if not screensaver_active and (time.time() - last_activity) > SCREENSAVER_DELAY:
        run_screensaver()

exit()