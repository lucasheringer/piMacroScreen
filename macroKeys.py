#!/usr/bin/python3

##
# Prerequisites:
# A Touchscreen properly installed on your system:
# - a device to output to it, e.g. /dev/fb1
# - a device to get input from it, e.g. /dev/input/touchscreen
##

import pygame, time, evdev, select, math, subprocess, random, cairosvg, glob, os, shlex
import RPi.GPIO as GPIO
import json
from usbHidKeyboard import send, KEYS_ALLOWED, DEFAULT_HID
from io import BytesIO

# We start by launching the fbtest utility to make sure the framebuffer device is properly initialized and ready to be written into.
subprocess.call("fbtest", shell=True)
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
    # time.sleep(0.01)

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
t_cfg = CONFIG.get('touch_calibration', {})
tftOrig = tuple(t_cfg.get('orig', [150, 3750]))
tftEnd = tuple(t_cfg.get('end', [3750, 180]))
TOUCH_SWAP_XY = bool(t_cfg.get('swap_xy', False))
TOUCH_INVERT_X = bool(t_cfg.get('invert_x', False))
TOUCH_INVERT_Y = bool(t_cfg.get('invert_y', False))
TOUCH_OFFSET_X = int(t_cfg.get('offset_x', 0))
TOUCH_OFFSET_Y = int(t_cfg.get('offset_y', 0))
TOUCH_CLAMP = bool(t_cfg.get('clamp', True))
TOUCH_DEBUG_OVERLAY = bool(t_cfg.get('debug_overlay', False))
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
    raw_x, raw_y = coords
    if TOUCH_SWAP_XY:
        raw_x, raw_y = raw_y, raw_x

    # TODO check divide by 0!
    if tftDelta [0] < 0:
        x = float(tftAbsDelta [0] - raw_x + tftEnd [0]) / float(tftAbsDelta [0]) * float(surfaceSize [0])
    else:    
        x = float(raw_x - tftOrig [0]) / float(tftAbsDelta [0]) * float(surfaceSize [0])
    if tftDelta [1] < 0:
        y = float(tftAbsDelta [1] - raw_y + tftEnd [1]) / float(tftAbsDelta [1]) * float(surfaceSize [1])
    else:        
        y = float(raw_y - tftOrig [1]) / float(tftAbsDelta [1]) * float(surfaceSize [1])

    if TOUCH_INVERT_X:
        x = float(surfaceSize[0] - 1) - x
    if TOUCH_INVERT_Y:
        y = float(surfaceSize[1] - 1) - y

    x += TOUCH_OFFSET_X
    y += TOUCH_OFFSET_Y

    if TOUCH_CLAMP:
        x = max(0, min(surfaceSize[0] - 1, x))
        y = max(0, min(surfaceSize[1] - 1, y))

    return (int(x), int(y))


def drawTouchDebugOverlay(raw_coords, pixel_coords):
    drawButtons()
    overlay_rect = pygame.Rect(4, 4, 230, 34)
    pygame.draw.rect(lcd, (0, 0, 0), overlay_rect)
    pygame.draw.rect(lcd, (255, 255, 255), overlay_rect, 1)
    label = f"raw:{raw_coords[0]:4d},{raw_coords[1]:4d} px:{pixel_coords[0]:3d},{pixel_coords[1]:3d}"
    txt = defaultFont.render(label, False, (255, 255, 0))
    lcd.blit(txt, (8, 8))
    refresh()

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
SCREENSAVER_CONFIG = CONFIG.get('screensaver', {})
SCREENSAVER_LINE_TRAIL = bool(SCREENSAVER_CONFIG.get('line_trail', False))
SCREENSAVER_TRAIL_ALPHA = int(SCREENSAVER_CONFIG.get('trail_alpha', 40))
if SCREENSAVER_TRAIL_ALPHA < 0:
    SCREENSAVER_TRAIL_ALPHA = 0
elif SCREENSAVER_TRAIL_ALPHA > 255:
    SCREENSAVER_TRAIL_ALPHA = 255

last_activity = time.time()
screensaver_active = False

# Simple screensaver: bouncing colorful line
def run_screensaver():
    global screensaver_active, last_activity
    screensaver_active = True
    x = surfaceSize[0] // 2.0
    y = surfaceSize[1] // 2.0
    vx = 3
    vy = 2
    angle = random.uniform(0, math.tau)
    angular_velocity = 0.05
    line_length = min(surfaceSize) * 0.45
    line_width = 3
    color_hue = 0
    fade_surface = None

    if SCREENSAVER_LINE_TRAIL:
        fade_surface = pygame.Surface(surfaceSize, pygame.SRCALPHA)
        fade_surface.fill((0, 0, 0, SCREENSAVER_TRAIL_ALPHA))

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

        # Update animation (bouncing center)
        x += vx
        y += vy
        half_len = line_length / 2.0
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        extent_x = abs(cos_a) * half_len
        extent_y = abs(sin_a) * half_len

        if x - extent_x < 0 or x + extent_x > surfaceSize[0]:
            vx = -vx
            x += vx
        if y - extent_y < 0 or y + extent_y > surfaceSize[1]:
            vy = -vy
            y += vy

        # Rotate line and pulse length a bit
        angle = (angle + angular_velocity) % math.tau
        pulse = 0.80 + 0.20 * math.sin(time.time() * 2.0)
        current_half_len = half_len * pulse
        dx = math.cos(angle) * current_half_len
        dy = math.sin(angle) * current_half_len

        x1 = int(x - dx)
        y1 = int(y - dy)
        x2 = int(x + dx)
        y2 = int(y + dy)

        color_hue = (color_hue + 3) % 360
        rgb = colorsys.hsv_to_rgb(color_hue / 360.0, 0.8, 0.9)
        color = tuple(int(c * 255) for c in rgb)

        if SCREENSAVER_LINE_TRAIL and fade_surface is not None:
            lcd.blit(fade_surface, (0, 0))
        else:
            lcd.fill((0, 0, 0))
        pygame.draw.line(lcd, color, (x1, y1), (x2, y2), line_width)
        pygame.draw.circle(lcd, (255, 255, 255), (int(x), int(y)), 2)
        refresh()

X = 0
Y = 0
last_overlay_refresh = 0

while True:
    r, w, xsel = select.select([touch], [], [], 0.01)
    if r:
        for event in touch.read():
            last_activity = time.time()
            if event.type == evdev.ecodes.EV_ABS:
                if event.code == 1:
                    X = event.value
                elif event.code == 0:
                    Y = event.value

                if TOUCH_DEBUG_OVERLAY and not screensaver_active:
                    now = time.time()
                    if now - last_overlay_refresh >= 0.04:
                        p = getPixelsFromCoordinates((X, Y))
                        drawTouchDebugOverlay((X, Y), p)
                        last_overlay_refresh = now
            elif event.type == evdev.ecodes.EV_KEY:
                if event.code == 330 and event.value == 1:  # Touch press
                    try:
                        p = getPixelsFromCoordinates((X, Y))
                    except Exception:
                        continue

                    if TOUCH_DEBUG_OVERLAY and not screensaver_active:
                        drawTouchDebugOverlay((X, Y), p)

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
                                    command_parts = shlex.split(action_value)
                                    if not command_parts:
                                        raise ValueError("Command is empty")
                                    subprocess.run(command_parts, check=False)
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
                            drawButtons()
                            refresh()
                            break

    # Start screensaver if idle
    if not screensaver_active and (time.time() - last_activity) > SCREENSAVER_DELAY:
        run_screensaver()

exit()