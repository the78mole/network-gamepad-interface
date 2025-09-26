#!/usr/bin/env python3
"""
Demo script to showcase the network gamepad interface functionality.
This simulates a gamepad client sending data to test the protocol.
"""
import asyncio
import time
import math
import logging
from ngi.common.protocol import GamepadState, MessageType, NetworkMessage, ProtocolEncoder

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def simulate_gamepad_data(timestamp: float) -> GamepadState:
    """Simulate realistic gamepad data for a racing scenario."""
    
    # Simulate steering wheel movement (sine wave)
    steering = 0.7 * math.sin(timestamp * 0.5)
    
    # Simulate throttle (accelerating/decelerating cycles)  
    throttle = max(0, 0.5 + 0.5 * math.sin(timestamp * 0.3))
    
    # Simulate brake (occasional braking)
    brake = max(0, 0.3 * math.sin(timestamp * 0.8)) if math.sin(timestamp * 0.2) < -0.5 else 0.0
    
    # Simulate clutch (occasional use)
    clutch = 0.5 if int(timestamp * 2) % 10 == 0 else 0.0
    
    # Simulate gear shifting
    gear_cycle = int(timestamp / 3) % 7
    gear = gear_cycle if gear_cycle <= 6 else 6
    
    # Simulate some buttons
    buttons = {
        "button_0": int(timestamp) % 5 == 0,  # Press every 5 seconds
        "button_1": False,
        "button_2": int(timestamp * 2) % 7 == 0,  # Press occasionally
        "shift_up": gear > 3,
        "shift_down": gear < 2
    }
    
    return GamepadState(
        steering=steering,
        throttle=throttle,
        brake=brake,
        clutch=clutch,
        gear=gear,
        buttons=buttons,
        timestamp=timestamp
    )

async def demo_protocol():
    """Demonstrate the protocol encoding/decoding."""
    logger.info("=== Network Gamepad Interface Protocol Demo ===")
    
    start_time = time.time()
    
    for i in range(10):
        current_time = time.time() - start_time
        
        # Create simulated gamepad state
        gamepad_state = simulate_gamepad_data(current_time)
        
        # Create network message
        message = NetworkMessage(
            type=MessageType.GAMEPAD_STATE,
            data=ProtocolEncoder.encode_gamepad_state(gamepad_state),
            timestamp=current_time
        )
        
        # Encode to bytes (simulate network transmission)
        encoded_bytes = ProtocolEncoder.encode_message(message)
        
        # Decode from bytes (simulate network reception)
        decoded_message = ProtocolEncoder.decode_message(encoded_bytes)
        decoded_state = ProtocolEncoder.decode_gamepad_state(decoded_message.data)
        
        # Display the data
        logger.info(f"Sample {i+1}:")
        logger.info(f"  Steering: {decoded_state.steering:.2f} (-1=left, +1=right)")
        logger.info(f"  Throttle: {decoded_state.throttle:.2f} (0=off, 1=full)")
        logger.info(f"  Brake:    {decoded_state.brake:.2f} (0=off, 1=full)")
        logger.info(f"  Clutch:   {decoded_state.clutch:.2f} (0=off, 1=full)")
        logger.info(f"  Gear:     {decoded_state.gear} (-1=reverse, 0=neutral, 1-6=forward)")
        logger.info(f"  Buttons:  {decoded_state.buttons}")
        logger.info(f"  Message Size: {len(encoded_bytes)} bytes")
        logger.info("  " + "-" * 50)
        
        await asyncio.sleep(1.0)
    
    logger.info("Demo complete! This data would be sent from the Raspberry Pi client")
    logger.info("to the gaming PC server to control games like SuperTuxKart.")

if __name__ == "__main__":
    asyncio.run(demo_protocol())