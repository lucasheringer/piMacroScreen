# Web Server Configuration Guide

## Overview

The web server allows you to configure your macro keyboard through a modern web interface. You can change the background image, configure button icons, colors, and assign different actions to each button.

## Installation

1. Install the required Python packages:
   ```bash
   pip3 install -r requirements.txt
   ```

## Starting the Web Server

1. Navigate to the project directory:
   ```bash
   cd /path/to/piMacroScreen
   ```

2. Run the web server:
   ```bash
   python3 webserver.py
   ```

3. The server will start on port 5000. Access it from:
   - Local machine: `http://localhost:5000`
   - Other devices on network: `http://YOUR_PI_IP:5000`

## Features

### 🖼️ Background Configuration

- Upload custom background images (PNG, JPG, JPEG, GIF)
- View current background
- Supports images up to 16MB

### 🔘 Button Configuration

Each button can be configured with:

1. **Icon Path**
   - Choose from system icons using the icon browser
   - Or enter a custom path to an SVG icon
   - Icon browser searches common icon directories

2. **Border Color**
   - RGB color for the button border
   - Use the color picker for easy selection

3. **Pressed Color**
   - RGB color when button is pressed
   - Visual feedback for button activation

4. **Action Type**
   - **Media Key**: Send standard media control keys
   - **HID Report**: Send custom HID keyboard/mouse reports
   - **Shell Command**: Execute system commands

5. **Action Value**
   - For Media Keys: Select from dropdown (PLAY, PAUSE, VOLUME_UP, etc.)
   - For HID Reports: Enter hex format with colons (e.g., `01:0D:00:10:00:00:00:00:00`)
   - For Shell Commands: Enter any bash command

## Using the Interface

### Editing a Button

1. Click on any button card in the grid
2. The edit modal will open
3. Modify the settings as needed
4. Click "Update Button" to save

### Browsing Icons

1. Click "Browse Icons" in the button editor
2. Search for icons by name
3. Click an icon to select it
4. The icon path will be automatically populated

### Saving Configuration

1. Click "Save Configuration" at the top
2. Changes are saved to `config.json`
3. Restart the macro keyboard service to apply changes

### Restarting the Service

1. Click "Restart Service" at the top
2. Confirm the restart
3. The macro keyboard will reload with new settings

## Configuration File

The configuration is stored in `config.json`:

```json
{
  "background": "bg.png",
  "buttons": [
    {
      "id": 1,
      "icon": "/path/to/icon.svg",
      "color": [100, 100, 100],
      "pressed_color": [255, 0, 0],
      "action_type": "media",
      "action_value": "PAUSE_UNPAUSE"
    }
  ]
}
```

## Action Types Explained

### Media Keys

Common media keys available:
- `PLAY` - Play media
- `PAUSE` - Pause media
- `PAUSE_UNPAUSE` - Toggle play/pause
- `NEXT` - Next track
- `PREVIOUS` - Previous track
- `VOLUME_UP` - Increase volume
- `VOLUME_DOWN` - Decrease volume
- `MUTE` - Toggle mute

### HID Reports

Raw HID reports for custom key combinations:
- Format: `01:0D:00:10:00:00:00:00:00`
- First byte: Report ID (usually `01`)
- Second byte: Modifier keys (Ctrl, Shift, Alt, etc.)
- Third byte: Reserved (usually `00`)
- Fourth-Ninth bytes: Key codes

Example HID codes:
- `01:0D:00:10:00:00:00:00:00` - Ctrl+Alt+M (mute in Teams/Zoom)
- `01:0A:00:10:00:00:00:00:00` - Ctrl+Shift+M

### Shell Commands

Execute any bash command:
- `echo 'Hello World'` - Print to console
- `pactl set-sink-mute @DEFAULT_SINK@ toggle` - Toggle audio mute
- `xdotool key super+l` - Lock screen (if xdotool is installed)

## Running on Startup

Before enabling startup services, set `APP_DIR` in `pimacrkeys.service` to your installation path.

Example:

```ini
Environment="APP_DIR=/home/pi/piMacroScreen"
```

To run the web server automatically on boot:

1. Create a systemd service file `/etc/systemd/system/macrokeys-web.service`:
   ```ini
   [Unit]
   Description=Macro Keyboard Web Server
   After=network.target

   [Service]
   ExecStart=/usr/bin/python3 /path/to/webserver.py
   WorkingDirectory=/path/to/piMacroScreen
   User=pi
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

2. Enable and start the service:
   ```bash
   sudo systemctl enable macrokeys-web.service
   sudo systemctl start macrokeys-web.service
   ```

## Troubleshooting

### Web server won't start
- Check if port 5000 is already in use
- Verify Flask is installed: `pip3 list | grep Flask`

### Changes not applying
- Make sure to click "Save Configuration"
- Restart the macro keyboard service
- Check `config.json` for syntax errors

### Icons not loading
- Verify icon paths are correct
- Check that SVG files exist at specified paths
- Try using absolute paths

### Buttons not responding
- Check that macroKeys.py is reading from config.json
- Verify the service is running: `sudo systemctl status pimacrkeys.service`
- Check logs for errors

## Security Notes

- The web server runs on all interfaces (0.0.0.0) by default
- Use firewall/router rules to limit access to your local network
- Authentication is enabled by default; change credentials after first login
- Disable debug mode for production or internet-exposed environments

## API Endpoints

For advanced users, the server provides REST API endpoints:

- `GET /api/config` - Get current configuration
- `POST /api/config` - Update entire configuration
- `PUT /api/button/<id>` - Update specific button
- `POST /api/background` - Upload background image
- `GET /api/icons` - Get available system icons
- `GET /api/media_keys` - Get available media keys
- `POST /api/restart` - Restart the macro keyboard service
