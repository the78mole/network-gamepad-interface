"""
Common protocol definitions and data structures for network gamepad interface.
"""
import json
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
from enum import Enum


class MessageType(Enum):
    """Message types for communication between client and server."""
    GAMEPAD_STATE = "gamepad_state"
    FORCE_FEEDBACK = "force_feedback"
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    HEARTBEAT = "heartbeat"


@dataclass
class GamepadState:
    """Represents the state of a gamepad/steering wheel."""
    # Steering wheel axis (-1.0 to 1.0, left to right)
    steering: float = 0.0
    
    # Pedals (0.0 to 1.0)
    throttle: float = 0.0
    brake: float = 0.0
    clutch: float = 0.0
    
    # Gear shifter (0 = neutral, -1 = reverse, 1-6 = forward gears)
    gear: int = 0
    
    # Buttons (True = pressed, False = released)
    buttons: Dict[str, bool] = None
    
    # Timestamp
    timestamp: float = 0.0
    
    def __post_init__(self):
        if self.buttons is None:
            self.buttons = {}


@dataclass
class ForceFeedback:
    """Represents force feedback information to send to the client."""
    # Force feedback strength (-1.0 to 1.0)
    force: float = 0.0
    
    # Duration in seconds
    duration: float = 0.0
    
    # Timestamp
    timestamp: float = 0.0


@dataclass
class NetworkMessage:
    """Generic network message container."""
    type: MessageType
    data: Dict[str, Any]
    timestamp: float = 0.0


class ProtocolEncoder:
    """Handles encoding/decoding of network messages."""
    
    @staticmethod
    def encode_message(msg: NetworkMessage) -> bytes:
        """Encode a NetworkMessage to bytes."""
        msg_dict = {
            "type": msg.type.value,
            "data": msg.data,
            "timestamp": msg.timestamp
        }
        return json.dumps(msg_dict).encode('utf-8')
    
    @staticmethod
    def decode_message(data: bytes) -> NetworkMessage:
        """Decode bytes to a NetworkMessage."""
        msg_dict = json.loads(data.decode('utf-8'))
        return NetworkMessage(
            type=MessageType(msg_dict["type"]),
            data=msg_dict["data"],
            timestamp=msg_dict["timestamp"]
        )
    
    @staticmethod
    def encode_gamepad_state(state: GamepadState) -> Dict[str, Any]:
        """Encode GamepadState to dictionary."""
        return asdict(state)
    
    @staticmethod
    def decode_gamepad_state(data: Dict[str, Any]) -> GamepadState:
        """Decode dictionary to GamepadState."""
        return GamepadState(**data)
    
    @staticmethod
    def encode_force_feedback(feedback: ForceFeedback) -> Dict[str, Any]:
        """Encode ForceFeedback to dictionary."""
        return asdict(feedback)
    
    @staticmethod
    def decode_force_feedback(data: Dict[str, Any]) -> ForceFeedback:
        """Decode dictionary to ForceFeedback."""
        return ForceFeedback(**data)


# Default port for the network interface
DEFAULT_PORT = 9999

# Heartbeat interval in seconds  
HEARTBEAT_INTERVAL = 1.0

# Connection timeout in seconds
CONNECTION_TIMEOUT = 5.0