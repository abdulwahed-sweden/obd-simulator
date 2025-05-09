# File: obd_simulator/ui/dashboard.py
"""
GUI dashboard for visualizing OBD-II data.
"""

import time
import threading
from typing import Dict, List, Any, Optional
import logging
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
from collections import deque

logger = logging.getLogger(__name__)

class Dashboard:
    """
    GUI dashboard for visualizing OBD-II data using matplotlib.
    """
    
    def __init__(self, simulator):
        """
        Initialize the dashboard.
        
        Args:
            simulator: OBD-II simulator instance
        """
        self.simulator = simulator
        self.running = False
        self.thread = None
        
        # Set up the figure with multiple subplots
        self.fig, self.axes = plt.subplots(2, 2, figsize=(12, 8))
        self.fig.suptitle('OBD-II Simulator Dashboard', fontsize=16)
        
        # Flatten axes for easier iteration
        self.axes = self.axes.flatten()
        
        # Set up data storage for time-series
        self.history_length = 100  # Number of points to keep
        self.time_points = deque(maxlen=self.history_length)
        
        # Data for each parameter
        self.data = {
            'RPM': deque(maxlen=self.history_length),
            'SPEED': deque(maxlen=self.history_length),
            'COOLANT_TEMP': deque(maxlen=self.history_length),
            'THROTTLE_POS': deque(maxlen=self.history_length)
        }
        
        # Set up initial plots
        self._setup_plots()
        
    def _setup_plots(self):
        """Set up the initial plot configuration"""
        # RPM gauge (top left)
        self.axes[0].set_title('Engine RPM')
        self.axes[0].set_xlim(0, 8000)
        self.axes[0].set_ylim(0, 1)
        self.rpm_line = self.axes[0].barh(0.5, 0, color='red', height=0.3)
        self.axes[0].set_yticks([])
        
        # Speed gauge (top right)
        self.axes[1].set_title('Vehicle Speed (km/h)')
        self.axes[1].set_xlim(0, 200)
        self.axes[1].set_ylim(0, 1)
        self.speed_line = self.axes[1].barh(0.5, 0, color='blue', height=0.3)
        self.axes[1].set_yticks([])
        
        # Temperature plot (bottom left)
        self.axes[2].set_title('Engine Temperature (°C)')
        self.axes[2].set_xlim(0, self.history_length)
        self.axes[2].set_ylim(0, 120)
        self.temp_line, = self.axes[2].plot([], [], 'g-')
        
        # Throttle plot (bottom right)
        self.axes[3].set_title('Throttle Position (%)')
        self.axes[3].set_xlim(0, self.history_length)
        self.axes[3].set_ylim(0, 100)
        self.throttle_line, = self.axes[3].plot([], [], 'y-')
        
        # Adjust layout
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        
    def _update_plots(self, frame):
        """Update the plots with new data"""
        # Get commands for querying data
        rpm_cmd = None
        speed_cmd = None
        temp_cmd = None
        throttle_cmd = None
        
        # Find the commands in supported_commands
        for cmd in self.simulator.supported_commands:
            if hasattr(cmd, 'name'):
                if cmd.name == 'RPM':
                    rpm_cmd = cmd
                elif cmd.name == 'SPEED':
                    speed_cmd = cmd
                elif cmd.name == 'COOLANT_TEMP':
                    temp_cmd = cmd
                elif cmd.name == 'THROTTLE_POS':
                    throttle_cmd = cmd
        
        # Query the simulator for data
        rpm_response = self.simulator.query(rpm_cmd) if rpm_cmd else None
        speed_response = self.simulator.query(speed_cmd) if speed_cmd else None
        temp_response = self.simulator.query(temp_cmd) if temp_cmd else None
        throttle_response = self.simulator.query(throttle_cmd) if throttle_cmd else None
        
        # Get current time
        current_time = len(self.time_points)
        self.time_points.append(current_time)
        
        # Update RPM gauge
        if rpm_response and not rpm_response.is_null():
            rpm = rpm_response.value.magnitude
            self.data['RPM'].append(rpm)
            self.rpm_line[0].set_width(rpm)
            
        # Update Speed gauge
        if speed_response and not speed_response.is_null():
            speed = speed_response.value.magnitude
            self.data['SPEED'].append(speed)
            self.speed_line[0].set_width(speed)
            
        # Update Temperature plot
        if temp_response and not temp_response.is_null():
            temp = temp_response.value.magnitude
            self.data['COOLANT_TEMP'].append(temp)
            self.temp_line.set_data(list(range(len(self.data['COOLANT_TEMP']))), 
                                  list(self.data['COOLANT_TEMP']))
            
        # Update Throttle plot
        if throttle_response and not throttle_response.is_null():
            throttle = throttle_response.value.magnitude
            self.data['THROTTLE_POS'].append(throttle)
            self.throttle_line.set_data(list(range(len(self.data['THROTTLE_POS']))), 
                                      list(self.data['THROTTLE_POS']))
            
        # Return all artists that need to be redrawn
        return [self.rpm_line[0], self.speed_line[0], self.temp_line, self.throttle_line]
        
    def run(self):
        """Run the dashboard"""
        self.running = True
        
        # Create animation
        self.animation = FuncAnimation(
            self.fig, self._update_plots, interval=100, blit=True)
        
        # Show the dashboard
        plt.show()
        
        # When window is closed, stop the simulator
        self.running = False
        
    def close(self):
        """Close the dashboard"""
        self.running = False
        plt.close(self.fig)
        

def main():
    """Main entry point for the dashboard"""
    from obd_simulator.mock_simulator.simulator import Simulator
    
    # Create simulator
    simulator = Simulator()
    simulator.connect()
    
    try:
        # Create and run dashboard
        dashboard = Dashboard(simulator)
        dashboard.run()
    finally:
        simulator.close()
        
if __name__ == "__main__":
    main()
