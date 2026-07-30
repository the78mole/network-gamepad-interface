"""
Network server for receiving gamepad data from clients.
"""

import asyncio
import websockets
import logging
import time
from typing import Set, Optional, Callable, Dict, Any
from ..common.protocol import (
    NetworkMessage,
    MessageType,
    ProtocolEncoder,
    GamepadState,
    ForceFeedback,
)
from ..common.protocol import DEFAULT_PORT, HEARTBEAT_INTERVAL, CONNECTION_TIMEOUT


class GamepadServer:
    """WebSocket server for receiving gamepad data from clients."""

    def __init__(self, host: str = "localhost", port: int = DEFAULT_PORT):
        self.host = host
        self.port = port
        self.logger = logging.getLogger(__name__)

        # Connected clients
        self.clients: Set[websockets.WebSocketServerProtocol] = set()

        # Callbacks
        self.gamepad_state_callback: Optional[Callable[[GamepadState], None]] = None

        # Server state
        self.is_running = False

        # Track client connection info
        self.client_info: Dict[websockets.WebSocketServerProtocol, Dict[str, Any]] = {}

    def set_gamepad_state_callback(self, callback: Callable[[GamepadState], None]):
        """Set callback function for gamepad state updates."""
        self.gamepad_state_callback = callback

    async def start_server(self):
        """Start the WebSocket server."""
        try:
            self.logger.info(f"Starting gamepad server on {self.host}:{self.port}")

            # Start the WebSocket server
            start_server = websockets.serve(
                self._handle_client,
                self.host,
                self.port,
                ping_interval=HEARTBEAT_INTERVAL,
                ping_timeout=CONNECTION_TIMEOUT,
            )

            self.server = await start_server
            self.is_running = True

            self.logger.info(f"Gamepad server started on {self.host}:{self.port}")

            # Start heartbeat task
            asyncio.create_task(self._heartbeat_task())

            return self.server

        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            raise

    async def stop_server(self):
        """Stop the WebSocket server."""
        if hasattr(self, "server") and self.server:
            self.is_running = False

            # Close all client connections
            if self.clients:
                await asyncio.gather(
                    *[client.close() for client in self.clients], return_exceptions=True
                )

            # Stop the server
            self.server.close()
            await self.server.wait_closed()

            self.logger.info("Gamepad server stopped")

    async def _handle_client(self, websocket, path):
        """Handle a new client connection."""
        client_address = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        self.logger.info(f"Client connected: {client_address}")

        # Add client to set
        self.clients.add(websocket)
        self.client_info[websocket] = {
            "address": client_address,
            "connected_at": time.time(),
            "last_heartbeat": time.time(),
            "client_type": "unknown",
        }

        try:
            async for message_data in websocket:
                try:
                    message = ProtocolEncoder.decode_message(message_data)
                    await self._handle_message(websocket, message)

                    # Update last heartbeat time
                    self.client_info[websocket]["last_heartbeat"] = time.time()

                except Exception as e:
                    self.logger.error(
                        f"Error handling message from {client_address}: {e}"
                    )

        except websockets.exceptions.ConnectionClosed:
            self.logger.info(f"Client disconnected: {client_address}")
        except Exception as e:
            self.logger.error(f"Error in client handler for {client_address}: {e}")
        finally:
            # Remove client from set
            self.clients.discard(websocket)
            if websocket in self.client_info:
                del self.client_info[websocket]

    async def _handle_message(self, websocket, message: NetworkMessage):
        """Handle incoming messages from clients."""
        client_address = self.client_info.get(websocket, {}).get("address", "unknown")

        try:
            if message.type == MessageType.CONNECT:
                client_type = message.data.get("client_type", "unknown")
                self.client_info[websocket]["client_type"] = client_type
                self.logger.info(
                    f"Client {client_address} identified as: {client_type}"
                )

                # Send acknowledgment
                ack_message = NetworkMessage(
                    type=MessageType.CONNECT,
                    data={"status": "connected"},
                    timestamp=time.time(),
                )
                await self._send_message(websocket, ack_message)

            elif message.type == MessageType.DISCONNECT:
                self.logger.info(f"Client {client_address} requested disconnect")
                await websocket.close()

            elif message.type == MessageType.GAMEPAD_STATE:
                # Decode gamepad state and forward to callback
                if self.gamepad_state_callback:
                    gamepad_state = ProtocolEncoder.decode_gamepad_state(message.data)
                    self.gamepad_state_callback(gamepad_state)

            elif message.type == MessageType.HEARTBEAT:
                # Respond to heartbeat
                heartbeat_response = NetworkMessage(
                    type=MessageType.HEARTBEAT,
                    data={"server_time": time.time()},
                    timestamp=time.time(),
                )
                await self._send_message(websocket, heartbeat_response)

        except Exception as e:
            self.logger.error(
                f"Error handling {message.type.value} message "
                f"from {client_address}: {e}"
            )

    async def _send_message(self, websocket, message: NetworkMessage):
        """Send a message to a specific client."""
        try:
            data = ProtocolEncoder.encode_message(message)
            await websocket.send(data)

        except Exception as e:
            client_address = self.client_info.get(websocket, {}).get(
                "address", "unknown"
            )
            self.logger.error(f"Error sending message to {client_address}: {e}")

    async def broadcast_force_feedback(self, feedback: ForceFeedback):
        """Broadcast force feedback to all connected gamepad clients."""
        if not self.clients:
            return

        message = NetworkMessage(
            type=MessageType.FORCE_FEEDBACK,
            data=ProtocolEncoder.encode_force_feedback(feedback),
            timestamp=time.time(),
        )

        # Send to all gamepad clients
        gamepad_clients = [
            client
            for client, info in self.client_info.items()
            if info.get("client_type") == "gamepad_client"
        ]

        if gamepad_clients:
            self.logger.debug(
                f"Broadcasting force feedback to {len(gamepad_clients)} clients"
            )
            await asyncio.gather(
                *[self._send_message(client, message) for client in gamepad_clients],
                return_exceptions=True,
            )

    async def _heartbeat_task(self):
        """Periodic heartbeat task to check client connections."""
        while self.is_running:
            try:
                current_time = time.time()
                disconnected_clients = []

                # Check for timed out clients
                for websocket, info in self.client_info.items():
                    if current_time - info["last_heartbeat"] > CONNECTION_TIMEOUT:
                        self.logger.warning(f"Client {info['address']} timed out")
                        disconnected_clients.append(websocket)

                # Close timed out connections
                for websocket in disconnected_clients:
                    try:
                        await websocket.close()
                    except Exception:
                        pass  # Connection might already be closed

                    self.clients.discard(websocket)
                    if websocket in self.client_info:
                        del self.client_info[websocket]

                await asyncio.sleep(HEARTBEAT_INTERVAL)

            except Exception as e:
                self.logger.error(f"Error in heartbeat task: {e}")

    def get_connected_clients(self) -> Dict[str, Dict[str, Any]]:
        """Get information about connected clients."""
        return {
            info["address"]: {
                "client_type": info["client_type"],
                "connected_at": info["connected_at"],
                "last_heartbeat": info["last_heartbeat"],
            }
            for info in self.client_info.values()
        }
