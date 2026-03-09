# SPDX-FileCopyrightText: 2018 Mikey Sklar for Adafruit Industries
#
# SPDX-License-Identifier: MIT
# Modified by Jonathan Seyfert, 2022-01-22
# to keep code from crashing when WiFi or IP is unavailable
from subprocess import Popen, PIPE
from pathlib import Path
from time import sleep, perf_counter
from datetime import datetime
import os
import board
import digitalio
import adafruit_character_lcd.character_lcd as characterlcd

# Modify this if you have a different sized character LCD
lcd_columns = 16
lcd_rows = 2

# 27=>12 22=>26 25=>19 24=>13 23=>6 18=>11
#    def __init__(self, pin_rs=12, pin_e=26, pins_db=[19, 13, 6, 11], GPIO = None):

# compatible with all versions of RPI as of Jan. 2019
# v1 - v3B+
lcd_rs = digitalio.DigitalInOut(board.D12)
lcd_en = digitalio.DigitalInOut(board.D26)
lcd_d4 = digitalio.DigitalInOut(board.D19)
lcd_d5 = digitalio.DigitalInOut(board.D13)
lcd_d6 = digitalio.DigitalInOut(board.D6)
lcd_d7 = digitalio.DigitalInOut(board.D5)


# Initialise the lcd class
lcd = characterlcd.Character_LCD_Mono(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6,
                                      lcd_d7, lcd_columns, lcd_rows)

# looking for an active Ethernet or WiFi device
def find_interface():
#    dev_name = 0 # sets dev_name so that function does not return Null and crash code
    find_device = "ip addr show"
    interface_parse = run_cmd(find_device)
    for line in interface_parse.splitlines():
        if "state UP" in line:
            dev_name = line.split(':')[1]
            return dev_name
    return 1 # avoids returning Null if "state UP" doesn't exist

# find an active IP on the first LIVE network device
def parse_ip():
    if interface == 1: # if true, no device is in "state UP", skip IP check
        return "not assigned " # display "IP not assigned"
    ip = "0"
    find_ip = "ip addr show %s" % interface
    ip_parse = run_cmd(find_ip)
    for line in ip_parse.splitlines():
        if "inet " in line:
            ip = line.split(' ')[5]
            ip = ip.split('/')[0]
            return ip # returns IP address, if found
    return "pending      " # display "IP pending" when "state UP", but no IPv4 address yet

# run unix shell command, return as ASCII
def run_cmd(cmd):
    p = Popen(cmd, shell=True, stdout=PIPE)
    output = p.communicate()[0]
    return output.decode('ascii')


def fit_line(text):
    # Ensure each LCD line always matches the configured width.
    return text[:lcd_columns].ljust(lcd_columns)


def get_cpu_temp_c():
    temp_file = Path('/sys/class/thermal/thermal_zone0/temp')
    if not temp_file.exists():
        return None
    try:
        raw = temp_file.read_text(encoding='ascii').strip()
        return float(raw) / 1000.0
    except (ValueError, OSError):
        return None


def get_load_avg():
    try:
        return os.getloadavg()[0]
    except OSError:
        return None


def is_web_running():
    return Popen("pgrep -f 'webserver.py'", shell=True, stdout=PIPE).wait() == 0


def is_macro_running():
    return Popen("pgrep -f 'macroKeys.py'", shell=True, stdout=PIPE).wait() == 0


def is_hid_ready():
    return Path('/dev/hidg0').exists()


def animate_scrolling_text(frame):
    """Scrolling marquee text animation."""
    message = "piMacroScreen - Built with vibe conding!"
    # Calculate position for smooth scrolling
    pos = frame % len(message)
    # Create a continuous loop by appending message to itself
    extended = message + message
    line1 = extended[pos:pos + lcd_columns]
    line2 = extended[pos + 3:pos + 3 + lcd_columns]  # Offset for visual effect
    return fit_line(line1), fit_line(line2)


def animate_loading_bar(frame):
    """Animated loading bar."""
    # Bar fills and empties
    total_width = lcd_columns - 2  # Account for [ and ]
    position = frame % (total_width * 2)
    
    if position < total_width:
        # Filling up
        filled = position
    else:
        # Draining
        filled = total_width * 2 - position
    
    bar = '[' + ('=' * filled) + (' ' * (total_width - filled)) + ']'
    percent = int((filled / total_width) * 100)
    
    line1 = fit_line("Loading...")
    line2 = fit_line(f"{bar}")
    return line1, line2


def animate_bouncing_ball(frame):
    """Bouncing ball animation."""
    # Ball bounces horizontally on line 2
    max_pos = lcd_columns - 1
    position = frame % (max_pos * 2)
    
    if position < max_pos:
        ball_pos = position
    else:
        ball_pos = max_pos * 2 - position
    
    line1 = fit_line("Bouncing Ball!")
    line2 = ' ' * ball_pos + 'O' + ' ' * (max_pos - ball_pos)
    return fit_line(line1), fit_line(line2)


# wipe LCD screen before we start
lcd.clear()


# before we start the main loop - detect active network device and ip address
# set timer to = perf_counter(), for later use in IP update check
interface = find_interface()
ip_address = parse_ip()
timer = perf_counter()

rotation_seconds = 30
ip_refresh_seconds = 15
status_refresh_seconds = 5

status_timer = perf_counter() - status_refresh_seconds
web_ok = False
macro_ok = False
hid_ok = False

# Animation frame counter (updates every loop iteration)
animation_frame = 0

while True:
    # check for new IP addresses, at a slower rate than updating the clock
    now = perf_counter()

    if now - timer >= ip_refresh_seconds:
        interface = find_interface()
        ip_address = parse_ip()
        timer = now

    if now - status_timer >= status_refresh_seconds:
        web_ok = is_web_running()
        macro_ok = is_macro_running()
        hid_ok = is_hid_ready()
        status_timer = now

    # 6 total pages: 3 info pages + 3 animation pages
    page_index = int(now / rotation_seconds) % 2

    if page_index == 0:
        # Page 1: Date/Time + IP
        lcd_line_1 = fit_line(datetime.now().strftime('%b %d %H:%M:%S'))
        lcd_line_2 = fit_line("IP " + ip_address)
    elif page_index == 1:
        # Page 2: CPU Temp + Load
        cpu_temp = get_cpu_temp_c()
        load = get_load_avg()
        cpu_text = "CPU --.-C" if cpu_temp is None else f"CPU {cpu_temp:4.1f}C"
        load_text = "Load -.--" if load is None else f"Load {load:.2f}"
        lcd_line_1 = fit_line(cpu_text)
        lcd_line_2 = fit_line(load_text)
    else :
        # Page 3: Service Health
        web_text = "OK" if web_ok else "NO"
        hid_text = "OK" if hid_ok else "NO"
        macro_text = "RUN" if macro_ok else "DOWN"
        lcd_line_1 = fit_line(f"WEB:{web_text} HID:{hid_text}")
        lcd_line_2 = fit_line(f"MACRO:{macro_text}")
    # elif page_index == 3:
    #     # Page 4: Scrolling marquee animation
    #     lcd_line_1, lcd_line_2 = animate_scrolling_text(animation_frame)
    # elif page_index == 4:
    #     # Page 5: Loading bar animation
    #     lcd_line_1, lcd_line_2 = animate_loading_bar(animation_frame)
    # else:
    #     # Page 6: Bouncing ball animation
    #     lcd_line_1, lcd_line_2 = animate_bouncing_ball(animation_frame)

    # combine both lines into one update to the display
    lcd.message = lcd_line_1 + "\n" + lcd_line_2

    animation_frame += 1
    sleep(1)