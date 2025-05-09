# File: obd_simulator/log_playback/log_generator.py
"""
Generator for sample OBD-II log files.
"""

import os
import csv
import json
import random
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, bool

logger = logging.getLogger(__name__)

def generate_log_file(output_file: str, num_entries: int = 100, scenario: str = 'city') -> bool:
    """
    Create a sample OBD log file for testing.
    
    Args:
        output_file: Path to the output file
        num_entries: Number of log entries to generate
        scenario: Driving scenario ('idle', 'city', 'highway')
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(f"Creating sample log file: {output_file}")
    
    # Determine file type from extension
    file_ext = os.path.splitext(output_file)[1].lower()
    
    # Create sample data
    data = []
    start_time = datetime.now()
    
    # Car parameters
    rpm = 800
    speed = 0
    coolant_temp = 20
    throttle = 0
    fuel_level = 90
    
    # Generate log entries
    for i in range(num_entries):
        # Timestamp
        timestamp = start_time + timedelta(seconds=i)
        
        # Simulate different driving scenarios
        if scenario == 'idle':
            # Idle scenario - engine running but not moving
            rpm = random.uniform(750, 850)
            speed = 0
            throttle = random.uniform(0, 5)
            coolant_temp = min(90, coolant_temp + 0.1)
        
        elif scenario == 'city':
            # City driving - stop and go
            if i % 30 < 5:
                # Stopped at light/sign
                rpm = random.uniform(750, 850)
                speed = 0
                throttle = random.uniform(0, 5)
            elif i % 30 < 10:
                # Accelerating
                rpm = min(3000, rpm + random.uniform(50, 150))
                speed = min(60, speed + random.uniform(1, 3))
                throttle = min(50, throttle + random.uniform(1, 5))
            elif i % 30 < 25:
                # Cruising
                rpm = 2000 + random.uniform(-100, 100)
                speed = 40 + random.uniform(-5, 5)
                throttle = 20 + random.uniform(-2, 2)
            else:
                # Slowing down
                rpm = max(800, rpm - random.uniform(50, 150))
                speed = max(0, speed - random.uniform(2, 5))
                throttle = max(0, throttle - random.uniform(1, 3))
                
        elif scenario == 'highway':
            # Highway driving - higher speeds, less variation
            if i < 10:
                # Accelerating onto highway
                rpm = min(3500, rpm + random.uniform(100, 200))
                speed = min(100, speed + random.uniform(2, 5))
                throttle = min(70, throttle + random.uniform(2, 7))
            elif i < 80:
                # Highway cruising
                rpm = 2500 + random.uniform(-100, 100)
                speed = 100 + random.uniform(-5, 5)
                throttle = 30 + random.uniform(-2, 2)
                
                # Occasional passing
                if 30 <= i < 40:
                    rpm = 3000 + random.uniform(-100, 100)
                    speed = 120 + random.uniform(-5, 5)
                    throttle = 50 + random.uniform(-2, 2)
            else:
                # Exiting highway
                rpm = max(800, rpm - random.uniform(50, 150))
                speed = max(0, speed - random.uniform(2, 5))
                throttle = max(0, throttle - random.uniform(1, 3))
                
        else:
            # Default - random values
            rpm = 800 + random.uniform(0, 3000)
            speed = random.uniform(0, 120)
            throttle = random.uniform(0, 100)
            
        # Calculate other values based on primary ones
        engine_load = (rpm / 6000) * 100
        intake_temp = 20 + (rpm / 3000) * 15
        maf = 5 + (rpm / 1000) * 10 * (1 + throttle / 100)
        
        # Reduce fuel gradually
        fuel_level = max(0, fuel_level - 0.02)
        
        # Engine temperature rises and stabilizes
        coolant_temp = min(90, coolant_temp + (0.5 if coolant_temp < 85 else 0.1))
        
        # Create log entry
        entry = {
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'RPM': round(rpm, 2),
            'SPEED': round(speed, 2),
            'COOLANT_TEMP': round(coolant_temp, 2),
            'THROTTLE_POS': round(throttle, 2),
            'FUEL_LEVEL': round(fuel_level, 2),
            'ENGINE_LOAD': round(engine_load, 2),
            'INTAKE_TEMP': round(intake_temp, 2),
            'MAF': round(maf, 2)
        }
        
        data.append(entry)
        
    # Write to file in appropriate format
    try:
        if file_ext == '.csv':
            with open(output_file, 'w', newline='') as f:
                if data:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
        elif file_ext == '.json':
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            logger.error(f"Unsupported file format: {file_ext}")
            return False
            
        logger.info(f"Sample log file created with {len(data)} entries")
        return True
    except Exception as e:
        logger.error(f"Error creating log file: {e}")
        return False

def create_real_world_log_file(output_file: str, duration_minutes: int = 30) -> bool:
    """
    Create a more realistic log file with complex driving patterns.
    
    Args:
        output_file: Path to the output file
        duration_minutes: Duration of the log in minutes
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Calculate number of entries (1 per second)
    num_entries = duration_minutes * 60
    
    # Driving phases
    phases = [
        # Start car, warm up (5 minutes)
        {'duration': 5*60, 'scenario': 'idle'},
        
        # City driving (10 minutes)
        {'duration': 10*60, 'scenario': 'city'},
        
        # Highway driving (10 minutes)
        {'duration': 10*60, 'scenario': 'highway'},
        
        # Return to city (5 minutes)
        {'duration': 5*60, 'scenario': 'city'}
    ]
    
    # Generate data for each phase
    all_data = []
    current_time = datetime.now()
    
    # Initial car state
    rpm = 0
    speed = 0
    coolant_temp = 20
    throttle = 0
    fuel_level = 90
    engine_running = False
    
    for phase in phases:
        scenario = phase['scenario']
        duration = phase['duration']
        
        for i in range(duration):
            # Timestamp
            timestamp = current_time + timedelta(seconds=len(all_data))
            
            # Phase-specific behavior
            if scenario == 'idle':
                if i == 0 and not engine_running:
                    # Start engine
                    engine_running = True
                    rpm = 1000  # Initial higher RPM when starting
                    throttle = 0
                    
                # Idle behavior - engine warming up
                rpm = random.uniform(750, 850)
                speed = 0
                throttle = random.uniform(0, 5)
                coolant_temp = min(90, coolant_temp + 0.3)
                
            elif scenario == 'city':
                if not engine_running:
                    # Start engine if not running
                    engine_running = True
                    rpm = 1000
                    
                # City patterns - traffic lights etc.
                cycle_position = i % 60  # 60-second traffic light cycle
                
                if cycle_position < 15:
                    # Stopped at light
                    rpm = random.uniform(750, 850)
                    speed = 0
                    throttle = random.uniform(0, 5)
                elif cycle_position < 25:
                    # Accelerating from light
                    rpm = min(3000, rpm + random.uniform(50, 200))
                    speed = min(50, speed + random.uniform(1, 4))
                    throttle = min(60, throttle + random.uniform(1, 10))
                elif cycle_position < 50:
                    # Cruising
                    rpm = 1800 + random.uniform(-200, 200)
                    speed = 40 + random.uniform(-5, 5)
                    throttle = 20 + random.uniform(-5, 5)
                else:
                    # Slowing for next light
                    rpm = max(800, rpm - random.uniform(50, 200))
                    speed = max(0, speed - random.uniform(1, 5))
                    throttle = max(0, throttle - random.uniform(2, 10))
                    
            elif scenario == 'highway':
                if i < 60:
                    # Highway entry ramp
                    rpm = min(3500, rpm + random.uniform(20, 70))
                    speed = min(100, speed + random.uniform(1, 3))
                    throttle = min(70, 40 + random.uniform(0, 5))
                elif i < duration - 60:
                    # Highway cruising with occasional speed changes
                    if i % 120 < 20:
                        # Passing another vehicle
                        rpm = 3000 + random.uniform(-100, 100)
                        speed = min(120, speed + random.uniform(0, 2))
                        throttle = 50 + random.uniform(-5, 5)
                    else:
                        # Normal cruising
                        rpm = 2500 + random.uniform(-100, 100)
                        speed = max(90, min(110, speed + random.uniform(-1, 1)))
                        throttle = 30 + random.uniform(-3, 3)
                else:
                    # Approaching exit
                    rpm = max(1200, rpm - random.uniform(10, 30))
                    speed = max(60, speed - random.uniform(0.5, 1.5))
                    throttle = max(10, throttle - random.uniform(0.5, 1.5))
                    
            # Calculate other values based on primary ones
            engine_load = (rpm / 6000) * 100
            intake_temp = 20 + (rpm / 3000) * 15
            maf = 5 + (rpm / 1000) * 10 * (1 + throttle / 100)
            
            # Reduce fuel gradually (more at higher RPM/load)
            consumption_factor = 0.01 * (1 + engine_load / 100)
            fuel_level = max(0, fuel_level - consumption_factor)
            
            # Engine temperature behavior
            if engine_running:
                # Warm up slowly, then stabilize
                if coolant_temp < 85:
                    coolant_temp = min(90, coolant_temp + 0.1 + (0.2 * engine_load / 100))
                else:
                    coolant_temp = 90 + random.uniform(-2, 2)
            else:
                # Cool down when engine off
                coolant_temp = max(20, coolant_temp - 0.05)
            
            # Create log entry
            entry = {
                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'RPM': round(rpm, 2),
                'SPEED': round(speed, 2),
                'COOLANT_TEMP': round(coolant_temp, 2),
                'THROTTLE_POS': round(throttle, 2),
                'FUEL_LEVEL': round(fuel_level, 2),
                'ENGINE_LOAD': round(engine_load, 2),
                'INTAKE_TEMP': round(intake_temp, 2),
                'MAF': round(maf, 2)
            }
            
            all_data.append(entry)
    
    # Write to file
    try:
        file_ext = os.path.splitext(output_file)[1].lower()
        
        if file_ext == '.csv':
            with open(output_file, 'w', newline='') as f:
                if all_data:
                    writer = csv.DictWriter(f, fieldnames=all_data[0].keys())
                    writer.writeheader()
                    writer.writerows(all_data)
        elif file_ext == '.json':
            with open(output_file, 'w') as f:
                json.dump(all_data, f, indent=2)
        else:
            logger.error(f"Unsupported file format: {file_ext}")
            return False
            
        logger.info(f"Real-world log file created with {len(all_data)} entries")
        return True
    except Exception as e:
        logger.error(f"Error creating log file: {e}")
        return False