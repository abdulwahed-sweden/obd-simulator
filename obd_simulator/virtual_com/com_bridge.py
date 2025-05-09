# File: obd_simulator/virtual_com/com_bridge.py
"""
COM port bridging for virtual serial port communication.
"""

import os
import subprocess
import platform
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

def setup_virtual_com_pair() -> Tuple[Optional[str], Optional[str]]:
    """
    Set up a virtual COM port pair.
    
    Returns:
        Tuple[Optional[str], Optional[str]]: Pair of COM ports or None if failed
    """
    system = platform.system()
    
    if system == "Windows":
        return _setup_com0com()
    elif system == "Linux":
        return _setup_socat()
    elif system == "Darwin":  # macOS
        return _setup_socat()
    else:
        logger.error(f"Unsupported platform: {system}")
        return None, None
        
def _setup_com0com() -> Tuple[Optional[str], Optional[str]]:
    """
    Set up a virtual COM port pair using com0com on Windows.
    
    Returns:
        Tuple[Optional[str], Optional[str]]: Pair of COM ports or None if failed
    """
    logger.info("Setting up com0com virtual port pair")
    
    try:
        # Check if com0com is installed
        subprocess.run(
            ["sc", "query", "com0com"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Find existing port pairs
        result = subprocess.run(
            ["com0com", "--list"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        output = result.stdout.decode("utf-8")
        
        # Look for CNCA0 <-> CNCB0 pair in output
        if "CNCA0" in output and "CNCB0" in output:
            # Get COM port numbers
            lines = output.split("\n")
            port_a = None
            port_b = None
            
            for line in lines:
                if "CNCA0" in line and "COM" in line:
                    port_a = line.split("COM")[1].split()[0]
                    port_a = f"COM{port_a}"
                if "CNCB0" in line and "COM" in line:
                    port_b = line.split("COM")[1].split()[0]
                    port_b = f"COM{port_b}"
                    
            if port_a and port_b:
                logger.info(f"Found existing port pair: {port_a} <-> {port_b}")
                return port_a, port_b
                
        # Create a new port pair
        subprocess.run(
            ["com0com", "--create", "CNCA0", "CNCB0"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Find the created ports
        result = subprocess.run(
            ["com0com", "--list"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        output = result.stdout.decode("utf-8")
        lines = output.split("\n")
        port_a = None
        port_b = None
        
        for line in lines:
            if "CNCA0" in line and "COM" in line:
                port_a = line.split("COM")[1].split()[0]
                port_a = f"COM{port_a}"
            if "CNCB0" in line and "COM" in line:
                port_b = line.split("COM")[1].split()[0]
                port_b = f"COM{port_b}"
                
        if port_a and port_b:
            logger.info(f"Created port pair: {port_a} <-> {port_b}")
            return port_a, port_b
            
        logger.error("Failed to create or find port pair")
        return None, None
        
    except subprocess.CalledProcessError as e:
        logger.error(f"com0com error: {e}")
        return None, None
    except FileNotFoundError:
        logger.error("com0com not found. Please install it first.")
        return None, None
        
def _setup_socat() -> Tuple[Optional[str], Optional[str]]:
    """
    Set up a virtual serial port pair using socat on Linux/macOS.
    
    Returns:
        Tuple[Optional[str], Optional[str]]: Pair of serial ports or None if failed
    """
    logger.info("Setting up socat virtual port pair")
    
    try:
        # Check if socat is installed
        subprocess.run(
            ["socat", "-V"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Create a virtual serial port pair
        system = platform.system()
        if system == "Linux":
            # Use pts devices on Linux
            subprocess.Popen(
                ["socat", "pty,raw,echo=0,link=/tmp/ttyV0", "pty,raw,echo=0,link=/tmp/ttyV1"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Check if the ports were created
            if os.path.exists("/tmp/ttyV0") and os.path.exists("/tmp/ttyV1"):
                logger.info("Created port pair: /tmp/ttyV0 <-> /tmp/ttyV1")
                return "/tmp/ttyV0", "/tmp/ttyV1"
                
        elif system == "Darwin":  # macOS
            # Use cu.usbserial devices on macOS
            subprocess.Popen(
                ["socat", "pty,raw,echo=0", "pty,raw,echo=0"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # On macOS, socat doesn't support the link= option, so we need to check dmesg
            result = subprocess.run(
                ["ls", "-la", "/dev/"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            output = result.stdout.decode("utf-8")
            pty_devices = []
            
            for line in output.split("\n"):
                if "tty.usbmodem" in line:
                    device = line.split()[-1]
                    pty_devices.append(f"/dev/{device}")
                    
            if len(pty_devices) >= 2:
                logger.info(f"Found port pair: {pty_devices[0]} <-> {pty_devices[1]}")
                return pty_devices[0], pty_devices[1]
                
        logger.error("Failed to create or find port pair")
        return None, None
        
    except subprocess.CalledProcessError as e:
        logger.error(f"socat error: {e}")
        return None, None
    except FileNotFoundError:
        logger.error("socat not found. Please install it first.")
        return None, None

def list_com_ports() -> List[str]:
    """
    List available COM ports.
    
    Returns:
        List[str]: List of available COM ports
    """
    try:
        import serial.tools.list_ports
        return [port.device for port in serial.tools.list_ports.comports()]
    except ImportError:
        logger.error("pyserial not installed. Please install it first.")
        return []