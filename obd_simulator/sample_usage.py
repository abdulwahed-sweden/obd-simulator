# File: sample_usage.py
"""
Sample script demonstrating OBD-II simulator usage.
"""

import time
import logging
import argparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def mock_simulator_demo():
    """Demonstrate the mock simulator"""
    from obd_simulator.mock_simulator.simulator import Simulator
    from obd_simulator.common.obd_command import OBDCommand
    
    print("=== Mock OBD-II Simulator Demo ===")
    
    # Create and connect to simulator
    simulator = Simulator()
    simulator.connect()
    
    print(f"Simulator status: {simulator.status()}")
    print(f"Supported commands: {len(simulator.supported_commands)}")
    
    # Initial readings
    print("\nInitial readings:")
    for cmd in simulator.supported_commands:
        response = simulator.query(cmd)
        if not response.is_null():
            print(f"{cmd.name}: {response.value}")
    
    # Run a simple driving scenario
    print("\nStarting engine and accelerating...")
    simulator.set_throttle(30)  # 30% throttle
    
    # Monitor for a few seconds
    for i in range(5):
        time.sleep(1)
        
        rpm = simulator.query(OBDCommand.RPM)
        speed = simulator.query(OBDCommand.SPEED)
        
        print(f"Second {i+1}: RPM = {rpm.value.magnitude:.1f} rpm, "
              f"Speed = {speed.value.magnitude:.1f} km/h")
    
    # Accelerate harder
    print("\nAccelerating harder...")
    simulator.set_throttle(70)  # 70% throttle
    
    # Monitor for a few more seconds
    for i in range(5):
        time.sleep(1)
        
        rpm = simulator.query(OBDCommand.RPM)
        speed = simulator.query(OBDCommand.SPEED)
        temp = simulator.query(OBDCommand.COOLANT_TEMP)
        
        print(f"Second {i+1}: RPM = {rpm.value.magnitude:.1f} rpm, "
              f"Speed = {speed.value.magnitude:.1f} km/h, "
              f"Temp = {temp.value.magnitude:.1f}°C")
    
    # Stop the engine
    print("\nStopping engine...")
    simulator.car.stop_engine()
    
    # Final readings
    print("\nFinal readings:")
    for cmd in simulator.supported_commands:
        response = simulator.query(cmd)
        if not response.is_null():
            print(f"{cmd.name}: {response.value}")
    
    # Close the connection
    simulator.close()
    print("\nSimulator closed")

def virtual_car_custom_demo():
    """Demonstrate a custom virtual car"""
    from obd_simulator.mock_simulator.simulator import Simulator
    from obd_simulator.mock_simulator.virtual_car import VirtualCar
    from obd_simulator.common.obd_command import OBDCommand
    
    print("=== Custom Virtual Car Demo ===")
    
    # Create a custom sports car
    sports_car = VirtualCar(
        idle_rpm=900,
        redline_rpm=8500,
        max_speed=250,
        rpm_per_throttle=70,
        normal_coolant_temp=95
    )
    
    # Create simulator with the custom car
    simulator = Simulator(car=sports_car)
    simulator.connect()
    
    print(f"Custom sports car simulator status: {simulator.status()}")
    
    # Run a quick acceleration test
    print("\nRunning acceleration test...")
    simulator.set_throttle(100)  # Full throttle
    
    # Monitor for a few seconds
    for i in range(10):
        time.sleep(0.5)
        
        rpm = simulator.query(OBDCommand.RPM)
        speed = simulator.query(OBDCommand.SPEED)
        
        print(f"Time {i*0.5:.1f}s: RPM = {rpm.value.magnitude:.1f} rpm, "
              f"Speed = {speed.value.magnitude:.1f} km/h")
    
    # Close the connection
    simulator.close()
    print("\nCustom car simulator closed")

def virtual_com_demo():
    """Demonstrate the virtual COM port simulator"""
    import threading
    from obd_simulator.virtual_com.elm327_device import ELM327Device
    
    print("=== Virtual COM Port Simulator Demo ===")
    
    # Try to set up virtual port pair
    from obd_simulator.port_detector.port_validator import setup_virtual_port_pair
    port1, port2 = setup_virtual_port_pair()
    
    if not port1 or not port2:
        print("Failed to set up virtual port pair.")
        print("Please specify a port to use:")
        port = input("Port: ")
    else:
        print(f"Virtual port pair created: {port1} <-> {port2}")
        port = port1
    
    print(f"\nStarting virtual COM port simulator on {port}...")
    
    # Create and start the virtual device
    device = ELM327Device(port=port)
    
    if device.start():
        print(f"Virtual OBD-II device running on {port}")
        print(f"Connect your OBD software to {port2 if port2 else 'this port'}.")
        print("Press Enter to stop")
        
        # Create a thread to run a driving scenario
        def driving_scenario():
            """Run a simple driving scenario"""
            print("\nRunning driving scenario...")
            
            # Start idle
            time.sleep(5)
            
            # Accelerate
            for throttle in range(0, 70, 10):
                device.set_throttle(throttle)
                time.sleep(1)
                
            # Cruise
            device.set_throttle(50)
            time.sleep(10)
            
            # Slow down
            for throttle in range(50, 0, -10):
                device.set_throttle(throttle)
                time.sleep(1)
                
            # Stop
            device.set_throttle(0)
            print("\nDriving scenario completed")
            
        # Start the driving scenario thread
        scenario_thread = threading.Thread(target=driving_scenario)
        scenario_thread.daemon = True
        scenario_thread.start()
        
        # Wait for user to press Enter
        input()
        
        # Close the device
        device.close()
        print("Virtual COM port simulator stopped")
    else:
        print(f"Failed to start virtual COM port simulator on {port}")

def log_playback_demo():
    """Demonstrate the log playback simulator"""
    from obd_simulator.log_playback.log_player import LogPlayer
    
    print("=== Log Playback Simulator Demo ===")
    
    # Generate a sample log file
    from obd_simulator.log_playback.log_generator import generate_log_file
    log_file = "sample_drive.csv"
    
    print(f"Generating sample log file: {log_file}...")
    generate_log_file(log_file, num_entries=300, scenario='highway')
    
    print(f"\nStarting log playback from {log_file}...")
    
    # Create and connect to log player
    player = LogPlayer(
        log_file=log_file,
        loop=True,
        speed=2.0  # 2x speed
    )
    
    if player.connect():
        print(f"Log playback started with speed 2.0x")
        print(f"Supported commands: {[cmd.name for cmd in player.supported_commands]}")
        
        # Monitor for a few iterations
        print("\nPlayback data:")
        for i in range(20):
            time.sleep(0.5)  # 0.5 second intervals (1 second in log at 2x speed)
            
            # Query each command
            values = {}
            for cmd in player.supported_commands:
                response = player.query(cmd)
                if not response.is_null():
                    values[cmd.name] = response.value
                    
            # Print the values
            print(f"Time {i*0.5:.1f}s: ", end="")
            for name, value in values.items():
                print(f"{name}={value.magnitude:.1f} {value.units}, ", end="")
            print()
            
        # Close the connection
        player.close()
        print("\nLog playback stopped")
    else:
        print(f"Failed to load log file {log_file}")

def dashboard_demo():
    """Demonstrate the dashboard"""
    from obd_simulator.mock_simulator.simulator import Simulator
    from obd_simulator.ui.dashboard import Dashboard
    
    print("=== Dashboard Demo ===")
    
    # Create and connect to simulator
    simulator = Simulator()
    simulator.connect()
    
    print(f"Simulator status: {simulator.status()}")
    print("Opening dashboard...")
    
    # Create a thread to run a driving scenario
    import threading
    
    def driving_scenario():
        """Run a simple driving scenario"""
        print("\nRunning driving scenario...")
        
        # Start idle
        time.sleep(5)
        
        # Accelerate
        for throttle in range(0, 70, 10):
            simulator.set_throttle(throttle)
            time.sleep(1)
            
        # Cruise
        simulator.set_throttle(50)
        time.sleep(10)
        
        # Slow down
        for throttle in range(50, 0, -10):
            simulator.set_throttle(throttle)
            time.sleep(1)
            
        # Stop
        simulator.set_throttle(0)
        print("\nDriving scenario completed")
        
    # Start the driving scenario thread
    scenario_thread = threading.Thread(target=driving_scenario)
    scenario_thread.daemon = True
    scenario_thread.start()
    
    # Create and run dashboard
    dashboard = Dashboard(simulator)
    dashboard.run()
    
    # Close the connection
    simulator.close()
    print("\nDashboard closed")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='OBD-II Simulator Sample')
    parser.add_argument('--demo', choices=['mock', 'custom', 'virtual-com', 'log-playback', 'dashboard'],
                      default='mock', help='Which demo to run')
    args = parser.parse_args()
    
    if args.demo == 'mock':
        mock_simulator_demo()
    elif args.demo == 'custom':
        virtual_car_custom_demo()
    elif args.demo == 'virtual-com':
        virtual_com_demo()
    elif args.demo == 'log-playback':
        log_playback_demo()
    elif args.demo == 'dashboard':
        dashboard_demo()
    else:
        print(f"Unknown demo: {args.demo}")
        return 1
    
    return 0

if __name__ == "__main__":
    main()