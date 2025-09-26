#!/bin/bash

# Start Network Gamepad Interface Client  
# Run this on the Raspberry Pi with connected Logitech G920

echo "Starting Network Gamepad Interface Client..."

# Install dependencies if needed
if [ ! -f "uv.lock" ]; then
    echo "Installing dependencies with uv..."
    uv sync
fi

# Start the client using uv
uv run ngi-client "$@"