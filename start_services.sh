#!/bin/bash

##
# start_services.sh - Manages piMacroScreen services (webserver and macroKeys)
# Usage: ./start_services.sh {start|stop|restart|reload}
#
# This script is designed to be used by systemd service (pimacrkeys.service)
# It manages both webserver.py and macroKeys.py processes
##

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="/usr/bin/python3"
PID_DIR="/var/run/pimacrkeys"
WEBSERVER_PID_FILE="$PID_DIR/webserver.pid"
MACROKEYS_PID_FILE="$PID_DIR/macrokeys.pid"
LOG_DIR="/var/log/pimacrkeys"

# Create necessary directories
mkdir -p "$PID_DIR" "$LOG_DIR"

# Function to start processes
start_services() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting piMacroScreen services..." >> "$LOG_DIR/services.log"
    
    # Start webserver in background
    if [[ ! -f "$WEBSERVER_PID_FILE" ]] || ! kill -0 $(cat "$WEBSERVER_PID_FILE" 2>/dev/null) 2>/dev/null; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting webserver.py..." >> "$LOG_DIR/services.log"
        cd "$SCRIPT_DIR"
        nohup "$PYTHON_BIN" webserver.py >> "$LOG_DIR/webserver.log" 2>&1 &
        echo $! > "$WEBSERVER_PID_FILE"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Webserver started with PID $(cat $WEBSERVER_PID_FILE)" >> "$LOG_DIR/services.log"
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Webserver already running (PID: $(cat $WEBSERVER_PID_FILE))" >> "$LOG_DIR/services.log"
    fi
    
    # Start macroKeys in background
    if [[ ! -f "$MACROKEYS_PID_FILE" ]] || ! kill -0 $(cat "$MACROKEYS_PID_FILE" 2>/dev/null) 2>/dev/null; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting macroKeys.py..." >> "$LOG_DIR/services.log"
        cd "$SCRIPT_DIR"
        nohup "$PYTHON_BIN" macroKeys.py >> "$LOG_DIR/macrokeys.log" 2>&1 &
        echo $! > "$MACROKEYS_PID_FILE"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] macroKeys started with PID $(cat $MACROKEYS_PID_FILE)" >> "$LOG_DIR/services.log"
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] macroKeys already running (PID: $(cat $MACROKEYS_PID_FILE))" >> "$LOG_DIR/services.log"
    fi
    
    # Keep the script alive
    wait_for_processes
}

# Function to stop processes
stop_services() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Stopping piMacroScreen services..." >> "$LOG_DIR/services.log"
    
    # Stop webserver
    if [[ -f "$WEBSERVER_PID_FILE" ]]; then
        WEBSERVER_PID=$(cat "$WEBSERVER_PID_FILE")
        if kill -0 "$WEBSERVER_PID" 2>/dev/null; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Stopping webserver (PID: $WEBSERVER_PID)..." >> "$LOG_DIR/services.log"
            kill -TERM "$WEBSERVER_PID" 2>/dev/null || true
            # Wait up to 10 seconds for graceful shutdown
            for i in {1..10}; do
                if ! kill -0 "$WEBSERVER_PID" 2>/dev/null; then
                    break
                fi
                sleep 1
            done
            # Force kill if still running
            kill -9 "$WEBSERVER_PID" 2>/dev/null || true
        fi
        rm -f "$WEBSERVER_PID_FILE"
    fi
    
    # Stop macroKeys
    if [[ -f "$MACROKEYS_PID_FILE" ]]; then
        MACROKEYS_PID=$(cat "$MACROKEYS_PID_FILE")
        if kill -0 "$MACROKEYS_PID" 2>/dev/null; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Stopping macroKeys (PID: $MACROKEYS_PID)..." >> "$LOG_DIR/services.log"
            kill -TERM "$MACROKEYS_PID" 2>/dev/null || true
            # Wait up to 10 seconds for graceful shutdown
            for i in {1..10}; do
                if ! kill -0 "$MACROKEYS_PID" 2>/dev/null; then
                    break
                fi
                sleep 1
            done
            # Force kill if still running
            kill -9 "$MACROKEYS_PID" 2>/dev/null || true
        fi
        rm -f "$MACROKEYS_PID_FILE"
    fi
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Services stopped" >> "$LOG_DIR/services.log"
}

# Function to wait for processes and restart if they die
wait_for_processes() {
    while true; do
        sleep 5
        
        # Check if webserver is still running
        if [[ -f "$WEBSERVER_PID_FILE" ]]; then
            WEBSERVER_PID=$(cat "$WEBSERVER_PID_FILE")
            if ! kill -0 "$WEBSERVER_PID" 2>/dev/null; then
                echo "[$(date '+%Y-%m-%d %H:%M:%S')] Webserver has died, restarting..." >> "$LOG_DIR/services.log"
                rm -f "$WEBSERVER_PID_FILE"
                cd "$SCRIPT_DIR"
                nohup "$PYTHON_BIN" webserver.py >> "$LOG_DIR/webserver.log" 2>&1 &
                echo $! > "$WEBSERVER_PID_FILE"
            fi
        fi
        
        # Check if macroKeys is still running
        if [[ -f "$MACROKEYS_PID_FILE" ]]; then
            MACROKEYS_PID=$(cat "$MACROKEYS_PID_FILE")
            if ! kill -0 "$MACROKEYS_PID" 2>/dev/null; then
                echo "[$(date '+%Y-%m-%d %H:%M:%S')] macroKeys has died, restarting..." >> "$LOG_DIR/services.log"
                rm -f "$MACROKEYS_PID_FILE"
                cd "$SCRIPT_DIR"
                nohup "$PYTHON_BIN" macroKeys.py >> "$LOG_DIR/macrokeys.log" 2>&1 &
                echo $! > "$MACROKEYS_PID_FILE"
            fi
        fi
    done
}

# Function to reload (gracefully restart) processes
reload_services() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Reloading piMacroScreen services..." >> "$LOG_DIR/services.log"
    stop_services
    sleep 2
    start_services
}

# Signal handlers for systemd
trap 'stop_services; exit 0' SIGTERM SIGINT

# Main script logic
case "${1:-start}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        exit 0
        ;;
    restart)
        reload_services
        ;;
    reload)
        reload_services
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|reload}"
        exit 1
        ;;
esac
