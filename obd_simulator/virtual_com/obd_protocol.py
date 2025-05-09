"""
OBD-II protocol implementation for virtual COM port simulation.
"""

from enum import Enum
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class OBDProtocolType(Enum):
    """OBD-II Protocol Types"""
    SAE_J1850_PWM = 1
    SAE_J1850_VPW = 2
    ISO_9141_2 = 3
    ISO_14230_4_KWP_5BAUD = 4
    ISO_14230_4_KWP_FAST = 5
    ISO_15765_4_CAN_11_500 = 6
    ISO_15765_4_CAN_29_500 = 7
    ISO_15765_4_CAN_11_250 = 8
    ISO_15765_4_CAN_29_250 = 9
    SAE_J1939_CAN_29_250 = 10

class OBDProtocol:
    """
    OBD-II protocol implementation for virtual COM port simulation.
    
    This class handles protocol-specific details for OBD-II communication.
    """
    
    def __init__(self, protocol_type: OBDProtocolType = OBDProtocolType.ISO_15765_4_CAN_11_500):
        """
        Initialize the OBD-II protocol handler.
        
        Args:
            protocol_type: Protocol type to use
        """
        self.protocol_type = protocol_type
        self.header_length = 3  # Default header length
        self.has_checksum = True  # Whether the protocol uses checksums
        
        # Set protocol-specific parameters
        self._init_protocol_parameters()
        
        logger.info(f"OBD Protocol initialized: {self.get_protocol_name()}")
        
    def _init_protocol_parameters(self) -> None:
        """Initialize protocol-specific parameters."""
        if self.protocol_type in [OBDProtocolType.SAE_J1850_PWM, OBDProtocolType.SAE_J1850_VPW]:
            self.header_length = 3
            self.has_checksum = True
        elif self.protocol_type in [OBDProtocolType.ISO_9141_2, OBDProtocolType.ISO_14230_4_KWP_5BAUD, 
                                  OBDProtocolType.ISO_14230_4_KWP_FAST]:
            self.header_length = 3
            self.has_checksum = True
        elif self.protocol_type in [OBDProtocolType.ISO_15765_4_CAN_11_500, OBDProtocolType.ISO_15765_4_CAN_11_250]:
            self.header_length = 3
            self.has_checksum = False
        elif self.protocol_type in [OBDProtocolType.ISO_15765_4_CAN_29_500, OBDProtocolType.ISO_15765_4_CAN_29_250, 
                                  OBDProtocolType.SAE_J1939_CAN_29_250]:
            self.header_length = 5
            self.has_checksum = False
            
    def get_protocol_name(self) -> str:
        """
        Get the name of the current protocol.
        
        Returns:
            str: Protocol name
        """
        protocol_names = {
            OBDProtocolType.SAE_J1850_PWM: "SAE J1850 PWM",
            OBDProtocolType.SAE_J1850_VPW: "SAE J1850 VPW",
            OBDProtocolType.ISO_9141_2: "ISO 9141-2",
            OBDProtocolType.ISO_14230_4_KWP_5BAUD: "ISO 14230-4 (KWP 5BAUD)",
            OBDProtocolType.ISO_14230_4_KWP_FAST: "ISO 14230-4 (KWP FAST)",
            OBDProtocolType.ISO_15765_4_CAN_11_500: "ISO 15765-4 (CAN 11/500)",
            OBDProtocolType.ISO_15765_4_CAN_29_500: "ISO 15765-4 (CAN 29/500)",
            OBDProtocolType.ISO_15765_4_CAN_11_250: "ISO 15765-4 (CAN 11/250)",
            OBDProtocolType.ISO_15765_4_CAN_29_250: "ISO 15765-4 (CAN 29/250)",
            OBDProtocolType.SAE_J1939_CAN_29_250: "SAE J1939 (CAN 29/250)"
        }
        return protocol_names.get(self.protocol_type, "Unknown Protocol")
        
    def format_message(self, sender_id: int, mode: int, pid: int, data: str) -> str:
        """
        Format a message according to the protocol.
        
        Args:
            sender_id: ECU ID (e.g., 0x7E8 for engine ECU)
            mode: OBD mode (e.g., 0x01 for current data)
            pid: Parameter ID
            data: Data bytes in hex format
            
        Returns:
            str: Formatted message
        """
        # Format header based on protocol
        if self.protocol_type in [OBDProtocolType.ISO_15765_4_CAN_11_500, OBDProtocolType.ISO_15765_4_CAN_11_250]:
            # CAN protocol - first byte is length of data
            header = f"{sender_id:03X}"
            data_length = (len(data) // 2) + 2  # mode, pid, and data bytes
            message = f"{data_length:02X}{(mode + 0x40):02X}{pid:02X}{data}"
        else:
            # Non-CAN protocols
            header = f"{sender_id:03X}"
            message = f"{(mode + 0x40):02X}{pid:02X}{data}"
            
        # Add checksum if needed
        if self.has_checksum:
            # Calculate checksum
            total = 0
            for i in range(0, len(message), 2):
                if i+1 < len(message):
                    total += int(message[i:i+2], 16)
                    
            checksum = ((total ^ 0xFF) + 1) & 0xFF
            return f"{header} {message} {checksum:02X}"
        else:
            return f"{header} {message}"
            
    def parse_message(self, message: str) -> dict:
        """
        Parse a message according to the protocol.
        
        Args:
            message: Message string
            
        Returns:
            dict: Parsed message components
        """
        # Remove spaces and other separators
        clean_message = message.replace(" ", "").replace("\r", "").replace("\n", "")
        
        # Parse header
        header_len = 3  # Default for most protocols
        if self.protocol_type in [OBDProtocolType.ISO_15765_4_CAN_29_500, 
                                OBDProtocolType.ISO_15765_4_CAN_29_250,
                                OBDProtocolType.SAE_J1939_CAN_29_250]:
            header_len = 8  # 29-bit CAN IDs are 8 hex digits
            
        if len(clean_message) < header_len:
            return {"error": "Message too short"}
            
        header = clean_message[:header_len]
        data = clean_message[header_len:]
        
        # For CAN protocols, first byte after header is length
        if self.protocol_type in [OBDProtocolType.ISO_15765_4_CAN_11_500, 
                                OBDProtocolType.ISO_15765_4_CAN_11_250,
                                OBDProtocolType.ISO_15765_4_CAN_29_500, 
                                OBDProtocolType.ISO_15765_4_CAN_29_250]:
            data_len = int(data[:2], 16)
            mode = int(data[2:4], 16)
            pid = int(data[4:6], 16) if len(data) >= 6 else None
            payload = data[6:6+data_len*2-4] if len(data) >= 6+data_len*2-4 else ""
        else:
            # Non-CAN protocols
            mode = int(data[:2], 16)
            pid = int(data[2:4], 16) if len(data) >= 4 else None
            payload = data[4:-2] if self.has_checksum and len(data) > 6 else data[4:]
            
        return {
            "header": header,
            "mode": mode,
            "pid": pid,
            "payload": payload
        }
