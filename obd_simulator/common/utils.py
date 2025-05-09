# File: obd_simulator/common/utils.py
"""
Utility functions for the OBD-II simulator.
"""

import time
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def calculate_checksum(message: str) -> str:
    """
    Calculate the OBD-II message checksum.
    
    Args:
        message: Message data in hex format
        
    Returns:
        str: Checksum as a hex string
    """
    total = 0
    for i in range(0, len(message), 2):
        if i+1 < len(message):
            total += int(message[i:i+2], 16)
            
    checksum = ((total ^ 0xFF) + 1) & 0xFF
    return f"{checksum:02X}"

def format_obd_message(mode: int, pid: int, data: str, headers: bool = False) -> str:
    """
    Format an OBD-II message with proper headers and checksums.
    
    Args:
        mode: OBD mode (e.g., 0x01 for current data)
        pid: Parameter ID
        data: Data bytes in hex format
        headers: Whether to include headers
        
    Returns:
        str: Formatted OBD-II message
    """
    if headers:
        # Standard ECU response header
        header = "7E8"
        
        # Calculate message length (mode, PID, and data bytes)
        length = (len(data) // 2 + 2)
        length_hex = f"{length:02X}"
        
        # Format response mode (request mode + 0x40)
        mode_resp = f"{(mode + 0x40):02X}"
        
        # Combine all parts
        pid_hex = f"{pid:02X}"
        message = f"{length_hex}{mode_resp}{pid_hex}{data}"
        
        # Calculate checksum
        checksum = calculate_checksum(message)
        
        # Full message
        return f"{header} {message} {checksum}"
    else:
        # Simple format without headers
        mode_resp = f"{(mode + 0x40):02X}"
        pid_hex = f"{pid:02X}"
        return f"{mode_resp}{pid_hex}{data}"