"""
Gamepad input handler for reading from Logitech G920 and other devices.
"""

import pygame
import time
import logging
from typing import Optional
from ..common.protocol import GamepadState


class GamepadInputHandler:
    """Handles reading input from gamepad devices, specifically
    optimized for Logitech G920."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.joystick: Optional[pygame.joystick.Joystick] = None
        self.is_initialized = False

        # Logitech G920 specific mappings
        self.g920_mappings = {
            "steering_axis": 0,  # Steering wheel
            "throttle_axis": 2,  # Right trigger (inverted)
            "brake_axis": 3,  # Left trigger (inverted)
            "clutch_axis": 1,  # Clutch pedal (if present)
            "gear_buttons": {  # Gear shifter buttons
                "reverse": 4,
                "gear_1": 5,
                "gear_2": 6,
                "gear_3": 7,
                "gear_4": 8,
                "gear_5": 9,
                "gear_6": 10,
            },
        }

    def initialize(self) -> bool:
        """Initialize pygame and find the gamepad device."""
        try:
            pygame.init()
            pygame.joystick.init()

            # Find the first joystick/gamepad
            if pygame.joystick.get_count() == 0:
                self.logger.error("No joystick/gamepad found")
                return False

            # Look for Logitech G920 specifically, or use first available
            g920_found = False
            for i in range(pygame.joystick.get_count()):
                joystick = pygame.joystick.Joystick(i)
                joystick.init()

                self.logger.info(f"Found device {i}: {joystick.get_name()}")

                # Check if this is a Logitech G920
                if "G920" in joystick.get_name() or "Logitech" in joystick.get_name():
                    self.joystick = joystick
                    g920_found = True
                    self.logger.info(f"Using Logitech G920: {joystick.get_name()}")
                    break

            # If no G920 found, use the first available device
            if not g920_found and pygame.joystick.get_count() > 0:
                self.joystick = pygame.joystick.Joystick(0)
                self.joystick.init()
                self.logger.info(
                    f"Using first available device: {self.joystick.get_name()}"
                )

            if self.joystick:
                self.logger.info(f"Gamepad initialized: {self.joystick.get_name()}")
                self.logger.info(
                    f"Axes: {self.joystick.get_numaxes()}, "
                    f"Buttons: {self.joystick.get_numbuttons()}"
                )
                self.is_initialized = True
                return True
            else:
                self.logger.error("Failed to initialize any gamepad")
                return False

        except Exception as e:
            self.logger.error(f"Failed to initialize gamepad: {e}")
            return False

    def read_gamepad_state(self) -> Optional[GamepadState]:
        """Read the current state of the gamepad and return GamepadState object."""
        if not self.is_initialized or not self.joystick:
            return None

        try:
            # Process pygame events to update joystick state
            pygame.event.pump()

            # Read steering wheel position
            steering = self.joystick.get_axis(self.g920_mappings["steering_axis"])

            # Read pedals (triggers are typically -1 to 1, we want 0 to 1)
            throttle_raw = self.joystick.get_axis(self.g920_mappings["throttle_axis"])
            brake_raw = self.joystick.get_axis(self.g920_mappings["brake_axis"])

            # Convert trigger values: -1 (released) to 1 (pressed) -> 0 to 1
            throttle = (throttle_raw + 1.0) / 2.0
            brake = (brake_raw + 1.0) / 2.0

            # Read clutch if available (some G920 setups don't have clutch)
            clutch = 0.0
            if self.joystick.get_numaxes() > self.g920_mappings["clutch_axis"]:
                clutch_raw = self.joystick.get_axis(self.g920_mappings["clutch_axis"])
                clutch = (clutch_raw + 1.0) / 2.0

            # Determine gear from buttons
            gear = 0  # Neutral by default
            if self.joystick.get_numbuttons() > max(
                self.g920_mappings["gear_buttons"].values()
            ):
                if self.joystick.get_button(
                    self.g920_mappings["gear_buttons"]["reverse"]
                ):
                    gear = -1
                else:
                    for gear_num in range(1, 7):
                        gear_key = f"gear_{gear_num}"
                        if gear_key in self.g920_mappings[
                            "gear_buttons"
                        ] and self.joystick.get_button(
                            self.g920_mappings["gear_buttons"][gear_key]
                        ):
                            gear = gear_num
                            break

            # Read all button states
            buttons = {}
            for i in range(self.joystick.get_numbuttons()):
                buttons[f"button_{i}"] = self.joystick.get_button(i)

            return GamepadState(
                steering=steering,
                throttle=throttle,
                brake=brake,
                clutch=clutch,
                gear=gear,
                buttons=buttons,
                timestamp=time.time(),
            )

        except Exception as e:
            self.logger.error(f"Error reading gamepad state: {e}")
            return None

    def cleanup(self):
        """Clean up pygame resources."""
        if self.joystick:
            self.joystick.quit()
        pygame.joystick.quit()
        pygame.quit()
        self.is_initialized = False
        self.logger.info("Gamepad input handler cleaned up")


class ForceFeedbackHandler:
    """Handles force feedback output to gamepad devices."""

    def __init__(self, joystick: Optional[pygame.joystick.Joystick] = None):
        self.logger = logging.getLogger(__name__)
        self.joystick = joystick

    def send_force_feedback(self, force: float, duration: float = 0.1):
        """Send force feedback to the device."""
        if not self.joystick:
            return

        try:
            # Note: Force feedback implementation depends on the specific device
            # For Logitech G920, this might require additional libraries like
            # python-uinput or direct device communication
            self.logger.debug(f"Force feedback: {force} for {duration}s")
            # TODO: Implement actual force feedback based on device capabilities

        except Exception as e:
            self.logger.error(f"Error sending force feedback: {e}")
