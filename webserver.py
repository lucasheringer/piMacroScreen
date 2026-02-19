#!/usr/bin/python3
"""
Web Server for Macro Keyboard Configuration
Allows changing background, button configuration, and actions through a web interface
"""

from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
import json
import os
import subprocess
import glob
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='static', template_folder='templates')

CONFIG_FILE = 'config.json'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_config():
    """Load configuration from JSON file"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {
        'background': 'bg.png',
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

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    config = load_config()
    return jsonify(config)

@app.route('/api/config', methods=['POST'])
def update_config():
    """Update configuration"""
    try:
        config = request.json
        save_config(config)
        return jsonify({'success': True, 'message': 'Configuration updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/button/<int:button_id>', methods=['PUT'])
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
def restart_macro_service():
    """Restart the macro keyboard service"""
    try:
        # Try to restart using systemctl
        result = subprocess.run(['sudo', 'systemctl', 'restart', 'pimacrkeys.service'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return jsonify({'success': True, 'message': 'Service restarted successfully'})
        else:
            return jsonify({'success': False, 'message': f'Error: {result.stderr}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    """Serve uploaded files"""
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    # Run on all interfaces so it's accessible from other devices on the network
    app.run(host='0.0.0.0', port=5000, debug=True)
