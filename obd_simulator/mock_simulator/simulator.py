# File: obd_simulator/mock_simulator/simulator.py
"""
Mock OBD-II simulator that emulates the python-OBD library interface.
"""

import time
import logging
from typing import List, Dict, Any, Optional, Set

from obd_simulator.common.obd_command import OBDCommand
from obd_simulator.common.obd_response import OBDResponse, Quantity
from obd_simulator.mock_simulator.virtual_car import VirtualCar

logger = logging.getLogger(__name__)

class Simulator:
    """
    OBD-II simulator that emulates the python-OBD library interface.
    
    This simulator works entirely in memory with no need for hardware
    connections. It provides an interface compatible with python-OBD.
    """
    
    def __init__(self, car: Optional[VirtualCar] = None):
        """
        Initialize the simulator with an optional virtual car.
        
        Args:
            car: VirtualCar instance to use, or None to create a new one
        """
        self.car = car or VirtualCar()
        self.connected = False
        self.commands = self._get_supported_commands()
        
        # Record the available commands as a set for faster lookup
        self.supported_commands = self.commands
        
        self.last_update = time.time()
        logger.info("OBD Simulator initialized")
        
    def is_connected(self) -> bool:
        """
        Check if simulator is connected.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self.connected
        
    def connect(self) -> bool:
        """
        Connect to virtual OBD-II interface and start the engine.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        logger.info("Connecting to virtual OBD-II interface")
        self.connected = True
        self.car.start_engine()
        return True
        
    def status(self) -> str:
        """
        Get simulator status.
        
        Returns:
            str: Status message
        """
        if self.connected:
            engine_state = "Running" if self.car.engine_running else "Off"
            return f"Virtual OBD-II Interface (Engine: {engine_state})"
        else:
            return "Disconnected"
            
    def protocol_name(self) -> str:
        """
        Get the protocol name.
        
        Returns:
            str: Protocol name
        """
        return "Mock OBD-II Protocol"
        
    def update(self) -> None:
        """
        Update the car simulator.
        """
        current_time = time.time()
        dt = current_time - self.last_update
        self.car.update(dt)
        self.last_update = current_time
        
    def _get_supported_commands(self) -> List[OBDCommand]:
        """
        Get all supported OBD commands.
        
        Returns:
            List[OBDCommand]: List of supported commands
        """
        return [
            OBDCommand.RPM,
            OBDCommand.SPEED,
            OBDCommand.COOLANT_TEMP,
            OBDCommand.THROTTLE_POS,
            OBDCommand.FUEL_LEVEL,
            OBDCommand.INTAKE_TEMP,
            OBDCommand.MAF,
            OBDCommand.ENGINE_LOAD
        ]
        
    def query(self, command: OBDCommand) -> OBDResponse:
        """
        Query an OBD command and get a response.
        
        Args:
            command: OBDCommand to query
            
        Returns:
            OBDResponse: Response with value or None if not supported
        """
        if not self.connected:
            return OBDResponse(command, None)
            
        # Update the simulator state
        self.update()
        
        # Process the command
        car_data = self.car.get_data()
        
        # Map commands to data
        if command == OBDCommand.RPM:
            return OBDResponse(command, Quantity(car_data['rpm'], 'rpm'))
        elif command == OBDCommand.SPEED:
            return OBDResponse(command, Quantity(car_data['speed'], 'kph'))
        elif command == OBDCommand.COOLANT_TEMP:
            return OBDResponse(command, Quantity(car_data['coolant_temp'], 'degC'))
        elif command == OBDCommand.THROTTLE_POS:
            return OBDResponse(command, Quantity(car_data['throttle'], 'percent'))
        elif command == OBDCommand.FUEL_LEVEL:
            return OBDResponse(command, Quantity(car_data['fuel_level'], 'percent'))
        elif command == OBDCommand.INTAKE_TEMP:
            return OBDResponse(command, Quantity(car_data['intake_temp'], 'degC'))
        elif command == OBDCommand.MAF:
            return OBDResponse(command, Quantity(car_data['maf'], 'g/s'))
        elif command == OBDCommand.ENGINE_LOAD:
            return OBDResponse(command, Quantity(car_data['engine_load'], 'percent'))
        else:
            return OBDResponse(command, None)
            
    def close(self) -> None:
        """
        Close the connection to the simulator.
        """
        if self.connected:
            logger.info("Disconnecting from virtual OBD-II interface")
            self.car.stop_engine()
            self.connected = False
            
    def set_throttle(self, percent: float) -> bool:
        """
        Set the car's throttle position (0-100%).
        
        Args:
            percent: Throttle position in percent (0-100)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.connected:
            return self.car.set_throttle(percent)
        return False
