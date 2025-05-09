# File: obd_simulator/virtual_com/elm327_device.py
"""
ELM327 device emulator for virtual serial port communication.
"""

import time
import random
import serial
import threading
import logging
from typing import Dict, List, Any, Optional

from obd_simulator.mock_simulator.virtual_car import VirtualCar
from obd_simulator.common.utils import format_obd_message

logger = logging.getLogger(__name__)

class ELM327Device:
    """
    Virtual ELM327 device that responds to OBD-II commands through a serial port.
    
    This class simulates an ELM327 OBD-II adapter connected to a vehicle,
    communicating through a serial port. It can be used with any OBD-II software
    that supports ELM327 adapters.
    """
    
    def __init__(self, port: str, baudrate: int = 38400):
        """
        Initialize the virtual ELM327 device.
        
        Args:
            port: Serial port to use
            baudrate: Baud rate for serial communication
        """
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.car = VirtualCar()
        self.running = False
        self.thread = None
        
        # ELM327 settings
        self.echo = True
        self.linefeed = True
        self.headers = False
        self.spaces = True
        self.adaptive_timing = 1
        self.protocol = "AUTO"
        self.last_command = ""
        
        logger.info(f"Virtual ELM327 device initialized on {port}")
        
    def connect(self) -> bool:
        """
        Connect to the serial port.
        
        Returns:
            bool: True if connected successfully, False otherwise
        """
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=1
            )
            logger.info(f"Connected to serial port {self.port}")
            
            # Start the car engine
            self.car.start_engine()
            
            return True
        except serial.SerialException as e:
            logger.error(f"Failed to connect to {self.port}: {e}")
            return False
            
    def close(self) -> None:
        """
        Close the connection and stop the device.
        """
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=2)
            
        if self.serial and self.serial.is_open:
            self.serial.close()
            logger.info("Serial connection closed")
            
        # Stop the car engine
        self.car.stop_engine()
            
    def start(self) -> bool:
        """
        Start the ELM327 device in a separate thread.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        if self.connect():
            self.running = True
            self.thread = threading.Thread(target=self._run)
            self.thread.daemon = True
            self.thread.start()
            logger.info("ELM327 device started")
            return True
        return False
        
    def _run(self) -> None:
        """
        Main loop to read commands and send responses.
        """
        if not self.serial or not self.serial.is_open:
            logger.error("Cannot run: Serial port not open")
            return
            
        # Initialize engine
        self.car.start_engine()
        logger.info("Engine started")
        
        # Send prompt character
        self.serial.write(">\r".encode())
        
        buffer = ""
        last_update_time = time.time()
        
        while self.running:
            try:
                # Update car state
                current_time = time.time()
                dt = current_time - last_update_time
                self.car.update(dt)
                last_update_time = current_time
                
                # Read data from serial port
                data = self.serial.read(1)
                
                if data:
                    # Convert bytes to string
                    char = data.decode('ascii', errors='ignore')
                    
                    # Handle carriage return (command terminator)
                    if char == '\r':
                        # Process complete command
                        response = self._process_command(buffer)
                        
                        # Send response if not empty
                        if response:
                            self.serial.write(response.encode())
                            
                            # Add prompt character after response
                            if not response.endswith(">"):
                                self.serial.write("\r>".encode())
                                
                        # Clear buffer
                        buffer = ""
                    else:
                        # Add character to buffer
                        buffer += char
                        
            except (serial.SerialException, ValueError) as e:
                logger.error(f"Serial error: {e}")
                break
                
        logger.info("ELM327 device stopped")
        
    def _process_command(self, command: str) -> str:
        """
        Process an incoming OBD command and generate a response.
        
        Args:
            command: OBD command string
            
        Returns:
            str: Response string
        """
        command = command.upper().strip()
        
        # No response to empty commands
        if not command:
            return ""
            
        # Save last command for reference
        self.last_command = command
        
        # Echo command if enabled
        if self.echo:
            echo_response = command + "\r"
            if self.linefeed:
                echo_response += "\n"
            self.serial.write(echo_response.encode())
            
        # AT commands for ELM327 configuration
        if command.startswith("AT"):
            return self._process_at_command(command)
            
        # OBD Mode 01: Current Data
        if command.startswith("01"):
            return self._process_mode01_command(command)
            
        # OBD Mode 09: Vehicle Information
        if command.startswith("09"):
            return self._process_mode09_command(command)
            
        # Unknown command
        return "?"
        
    def _process_at_command(self, command: str) -> str:
        """
        Process ELM327 AT commands.
        
        Args:
            command: AT command string
            
        Returns:
            str: Response string
        """
        # Common AT commands
        if command == "ATZ":  # Reset
            self.echo = True
            self.linefeed = True
            self.headers = False
            self.spaces = True
            self.adaptive_timing = 1
            self.protocol = "AUTO"
            time.sleep(1)  # Simulate reset time
            return "ELM327 v1.5\r>"
            
        elif command == "ATE0":  # Echo Off
            self.echo = False
            return "OK"
            
        elif command == "ATE1":  # Echo On
            self.echo = True
            return "OK"
            
        elif command == "ATL0":  # Linefeeds Off
            self.linefeed = False
            return "OK"
            
        elif command == "ATL1":  # Linefeeds On
            self.linefeed = True
            return "OK"
            
        elif command == "ATH0":  # Headers Off
            self.headers = False
            return "OK"
            
        elif command == "ATH1":  # Headers On
            self.headers = True
            return "OK"
            
        elif command == "ATS0":  # Spaces Off
            self.spaces = False
            return "OK"
            
        elif command == "ATS1":  # Spaces On
            self.spaces = True
            return "OK"
            
        elif command == "ATSP0":  # Set Protocol to Auto
            self.protocol = "AUTO"
            return "OK"
            
        elif command.startswith("ATSP"):  # Set Protocol
            protocol_num = command[4:]
            protocols = {
                "1": "SAE J1850 PWM",
                "2": "SAE J1850 VPW",
                "3": "ISO 9141-2",
                "4": "ISO 14230-4 (KWP 5BAUD)",
                "5": "ISO 14230-4 (KWP FAST)",
                "6": "ISO 15765-4 (CAN 11/500)",
                "7": "ISO 15765-4 (CAN 29/500)",
                "8": "ISO 15765-4 (CAN 11/250)",
                "9": "ISO 15765-4 (CAN 29/250)",
                "A": "SAE J1939 (CAN 29/250)"
            }
            if protocol_num in protocols:
                self.protocol = protocols[protocol_num]
                return "OK"
                
        elif command == "ATDP":  # Display Protocol
            return self.protocol
            
        elif command == "ATRV":  # Read Voltage
            # Simulate battery voltage between 12-14.5V
            voltage = 12.0 + random.random() * 2.5
            return f"{voltage:.1f}V"
            
        elif command == "ATI":  # Identify
            return "ELM327 v1.5 OBD Simulator"
            
        elif command == "AT@1":  # Display device description
            return "Virtual OBD-II Simulator"
            
        elif command == "ATWS":  # Warm Start
            time.sleep(0.5)
            return "ELM327 v1.5\r>"
            
        # Default response for unhandled AT commands
        return "OK"
        
    def _process_mode01_command(self, command: str) -> str:
        """
        Process OBD-II Mode 01 (current data) commands.
        
        Args:
            command: Mode 01 command string (e.g., "0101")
            
        Returns:
            str: Response string
        """
        # Check for PID request format (01XX where XX is the PID)
        if len(command) != 4:
            return "?"
            
        mode = command[0:2]
        pid = command[2:4]
        
        # Get current car data
        car_data = self.car.get_data()
        
        # Handle specific PIDs
        if pid == "00":  # PIDs supported (01-20)
            data = "BE1FA813"  # Bit-encoded supported PIDs
            return self._format_response(mode, pid, data)
            
        elif pid == "04":  # Calculated engine load
            load_percent = int(car_data['engine_load'])
            data = f"{load_percent * 255 // 100:02X}"
            return self._format_response(mode, pid, data)
            
        elif pid == "05":  # Engine coolant temperature
            # Formula: A - 40 = temperature in °C
            temp_value = int(car_data['coolant_temp']) + 40
            data = f"{temp_value:02X}"
            return self._format_response(mode, pid, data)
            
        elif pid == "0C":  # Engine RPM
            # Formula: ((A * 256) + B) / 4 = RPM
            rpm_value = int(car_data['rpm'] * 4)
            data = f"{rpm_value // 256:02X}{rpm_value % 256:02X}"
            return self._format_response(mode, pid, data)
            
        elif pid == "0D":  # Vehicle speed
            # Speed in km/h
            speed_value = int(car_data['speed'])
            data = f"{speed_value:02X}"
            return self._format_response(mode, pid, data)
            
        elif pid == "0F":  # Intake air temperature
            # Formula: A - 40 = temperature in °C
            temp_value = int(car_data['intake_temp']) + 40
            data = f"{temp_value:02X}"
            return self._format_response(mode, pid, data)
            
        elif pid == "10":  # MAF air flow rate
            # Formula: ((A * 256) + B) / 100 = grams/sec
            maf_value = int(car_data['maf'] * 100)
            data = f"{maf_value // 256:02X}{maf_value % 256:02X}"
            return self._format_response(mode, pid, data)
            
        elif pid == "11":  # Throttle position
            # Formula: A * 100 / 255 = %
            throttle_value = int(car_data['throttle'] * 255 // 100)
            data = f"{throttle_value:02X}"
            return self._format_response(mode, pid, data)
            
        elif pid == "2F":  # Fuel Level Input
            # Formula: A * 100 / 255 = %
            fuel_value = int(car_data['fuel_level'] * 255 // 100)
            data = f"{fuel_value:02X}"
            return self._format_response(mode, pid, data)
            
        # Default response for unsupported PIDs
        return "NO DATA"
        
    def _process_mode09_command(self, command: str) -> str:
        """
        Process OBD-II Mode 09 (vehicle info) commands.
        
        Args:
            command: Mode 09 command string (e.g., "0902")
            
        Returns:
            str: Response string
        """
        # Check for PID request format (09XX where XX is the PID)
        if len(command) != 4:
            return "?"
            
        mode = command[0:2]
        pid = command[2:4]
        
        # VIN (Vehicle Identification Number)
        if pid == "02":
            # Example VIN for a virtual vehicle
            vin = "VSIM00OBD00000001"
            vin_hex = ''.join([f"{ord(c):02X}" for c in vin])
            return self._format_response(mode, pid, vin_hex)
            
        # Calibration ID
        elif pid == "04":
            cal_id = "VIRTUAL-OBD-SIM"
            cal_id_hex = ''.join([f"{ord(c):02X}" for c in cal_id])
            return self._format_response(mode, pid, cal_id_hex)
            
        # ECU Name
        elif pid == "0A":
            ecu_name = "VIRTUAL-ENGINE-ECU"
            ecu_name_hex = ''.join([f"{ord(c):02X}" for c in ecu_name])
            return self._format_response(mode, pid, ecu_name_hex)
            
        # Default response for unsupported PIDs
        return "NO DATA"
        
    def _format_response(self, mode: str, pid: str, data: str) -> str:
        """
        Format a response according to current settings.
        
        Args:
            mode: OBD mode (e.g., "01")
            pid: Parameter ID (e.g., "0C")
            data: Data bytes in hex format
            
        Returns:
            str: Formatted response
        """
        mode_int = int(mode, 16)
        pid_int = int(pid, 16)
        
        if self.headers:
            response = format_obd_message(mode_int, pid_int, data, headers=True)
        else:
            # Calculate response mode (request mode + 0x40)
            mode_resp = f"{mode_int + 0x40:02X}"
            response = f"{mode_resp}{pid}{data}"
            
            # Add spaces if enabled
            if self.spaces:
                response = ' '.join(response[i:i+2] for i in range(0, len(response), 2))
            
        # Add carriage return and optional linefeed
        response += "\r"
        if self.linefeed:
            response += "\n"
            
        return response
        
    def set_throttle(self, percent: float) -> bool:
        """
        Set the throttle position (0-100%).
        
        Args:
            percent: Throttle position in percent (0-100)
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.car.set_throttle(percent)
        
    def engine_stop(self) -> bool:
        """
        Stop the engine.
        
        Returns:
            bool: True if successful, False otherwise
        """
        return self.car.stop_engine()
        
    def engine_start(self) -> bool:
        """
        Start the engine.
        
        Returns:
            bool: True if successful, False otherwise
        """
        return self.car.start_engine()