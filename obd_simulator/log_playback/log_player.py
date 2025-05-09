
# File: obd_simulator/log_playback/log_player.py
"""
Log playback OBD-II simulator that replays recorded data.
"""

import os
import time
import csv
import json
import random
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from obd_simulator.common.obd_command import OBDCommand
from obd_simulator.common.obd_response import OBDResponse, Quantity

logger = logging.getLogger(__name__)

class MockOBDCommand:
    """
    Mock OBD command class that mimics the python-OBD library's command objects.
    """
    
    def __init__(self, name: str):
        """
        Initialize a mock OBD command.
        
        Args:
            name: Command name
        """
        self.name = name
        self.desc = name
        
    def __eq__(self, other):
        if isinstance(other, MockOBDCommand):
            return self.name == other.name
        return False
        
    def __hash__(self):
        return hash(self.name)
        
    def __str__(self):
        return self.name


class LogPlayer:
    """
    OBD-II log player that simulates OBD-II interface by replaying log files.
    
    This class provides an interface compatible with python-OBD that reads
    data from log files instead of a physical OBD-II adapter.
    """
    
    def __init__(self, log_file: str = None, loop: bool = True, speed: float = 1.0, 
                random_variation: float = 0.05):
        """
        Initialize the log player.
        
        Args:
            log_file: Path to the log file
            loop: Whether to loop the log file when it ends
            speed: Playback speed multiplier
            random_variation: Random variation factor (0-1)
        """
        self.log_file = log_file
        self.loop = loop
        self.speed = speed
        self.random_variation = random_variation
        
        self.log_data = []
        self.current_index = 0
        self.last_timestamp = None
        self.connected = False
        self.supported_commands = []
        
        # Map of command names to their handlers
        self.command_map = {
            'RPM': self._get_rpm,
            'SPEED': self._get_speed,
            'COOLANT_TEMP': self._get_coolant_temp,
            'THROTTLE_POS': self._get_throttle_pos,
            'FUEL_LEVEL': self._get_fuel_level,
            'INTAKE_TEMP': self._get_intake_temp,
            'MAF': self._get_maf,
            'ENGINE_LOAD': self._get_engine_load
        }
        
        # Current state (will be updated during playback)
        self.current_state = {
            'timestamp': None,
            'RPM': 0,
            'SPEED': 0,
            'COOLANT_TEMP': 0,
            'THROTTLE_POS': 0, 
            'FUEL_LEVEL': 0,
            'INTAKE_TEMP': 0,
            'MAF': 0,
            'ENGINE_LOAD': 0
        }
        
    def load_log_file(self) -> bool:
        """
        Load and parse the log file.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.log_file or not os.path.exists(self.log_file):
            logger.error(f"Log file not found: {self.log_file}")
            return False
            
        logger.info(f"Loading log file: {self.log_file}")
        
        file_ext = os.path.splitext(self.log_file)[1].lower()
        
        try:
            if file_ext == '.csv':
                self._load_csv_log()
            elif file_ext == '.json':
                self._load_json_log()
            else:
                logger.error(f"Unsupported log file format: {file_ext}")
                return False
                
            logger.info(f"Loaded {len(self.log_data)} log entries")
            
            # Initialize commands based on first log entry
            if self.log_data:
                self._init_supported_commands()
                return True
            else:
                logger.error("No data found in log file")
                return False
                
        except Exception as e:
            logger.error(f"Error loading log file: {e}")
            return False
            
    def _load_csv_log(self) -> None:
        """Load data from CSV log file."""
        self.log_data = []
        with open(self.log_file, 'r') as f:
            # Try to detect CSV format
            dialect = csv.Sniffer().sniff(f.read(4096))
            f.seek(0)
            
            # Read CSV header
            reader = csv.reader(f, dialect)
            headers = next(reader)
            
            # Clean up headers (remove whitespace, convert to lowercase for comparison)
            clean_headers = [h.strip().lower() for h in headers]
            
            # Find timestamp column
            timestamp_col = -1
            for i, header in enumerate(clean_headers):
                if header in ['timestamp', 'time', 'datetime']:
                    timestamp_col = i
                    break
                    
            if timestamp_col == -1:
                # No timestamp column, we'll generate one
                timestamp_col = None
                logger.warning("No timestamp column found, generating timestamps")
                
            # Process each row
            for row in reader:
                if not row or len(row) != len(headers):
                    continue  # Skip malformed rows
                    
                entry = {}
                
                # Process timestamp
                if timestamp_col is not None:
                    try:
                        timestamp_str = row[timestamp_col].strip()
                        entry['timestamp'] = self._parse_timestamp(timestamp_str)
                    except:
                        # In case of parsing error, use the current time
                        entry['timestamp'] = datetime.now()
                else:
                    # Generate timestamp (1 second after previous, or now for first entry)
                    if not self.log_data:
                        entry['timestamp'] = datetime.now()
                    else:
                        entry['timestamp'] = self.log_data[-1]['timestamp'].replace(
                            second=self.log_data[-1]['timestamp'].second + 1
                        )
                
                # Process data columns
                for i, value in enumerate(row):
                    if i != timestamp_col:  # Skip timestamp column
                        header = headers[i].strip()
                        # Try to convert to appropriate type
                        try:
                            entry[header] = float(value)
                        except:
                            entry[header] = value
                            
                self.log_data.append(entry)
                
    def _load_json_log(self) -> None:
        """Load data from JSON log file."""
        with open(self.log_file, 'r') as f:
            data = json.load(f)
            
        # Check format - can be array of objects or object with arrays
        if isinstance(data, list):
            # Array of log entries
            self.log_data = data
        elif isinstance(data, dict):
            # Columns of data
            # Convert to array of objects
            timestamps = data.get('timestamp', [])
            if not timestamps:
                # Try other possible column names
                for name in ['time', 'datetime', 'date']:
                    if name in data:
                        timestamps = data[name]
                        break
                        
            if not timestamps:
                # Generate timestamps
                logger.warning("No timestamp column found, generating timestamps")
                timestamps = [datetime.now().strftime('%Y-%m-%d %H:%M:%S') 
                            for _ in range(len(list(data.values())[0]))]
                
            # Create entries for each timestamp
            self.log_data = []
            for i, ts in enumerate(timestamps):
                entry = {'timestamp': self._parse_timestamp(ts) if isinstance(ts, str) else ts}
                
                # Add all other columns
                for col, values in data.items():
                    if col != 'timestamp' and i < len(values):
                        entry[col] = values[i]
                        
                self.log_data.append(entry)
        else:
            logger.error("Unknown JSON format")
            
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """
        Try to parse a timestamp string in various formats.
        
        Args:
            timestamp_str: Timestamp string
            
        Returns:
            datetime: Parsed timestamp or current time if parsing fails
        """
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y/%m/%d %H:%M:%S',
            '%Y/%m/%d %H:%M:%S.%f',
            '%d/%m/%Y %H:%M:%S',
            '%m/%d/%Y %H:%M:%S',
            '%H:%M:%S'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue
                
        # If no format matches, return current time
        logger.warning(f"Could not parse timestamp: {timestamp_str}")
        return datetime.now()
        
    def _init_supported_commands(self) -> None:
        """Initialize supported commands based on log data."""
        if not self.log_data:
            return
            
        # Get first entry as reference
        first_entry = self.log_data[0]
        
        # Map log columns to OBD commands
        self.supported_commands = []
        
        # Define mappings between common column names and OBD command names
        column_mappings = {
            'rpm': 'RPM',
            'speed': 'SPEED',
            'vehicle_speed': 'SPEED',
            'coolant_temp': 'COOLANT_TEMP',
            'coolant': 'COOLANT_TEMP',
            'throttle': 'THROTTLE_POS',
            'throttle_pos': 'THROTTLE_POS',
            'fuel': 'FUEL_LEVEL',
            'fuel_level': 'FUEL_LEVEL',
            'intake_temp': 'INTAKE_TEMP',
            'maf': 'MAF',
            'air_flow': 'MAF',
            'engine_load': 'ENGINE_LOAD',
            'load': 'ENGINE_LOAD'
        }
        
        # Check for each OBD command in the log data
        for col in first_entry.keys():
            if col == 'timestamp':
                continue
                
            col_lower = col.lower()
            
            # Try to match column with OBD command
            for pattern, command in column_mappings.items():
                if pattern in col_lower:
                    # Create a mock command object
                    mock_command = MockOBDCommand(command)
                    self.supported_commands.append(mock_command)
                    break
                    
        logger.info(f"Detected {len(self.supported_commands)} supported commands")
        
    def connect(self) -> bool:
        """
        Connect to the virtual OBD interface (load log file).
        
        Returns:
            bool: True if connected successfully, False otherwise
        """
        if self.load_log_file():
            self.connected = True
            self.current_index = 0
            self.last_timestamp = datetime.now()
            
            # Initialize state with first log entry
            if self.log_data:
                self._update_current_state()
                
            logger.info("Connected to virtual OBD interface")
            return True
        else:
            logger.error("Failed to connect to virtual OBD interface")
            return False
            
    def is_connected(self) -> bool:
        """
        Check if connected to the OBD interface.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self.connected
        
    def status(self) -> str:
        """
        Get OBD interface status.
        
        Returns:
            str: Status message
        """
        if self.connected:
            return f"Connected to log file: {self.log_file}"
        else:
            return "Not connected"
            
    def close(self) -> None:
        """Close the OBD interface."""
        self.connected = False
        logger.info("Disconnected from virtual OBD interface")
        
    def _update_current_state(self) -> None:
        """Update current state based on log playback position."""
        if not self.connected or not self.log_data:
            return
            
        # Get current log entry
        current_entry = self.log_data[self.current_index]
        
        # Update timestamp
        self.current_state['timestamp'] = current_entry.get('timestamp')
        
        # Update all available values from log
        for field in self.current_state.keys():
            if field in current_entry:
                self.current_state[field] = current_entry[field]
            elif field.lower() in current_entry:
                self.current_state[field] = current_entry[field.lower()]
                
        # Add random variation to values
        if self.random_variation > 0:
            for field in self.current_state.keys():
                if field != 'timestamp' and isinstance(self.current_state[field], (int, float)):
                    value = self.current_state[field]
                    variation = value * self.random_variation
                    self.current_state[field] = value + random.uniform(-variation, variation)
        
    def _advance_playback(self) -> bool:
        """
        Advance to the next log entry based on time elapsed and playback speed.
        
        Returns:
            bool: True if advanced to a new entry, False otherwise
        """
        if not self.connected or not self.log_data:
            return False
            
        # Get current and next timestamps
        current_ts = self.log_data[self.current_index].get('timestamp')
        
        # If at the end of log, loop back to beginning or stop
        if self.current_index >= len(self.log_data) - 1:
            if self.loop:
                self.current_index = 0
                self.last_timestamp = datetime.now()
                logger.info("Reached end of log file, looping to beginning")
                self._update_current_state()
                return True
            else:
                # Stay at the last entry
                return False
        else:
            next_index = self.current_index + 1
            next_ts = self.log_data[next_index].get('timestamp')
            
            # Calculate time difference between log entries
            if current_ts and next_ts:
                log_time_diff = (next_ts - current_ts).total_seconds()
            else:
                # Default to 1 second if timestamps are missing
                log_time_diff = 1.0
                
            # Calculate real time elapsed since last update
            now = datetime.now()
            real_time_diff = (now - self.last_timestamp).total_seconds()
            
            # Scale by playback speed
            adjusted_time_diff = real_time_diff * self.speed
            
            # Check if it's time to advance to next entry
            if adjusted_time_diff >= log_time_diff:
                self.current_index = next_index
                self.last_timestamp = now
                self._update_current_state()
                return True
                
        return False
        
    def query(self, command) -> OBDResponse:
        """
        Query an OBD command and get a response.
        
        Args:
            command: OBD command to query
            
        Returns:
            OBDResponse: Response with value or None if not supported
        """
        if not self.connected:
            return OBDResponse(command, None)
            
        # Advance playback based on elapsed time
        self._advance_playback()
        
        # Find the command handler
        if hasattr(command, 'name'):
            command_name = command.name
            if command_name in self.command_map:
                return self.command_map[command_name](command)
                
        # Command not supported
        return OBDResponse(command, None)
        
    def _get_rpm(self, command) -> OBDResponse:
        """
        Get engine RPM.
        
        Args:
            command: OBD command object
            
        Returns:
            OBDResponse: Response with RPM value
        """
        value = self.current_state.get('RPM', 0)
        return OBDResponse(command, Quantity(value, 'rpm'))
        
    def _get_speed(self, command) -> OBDResponse:
        """
        Get vehicle speed.
        
        Args:
            command: OBD command object
            
        Returns:
            OBDResponse: Response with speed value
        """
        value = self.current_state.get('SPEED', 0)
        return OBDResponse(command, Quantity(value, 'kph'))
        
    def _get_coolant_temp(self, command) -> OBDResponse:
        """
        Get engine coolant temperature.
        
        Args:
            command: OBD command object
            
        Returns:
            OBDResponse: Response with temperature value
        """
        value = self.current_state.get('COOLANT_TEMP', 80)
        return OBDResponse(command, Quantity(value, 'degC'))
        
    def _get_throttle_pos(self, command) -> OBDResponse:
        """
        Get throttle position.
        
        Args:
            command: OBD command object
            
        Returns:
            OBDResponse: Response with throttle position value
        """
        value = self.current_state.get('THROTTLE_POS', 0)
        return OBDResponse(command, Quantity(value, 'percent'))
        
    def _get_fuel_level(self, command) -> OBDResponse:
        """
        Get fuel level.
        
        Args:
            command: OBD command object
            
        Returns:
            OBDResponse: Response with fuel level value
        """
        value = self.current_state.get('FUEL_LEVEL', 50)
        return OBDResponse(command, Quantity(value, 'percent'))
        
    def _get_intake_temp(self, command) -> OBDResponse:
        """
        Get intake air temperature.
        
        Args:
            command: OBD command object
            
        Returns:
            OBDResponse: Response with temperature value
        """
        value = self.current_state.get('INTAKE_TEMP', 20)
        return OBDResponse(command, Quantity(value, 'degC'))
        
    def _get_maf(self, command) -> OBDResponse:
        """
        Get mass air flow.
        
        Args:
            command: OBD command object
            
        Returns:
            OBDResponse: Response with MAF value
        """
        value = self.current_state.get('MAF', 10)
        return OBDResponse(command, Quantity(value, 'g/s'))
        
    def _get_engine_load(self, command) -> OBDResponse:
        """
        Get engine load.
        
        Args:
            command: OBD command object
            
        Returns:
            OBDResponse: Response with engine load value
        """
        value = self.current_state.get('ENGINE_LOAD', 20)
        return OBDResponse(command, Quantity(value, 'percent'))