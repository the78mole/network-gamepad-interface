import uinput
import time

# Minimal example for a virtual gamepad

def main():
    device = uinput.Device([
        uinput.BTN_A,
        uinput.ABS_X + (0, 255, 0, 0),
    ], name="Test Gamepad")
    print("Created virtual gamepad!")

    # Find correct /dev/input/eventX-node with device name
    import os
    import glob
    event_node = None
    device_name = None
    for event_path in glob.glob("/dev/input/event*"):
        try:
            with open(f"/sys/class/input/{os.path.basename(event_path)}/device/name") as f:
                name = f.read().strip()
            if name == "Test Gamepad":
                event_node = event_path
                device_name = name
                break
        except Exception:
            continue
    if event_node:
        print(f"Device-Name: {device_name}, Event-Node: {event_node}")
    else:
        print("No matching event node found.")

    device.emit(uinput.BTN_A, 1)  # Press button
    device.emit(uinput.ABS_X, 128)  # Move axis
    time.sleep(10)
    device.emit(uinput.BTN_A, 0)  # Release button
    print("Test finished.")

if __name__ == "__main__":
    main()
