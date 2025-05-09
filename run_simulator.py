# File: run_simulator.py

# Import necessary libraries
import sys
import os

# Add current folder to search path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import simulator
from obd_simulator.mock_simulator.simulator import Simulator
from obd_simulator.common.obd_command import OBDCommand

def main():
    # Create and connect the simulator
    simulator = Simulator()
    simulator.connect()
    
    print(f"Simulator status: {simulator.status()}")
    
    # Query vehicle data
    rpm = simulator.query(OBDCommand.RPM)
    speed = simulator.query(OBDCommand.SPEED)
    temp = simulator.query(OBDCommand.COOLANT_TEMP)
    
    print(f"RPM: {rpm.value}")
    print(f"Speed: {speed.value}")
    print(f"Engine temperature: {temp.value}")
    
    # Change throttle position (gas pedal)
    simulator.set_throttle(50)  # 50%
    
    # Wait briefly then read values again
    import time
    time.sleep(2)
    
    rpm = simulator.query(OBDCommand.RPM)
    speed = simulator.query(OBDCommand.SPEED)
    
    print(f"After acceleration:")
    print(f"RPM: {rpm.value}")
    print(f"Speed: {speed.value}")
    
    # Close connection
    simulator.close()
    
if __name__ == "__main__":
    main()