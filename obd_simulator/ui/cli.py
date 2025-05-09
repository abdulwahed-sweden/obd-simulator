# File: obd_simulator/ui/cli.py
"""
Command-line interface for the OBD-II simulator.
"""

import argparse
import sys
import time
import logging
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description='OBD-II Simulator CLI')
    subparsers = parser.add_subparsers(dest='command', help='Simulator commands')
    
    # Mock Simulator
    mock_parser = subparsers.add_parser('mock', help='Run the mock simulator')
    mock_parser.add_argument('--dashboard', action='store_true', help='Show dashboard')
    mock_parser.add_argument('--duration', type=float, help='Simulation duration in seconds')
    mock_parser.add_argument('--interval', type=float, default=1.0, help='Update interval in seconds')
    mock_parser.add_argument('--scenario', choices=['idle', 'city', 'highway'], default='idle',
                           help='Driving scenario to simulate')
    mock_parser.add_argument('--profile', choices=['sedan', 'sports_car', 'truck', 'electric'],
                           help='Vehicle profile to use')
    
    # Virtual COM Simulator
    virtual_parser = subparsers.add_parser('virtual-com', help='Run the virtual COM port simulator')
    virtual_parser.add_argument('--port', required=True, help='Serial port to use')
    virtual_parser.add_argument('--baudrate', type=int, default=38400, help='Baudrate')
    
    # Log Playback
    log_parser = subparsers.add_parser('log-player', help='Run the log playback simulator')
    log_parser.add_argument('--file', required=True, help='Log file to play')
    log_parser.add_argument('--loop', action='store_true', help='Loop the log file')
    log_parser.add_argument('--speed', type=float, default=1.0, help='Playback speed multiplier')
    
    # Log Generator
    gen_parser = subparsers.add_parser('generate-log', help='Generate a sample log file')
    gen_parser.add_argument('--output', required=True, help='Output file path')
    gen_parser.add_argument('--entries', type=int, default=100, help='Number of log entries')
    gen_parser.add_argument('--scenario', choices=['idle', 'city', 'highway'], default='city',
                          help='Driving scenario to simulate')
    
    # Auto-Detector
    detect_parser = subparsers.add_parser('detect-ports', help='Detect OBD-II ports')
    detect_parser.add_argument('--test', action='store_true', help='Test connection to detected ports')
    
    # Setup Virtual Ports
    vport_parser = subparsers.add_parser('setup-virtual-ports', help='Set up virtual serial port pair')
    
    return parser.parse_args()

def run_mock_simulator(args):
    """Run the mock simulator"""
    from obd_simulator.mock_simulator.simulator import Simulator
    from obd_simulator.mock_simulator.virtual_car import VirtualCar
    from obd_simulator.mock_simulator.vehicle_parameters import get_vehicle_profile
    
    # Create a custom car if profile specified
    car = None
    if args.profile:
        profile = get_vehicle_profile(args.profile)
        if profile:
            car = VirtualCar(**profile)
            print(f"Using {args.profile} vehicle profile")
    
    # Create and connect to simulator
    simulator = Simulator(car=car)
    simulator.connect()
    
    print(f"Simulator status: {simulator.status()}")
    
    # Show dashboard if requested
    if args.dashboard:
        from obd_simulator.ui.dashboard import Dashboard
        dashboard = Dashboard(simulator)
        dashboard.run()
        return
    
    # Run a driving scenario if specified
    if args.scenario != 'idle':
        run_driving_scenario(simulator, args.scenario)
    
    # Run simulator loop
    try:
        start_time = time.time()
        interval = args.interval or 1.0
        duration = args.duration
        
        # Print header
        print("\n" + "-"*50)
        print(f"{'Parameter':<20} {'Value':>10} {'Units':<10}")
        print("-"*50)
        
        counter = 0
        while True:
            counter += 1
            # Check if we've reached the duration limit
            if duration and time.time() - start_time >= duration:
                print(f"\nSimulation complete ({duration}s)")
                break
                
            # Print header every 10 iterations
            if counter % 10 == 1:
                print("\n" + "-"*50)
                print(f"{'Parameter':<20} {'Value':>10} {'Units':<10}")
                print("-"*50)
                
            # Query all commands
            for cmd in simulator.supported_commands:
                response = simulator.query(cmd)
                if not response.is_null():
                    value = response.value.magnitude
                    unit = response.value.units
                    print(f"{cmd.name:<20} {value:>10.2f} {unit:<10}")
                
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\nSimulation stopped by user")
    finally:
        simulator.close()
        print("Simulator closed")

def run_driving_scenario(simulator, scenario):
    """Run a driving scenario on the simulator"""
    import threading
    
    def _city_driving():
        """City driving scenario: stop and go traffic"""
        while simulator.is_connected():
            # Idle at traffic light
            simulator.set_throttle(0)
            time.sleep(5)
            
            # Accelerate
            for throttle in range(0, 40, 5):
                if not simulator.is_connected():
                    break
                simulator.set_throttle(throttle)
                time.sleep(1)
                
            # Cruise
            simulator.set_throttle(20)
            time.sleep(10)
            
            # Slow down for traffic
            simulator.set_throttle(5)
            time.sleep(3)
            
            # Speed up again
            simulator.set_throttle(30)
            time.sleep(8)
            
            # Stop at next light
            simulator.set_throttle(0)
            time.sleep(5)
    
    def _highway_driving():
        """Highway driving scenario: higher speeds, less variation"""
        # Accelerate onto highway
        for throttle in range(0, 70, 10):
            if not simulator.is_connected():
                break
            simulator.set_throttle(throttle)
            time.sleep(1)
            
        # Highway cruising
        simulator.set_throttle(50)
        time.sleep(20)
        
        # Pass another vehicle
        simulator.set_throttle(70)
        time.sleep(5)
        
        # Back to cruising
        simulator.set_throttle(50)
        time.sleep(15)
        
        # Slow for exit
        for throttle in range(50, 0, -10):
            if not simulator.is_connected():
                break
            simulator.set_throttle(throttle)
            time.sleep(1)
            
        # Exit ramp
        simulator.set_throttle(20)
        time.sleep(5)
        
        # Stop at light
        simulator.set_throttle(0)
    
    # Start the appropriate scenario
    if scenario == 'city':
        thread = threading.Thread(target=_city_driving)
    elif scenario == 'highway':
        thread = threading.Thread(target=_highway_driving)
    else:
        return
        
    thread.daemon = True
    thread.start()
    
    print(f"Running {scenario} driving scenario...")

def run_virtual_com_simulator(args):
    """Run the virtual COM port simulator"""
    try:
        from obd_simulator.virtual_com.elm327_device import ELM327Device
    except ImportError:
        print("Error: Virtual COM port simulator not available.")
        print("Please install the required dependencies:")
        print("pip install pyserial")
        return
    
    print(f"Starting virtual COM port simulator on {args.port}...")
    
    try:
        # Create and start the virtual device
        device = ELM327Device(port=args.port, baudrate=args.baudrate)
        device.start()
        
        print(f"Virtual OBD-II device running on {args.port}")
        print("Connect your OBD software to this port.")
        print("Press Ctrl+C to stop")
        
        # Keep the script running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping simulator...")
    finally:
        if 'device' in locals():
            device.close()
        print("Simulator stopped")

def run_log_playback(args):
    """Run the log playback simulator"""
    try:
        from obd_simulator.log_playback.log_player import LogPlayer
    except ImportError:
        print("Error: Log playback simulator not available.")
        print("Please install the required dependencies:")
        print("pip install pandas")
        return
    
    print(f"Starting log playback from {args.file}...")
    
    try:
        # Create and connect to log player
        player = LogPlayer(
            log_file=args.file,
            loop=args.loop,
            speed=args.speed
        )
        
        if not player.connect():
            print(f"Error: Failed to load log file {args.file}")
            return
            
        print(f"Log playback started with speed {args.speed}x")
        
        # Run playback loop
        interval = 1.0
        
        # Print header
        print("\n" + "-"*50)
        print(f"{'Parameter':<20} {'Value':>10} {'Units':<10}")
        print("-"*50)
        
        counter = 0
        try:
            while True:
                counter += 1
                # Print header every 10 iterations
                if counter % 10 == 1:
                    print("\n" + "-"*50)
                    print(f"{'Parameter':<20} {'Value':>10} {'Units':<10}")
                    print("-"*50)
                    
                # Query all commands
                for cmd in player.supported_commands:
                    response = player.query(cmd)
                    if not response.is_null():
                        value = response.value.magnitude
                        unit = response.value.units
                        print(f"{cmd.name:<20} {value:>10.2f} {unit:<10}")
                    
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nPlayback stopped by user")
            
    finally:
        if 'player' in locals():
            player.close()
        print("Playback stopped")

def generate_log_file(args):
    """Generate a sample log file"""
    try:
        from obd_simulator.log_playback.log_generator import generate_log_file
    except ImportError:
        print("Error: Log generator not available.")
        print("Please install the required dependencies:")
        print("pip install pandas")
        return
    
    print(f"Generating sample log file: {args.output}")
    
    try:
        generate_log_file(
            output_file=args.output,
            num_entries=args.entries,
            scenario=args.scenario
        )
        print(f"Log file generated successfully with {args.entries} entries")
        
    except Exception as e:
        print(f"Error generating log file: {e}")

def detect_ports(args):
    """Detect OBD-II ports"""
    try:
        from obd_simulator.port_detector.auto_detect import OBDPortDetector
    except ImportError:
        print("Error: Port detector not available.")
        print("Please install the required dependencies:")
        print("pip install pyserial")
        return
    
    print("Detecting OBD-II ports...")
    
    detector = OBDPortDetector()
    ports = detector.detect_ports(test_connection=args.test)
    
    if not ports:
        print("No OBD-II ports detected")
        return
        
    print(f"Found {len(ports)} potential OBD-II port(s):")
    
    for i, port in enumerate(ports, 1):
        device = port['device']
        desc = port.get('description', '')
        adapter = port.get('adapter_type', 'Unknown')
        
        connection_status = ""
        if port.get('connection_tested', False):
            if port.get('connection_successful', False):
                connection_status = " [Connection successful]"
            else:
                connection_status = " [Connection failed]"
                
        print(f"{i}. {device} - {adapter} ({desc}){connection_status}")
        
    # Show recommendation
    recommended = detector.get_recommended_port()
    if recommended:
        print(f"\nRecommended port: {recommended}")
        
    # Show suggestions for using the ports
    print("\nTo use a port with the simulator:")
    print("  Mock simulator:      obd-simulator mock")
    print("  Virtual COM:         obd-simulator virtual-com --port [PORT]")
    print("  Log player:          obd-simulator log-player --file [LOG_FILE]")

def setup_virtual_ports(args):
    """Set up virtual serial port pair"""
    try:
        from obd_simulator.port_detector.port_validator import setup_virtual_port_pair
    except ImportError:
        print("Error: Virtual port setup not available.")
        print("Please install the required dependencies:")
        print("pip install pyserial")
        return
    
    print("Setting up virtual serial port pair...")
    
    port1, port2 = setup_virtual_port_pair()
    
    if port1 and port2:
        print(f"Virtual port pair created: {port1} <-> {port2}")
        print("\nTo use these ports:")
        print(f"  1. Run virtual-com simulator on one port: obd-simulator virtual-com --port {port1}")
        print(f"  2. Connect your OBD-II software to the other port: {port2}")
    else:
        print("Failed to create virtual port pair")
        
        # Show installation instructions based on platform
        import platform
        system = platform.system()
        
        if system == "Windows":
            print("\nTo set up virtual COM ports on Windows:")
            print("  1. Download and install com0com: https://sourceforge.net/projects/com0com/")
            print("  2. Run the com0com setup utility to create port pairs")
        elif system == "Linux":
            print("\nTo set up virtual COM ports on Linux:")
            print("  1. Install socat: sudo apt-get install socat")
            print("  2. Create a port pair: socat -d -d pty,raw,echo=0 pty,raw,echo=0")
        elif system == "Darwin":  # macOS
            print("\nTo set up virtual COM ports on macOS:")
            print("  1. Install socat: brew install socat")
            print("  2. Create a port pair: socat -d -d pty,raw,echo=0 pty,raw,echo=0")

def main():
    """Main entry point for the CLI"""
    args = parse_args()
    
    if args.command == 'mock':
        run_mock_simulator(args)
    elif args.command == 'virtual-com':
        run_virtual_com_simulator(args)
    elif args.command == 'log-player':
        run_log_playback(args)
    elif args.command == 'generate-log':
        generate_log_file(args)
    elif args.command == 'detect-ports':
        detect_ports(args)
    elif args.command == 'setup-virtual-ports':
        setup_virtual_ports(args)
    else:
        print("Please specify a valid command. Use -h for help.")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
