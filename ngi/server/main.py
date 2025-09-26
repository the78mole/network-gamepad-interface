"""
Main server application for network gamepad interface.
Runs on the host machine where the game is running.
"""

import asyncio
import logging
import argparse
import signal
import sys
from typing import Optional
from .virtual_gamepad import VirtualGamepadDevice
from .network_server import GamepadServer
from ..common.protocol import GamepadState, ForceFeedback, DEFAULT_PORT


class GamepadServerApp:
    """Main gamepad server application."""

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

        # Initialize components
        self.virtual_gamepad = VirtualGamepadDevice("Network Gamepad Interface")
        self.network_server = GamepadServer(host, port)

        # Setup logging
        self.logger = logging.getLogger(__name__)

        # Control flags
        self.running = False

        # Statistics
        self.messages_received = 0
        self.last_gamepad_state: Optional[GamepadState] = None

    async def initialize(self) -> bool:
        """Initialize all components."""
        self.logger.info("Initializing gamepad server...")

        # Initialize virtual gamepad device
        if not self.virtual_gamepad.initialize():
            self.logger.error("Failed to initialize virtual gamepad device")
            return False

        # Set up network server callbacks
        self.network_server.set_gamepad_state_callback(self._handle_gamepad_state)

        # Start network server
        try:
            await self.network_server.start_server()
        except Exception as e:
            self.logger.error(f"Failed to start network server: {e}")
            return False

        self.logger.info("Gamepad server initialized successfully")
        return True

    def _handle_gamepad_state(self, state: GamepadState):
        """Handle gamepad state received from client."""
        self.messages_received += 1
        self.last_gamepad_state = state

        # Update virtual gamepad device
        success = self.virtual_gamepad.update_gamepad_state(state)

        if success:
            # Log state periodically for monitoring
            if (
                self.messages_received % 60 == 0
            ):  # Every 60 messages (roughly 1 second at 60Hz)
                self.logger.info(f"Messages received: {self.messages_received}")
                self.logger.debug(
                    f"Gamepad state - Steering: {state.steering:.2f}, "
                    f"Throttle: {state.throttle:.2f}, "
                    f"Brake: {state.brake:.2f}, "
                    f"Gear: {state.gear}"
                )

        # TODO: Implement force feedback generation based on game state
        # For now, we'll send a simple example force feedback occasionally
        if self.messages_received % 300 == 0:  # Every 5 seconds
            asyncio.create_task(self._send_example_force_feedback())

    async def _send_example_force_feedback(self):
        """Send example force feedback to demonstrate the feature."""
        try:
            # Create a simple force feedback effect
            feedback = ForceFeedback(
                force=0.3,  # 30% force
                duration=0.2,  # 200ms duration
                timestamp=asyncio.get_event_loop().time(),
            )

            await self.network_server.broadcast_force_feedback(feedback)
            self.logger.debug("Sent example force feedback")

        except Exception as e:
            self.logger.error(f"Error sending force feedback: {e}")

    async def run(self):
        """Main application loop."""
        self.running = True
        self.logger.info("Starting gamepad server...")

        try:
            # Start status reporting task
            status_task = asyncio.create_task(self._status_reporting_task())

            # Main loop - just keep the server running
            while self.running:
                await asyncio.sleep(1.0)

        except Exception as e:
            self.logger.error(f"Error in main loop: {e}")
        finally:
            # Cancel status task
            status_task.cancel()
            try:
                await status_task
            except asyncio.CancelledError:
                pass

    async def _status_reporting_task(self):
        """Periodic status reporting task."""
        while self.running:
            try:
                # Log server status every 30 seconds
                await asyncio.sleep(30.0)

                clients = self.network_server.get_connected_clients()
                self.logger.info(
                    f"Server status - Connected clients: {len(clients)}, "
                    f"Messages received: {self.messages_received}"
                )

                if clients:
                    for address, info in clients.items():
                        self.logger.info(f"  Client {address}: {info['client_type']}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in status reporting: {e}")

    async def cleanup(self):
        """Clean up resources."""
        self.logger.info("Cleaning up gamepad server...")
        self.running = False

        # Stop network server
        await self.network_server.stop_server()

        # Clean up virtual gamepad
        self.virtual_gamepad.cleanup()

        self.logger.info("Gamepad server cleanup complete")


def setup_logging(level: str = "INFO"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("/tmp/gamepad_server.log"),
        ],
    )


async def async_main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Network Gamepad Interface Server")
    parser.add_argument("--host", default="0.0.0.0", help="Server bind address")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Server port")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    # Create server
    server = GamepadServerApp(args.host, args.port)

    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        server.running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Initialize and run
        if await server.initialize():
            await server.run()
        else:
            logger.error("Failed to initialize server")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        await server.cleanup()


def main():
    """Synchronous main entry point for console scripts."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
