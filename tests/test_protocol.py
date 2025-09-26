"""
Basic tests for the network gamepad interface protocol.
"""
import unittest
import time
from ngi.common.protocol import (
    GamepadState, ForceFeedback, NetworkMessage, MessageType,
    ProtocolEncoder
)


class TestProtocol(unittest.TestCase):
    """Test protocol encoding/decoding."""
    
    def test_gamepad_state_encoding(self):
        """Test GamepadState encoding and decoding."""
        # Create a test gamepad state
        original_state = GamepadState(
            steering=0.5,
            throttle=0.8,
            brake=0.2,
            clutch=0.0,
            gear=3,
            buttons={"button_0": True, "button_1": False},
            timestamp=time.time()
        )
        
        # Encode and decode
        encoded = ProtocolEncoder.encode_gamepad_state(original_state)
        decoded_state = ProtocolEncoder.decode_gamepad_state(encoded)
        
        # Verify all fields match
        self.assertEqual(original_state.steering, decoded_state.steering)
        self.assertEqual(original_state.throttle, decoded_state.throttle)
        self.assertEqual(original_state.brake, decoded_state.brake)
        self.assertEqual(original_state.clutch, decoded_state.clutch)
        self.assertEqual(original_state.gear, decoded_state.gear)
        self.assertEqual(original_state.buttons, decoded_state.buttons)
        self.assertEqual(original_state.timestamp, decoded_state.timestamp)
    
    def test_force_feedback_encoding(self):
        """Test ForceFeedback encoding and decoding."""
        # Create a test force feedback
        original_feedback = ForceFeedback(
            force=0.7,
            duration=0.5,
            timestamp=time.time()
        )
        
        # Encode and decode
        encoded = ProtocolEncoder.encode_force_feedback(original_feedback)
        decoded_feedback = ProtocolEncoder.decode_force_feedback(encoded)
        
        # Verify all fields match
        self.assertEqual(original_feedback.force, decoded_feedback.force)
        self.assertEqual(original_feedback.duration, decoded_feedback.duration)
        self.assertEqual(original_feedback.timestamp, decoded_feedback.timestamp)
    
    def test_network_message_encoding(self):
        """Test NetworkMessage encoding and decoding."""
        # Create test gamepad state
        gamepad_state = GamepadState(steering=0.3, throttle=0.6, brake=0.1)
        
        # Create network message
        original_message = NetworkMessage(
            type=MessageType.GAMEPAD_STATE,
            data=ProtocolEncoder.encode_gamepad_state(gamepad_state),
            timestamp=time.time()
        )
        
        # Encode and decode
        encoded_bytes = ProtocolEncoder.encode_message(original_message)
        decoded_message = ProtocolEncoder.decode_message(encoded_bytes)
        
        # Verify message type and timestamp
        self.assertEqual(original_message.type, decoded_message.type)
        self.assertEqual(original_message.timestamp, decoded_message.timestamp)
        
        # Verify gamepad state data
        decoded_state = ProtocolEncoder.decode_gamepad_state(decoded_message.data)
        self.assertEqual(gamepad_state.steering, decoded_state.steering)
        self.assertEqual(gamepad_state.throttle, decoded_state.throttle)
        self.assertEqual(gamepad_state.brake, decoded_state.brake)
    
    def test_gamepad_state_defaults(self):
        """Test GamepadState default values."""
        state = GamepadState()
        
        self.assertEqual(state.steering, 0.0)
        self.assertEqual(state.throttle, 0.0)
        self.assertEqual(state.brake, 0.0)
        self.assertEqual(state.clutch, 0.0)
        self.assertEqual(state.gear, 0)
        self.assertEqual(state.buttons, {})
        self.assertEqual(state.timestamp, 0.0)
    
    def test_gear_values(self):
        """Test gear shifter values."""
        # Test reverse gear
        state_reverse = GamepadState(gear=-1)
        self.assertEqual(state_reverse.gear, -1)
        
        # Test neutral
        state_neutral = GamepadState(gear=0) 
        self.assertEqual(state_neutral.gear, 0)
        
        # Test forward gears
        for gear in range(1, 7):
            state_forward = GamepadState(gear=gear)
            self.assertEqual(state_forward.gear, gear)
    
    def test_button_states(self):
        """Test button state handling."""
        buttons = {
            "button_0": True,
            "button_1": False,
            "button_2": True,
            "shift_up": False,
            "shift_down": True
        }
        
        state = GamepadState(buttons=buttons)
        
        # Verify button states are preserved
        self.assertTrue(state.buttons["button_0"])
        self.assertFalse(state.buttons["button_1"])
        self.assertTrue(state.buttons["button_2"])
        self.assertFalse(state.buttons["shift_up"])
        self.assertTrue(state.buttons["shift_down"])


if __name__ == "__main__":
    unittest.main()