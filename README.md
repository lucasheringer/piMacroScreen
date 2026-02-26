# piMacroScreen

Touchscreen-based macro pad + USB HID keyboard/media controller for Raspberry Pi, with a web UI to configure buttons, icons, and actions.

## What this project runs

- `macroKeys.py`: touchscreen UI + macro buttons
- `rotary_encoder.py`: volume/mute rotary encoder handling
- `webserver.py`: configuration web interface (port `5000`)
- `start_services.sh`: starts and supervises all services

## Requirements

### Hardware

- Raspberry Pi (USB gadget capable model)
- 320x240 touchscreen wired and configured
- Rotary encoder (optional)

### OS / system

- Raspberry Pi OS (or another Linux distro with `systemd`)
- Python 3.9+
- USB gadget support enabled (`libcomposite`, configfs)

### Python dependencies

Install from the included `requirements.txt` (added in this repo):

```bash
python3 -m pip install -r requirements.txt
```

## 1) Clone and install

```bash
git clone <your-repo-url> piMacroScreen
cd piMacroScreen

sudo apt update
sudo apt install -y python3 python3-pip python3-venv python3-dev \
	libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
	libfreetype6-dev libjpeg-dev libpng-dev libatlas-base-dev \
	libopenjp2-7 libtiff5

python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

## 2) Configure USB HID gadget

This project sends HID reports to `/dev/hidg0`, so the gadget device must exist first.

```bash
sudo bash report_descriptor.sh
```

If successful, `/dev/hidg0` should be present and writable.

## 3) Configure paths and permissions

### Service file path

The provided `pimacrkeys.service` uses an `APP_DIR` environment variable.
Update `APP_DIR` to your own project path before enabling the service.

Example:

```ini
Environment="APP_DIR=/home/pi/piMacroScreen"
```

### Start script executable bit

```bash
chmod +x start_services.sh start_webserver.sh report_descriptor.sh
```

## 4) Run manually (first test)

### Web UI only

```bash
python3 webserver.py
```

Open:
- `http://localhost:5000`
- `http://<PI_IP>:5000`

Default login:
- username: `admin`
- password: `admin`

Change credentials immediately from the web UI.

### Full stack (web + touchscreen + rotary)

```bash
./start_services.sh start
```

Stop:

```bash
./start_services.sh stop
```

## 5) Enable startup with systemd

Copy and enable service:

```bash
sudo cp pimacrkeys.service /etc/systemd/system/pimacrkeys.service
sudo systemctl daemon-reload
sudo systemctl enable pimacrkeys.service
sudo systemctl start pimacrkeys.service
```

Check status/logs:

```bash
sudo systemctl status pimacrkeys.service
journalctl -u pimacrkeys.service -f
```

## Configuration

- Main config file: `config.json`
- Uploaded backgrounds: `uploads/`
- Auth config (created automatically): `auth.json`

Use the web UI to edit button actions, icons, colors, and background.

## Troubleshooting

- `ModuleNotFoundError`: ensure virtual env is active and reinstall `requirements.txt`
- Web UI not reachable: verify port `5000` and firewall/network
- No HID output: confirm `/dev/hidg0` exists and rerun `report_descriptor.sh`
- Service restarts/fails: check `journalctl -u pimacrkeys.service`
- Touch input missing: verify `/dev/input/touchscreen` exists and permissions are correct

## Notes

- `start_webserver.sh` can auto-install missing Python dependencies via `requirements.txt`.
- `WEB_SERVER_GUIDE.md` includes UI/API usage details.