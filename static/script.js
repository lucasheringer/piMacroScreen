// Global state
let config = null;
let currentButton = null;
let availableIcons = [];
let availableMediaKeys = [];
const THEME_MODE_STORAGE_KEY = 'themeMode';

const HID_PRESETS = [
    { label: 'Custom (manual HEX)', value: '' },
    { label: 'Alt + Tab', value: '01:04:00:2B:00:00:00:00:00' },
    { label: 'Alt + F4', value: '01:04:00:3D:00:00:00:00:00' },
    { label: 'Ctrl + C', value: '01:01:00:06:00:00:00:00:00' },
    { label: 'Ctrl + V', value: '01:01:00:19:00:00:00:00:00' },
    { label: 'Ctrl + X', value: '01:01:00:1B:00:00:00:00:00' },
    { label: 'Ctrl + Z', value: '01:01:00:1D:00:00:00:00:00' },
    { label: 'Ctrl + Y', value: '01:01:00:1C:00:00:00:00:00' },
    { label: 'Ctrl + A', value: '01:01:00:04:00:00:00:00:00' },
    { label: 'Ctrl + S', value: '01:01:00:16:00:00:00:00:00' },
    { label: 'Ctrl + P', value: '01:01:00:13:00:00:00:00:00' },
    { label: 'Ctrl + F', value: '01:01:00:09:00:00:00:00:00' },
    { label: 'Ctrl + N', value: '01:01:00:11:00:00:00:00:00' },
    { label: 'Ctrl + T', value: '01:01:00:17:00:00:00:00:00' },
    { label: 'Ctrl + W', value: '01:01:00:1A:00:00:00:00:00' },
    { label: 'Ctrl + Shift + Esc', value: '01:03:00:29:00:00:00:00:00' },
    { label: 'Win + R', value: '01:08:00:15:00:00:00:00:00' },
    { label: 'Win + D', value: '01:08:00:07:00:00:00:00:00' },
    { label: 'Win + L', value: '01:08:00:0F:00:00:00:00:00' },
    { label: 'Enter', value: '01:00:00:28:00:00:00:00:00' },
    { label: 'Escape', value: '01:00:00:29:00:00:00:00:00' },
    { label: 'Tab', value: '01:00:00:2B:00:00:00:00:00' },
    { label: 'Space', value: '01:00:00:2C:00:00:00:00:00' }
];

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    initializeThemeMode();
    await loadConfig();
    await loadMediaKeys();
    await loadIcons();
    setupEventListeners();
});

function initializeThemeMode() {
    const savedMode = localStorage.getItem(THEME_MODE_STORAGE_KEY) || 'auto';
    applyThemeMode(savedMode);
}

function applyThemeMode(mode) {
    const root = document.documentElement;
    const normalizedMode = mode === 'dark' || mode === 'light' ? mode : 'auto';

    if (normalizedMode === 'auto') {
        root.removeAttribute('data-theme');
    } else {
        root.setAttribute('data-theme', normalizedMode);
    }

    const themeSelect = document.getElementById('themeMode');
    if (themeSelect) {
        themeSelect.value = normalizedMode;
    }
}

// Load configuration from server
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        config = await response.json();
        updateUI();
    } catch (error) {
        showToast('Failed to load configuration', 'error');
        console.error('Error loading config:', error);
    }
}

// Update UI with current configuration
function updateUI() {
    // Update background display
    document.getElementById('currentBg').textContent = config.background;
    
    // Update buttons grid
    const buttonsGrid = document.getElementById('buttonsGrid');
    buttonsGrid.innerHTML = '';
    
    const sortedButtons = [...config.buttons].sort((a, b) => a.id - b.id);
    sortedButtons.forEach(button => {
        const buttonCard = createButtonCard(button);
        buttonsGrid.appendChild(buttonCard);
    });
}

function resolveIconUrl(iconPath) {
    if (!iconPath) return '';

    if (iconPath.startsWith('http://') || iconPath.startsWith('https://')) {
        return iconPath;
    }

    if (iconPath.startsWith('/uploads/') || iconPath.startsWith('/static/')) {
        return iconPath;
    }

    if (iconPath.startsWith('uploads/') || iconPath.startsWith('static/')) {
        return `/${iconPath}`;
    }

    return `/api/icon_file?path=${encodeURIComponent(iconPath)}`;
}

// Create a button card element
function createButtonCard(button) {
    const card = document.createElement('div');
    card.className = 'button-card';
    card.onclick = () => openEditModal(button);
    
    const colorRgb = `rgb(${button.color.join(', ')})`;
    const pressedColorRgb = `rgb(${button.pressed_color.join(', ')})`;
    const iconUrl = resolveIconUrl(button.icon);

    if (iconUrl) {
        card.style.setProperty('--button-icon-url', `url("${iconUrl}")`);
    }
    
    card.innerHTML = `
        <div class="button-card-header">
            <div class="button-card-title">Button ${button.id}</div>
        </div>
        <div class="button-card-content">
            <div class="button-info-row">
                <span class="button-info-label">Icon:</span>
                <span class="button-info-value">${getShortPath(button.icon)}</span>
            </div>
            <div class="button-info-row">
                <span class="button-info-label">Color:</span>
                <span class="button-info-value">
                    <span class="color-preview" style="background-color: ${colorRgb}"></span>
                </span>
            </div>
            <div class="button-info-row">
                <span class="button-info-label">Pressed:</span>
                <span class="button-info-value">
                    <span class="color-preview" style="background-color: ${pressedColorRgb}"></span>
                </span>
            </div>
            <div class="button-info-row">
                <span class="button-info-label">Action:</span>
                <span class="button-info-value">${button.action_type}</span>
            </div>
            <div class="button-info-row">
                <span class="button-info-label">Value:</span>
                <span class="button-info-value">${getShortValue(button.action_value)}</span>
            </div>
        </div>
    `;
    
    return card;
}

// Get shortened path for display
function getShortPath(path) {
    if (!path) return 'None';
    const parts = path.split('/');
    return parts[parts.length - 1];
}

// Get shortened value for display
function getShortValue(value) {
    if (!value) return 'None';
    if (value.length > 20) {
        return value.substring(0, 20) + '...';
    }
    return value;
}

// Open edit modal for a button
function openEditModal(button) {
    currentButton = button;
    const modal = document.getElementById('editModal');
    
    // Populate form with button data
    document.getElementById('modalButtonId').textContent = button.id;
    document.getElementById('buttonIcon').value = button.icon || '';
    document.getElementById('buttonColor').value = button.color.join(', ');
    document.getElementById('buttonPressedColor').value = button.pressed_color.join(', ');
    document.getElementById('actionType').value = button.action_type;
    
    // Set color pickers
    document.getElementById('buttonColorPicker').value = rgbToHex(button.color);
    document.getElementById('buttonPressedColorPicker').value = rgbToHex(button.pressed_color);
    
    // Set action value based on type
    updateActionFields(button.action_type);
    if (button.action_type === 'media') {
        document.getElementById('mediaKeySelect').value = button.action_value;
    } else if (button.action_type === 'hid') {
        document.getElementById('hidReport').value = button.action_value;
        syncHidPresetSelection(button.action_value);
    } else if (button.action_type === 'shell') {
        document.getElementById('shellCommand').value = button.action_value;
    }
    
    modal.classList.add('show');
}

// Close modal
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.classList.remove('show');
}

// Update action fields visibility based on type
function updateActionFields(actionType) {
    document.getElementById('mediaKeyGroup').classList.add('hidden');
    document.getElementById('hidReportGroup').classList.add('hidden');
    document.getElementById('shellCommandGroup').classList.add('hidden');
    
    if (actionType === 'media') {
        document.getElementById('mediaKeyGroup').classList.remove('hidden');
    } else if (actionType === 'hid') {
        document.getElementById('hidReportGroup').classList.remove('hidden');
        syncHidPresetSelection(document.getElementById('hidReport').value);
    } else if (actionType === 'shell') {
        document.getElementById('shellCommandGroup').classList.remove('hidden');
    }
}

function normalizeHidValue(value) {
    return (value || '').trim().toUpperCase();
}

function loadHidPresets() {
    const select = document.getElementById('hidPresetSelect');
    select.innerHTML = '';

    HID_PRESETS.forEach(preset => {
        const option = document.createElement('option');
        option.value = preset.value;
        option.textContent = preset.label;
        select.appendChild(option);
    });
}

function syncHidPresetSelection(hidValue) {
    const select = document.getElementById('hidPresetSelect');
    const normalizedValue = normalizeHidValue(hidValue);

    const matchingPreset = HID_PRESETS.find(preset => normalizeHidValue(preset.value) === normalizedValue);
    select.value = matchingPreset ? matchingPreset.value : '';
}

// Load available media keys
async function loadMediaKeys() {
    try {
        const response = await fetch('/api/media_keys');
        availableMediaKeys = await response.json();
        
        const select = document.getElementById('mediaKeySelect');
        select.innerHTML = '';
        availableMediaKeys.forEach(key => {
            const option = document.createElement('option');
            option.value = key;
            option.textContent = key;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading media keys:', error);
    }
}

// Load available icons
async function loadIcons() {
    try {
        const response = await fetch('/api/icons');
        availableIcons = await response.json();
    } catch (error) {
        console.error('Error loading icons:', error);
    }
}

// Open icon browser
function openIconBrowser() {
    const modal = document.getElementById('iconBrowserModal');
    const iconGrid = document.getElementById('iconGrid');
    
    iconGrid.innerHTML = '';
    availableIcons.forEach(icon => {
        const iconItem = document.createElement('div');
        iconItem.className = 'icon-item';
        iconItem.onclick = () => selectIcon(icon.path, iconItem);
        iconItem.innerHTML = `
            <div class="icon-item-name">${icon.name}</div>
        `;
        iconGrid.appendChild(iconItem);
    });
    
    modal.classList.add('show');
}

// Select an icon from the browser
function selectIcon(iconPath, element) {
    document.querySelectorAll('.icon-item').forEach(item => {
        item.classList.remove('selected');
    });
    element.classList.add('selected');
    document.getElementById('buttonIcon').value = iconPath;
    closeModal('iconBrowserModal');
}

// Filter icons based on search
function filterIcons(searchTerm) {
    const iconGrid = document.getElementById('iconGrid');
    const items = iconGrid.getElementsByClassName('icon-item');
    
    searchTerm = searchTerm.toLowerCase();
    
    Array.from(items).forEach(item => {
        const name = item.textContent.toLowerCase();
        if (name.includes(searchTerm)) {
            item.style.display = '';
        } else {
            item.style.display = 'none';
        }
    });
}

// Convert RGB array to hex color
function rgbToHex(rgb) {
    return '#' + rgb.map(x => {
        const hex = x.toString(16);
        return hex.length === 1 ? '0' + hex : hex;
    }).join('');
}

// Convert hex color to RGB array
function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? [
        parseInt(result[1], 16),
        parseInt(result[2], 16),
        parseInt(result[3], 16)
    ] : [0, 0, 0];
}

// Save button configuration
async function saveButtonConfig(event) {
    event.preventDefault();
    
    const icon = document.getElementById('buttonIcon').value;
    const color = document.getElementById('buttonColor').value.split(',').map(x => parseInt(x.trim()));
    const pressedColor = document.getElementById('buttonPressedColor').value.split(',').map(x => parseInt(x.trim()));
    const actionType = document.getElementById('actionType').value;
    
    let actionValue = '';
    if (actionType === 'media') {
        actionValue = document.getElementById('mediaKeySelect').value;
    } else if (actionType === 'hid') {
        actionValue = document.getElementById('hidReport').value;
    } else if (actionType === 'shell') {
        actionValue = document.getElementById('shellCommand').value;
    }
    
    const updatedButton = {
        id: currentButton.id,
        icon: icon,
        color: color,
        pressed_color: pressedColor,
        action_type: actionType,
        action_value: actionValue
    };
    
    try {
        const response = await fetch(`/api/button/${currentButton.id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updatedButton)
        });
        
        const result = await response.json();
        if (result.success) {
            showToast('Button updated successfully', 'success');
            await loadConfig();
            closeModal('editModal');
        } else {
            showToast('Failed to update button: ' + result.message, 'error');
        }
    } catch (error) {
        showToast('Error updating button', 'error');
        console.error('Error:', error);
    }
}

// Save entire configuration
async function saveConfiguration() {
    try {
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });
        
        const result = await response.json();
        if (result.success) {
            showToast('Configuration saved successfully', 'success');
        } else {
            showToast('Failed to save configuration: ' + result.message, 'error');
        }
    } catch (error) {
        showToast('Error saving configuration', 'error');
        console.error('Error:', error);
    }
}

// Upload background image
async function uploadBackground() {
    const fileInput = document.getElementById('bgFileInput');
    const file = fileInput.files[0];
    
    if (!file) {
        showToast('Please select a file first', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/background', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        if (result.success) {
            showToast('Background uploaded successfully', 'success');
            await loadConfig();
        } else {
            showToast('Failed to upload background: ' + result.message, 'error');
        }
    } catch (error) {
        showToast('Error uploading background', 'error');
        console.error('Error:', error);
    }
}

// Restart service
async function restartService() {
    if (!confirm('Are you sure you want to restart the macro keyboard service?')) {
        return;
    }

    const restartBtn = document.getElementById('restartBtn');
    const originalRestartLabel = restartBtn.textContent;
    restartBtn.disabled = true;
    restartBtn.textContent = '⏳ Restarting...';
    
    try {
        const response = await fetch('/api/restart', {
            method: 'POST'
        });

        let result = { success: response.ok, message: '' };
        try {
            result = await response.json();
        } catch (_) {
            // Service restart can briefly interrupt the web server and return no body.
        }

        if (response.ok && result.success !== false) {
            showToast('Service restart requested. Reconnecting...', 'success');

            const reconnected = await waitForServerReconnect();
            if (reconnected) {
                await loadConfig();
                showToast('Service restarted and reconnected', 'success');
            } else {
                showToast('Restart requested, but reconnect timed out', 'error');
            }
        } else {
            showToast('Failed to restart service: ' + (result.message || response.statusText), 'error');
        }
    } catch (error) {
        showToast('Web server restarting. Reconnecting...', 'success');

        const reconnected = await waitForServerReconnect();
        if (reconnected) {
            await loadConfig();
            showToast('Service restarted and reconnected', 'success');
        } else {
            showToast('Could not reconnect yet. Please try again shortly', 'error');
        }

        console.error('Error:', error);
    } finally {
        restartBtn.disabled = false;
        restartBtn.textContent = originalRestartLabel;
    }
}

async function waitForServerReconnect(maxAttempts = 15, delayMs = 1000) {
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
            const response = await fetch('/api/config', { cache: 'no-store' });
            if (response.ok) {
                return true;
            }
        } catch (_) {
            // Expected while the web service is restarting.
        }

        await new Promise(resolve => setTimeout(resolve, delayMs));
    }

    return false;
}

// Show toast notification
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Setup event listeners
function setupEventListeners() {
    // Theme mode change
    document.getElementById('themeMode').addEventListener('change', (e) => {
        const mode = e.target.value;
        localStorage.setItem(THEME_MODE_STORAGE_KEY, mode);
        applyThemeMode(mode);
    });

    // Save button
    document.getElementById('saveBtn').addEventListener('click', saveConfiguration);
    
    // Restart button
    document.getElementById('restartBtn').addEventListener('click', restartService);
    
    // Upload background button
    document.getElementById('uploadBgBtn').addEventListener('click', uploadBackground);
    
    // Button edit form
    document.getElementById('buttonEditForm').addEventListener('submit', saveButtonConfig);
    
    // Action type change
    document.getElementById('actionType').addEventListener('change', (e) => {
        updateActionFields(e.target.value);
    });

    // HID preset change
    document.getElementById('hidPresetSelect').addEventListener('change', (e) => {
        const selectedValue = e.target.value;
        if (selectedValue) {
            document.getElementById('hidReport').value = selectedValue;
        }
    });

    // HID manual input
    document.getElementById('hidReport').addEventListener('input', (e) => {
        syncHidPresetSelection(e.target.value);
    });
    
    // Color pickers
    document.getElementById('buttonColorPicker').addEventListener('input', (e) => {
        const rgb = hexToRgb(e.target.value);
        document.getElementById('buttonColor').value = rgb.join(', ');
    });
    
    document.getElementById('buttonPressedColorPicker').addEventListener('input', (e) => {
        const rgb = hexToRgb(e.target.value);
        document.getElementById('buttonPressedColor').value = rgb.join(', ');
    });
    
    // Browse icons button
    document.getElementById('browseIconBtn').addEventListener('click', openIconBrowser);
    
    // Icon search
    document.getElementById('iconSearchInput').addEventListener('input', (e) => {
        filterIcons(e.target.value);
    });
    
    // Modal close buttons
    document.querySelectorAll('.close, .close-modal').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const modal = e.target.closest('.modal');
            if (modal) {
                closeModal(modal.id);
            }
        });
    });
    
    // Close modal on outside click
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            closeModal(e.target.id);
        }
    });
}

loadHidPresets();
