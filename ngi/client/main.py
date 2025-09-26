"""
Main client application for network gamepad interface.
Runs on Raspberry Pi with connected Logitech G920.
"""

import asyncio
import logging
import argparse
import signal
import sys
from typing import Optional
from .gamepad_input import GamepadInputHandler, ForceFeedbackHandler
from .network_client import NetworkClient
from ..common.protocol import ForceFeedback, DEFAULT_PORT


class GamepadClient:
    """Main gamepad client application."""

    def __init__(self, server_host: str, server_port: int):
        self.server_host = server_host
        self.server_port = server_port

        # Initialize components
        self.gamepad_handler = GamepadInputHandler()
        self.force_feedback_handler: Optional[ForceFeedbackHandler] = None
        self.network_client = NetworkClient(server_host, server_port)

        # Setup logging
        self.logger = logging.getLogger(__name__)

        # Control flags
        self.running = False
        self.update_rate = 60  # Hz - gamepad update rate

    async def initialize(self) -> bool:
        """Initialize all components."""
        self.logger.info("Initializing gamepad client...")

        # Initialize gamepad
        if not self.gamepad_handler.initialize():
            self.logger.error("Failed to initialize gamepad")
            return False

        # Initialize force feedback
        if self.gamepad_handler.joystick:
            self.force_feedback_handler = ForceFeedbackHandler(
                self.gamepad_handler.joystick
            )

        # Connect to server
        if not await self.network_client.connect():
            self.logger.error("Failed to connect to server")
            return False

        # Set up force feedback callback
        self.network_client.set_force_feedback_callback(self._handle_force_feedback)

        self.logger.info("Gamepad client initialized successfully")
        return True

    def _handle_force_feedback(self, feedback: ForceFeedback):
        """Handle force feedback from server."""
        if self.force_feedback_handler:
            self.force_feedback_handler.send_force_feedback(
                feedback.force, feedback.duration
            )

    async def run(self):
        """Main application loop."""
        self.running = True
        self.logger.info("Starting gamepad client...")

        # Start message listener task
        listener_task = asyncio.create_task(self.network_client.listen_for_messages())

        try:
            while self.running:
                # Read gamepad state
                gamepad_state = self.gamepad_handler.read_gamepad_state()

                if gamepad_state:
                    # Send to server
                    await self.network_client.send_gamepad_state(gamepad_state)

                    # Log state for debugging (reduce frequency for less spam)
                    if int(gamepad_state.timestamp * 10) % 10 == 0:  # Every second
                        self.logger.debug(
                            f"Gamepad state - Steering: {gamepad_state.steering:.2f}, "
                            f"Throttle: {gamepad_state.throttle:.2f}, "
                            f"Brake: {gamepad_state.brake:.2f}, "
                            f"Gear: {gamepad_state.gear}"
                        )

                # Sleep to maintain update rate
                await asyncio.sleep(1.0 / self.update_rate)

        except Exception as e:
            self.logger.error(f"Error in main loop: {e}")
        finally:
            # Cancel listener task
            listener_task.cancel()
            try:
                await listener_task
            except asyncio.CancelledError:
                pass

    async def cleanup(self):
        """Clean up resources."""
        self.logger.info("Cleaning up gamepad client...")
        self.running = False

        # Disconnect from server
        await self.network_client.disconnect()

        # Clean up gamepad
        self.gamepad_handler.cleanup()

        self.logger.info("Gamepad client cleanup complete")


def setup_logging(level: str = "INFO"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("/tmp/gamepad_client.log"),
        ],
    )


async def async_main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Network Gamepad Interface Client")
    parser.add_argument("--host", default="localhost", help="Server host address")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Server port")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )
    parser.add_argument("--rate", type=int, default=60, help="Update rate in Hz")

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    # Create client
    client = GamepadClient(args.host, args.port)
    client.update_rate = args.rate

    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        client.running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Initialize and run
        if await client.initialize():
            await client.run()
        else:
            logger.error("Failed to initialize client")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        await client.cleanup()


def main():
    """Synchronous main entry point for console scripts."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
