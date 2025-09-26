# Network Gamepad Interface

This project provides a network interface that allows clients to share their connected gamepad, joystick, or steering wheel with a remote server. The server emulates the device virtually, enabling remote gaming with physical controllers.

## Features

- **Remote Gamepad Control**: Connect your gamepad/steering wheel to one machine and use it to control games on another
- **Logitech G920 Support**: Optimized for Logitech G920 steering wheel with pedals and gear shifter  
- **Force Feedback**: Bi-directional communication for force feedback effects
- **Real-time Communication**: Low-latency WebSocket communication for responsive gaming
- **Virtual Device Emulation**: Creates virtual input devices that games can recognize natively
- **Cross-platform**: Works on Linux systems (tested with Raspberry Pi and desktop Linux)

## Use Case

The primary use case is connecting a Logitech G920 steering wheel to a Raspberry Pi (client) and using it to control racing games like SuperTuxKart running on a more powerful host machine (server).

```
[Raspberry Pi] <-- USB --> [Logitech G920] 
     |
     | (Network)
     v
[Gaming PC] <-- Virtual Device --> [SuperTuxKart/Other Games]
```

## Quick Start

### Prerequisites

- Python 3.8 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- Linux system with uinput support (for server)
- Logitech G920 or compatible gamepad (for client)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/the78mole/network-gamepad-interface.git
cd network-gamepad-interface
```

2. Install uv if you haven't already:
```bash
# Install uv using the official installer
curl -LsSf https://astral.sh/uv/install.sh | sh
# Or using pip
pip install uv
```

3. Install dependencies using uv:
```bash
uv sync
```

4. For development installation:
```bash
uv sync --dev
```

### Server Setup (Gaming PC)

The server creates a virtual gamepad device and receives input from clients.

1. **Install uinput kernel module** (if not already loaded):
```bash
sudo modprobe uinput
```

2. **Set up permissions** (choose one option):
   - Option A: Run as root (simple but less secure)
   - Option B: Add user to input group and set uinput permissions:
```bash
sudo usermod -a -G input $USER
sudo udevadm control --reload-rules
sudo udevadm trigger
```

3. **Start the server**:
```bash
./start_server.sh
# Or manually:
uv run ngi-server --host 0.0.0.0 --port 9999
```

The server will create a virtual gamepad device that games can detect and use.

### Client Setup (Raspberry Pi)

The client reads from your physical gamepad and sends the data to the server.

1. **Connect your Logitech G920** (or compatible gamepad) via USB

2. **Start the client**:
```bash
./start_client.sh --host YOUR_SERVER_IP
# Or manually:
uv run ngi-client --host YOUR_SERVER_IP --port 9999
```

### Testing with SuperTuxKart

1. Start the server on your gaming PC
2. Start SuperTuxKart and go to Options > Controls
3. The virtual gamepad should appear as "Network Gamepad Interface"
4. Configure the controls in SuperTuxKart to use the virtual device
5. Start the client on your Raspberry Pi
6. Your G920 steering wheel should now control SuperTuxKart!

## Configuration

### Command Line Options

**Server:**
```bash
uv run ngi-server [options]
  --host HOST          Server bind address (default: 0.0.0.0)
  --port PORT          Server port (default: 9999) 
  --log-level LEVEL    Logging level (DEBUG, INFO, WARNING, ERROR)
```

**Client:**
```bash
uv run ngi-client [options]
  --host HOST          Server host address (default: localhost)
  --port PORT          Server port (default: 9999)
  --log-level LEVEL    Logging level (DEBUG, INFO, WARNING, ERROR) 
  --rate HZ            Update rate in Hz (default: 60)
```

### Configuration File

Edit `config.ini` to customize settings:

```ini
[server]
host = 0.0.0.0
port = 9999
device_name = Network Gamepad Interface

[client]
server_host = localhost
server_port = 9999
update_rate = 60
```

## Architecture

### Components

- **Client (ngi.client)**:
  - `gamepad_input.py`: Reads input from physical gamepad using pygame
  - `network_client.py`: WebSocket client for communication with server
  - `main.py`: Main client application

- **Server (ngi.server)**:
  - `virtual_gamepad.py`: Creates virtual input device using uinput
  - `network_server.py`: WebSocket server for receiving gamepad data
  - `main.py`: Main server application

- **Common (ngi.common)**:
  - `protocol.py`: Shared protocol definitions and data structures

### Protocol

The system uses WebSocket communication with JSON messages:

- **GAMEPAD_STATE**: Gamepad input data (steering, pedals, buttons, gear)
- **FORCE_FEEDBACK**: Force feedback effects to send to client
- **CONNECT/DISCONNECT**: Connection management
- **HEARTBEAT**: Keep-alive messages

### Data Flow

1. Client reads gamepad input using pygame
2. Input data is packaged into GamepadState message
3. Message sent to server via WebSocket
4. Server updates virtual gamepad device using uinput
5. Games see the virtual device as a real gamepad
6. Force feedback flows back from server to client

## Supported Hardware

### Tested Devices
- Logitech G920 Driving Force Racing Wheel
- Generic USB gamepads and joysticks

### Adding Support for New Devices

To add support for new devices, modify the gamepad mappings in `ngi/client/gamepad_input.py`:

```python
self.device_mappings = {
    'steering_axis': 0,      # Steering wheel axis
    'throttle_axis': 2,      # Throttle pedal
    'brake_axis': 3,         # Brake pedal
    'clutch_axis': 1,        # Clutch pedal (if available)
    # ... button mappings
}
```

## Troubleshooting

### Common Issues

**Server fails to create virtual device:**
- Make sure uinput module is loaded: `sudo modprobe uinput`
- Check permissions: run as root or configure uinput permissions
- Verify `/dev/uinput` exists and is writable

**Client can't find gamepad:**
- Connect gamepad before starting client
- Check `pygame.joystick.get_count()` returns > 0
- Verify gamepad is detected: `ls /dev/input/`

**High latency/lag:**
- Ensure good network connection between client and server
- Try increasing update rate: `--rate 120`
- Use wired ethernet instead of WiFi if possible

**Games don't detect virtual device:**
- Restart the game after starting the server
- Check game's controller settings
- Some games may need to be restarted to detect new controllers

### Debug Mode

Enable debug logging to troubleshoot issues:

```bash
# Server debug mode
uv run ngi-server --log-level DEBUG

# Client debug mode  
uv run ngi-client --log-level DEBUG
```

Debug logs are also written to `/tmp/gamepad_server.log` and `/tmp/gamepad_client.log`.

## Development

### Project Structure
```
ngi/
├── common/
│   ├── __init__.py
│   └── protocol.py          # Shared protocol definitions
├── server/
│   ├── __init__.py
│   ├── main.py             # Server application
│   ├── network_server.py   # WebSocket server
│   └── virtual_gamepad.py  # Virtual device creation
└── client/
    ├── __init__.py
    ├── main.py             # Client application
    ├── network_client.py   # WebSocket client
    └── gamepad_input.py    # Gamepad input handling
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and test thoroughly
4. Submit a pull request

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Acknowledgments

- Inspired by the need for remote gaming with physical controllers
- Uses pygame for gamepad input handling
- Uses python-uinput for virtual device creation
- WebSocket communication for low-latency networking
