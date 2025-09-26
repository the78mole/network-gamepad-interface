#!/bin/bash

# Start Network Gamepad Interface Client  
# Run this on the Raspberry Pi with connected Logitech G920

echo "Starting Network Gamepad Interface Client..."

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Start the client
python -m ngi.client.main "$@"