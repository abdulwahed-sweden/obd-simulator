# File: obd_simulator/log_playback/log_validator.py
"""
Validator for OBD-II log files.
"""

import os
import csv
import json
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

def validate_log_file(log_file: str) -> Tuple[bool, str]:
    """
    Validate an OBD-II log file.
    
    Args:
        log_file: Path to the log file
        
    Returns:
        Tuple[bool, str]: Tuple of (is_valid, message)
    """
    if not os.path.exists(log_file):
        return False, f"File not found: {log_file}"
        
    file_ext = os.path.splitext(log_file)[1].lower()
    
    try:
        if file_ext == '.csv':
            return validate_csv_log(log_file)
        elif file_ext == '.json':
            return validate_json_log(log_file)
        else:
            return False, f"Unsupported file format: {file_ext}"
    except Exception as e:
        return False, f"Error validating log file: {e}"
        
def validate_csv_log(log_file: str) -> Tuple[bool, str]:
    """
    Validate a CSV log file.
    
    Args:
        log_file: Path to the CSV log file
        
    Returns:
        Tuple[bool, str]: Tuple of (is_valid, message)
    """
    try:
        with open(log_file, 'r') as f:
            # Try to detect CSV format
            sample = f.read(4096)
            f.seek(0)
            
            if not sample:
                return False, "Empty file"
                
            try:
                dialect = csv.Sniffer().sniff(sample)
            except csv.Error:
                return False, "Invalid CSV format"
                
            # Check if there's a header
            has_header = csv.Sniffer().has_header(sample)
            if not has_header:
                return False, "No header row found"
                
            # Read CSV
            reader = csv.reader(f, dialect)
            headers = next(reader)
            
            # Check required columns
            required_columns = ['timestamp', 'time', 'datetime']
            obd_columns = ['rpm', 'speed', 'coolant_temp', 'throttle_pos', 'fuel_level']
            
            # Clean up headers
            clean_headers = [h.strip().lower() for h in headers]
            
            # Check for timestamp column
            has_timestamp = any(col in clean_headers for col in required_columns)
            if not has_timestamp:
                logger.warning("No timestamp column found")
                
            # Check for OBD data columns
            found_obd_columns = []
            for col in obd_columns:
                for header in clean_headers:
                    if col in header:
                        found_obd_columns.append(col)
                        break
                        
            if not found_obd_columns:
                return False, "No OBD data columns found"
                
            # Check for data rows
            row_count = 0
            for row in reader:
                row_count += 1
                if len(row) != len(headers):
                    return False, f"Row {row_count} has {len(row)} columns, expected {len(headers)}"
                    
            if row_count == 0:
                return False, "No data rows found"
                
            return True, f"Valid CSV log file with {row_count} rows. Found data columns: {', '.join(found_obd_columns)}"
            
    except Exception as e:
        return False, f"Error reading CSV file: {e}"
        
def validate_json_log(log_file: str) -> Tuple[bool, str]:
    """
    Validate a JSON log file.
    
    Args:
        log_file: Path to the JSON log file
        
    Returns:
        Tuple[bool, str]: Tuple of (is_valid, message)
    """
    try:
        with open(log_file, 'r') as f:
            data = json.load(f)
            
        if not data:
            return False, "Empty JSON file"
            
        # Check format - can be array of objects or object with arrays
        if isinstance(data, list):
            # Array of log entries
            if not all(isinstance(entry, dict) for entry in data):
                return False, "Invalid format: Not all entries are objects"
                
            # Check for timestamp and OBD data
            timestamp_keys = ['timestamp', 'time', 'datetime']
            obd_keys = ['rpm', 'speed', 'coolant_temp', 'throttle_pos', 'fuel_level']
            
            # Check first entry
            first_entry = data[0]
            
            # Check for timestamp
            has_timestamp = any(key in first_entry for key in timestamp_keys)
            if not has_timestamp:
                logger.warning("No timestamp field found")
                
            # Check for OBD data
            found_obd_keys = []
            first_entry_lower = {k.lower(): v for k, v in first_entry.items()}
            
            for key in obd_keys:
                for entry_key in first_entry_lower:
                    if key in entry_key:
                        found_obd_keys.append(key)
                        break
                        
            if not found_obd_keys:
                return False, "No OBD data fields found"
                
            return True, f"Valid JSON log file with {len(data)} entries. Found data fields: {', '.join(found_obd_keys)}"
            
        elif isinstance(data, dict):
            # Object with arrays
            if not all(isinstance(value, list) for value in data.values()):
                return False, "Invalid format: Not all values are arrays"
                
            # Check for timestamp and OBD data
            timestamp_keys = ['timestamp', 'time', 'datetime']
            obd_keys = ['rpm', 'speed', 'coolant_temp', 'throttle_pos', 'fuel_level']
            
            # Check for timestamp
            has_timestamp = any(key in data for key in timestamp_keys)
            if not has_timestamp:
                logger.warning("No timestamp array found")
                
            # Check for OBD data
            found_obd_keys = []
            for key in obd_keys:
                for data_key in data:
                    if key in data_key.lower():
                        found_obd_keys.append(key)
                        break
                        
            if not found_obd_keys:
                return False, "No OBD data arrays found"
                
            # Get length of first array
            first_array_len = len(next(iter(data.values())))
            
            # Check all arrays have same length
            if not all(len(value) == first_array_len for value in data.values()):
                return False, "Not all arrays have same length"
                
            return True, f"Valid JSON log file with {first_array_len} entries. Found data fields: {', '.join(found_obd_keys)}"
            
        else:
            return False, "Invalid JSON format: Neither a list nor an object"
            
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"
    except Exception as e:
        return False, f"Error reading JSON file: {e}"