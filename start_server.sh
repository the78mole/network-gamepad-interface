#!/bin/bash

# Start Network Gamepad Interface Server
# Run this on the host machine where the game is running

echo "Starting Network Gamepad Interface Server..."

# Check if running as root (required for uinput)
if [ "$EUID" -ne 0 ]; then
    echo "Warning: Server may need to run as root to create virtual input devices."
    echo "If you get permission errors, try running with: sudo $0"
fi

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Start the server
python -m ngi.server.main "$@"