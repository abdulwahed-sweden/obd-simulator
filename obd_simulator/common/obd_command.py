# File: obd_simulator/common/obd_command.py
"""
OBD Command definitions that mirror the python-OBD library.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Callable

class Mode(Enum):
    """OBD-II Mode Enumeration"""
    CURRENT_DATA = 0x01
    FREEZE_FRAME = 0x02
    STORED_DTC = 0x03
    CLEAR_DTC = 0x04
    TEST_RESULTS = 0x05
    CONTROL = 0x06
    PENDING_DTC = 0x07
    SPECIAL_CONTROL = 0x08
    VEHICLE_INFO = 0x09
    PERMANENT_DTC = 0x0A

@dataclass
class OBDCommand:
    """OBD Command class compatible with python-OBD"""
    name: str
    desc: str
    mode: Mode
    pid: int
    bytes: int
    decode: Optional[Callable] = None
    
    def __str__(self) -> str:
        return self.name
        
    def __repr__(self) -> str:
        return f"OBDCommand({self.name}, {self.mode}, {hex(self.pid)})"
        
    def __eq__(self, other):
        if isinstance(other, OBDCommand):
            return (self.mode == other.mode and 
                    self.pid == other.pid)
        return False
        
    def __hash__(self):
        return hash((self.mode, self.pid))
    
    # Standard OBD Commands
    RPM = None  # Will be initialized below
    SPEED = None
    COOLANT_TEMP = None
    THROTTLE_POS = None
    FUEL_LEVEL = None
    INTAKE_TEMP = None
    MAF = None
    ENGINE_LOAD = None

# Initialize standard commands
OBDCommand.RPM = OBDCommand("RPM", "Engine RPM", Mode.CURRENT_DATA, 0x0C, 2, None)
OBDCommand.SPEED = OBDCommand("SPEED", "Vehicle Speed", Mode.CURRENT_DATA, 0x0D, 1, None)
OBDCommand.COOLANT_TEMP = OBDCommand("COOLANT_TEMP", "Engine Coolant Temperature", Mode.CURRENT_DATA, 0x05, 1, None)
OBDCommand.THROTTLE_POS = OBDCommand("THROTTLE_POS", "Throttle Position", Mode.CURRENT_DATA, 0x11, 1, None)
OBDCommand.FUEL_LEVEL = OBDCommand("FUEL_LEVEL", "Fuel Level", Mode.CURRENT_DATA, 0x2F, 1, None)
OBDCommand.INTAKE_TEMP = OBDCommand("INTAKE_TEMP", "Intake Air Temperature", Mode.CURRENT_DATA, 0x0F, 1, None)
OBDCommand.MAF = OBDCommand("MAF", "Mass Air Flow", Mode.CURRENT_DATA, 0x10, 2, None)
OBDCommand.ENGINE_LOAD = OBDCommand("ENGINE_LOAD", "Engine Load", Mode.CURRENT_DATA, 0x04, 1, None)