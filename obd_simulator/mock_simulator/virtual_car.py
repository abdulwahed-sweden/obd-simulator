# File: obd_simulator/mock_simulator/virtual_car.py
"""
Virtual Car implementation that simulates vehicle behavior.
"""

import time
import random
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class VirtualCar:
    """
    A virtual car that simulates realistic vehicle behavior.
    
    This class models basic vehicle dynamics and parameters including
    engine operation, fuel consumption, and sensor readings.
    """
    
    def __init__(self, **kwargs):
        """
        Initialize a virtual car with optional parameter overrides.
        
        Args:
            **kwargs: Optional parameter overrides
        """
        # Car state variables
        self.ignition = False
        self.engine_running = False
        self.throttle = 0  # 0-100%
        self.rpm = 0
        self.speed = 0
        self.coolant_temp = 20  # Start at ambient temp
        self.fuel_level = 75
        self.fuel_consumption_rate = 0.02  # % per second at idle
        self.intake_temp = 20
        self.maf = 0
        self.engine_load = 0
        
        # Car parameters (customizable)
        self.idle_rpm = kwargs.get('idle_rpm', 800)
        self.redline_rpm = kwargs.get('redline_rpm', 6500)
        self.max_speed = kwargs.get('max_speed', 180)
        self.rpm_per_throttle = kwargs.get('rpm_per_throttle', 50)  # RPM increase per throttle %
        self.speed_per_rpm = kwargs.get('speed_per_rpm', 0.03)   # kph per RPM in top gear
        self.normal_coolant_temp = kwargs.get('normal_coolant_temp', 90)
        
        # Behavior simulation
        self.warming_up = False
        self.warming_up_time = 0
        self.last_update_time = time.time()
        
        logger.info("Virtual car initialized")
        
    def start_engine(self) -> bool:
        """
        Start the car engine.
        
        Returns:
            bool: True if engine started successfully, False otherwise
        """
        if not self.ignition:
            logger.info("Starting engine")
            self.ignition = True
            self.engine_running = True
            self.rpm = self.idle_rpm
            self.warming_up = True
            self.warming_up_time = time.time()
            return True
        return False
        
    def stop_engine(self) -> bool:
        """
        Stop the car engine.
        
        Returns:
            bool: True if engine stopped successfully, False otherwise
        """
        if self.ignition:
            logger.info("Stopping engine")
            self.ignition = False
            self.engine_running = False
            self.rpm = 0
            self.speed = 0
            self.throttle = 0
            self.warming_up = False
            self.engine_load = 0
            self.maf = 0
            return True
        return False
        
    def set_throttle(self, throttle_percent: float) -> bool:
        """
        Set the throttle position (0-100%).
        
        Args:
            throttle_percent: Throttle position in percent (0-100)
            
        Returns:
            bool: True if throttle was set successfully, False otherwise
        """
        if not self.engine_running:
            return False
            
        self.throttle = max(0, min(100, throttle_percent))
        logger.info(f"Throttle set to {self.throttle:.1f}%")
        return True
        
    def update(self, dt: float) -> None:
        """
        Update the car state based on elapsed time (in seconds).
        
        Args:
            dt: Time elapsed since last update in seconds
        """
        if not self.engine_running:
            return
            
        # Engine warmup simulation
        if self.warming_up:
            warmup_elapsed = time.time() - self.warming_up_time
            if warmup_elapsed > 180:  # 3 minutes to warm up
                self.warming_up = False
                self.coolant_temp = self.normal_coolant_temp
            else:
                # Gradually increase temperature
                target_temp = self.normal_coolant_temp
                self.coolant_temp = min(
                    target_temp,
                    20 + (target_temp - 20) * (warmup_elapsed / 180)
                )
                
        # RPM simulation - responds to throttle with some randomness
        target_rpm = self.idle_rpm + (self.throttle * self.rpm_per_throttle)
        rpm_noise = random.uniform(-50, 50)  # Slight fluctuation
        self.rpm = max(self.idle_rpm, min(self.redline_rpm, 
                                           target_rpm + rpm_noise))
        
        # Speed simulation - simplified gear model
        target_speed = self.rpm * self.speed_per_rpm
        if self.throttle < 5:  # Coasting
            self.speed = max(0, self.speed - 2 * dt)
        else:
            # Accelerate more slowly than decelerate
            speed_diff = target_speed - self.speed
            speed_change = speed_diff * 0.2 * dt  # Gradual acceleration
            self.speed = max(0, min(self.max_speed, self.speed + speed_change))
        
        # Fuel consumption
        consumption_rate = self.fuel_consumption_rate
        if self.throttle > 10:
            consumption_rate *= (1 + (self.throttle / 50))
        self.fuel_level = max(0, self.fuel_level - consumption_rate * dt)
        
        # Engine load calculation
        self.engine_load = (self.rpm / self.redline_rpm) * 100
        
        # MAF calculation (simplified)
        self.maf = 5 + (self.rpm / 1000) * 10 * (1 + self.throttle / 100)
        
        # Intake temperature (affected by engine temperature and speed)
        self.intake_temp = 20 + (self.rpm / self.redline_rpm) * 15
        
    def get_data(self) -> Dict[str, Any]:
        """
        Get the current car data as a dictionary.
        
        Returns:
            Dict[str, Any]: Current vehicle parameter values
        """
        return {
            'engine_running': self.engine_running,
            'rpm': self.rpm,
            'speed': self.speed,
            'throttle': self.throttle,
            'coolant_temp': self.coolant_temp,
            'fuel_level': self.fuel_level,
            'intake_temp': self.intake_temp,
            'maf': self.maf,
            'engine_load': self.engine_load
        }
