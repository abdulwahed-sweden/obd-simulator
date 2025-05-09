
# File: obd_simulator/port_detector/auto_detect.py
"""
Auto-detection for OBD-II adapters.
"""

import time
import logging
import platform
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def list_available_ports() -> List[str]:
    """
    List all available serial ports.
    
    Returns:
        List[str]: List of available ports
    """
    try:
        import serial.tools.list_ports
        return [port.device for port in serial.tools.list_ports.comports()]
    except ImportError:
        logger.error("pyserial not installed. Please install it using: pip install pyserial")
        return []
        
def get_port_details() -> List[Dict[str, Any]]:
    """
    Get detailed information about available ports.
    
    Returns:
        List[Dict[str, Any]]: List of port details
    """
    try:
        import serial.tools.list_ports
        ports = []
        
        for port in serial.tools.list_ports.comports():
            ports.append({
                'device': port.device,
                'name': port.name,
                'description': port.description,
                'hwid': port.hwid,
                'vid': port.vid,
                'pid': port.pid,
                'serial_number': port.serial_number,
                'location': port.location,
                'manufacturer': port.manufacturer,
                'product': port.product,
                'interface': port.interface
            })
            
        return ports
    except ImportError:
        logger.error("pyserial not installed. Please install it using: pip install pyserial")
        return []

class OBDPortDetector:
    """
    Detector for OBD-II adapter ports.
    
    This class provides methods to detect and validate OBD-II adapters
    connected to the system.
    """
    
    def __init__(self):
        """Initialize the OBD port detector."""
        self.known_adapters = [
            {'name': 'ELM327', 'keywords': ['elm327', 'obd', 'usb', 'bluetooth']},
            {'name': 'STN', 'keywords': ['stn', 'obdlink']},
            {'name': 'Kiwi', 'keywords': ['kiwi', 'plx']},
            {'name': 'OBDPro', 'keywords': ['obdpro']},
            {'name': 'Scan Tool', 'keywords': ['scantool', 'scan tool']},
            {'name': 'OBDII', 'keywords': ['obdii', 'obd-ii', 'obd2']},
            {'name': 'FTDI', 'keywords': ['ftdi', 'ft232']},
            {'name': 'CH340', 'keywords': ['ch340', 'ch341']}
        ]
        
    def detect_ports(self, test_connection: bool = False) -> List[Dict[str, Any]]:
        """
        Detect OBD-II adapter ports.
        
        Args:
            test_connection: Whether to test the connection to each port
            
        Returns:
            List[Dict[str, Any]]: List of detected OBD-II ports
        """
        all_ports = get_port_details()
        obd_ports = []
        
        for port in all_ports:
            # Check description and other fields for known adapter keywords
            port_info = port.get('description', '').lower() + ' ' + \
                       port.get('manufacturer', '').lower() + ' ' + \
                       port.get('product', '').lower()
                       
            for adapter in self.known_adapters:
                if any(keyword in port_info for keyword in adapter['keywords']):
                    port['adapter_type'] = adapter['name']
                    port['is_obd'] = True
                    port['connection_tested'] = False
                    port['connection_successful'] = False
                    obd_ports.append(port)
                    break
            else:
                # Check if it's a Bluetooth device (many OBD adapters use Bluetooth)
                if 'bluetooth' in port_info.lower():
                    port['adapter_type'] = 'Unknown Bluetooth'
                    port['is_obd'] = True
                    port['connection_tested'] = False
                    port['connection_successful'] = False
                    obd_ports.append(port)
                    
        # Test connections if requested
        if test_connection and obd_ports:
            for port in obd_ports:
                port['connection_tested'] = True
                port['connection_successful'] = self._test_obd_connection(port['device'])
                
        return obd_ports
        
    def _test_obd_connection(self, port: str) -> bool:
        """
        Test if a port is a valid OBD-II adapter.
        
        Args:
            port: Port to test
            
        Returns:
            bool: True if port is a valid OBD-II adapter, False otherwise
        """
        try:
            import serial
            
            # Common baud rates for OBD-II adapters
            baudrates = [38400, 9600, 115200, 57600]
            
            for baudrate in baudrates:
                try:
                    # Try to open the serial port
                    ser = serial.Serial(
                        port=port,
                        baudrate=baudrate,
                        bytesize=8,
                        parity='N',
                        stopbits=1,
                        timeout=1
                    )
                    
                    # Send ATZ (reset) command
                    ser.write(b"ATZ\r")
                    time.sleep(1)
                    
                    # Read response
                    response = ser.read(100)
                    
                    # Close port
                    ser.close()
                    
                    # Check if response contains ELM or similar
                    if b'ELM' in response or b'STN' in response or b'OBD' in response:
                        logger.info(f"Valid OBD-II adapter found on {port} at {baudrate} baud")
                        return True
                        
                except (serial.SerialException, OSError):
                    continue
                    
            return False
            
        except ImportError:
            logger.error("pyserial not installed. Please install it using: pip install pyserial")
            return False
            
    def get_recommended_port(self) -> Optional[str]:
        """
        Get the recommended OBD-II port.
        
        Returns:
            Optional[str]: Recommended port or None if not found
        """
        ports = self.detect_ports(test_connection=True)
        
        # First, try ports with successful connection test
        for port in ports:
            if port['connection_tested'] and port['connection_successful']:
                return port['device']
                
        # Then, try known OBD-II adapters
        for port in ports:
            if port['is_obd']:
                return port['device']
                
        # No suitable port found
        return None
        
    def get_port_suggestions(self) -> List[Dict[str, Any]]:
        """
        Get a list of suggested OBD-II ports with confidence levels.
        
        Returns:
            List[Dict[str, Any]]: List of suggested ports
        """
        ports = self.detect_ports(test_connection=False)
        suggestions = []
        
        for port in ports:
            confidence = 0
            
            # Increase confidence for known adapters
            if port['adapter_type'] != 'Unknown Bluetooth':
                confidence += 50
                
            # Check description for more clues
            description = port.get('description', '').lower()
            if 'elm' in description:
                confidence += 20
            if 'obd' in description:
                confidence += 20
            if 'can' in description:
                confidence += 10
                
            # Add to suggestions
            suggestions.append({
                'device': port['device'],
                'description': port.get('description', ''),
                'adapter_type': port['adapter_type'],
                'confidence': min(100, confidence)
            })
            
        # Sort by confidence (highest first)
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        
        return suggestions
