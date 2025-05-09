# File: obd_simulator/port_detector/port_validator.py
"""
Validation for OBD-II adapter ports.
"""

import time
import logging
from typing import Dict, Any, Tuple, Optional, List

logger = logging.getLogger(__name__)

class PortValidator:
    """
    Validator for OBD-II adapter ports.
    
    This class provides methods to validate if a port is a valid OBD-II adapter
    and determine its capabilities.
    """
    
    def __init__(self, port: str, baudrate: int = 38400):
        """
        Initialize the port validator.
        
        Args:
            port: Port to validate
            baudrate: Baud rate to use
        """
        self.port = port
        self.baudrate = baudrate
        self.valid = False
        self.adapter_info = {}
        
    def validate(self) -> bool:
        """
        Validate if the port is a valid OBD-II adapter.
        
        Returns:
            bool: True if port is a valid OBD-II adapter, False otherwise
        """
        try:
            import serial
            
            try:
                # Try to open the serial port
                ser = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    bytesize=8,
                    parity='N',
                    stopbits=1,
                    timeout=1
                )
                
                # Basic validation tests
                tests = [
                    self._test_basic_commands,
                    self._test_protocol_support,
                    self._test_pid_support
                ]
                
                # Run tests
                self.adapter_info = {}
                for test in tests:
                    test_result = test(ser)
                    if test_result:
                        self.adapter_info.update(test_result)
                    else:
                        # Test failed
                        ser.close()
                        return False
                        
                # All tests passed
                ser.close()
                self.valid = True
                return True
                
            except (serial.SerialException, OSError) as e:
                logger.error(f"Serial error: {e}")
                return False
                
        except ImportError:
            logger.error("pyserial not installed. Please install it using: pip install pyserial")
            return False
            
    def _test_basic_commands(self, ser) -> Optional[Dict[str, Any]]:
        """
        Test basic ELM327 commands.
        
        Args:
            ser: Serial connection
            
        Returns:
            Optional[Dict[str, Any]]: Test results or None if failed
        """
        # Reset
        if not self._send_command(ser, b"ATZ"):
            return None
            
        # Get version
        response = self._send_command(ser, b"ATI")
        if not response:
            return None
            
        # Parse version
        version = response.decode('ascii', errors='ignore').strip()
        
        # Echo off
        if not self._send_command(ser, b"ATE0"):
            return None
            
        # Get voltage
        response = self._send_command(ser, b"ATRV")
        if not response:
            return None
            
        # Parse voltage
        voltage = response.decode('ascii', errors='ignore').strip()
        
        return {
            'version': version,
            'voltage': voltage
        }
        
    def _test_protocol_support(self, ser) -> Optional[Dict[str, Any]]:
        """
        Test protocol support.
        
        Args:
            ser: Serial connection
            
        Returns:
            Optional[Dict[str, Any]]: Test results or None if failed
        """
        # Get protocol
        response = self._send_command(ser, b"ATDP")
        if not response:
            return None
            
        # Parse protocol
        protocol = response.decode('ascii', errors='ignore').strip()
        
        # Get supported protocols
        response = self._send_command(ser, b"ATSP0")
        if not response:
            return None
            
        return {
            'protocol': protocol
        }
        
    def _test_pid_support(self, ser) -> Optional[Dict[str, Any]]:
        """
        Test PID support.
        
        Args:
            ser: Serial connection
            
        Returns:
            Optional[Dict[str, Any]]: Test results or None if failed
        """
        # Get supported PIDs
        response = self._send_command(ser, b"0100")
        if not response:
            # No real car connected, but adapter might still be valid
            return {'pid_support': False}
            
        # Try a few common PIDs
        rpm_response = self._send_command(ser, b"010C")
        speed_response = self._send_command(ser, b"010D")
        
        return {
            'pid_support': True,
            'rpm_supported': rpm_response is not None,
            'speed_supported': speed_response is not None
        }
        
    def _send_command(self, ser, command: bytes) -> Optional[bytes]:
        """
        Send a command to the adapter and get the response.
        
        Args:
            ser: Serial connection
            command: Command to send
            
        Returns:
            Optional[bytes]: Response or None if failed
        """
        try:
            # Clear input buffer
            ser.flushInput()
            
            # Send command
            ser.write(command + b"\r")
            
            # Wait for response
            time.sleep(0.1)
            
            # Read response
            response = b""
            start_time = time.time()
            while time.time() - start_time < 2:  # 2 second timeout
                if ser.in_waiting:
                    response += ser.read(ser.in_waiting)
                    if b">" in response:  # ELM prompt
                        break
                time.sleep(0.1)
                
            # Check for success
            if b"OK" in response or b"ELM" in response or b">" in response:
                return response
            else:
                return None
                
        except Exception as e:
            logger.error(f"Command error: {e}")
            return None
            
    def get_adapter_info(self) -> Dict[str, Any]:
        """
        Get adapter information.
        
        Returns:
            Dict[str, Any]: Adapter information
        """
        if not self.valid:
            self.validate()
            
        return self.adapter_info

def check_virtual_ports() -> List[str]:
    """
    Check if virtual serial ports are available.
    
    Returns:
        List[str]: List of detected virtual ports
    """
    import platform
    system = platform.system()
    virtual_ports = []
    
    try:
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        
        for port in ports:
            if system == "Windows":
                # Check for com0com or virtual serial port emulator
                if "virtual" in port.description.lower() or \
                   "com0com" in port.description.lower() or \
                   "vsp" in port.description.lower():
                    virtual_ports.append(port.device)
            elif system == "Linux":
                # Check for socat or tty0tty
                if port.device.startswith("/dev/pts/") or \
                   port.device.startswith("/dev/tnt"):
                    virtual_ports.append(port.device)
            elif system == "Darwin":  # macOS
                # Check for socat
                if "usbmodem" in port.device and "tty." in port.device:
                    virtual_ports.append(port.device)
                    
        return virtual_ports
        
    except ImportError:
        logger.error("pyserial not installed. Please install it using: pip install pyserial")
        return []

def setup_virtual_port_pair() -> Tuple[Optional[str], Optional[str]]:
    """
    Set up a virtual serial port pair.
    
    Returns:
        Tuple[Optional[str], Optional[str]]: Pair of virtual ports or None if failed
    """
    import platform
    system = platform.system()
    
    if system == "Windows":
        # Try to use com0com
        return _setup_com0com()
    elif system == "Linux":
        # Try to use socat
        return _setup_socat_linux()
    elif system == "Darwin":  # macOS
        # Try to use socat
        return _setup_socat_macos()
    else:
        logger.error(f"Unsupported platform: {system}")
        return None, None
        
def _setup_com0com() -> Tuple[Optional[str], Optional[str]]:
    """
    Set up a virtual serial port pair using com0com on Windows.
    
    Returns:
        Tuple[Optional[str], Optional[str]]: Pair of virtual ports or None if failed
    """
    import subprocess
    import re
    
    try:
        # Check if com0com is installed
        subprocess.run(
            ["sc", "query", "com0com"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # List ports to find existing pairs
        result = subprocess.run(
            ["com0com", "--list"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        output = result.stdout.decode("utf-8")
        
        # Check if there's already a pair
        match = re.search(r"COM(\d+)\s+?-\s+?COM(\d+)", output)
        if match:
            port1 = f"COM{match.group(1)}"
            port2 = f"COM{match.group(2)}"
            logger.info(f"Found existing virtual port pair: {port1} - {port2}")
            return port1, port2
            
        # Create a new pair
        result = subprocess.run(
            ["com0com", "--install", "0", "1"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # List ports again to find the new pair
        result = subprocess.run(
            ["com0com", "--list"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        output = result.stdout.decode("utf-8")
        
        # Find the pair
        match = re.search(r"COM(\d+)\s+?-\s+?COM(\d+)", output)
        if match:
            port1 = f"COM{match.group(1)}"
            port2 = f"COM{match.group(2)}"
            logger.info(f"Created virtual port pair: {port1} - {port2}")
            return port1, port2
            
        logger.error("Failed to create virtual port pair")
        return None, None
        
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        logger.error(f"com0com error: {e}")
        logger.info("Please install com0com: https://sourceforge.net/projects/com0com/")
        return None, None
        
def _setup_socat_linux() -> Tuple[Optional[str], Optional[str]]:
    """
    Set up a virtual serial port pair using socat on Linux.
    
    Returns:
        Tuple[Optional[str], Optional[str]]: Pair of virtual ports or None if failed
    """
    import subprocess
    import os
    
    try:
        # Create a pair of PTYs
        process = subprocess.Popen(
            ["socat", "-d", "-d", "pty,raw,echo=0", "pty,raw,echo=0"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for socat to create the PTYs
        time.sleep(1)
        
        # Get the PTY names from stderr
        stderr = process.stderr.read(1024).decode("utf-8")
        
        # Extract the PTY names
        import re
        match = re.search(r"N PTY is ([^\s]+).*N PTY is ([^\s]+)", stderr, re.DOTALL)
        if match:
            port1 = match.group(1)
            port2 = match.group(2)
            logger.info(f"Created virtual port pair: {port1} - {port2}")
            return port1, port2
            
        logger.error("Failed to create virtual port pair")
        return None, None
        
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        logger.error(f"socat error: {e}")
        logger.info("Please install socat: sudo apt-get install socat")
        return None, None
        
def _setup_socat_macos() -> Tuple[Optional[str], Optional[str]]:
    """
    Set up a virtual serial port pair using socat on macOS.
    
    Returns:
        Tuple[Optional[str], Optional[str]]: Pair of virtual ports or None if failed
    """
    # macOS uses the same approach as Linux
    return _setup_socat_linux()