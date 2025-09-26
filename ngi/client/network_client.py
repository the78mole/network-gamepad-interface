"""
Network client for sending gamepad data to the server.
"""
import asyncio
import websockets
import logging
import time
from typing import Optional, Callable
from ..common.protocol import NetworkMessage, MessageType, ProtocolEncoder, GamepadState, ForceFeedback
from ..common.protocol import DEFAULT_PORT, HEARTBEAT_INTERVAL, CONNECTION_TIMEOUT


class NetworkClient:
    """WebSocket client for communicating with the gamepad server."""
    
    def __init__(self, server_host: str = "localhost", server_port: int = DEFAULT_PORT):
        self.server_host = server_host
        self.server_port = server_port
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.logger = logging.getLogger(__name__)
        self.is_connected = False
        self.last_heartbeat = 0.0
        
        # Callbacks
        self.force_feedback_callback: Optional[Callable[[ForceFeedback], None]] = None
        
    async def connect(self) -> bool:
        """Connect to the gamepad server."""
        try:
            uri = f"ws://{self.server_host}:{self.server_port}"
            self.logger.info(f"Connecting to {uri}")
            
            self.websocket = await websockets.connect(uri)
            self.is_connected = True
            
            # Send connect message
            connect_msg = NetworkMessage(
                type=MessageType.CONNECT,
                data={"client_type": "gamepad_client"},
                timestamp=time.time()
            )
            
            await self._send_message(connect_msg)
            self.logger.info("Successfully connected to server")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to server: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from the server."""
        if self.websocket and self.is_connected:
            try:
                # Send disconnect message
                disconnect_msg = NetworkMessage(
                    type=MessageType.DISCONNECT,
                    data={},
                    timestamp=time.time()
                )
                await self._send_message(disconnect_msg)
                await self.websocket.close()
                
            except Exception as e:
                self.logger.error(f"Error during disconnect: {e}")
            finally:
                self.is_connected = False
                self.websocket = None
                self.logger.info("Disconnected from server")
    
    async def send_gamepad_state(self, state: GamepadState):
        """Send gamepad state to the server."""
        if not self.is_connected or not self.websocket:
            return False
            
        try:
            message = NetworkMessage(
                type=MessageType.GAMEPAD_STATE,
                data=ProtocolEncoder.encode_gamepad_state(state),
                timestamp=time.time()
            )
            
            await self._send_message(message)
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending gamepad state: {e}")
            return False
    
    async def _send_message(self, message: NetworkMessage):
        """Send a message to the server."""
        if not self.websocket or not self.is_connected:
            raise ConnectionError("Not connected to server")
            
        data = ProtocolEncoder.encode_message(message)
        await self.websocket.send(data)
        self.logger.debug(f"Sent message: {message.type.value}")
    
    async def _receive_message(self) -> Optional[NetworkMessage]:
        """Receive a message from the server."""
        if not self.websocket or not self.is_connected:
            return None
            
        try:
            data = await asyncio.wait_for(self.websocket.recv(), timeout=1.0)
            message = ProtocolEncoder.decode_message(data)
            self.logger.debug(f"Received message: {message.type.value}")
            return message
            
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            self.logger.error(f"Error receiving message: {e}")
            return None
    
    async def listen_for_messages(self):
        """Listen for incoming messages from the server."""
        while self.is_connected:
            try:
                message = await self._receive_message()
                if message:
                    await self._handle_message(message)
                    
                # Send periodic heartbeat
                if time.time() - self.last_heartbeat > HEARTBEAT_INTERVAL:
                    await self._send_heartbeat()
                    
            except Exception as e:
                self.logger.error(f"Error in message listener: {e}")
                break
    
    async def _handle_message(self, message: NetworkMessage):
        """Handle incoming messages from the server."""
        try:
            if message.type == MessageType.FORCE_FEEDBACK:
                if self.force_feedback_callback:
                    feedback = ProtocolEncoder.decode_force_feedback(message.data)
                    self.force_feedback_callback(feedback)
                    
            elif message.type == MessageType.HEARTBEAT:
                self.logger.debug("Received heartbeat from server")
                
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
    
    async def _send_heartbeat(self):
        """Send heartbeat to server."""
        try:
            heartbeat_msg = NetworkMessage(
                type=MessageType.HEARTBEAT,
                data={},
                timestamp=time.time()
            )
            await self._send_message(heartbeat_msg)
            self.last_heartbeat = time.time()
            
        except Exception as e:
            self.logger.error(f"Error sending heartbeat: {e}")
    
    def set_force_feedback_callback(self, callback: Callable[[ForceFeedback], None]):
        """Set callback function for force feedback messages."""
        self.force_feedback_callback = callback