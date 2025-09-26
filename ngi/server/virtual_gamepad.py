"""
Virtual gamepad device emulator using uinput.
Creates a virtual gamepad device that games can use.
"""
import logging
import time
from typing import Optional, Dict, Any
try:
    import uinput
except ImportError:
    uinput = None

from ..common.protocol import GamepadState


class VirtualGamepadDevice:
    """Creates and manages a virtual gamepad device."""
    
    def __init__(self, device_name: str = "Network Gamepad Interface"):
        self.device_name = device_name
        self.logger = logging.getLogger(__name__)
        self.device: Optional[uinput.Device] = None
        self.is_initialized = False
        
        # Track previous state to only send changes
        self.previous_state: Optional[GamepadState] = None
        
        # Define the capabilities of our virtual device
        if uinput is not None:
            self.capabilities = [
                # Absolute axes for steering wheel and pedals
                (uinput.ABS_X, (0, 65535, 0, 0)),      # Steering wheel
                (uinput.ABS_Y, (0, 65535, 0, 0)),      # Throttle
                (uinput.ABS_Z, (0, 65535, 0, 0)),      # Brake
                (uinput.ABS_RZ, (0, 65535, 0, 0)),     # Clutch
                (uinput.ABS_HAT0X, (-1, 1, 0, 0)),     # Gear shifter X-axis
                (uinput.ABS_HAT0Y, (-1, 1, 0, 0)),     # Gear shifter Y-axis
                
                # Buttons
                uinput.BTN_A,        # Button 0
                uinput.BTN_B,        # Button 1  
                uinput.BTN_C,        # Button 2
                uinput.BTN_X,        # Button 3
                uinput.BTN_Y,        # Button 4
                uinput.BTN_Z,        # Button 5
                uinput.BTN_TL,       # Button 6
                uinput.BTN_TR,       # Button 7
                uinput.BTN_TL2,      # Button 8
                uinput.BTN_TR2,      # Button 9
                uinput.BTN_SELECT,   # Button 10
                uinput.BTN_START,    # Button 11
                uinput.BTN_MODE,     # Button 12
                uinput.BTN_THUMBL,   # Button 13
                uinput.BTN_THUMBR,   # Button 14
            ]
        else:
            self.capabilities = []
        
        # Button mapping for easy access
        if uinput is not None:
            self.button_map = [
                uinput.BTN_A, uinput.BTN_B, uinput.BTN_C, uinput.BTN_X,
                uinput.BTN_Y, uinput.BTN_Z, uinput.BTN_TL, uinput.BTN_TR,
                uinput.BTN_TL2, uinput.BTN_TR2, uinput.BTN_SELECT, uinput.BTN_START,
                uinput.BTN_MODE, uinput.BTN_THUMBL, uinput.BTN_THUMBR
            ]
        else:
            self.button_map = []
    
    def initialize(self) -> bool:
        """Initialize the virtual gamepad device."""
        if uinput is None:
            self.logger.error("python-uinput not available. Install dependencies with: uv sync")
            return False
            
        try:
            # Create the virtual device
            self.device = uinput.Device(
                events=self.capabilities,
                name=self.device_name,
                vendor=0x046d,  # Logitech vendor ID
                product=0xc262,  # G920 product ID (for compatibility)
                version=0x0111
            )
            
            self.is_initialized = True
            self.logger.info(f"Virtual gamepad device created: {self.device_name}")
            
            # Send initial neutral state
            self._send_initial_state()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create virtual gamepad device: {e}")
            self.logger.error("Make sure you have proper permissions to create uinput devices.")
            self.logger.error("You may need to run as root or add your user to the input group.")
            return False
    
    def _send_initial_state(self):
        """Send initial neutral state to the device."""
        if not self.device:
            return
            
        try:
            # Set all axes to neutral position
            self.device.emit(uinput.ABS_X, 32768)      # Steering center
            self.device.emit(uinput.ABS_Y, 0)          # Throttle released
            self.device.emit(uinput.ABS_Z, 0)          # Brake released
            self.device.emit(uinput.ABS_RZ, 0)         # Clutch released
            self.device.emit(uinput.ABS_HAT0X, 0)      # Gear neutral
            self.device.emit(uinput.ABS_HAT0Y, 0)      # Gear neutral
            
            # Ensure all buttons are released
            for button in self.button_map:
                self.device.emit(button, 0)
            
            # Sync the device
            self.device.syn()
            
        except Exception as e:
            self.logger.error(f"Error sending initial state: {e}")
    
    def update_gamepad_state(self, state: GamepadState):
        """Update the virtual gamepad with new state from the client."""
        if not self.is_initialized or not self.device:
            return False
            
        try:
            # Convert steering (-1 to 1) to 0-65535 range
            steering_value = int((state.steering + 1.0) * 32767.5)
            self.device.emit(uinput.ABS_X, steering_value)
            
            # Convert pedals (0 to 1) to 0-65535 range
            throttle_value = int(state.throttle * 65535)
            brake_value = int(state.brake * 65535)
            clutch_value = int(state.clutch * 65535)
            
            self.device.emit(uinput.ABS_Y, throttle_value)
            self.device.emit(uinput.ABS_Z, brake_value)
            self.device.emit(uinput.ABS_RZ, clutch_value)
            
            # Handle gear shifter
            self._update_gear_shifter(state.gear)
            
            # Handle buttons
            self._update_buttons(state.buttons)
            
            # Sync all changes
            self.device.syn()
            
            self.previous_state = state
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating gamepad state: {e}")
            return False
    
    def _update_gear_shifter(self, gear: int):
        """Update gear shifter hat switch based on gear number."""
        if not self.device:
            return
            
        # Map gear to hat switch positions
        # This is a simple mapping - could be enhanced based on actual shifter layout
        if gear == -1:  # Reverse
            self.device.emit(uinput.ABS_HAT0X, -1)
            self.device.emit(uinput.ABS_HAT0Y, 1)
        elif gear == 0:  # Neutral
            self.device.emit(uinput.ABS_HAT0X, 0)
            self.device.emit(uinput.ABS_HAT0Y, 0)
        elif gear == 1:
            self.device.emit(uinput.ABS_HAT0X, -1)
            self.device.emit(uinput.ABS_HAT0Y, -1)
        elif gear == 2:
            self.device.emit(uinput.ABS_HAT0X, -1)
            self.device.emit(uinput.ABS_HAT0Y, 0)
        elif gear == 3:
            self.device.emit(uinput.ABS_HAT0X, 0)
            self.device.emit(uinput.ABS_HAT0Y, -1)
        elif gear == 4:
            self.device.emit(uinput.ABS_HAT0X, 0)
            self.device.emit(uinput.ABS_HAT0Y, 0)
        elif gear == 5:
            self.device.emit(uinput.ABS_HAT0X, 1)
            self.device.emit(uinput.ABS_HAT0Y, -1)
        elif gear == 6:
            self.device.emit(uinput.ABS_HAT0X, 1)
            self.device.emit(uinput.ABS_HAT0Y, 0)
    
    def _update_buttons(self, buttons: Dict[str, bool]):
        """Update button states."""
        if not self.device or not buttons:
            return
            
        # Map button names to uinput events
        for button_name, is_pressed in buttons.items():
            # Extract button number from button name (e.g., "button_0" -> 0)
            if button_name.startswith("button_"):
                try:
                    button_num = int(button_name.split("_")[1])
                    if 0 <= button_num < len(self.button_map):
                        self.device.emit(self.button_map[button_num], 1 if is_pressed else 0)
                except (ValueError, IndexError):
                    continue
    
    def cleanup(self):
        """Clean up the virtual device."""
        if self.device:
            try:
                # Send neutral state before closing
                self._send_initial_state()
                time.sleep(0.1)  # Brief delay to ensure state is sent
                
                # Close the device
                self.device.close()
                self.device = None
                self.is_initialized = False
                self.logger.info("Virtual gamepad device cleaned up")
                
            except Exception as e:
                self.logger.error(f"Error during cleanup: {e}")