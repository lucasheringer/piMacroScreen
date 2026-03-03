#!/usr/bin/python3
"""
Web Server for Macro Keyboard Configuration
Allows changing background, button configuration, and actions through a web interface
"""

from flask import Flask, request, jsonify, send_from_directory, send_file, session
import json
import os
import subprocess
import glob
from functools import wraps
import secrets
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.environ.get('WEB_SECRET_KEY', secrets.token_hex(32))

CONFIG_FILE = 'config.json'
AUTH_FILE = 'auth.json'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
DEFAULT_USERNAME = 'admin'
DEFAULT_PASSWORD = 'admin'

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_auth():
    """Load authentication settings, bootstrapping defaults when missing."""
    if os.path.exists(AUTH_FILE):
        with open(AUTH_FILE, 'r') as f:
            return json.load(f)

    default_auth = {
        'username': DEFAULT_USERNAME,
        'password_hash': generate_password_hash(DEFAULT_PASSWORD)
    }
    save_auth(default_auth)
    return default_auth

def save_auth(auth_config):
    """Save authentication settings to JSON file."""
    with open(AUTH_FILE, 'w') as f:
        json.dump(auth_config, f, indent=2)

def login_required(func):
    """Require a valid authenticated session."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get('authenticated'):
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
        return func(*args, **kwargs)
    return wrapper

def load_config():
    """Load configuration from JSON file"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            if 'touchscreen' not in config:
                config['touchscreen'] = {
                    'raw_origin': [3750, 180],
                    'raw_end': [150, 3750],
                    'rotation': 0
                }
            return config
    return {
        'background': 'bg.png',
        'touchscreen': {
            'raw_origin': [3750, 180],
            'raw_end': [150, 3750],
            'rotation': 0
        },
        'buttons': []
    }

def save_config(config):
    """Save configuration to JSON file"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

@app.route('/')
def index():
    """Serve the main configuration page"""
    return send_from_directory('static', 'index.html')

@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    """Get current authentication status."""
    return jsonify({
        'authenticated': bool(session.get('authenticated')),
        'username': session.get('username') if session.get('authenticated') else None
    })

@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    """Log in a user and create an authenticated session."""
    try:
        payload = request.json or {}
        username = (payload.get('username') or '').strip()
        password = payload.get('password') or ''

        auth = load_auth()
        if username != auth.get('username') or not check_password_hash(auth.get('password_hash', ''), password):
            return jsonify({'success': False, 'message': 'Invalid username or password'}), 401

        session['authenticated'] = True
        session['username'] = username
        return jsonify({'success': True, 'message': 'Login successful'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/auth/logout', methods=['POST'])
def auth_logout():
    """Log out current user."""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out'})

@app.route('/api/auth/change_password', methods=['POST'])
@login_required
def change_password():
    """Change current user's password."""
    try:
        payload = request.json or {}
        current_password = payload.get('current_password') or ''
        new_password = payload.get('new_password') or ''

        if len(new_password) < 4:
            return jsonify({'success': False, 'message': 'New password must be at least 4 characters'}), 400

        auth = load_auth()
        if not check_password_hash(auth.get('password_hash', ''), current_password):
            return jsonify({'success': False, 'message': 'Current password is incorrect'}), 401

        auth['password_hash'] = generate_password_hash(new_password)
        save_auth(auth)
        return jsonify({'success': True, 'message': 'Password changed successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/auth/change_username', methods=['POST'])
@login_required
def change_username():
    """Change current user's username."""
    try:
        payload = request.json or {}
        current_password = payload.get('current_password') or ''
        new_username = (payload.get('new_username') or '').strip()

        if len(new_username) < 3:
            return jsonify({'success': False, 'message': 'New username must be at least 3 characters'}), 400

        auth = load_auth()
        if not check_password_hash(auth.get('password_hash', ''), current_password):
            return jsonify({'success': False, 'message': 'Current password is incorrect'}), 401

        auth['username'] = new_username
        save_auth(auth)
        session['username'] = new_username

        return jsonify({'success': True, 'message': 'Username changed successfully', 'username': new_username})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/config', methods=['GET'])
@login_required
def get_config():
    """Get current configuration"""
    config = load_config()
    return jsonify(config)

@app.route('/api/config', methods=['POST'])
@login_required
def update_config():
    """Update configuration"""
    try:
        config = request.json
        save_config(config)
        return jsonify({'success': True, 'message': 'Configuration updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/button/<int:button_id>', methods=['PUT'])
@login_required
def update_button(button_id):
    """Update a specific button configuration"""
    try:
        config = load_config()
        button_data = request.json
        
        # Find and update the button
        for btn in config['buttons']:
            if btn['id'] == button_id:
                btn.update(button_data)
                break
        else:
            # Button not found, add it
            config['buttons'].append(button_data)
        
        save_config(config)
        return jsonify({'success': True, 'message': 'Button updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/background', methods=['POST'])
@login_required
def upload_background():
    """Upload a new background image"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Update config with new background
        config = load_config()
        config['background'] = filepath
        save_config(config)
        
        return jsonify({'success': True, 'message': 'Background uploaded successfully', 'filename': filepath})
    
    return jsonify({'success': False, 'message': 'Invalid file type'}), 400

@app.route('/api/icons', methods=['GET'])
@login_required
def get_available_icons():
    """Get list of available system icons"""
    icon_paths = []
    search_paths = [
        '/usr/share/icons/Adwaita/symbolic/actions/*.svg',
        '/usr/share/icons/Adwaita/symbolic/status/*.svg',
        '/usr/share/icons/Adwaita/symbolic/devices/*.svg',
        '/usr/share/icons/Adwaita/symbolic/places/*.svg',
        '/usr/share/icons/Adwaita/symbolic/ui/*.svg'
    ]
    
    for pattern in search_paths:
        icons = glob.glob(pattern)
        icon_paths.extend(icons)
    
    # Extract just the icon names for display
    icon_list = []
    for path in sorted(icon_paths):
        icon_list.append({
            'path': path,
            'name': os.path.basename(path).replace('.svg', '').replace('-symbolic', '')
        })
    
    return jsonify(icon_list)

@app.route('/api/icon_file', methods=['GET'])
@login_required
def serve_icon_file():
    """Serve icon files for browser preview backgrounds"""
    icon_path = request.args.get('path', '')
    if not icon_path:
        return jsonify({'success': False, 'message': 'Missing icon path'}), 400

    real_icon_path = os.path.realpath(icon_path)
    allowed_roots = [
        os.path.realpath('/usr/share/icons'),
        os.path.realpath(os.path.join(os.getcwd(), 'uploads')),
        os.path.realpath(os.path.join(os.getcwd(), 'static')),
    ]

    if not any(os.path.commonpath([real_icon_path, root]) == root for root in allowed_roots):
        return jsonify({'success': False, 'message': 'Icon path not allowed'}), 403

    if not os.path.isfile(real_icon_path):
        return jsonify({'success': False, 'message': 'Icon file not found'}), 404

    return send_file(real_icon_path)

@app.route('/api/media_keys', methods=['GET'])
@login_required
def get_media_keys():
    """Get list of available media keys"""
    # Import from usbHidKeyboard to get available keys
    try:
        from usbHidKeyboard import KEYS_ALLOWED
        media_keys = [key for key in KEYS_ALLOWED.keys()]
        return jsonify(media_keys)
    except Exception as e:
        # Fallback list
        return jsonify([
            'PLAY', 'PAUSE', 'PAUSE_UNPAUSE', 'NEXT', 'PREVIOUS',
            'VOLUME_UP', 'VOLUME_DOWN', 'MUTE',
            'ESCAPE', 'ENTER', 'TAB', 'SPACE'
        ])

@app.route('/api/restart', methods=['POST'])
@login_required
def restart_macro_service():
    """Restart the macro keyboard service asynchronously"""
    try:
        # Restart in a detached process after a short delay so this HTTP response can complete.
        subprocess.Popen(
            ['bash', '-lc', 'sleep 1 && sudo systemctl restart pimacrkeys.service'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return jsonify({'success': True, 'message': 'Service restart requested'}), 202
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    """Serve uploaded files"""
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    load_auth()
    # Remember to change to your actual CIDR range or use 0.0.0.0 for all interfaces if you want to allow access from anywhere (not recommended for production without proper security measures).
    app.run(host='192.168.1.0', port=5000, debug=False)
