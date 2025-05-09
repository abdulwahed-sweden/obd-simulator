# File: obd_simulator/ui/widgets.py
"""
Custom widgets for OBD-II simulator UI.
"""

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from typing import Dict, List, Any, Optional

class GaugeWidget(ttk.Frame):
    """
    Custom gauge widget for displaying OBD-II data.
    """
    
    def __init__(self, parent, title: str, min_value: float = 0, max_value: float = 100,
                unit: str = "", **kwargs):
        """
        Initialize the gauge widget.
        
        Args:
            parent: Parent widget
            title: Gauge title
            min_value: Minimum value
            max_value: Maximum value
            unit: Unit of measurement
            **kwargs: Additional keyword arguments
        """
        ttk.Frame.__init__(self, parent, **kwargs)
        
        self.title = title
        self.min_value = min_value
        self.max_value = max_value
        self.unit = unit
        self.value = min_value
        
        # Create figure and axis
        self.fig, self.ax = plt.subplots(figsize=(3, 3))
        
        # Set up gauge
        self.gauge = self.ax.pie(
            [0, 1], 
            startangle=90, 
            colors=['red', 'lightgray'], 
            wedgeprops={'width': 0.3}
        )
        
        # Add center text
        self.value_text = self.ax.text(
            0, 0, f"{self.value:.1f}\n{self.unit}", 
            ha='center', va='center', fontsize=12
        )
        
        # Add title
        self.ax.set_title(self.title)
        
        # Set aspect ratio and remove axis
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def update_value(self, value: float):
        """
        Update the gauge value.
        
        Args:
            value: New value
        """
        self.value = max(self.min_value, min(self.max_value, value))
        
        # Update gauge
        ratio = (self.value - self.min_value) / (self.max_value - self.min_value)
        self.gauge[0][0].set_value(ratio)
        self.gauge[0][1].set_value(1 - ratio)
        
        # Update text
        self.value_text.set_text(f"{self.value:.1f}\n{self.unit}")
        
        # Redraw
        self.canvas.draw()

class GraphWidget(ttk.Frame):
    """
    Custom graph widget for displaying OBD-II data.
    """
    
    def __init__(self, parent, title: str, min_value: float = 0, max_value: float = 100,
                unit: str = "", history_length: int = 100, **kwargs):
        """
        Initialize the graph widget.
        
        Args:
            parent: Parent widget
            title: Graph title
            min_value: Minimum value
            max_value: Maximum value
            unit: Unit of measurement
            history_length: Number of points to keep
            **kwargs: Additional keyword arguments
        """
        ttk.Frame.__init__(self, parent, **kwargs)
        
        self.title = title
        self.min_value = min_value
        self.max_value = max_value
        self.unit = unit
        self.history_length = history_length
        
        # Data storage
        self.x_data = np.arange(history_length)
        self.y_data = np.zeros(history_length)
        
        # Create figure and axis
        self.fig, self.ax = plt.subplots(figsize=(5, 3))
        
        # Set up plot
        self.line, = self.ax.plot(self.x_data, self.y_data, 'b-')
        
        # Set axis limits
        self.ax.set_xlim(0, history_length - 1)
        self.ax.set_ylim(min_value, max_value)
        
        # Add labels
        self.ax.set_title(title)
        self.ax.set_ylabel(unit)
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def update_value(self, value: float):
        """
        Update the graph with a new value.
        
        Args:
            value: New value
        """
        # Shift data to the left
        self.y_data = np.roll(self.y_data, -1)
        
        # Add new value
        self.y_data[-1] = max(self.min_value, min(self.max_value, value))
        
        # Update plot
        self.line.set_ydata(self.y_data)
        
        # Redraw
        self.canvas.draw()

class FullDashboard(tk.Tk):
    """
    Full dashboard for OBD-II simulator.
    """
    
    def __init__(self, simulator):
        """
        Initialize the full dashboard.
        
        Args:
            simulator: OBD-II simulator instance
        """
        tk.Tk.__init__(self)
        
        self.simulator = simulator
        self.title("OBD-II Simulator Dashboard")
        self.geometry("800x600")
        
        # Create main frame
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create gauge frame
        self.gauge_frame = ttk.Frame(self.main_frame)
        self.gauge_frame.pack(fill=tk.X, expand=False, pady=10)
        
        # Create RPM gauge
        self.rpm_gauge = GaugeWidget(
            self.gauge_frame, 
            title="Engine RPM", 
            min_value=0, 
            max_value=8000, 
            unit="rpm"
        )
        self.rpm_gauge.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Create speed gauge
        self.speed_gauge = GaugeWidget(
            self.gauge_frame, 
            title="Vehicle Speed", 
            min_value=0, 
            max_value=200, 
            unit="km/h"
        )
        self.speed_gauge.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Create graph frame
        self.graph_frame = ttk.Frame(self.main_frame)
        self.graph_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create temperature graph
        self.temp_graph = GraphWidget(
            self.graph_frame, 
            title="Engine Temperature", 
            min_value=0, 
            max_value=120, 
            unit="°C"
        )
        self.temp_graph.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Create throttle graph
        self.throttle_graph = GraphWidget(
            self.graph_frame, 
            title="Throttle Position", 
            min_value=0, 
            max_value=100, 
            unit="%"
        )
        self.throttle_graph.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Create control frame
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.pack(fill=tk.X, expand=False, pady=10)
        
        # Create throttle slider
        ttk.Label(self.control_frame, text="Throttle:").pack(side=tk.LEFT, padx=5)
        self.throttle_slider = ttk.Scale(
            self.control_frame, 
            from_=0, 
            to=100, 
            orient=tk.HORIZONTAL, 
            length=200, 
            command=self._set_throttle
        )
        self.throttle_slider.pack(side=tk.LEFT, padx=5)
        
        # Create engine control buttons
        self.engine_button = ttk.Button(
            self.control_frame, 
            text="Stop Engine", 
            command=self._toggle_engine
        )
        self.engine_button.pack(side=tk.RIGHT, padx=5)
        
        # Start update timer
        self.after(100, self._update)
        
    def _set_throttle(self, value):
        """Set the throttle position"""
        throttle = float(value)
        self.simulator.set_throttle(throttle)
        
    def _toggle_engine(self):
        """Toggle the engine state"""
        if self.simulator.car.engine_running:
            self.simulator.car.stop_engine()
            self.engine_button.config(text="Start Engine")
        else:
            self.simulator.car.start_engine()
            self.engine_button.config(text="Stop Engine")
            
    def _update(self):
        """Update the dashboard with current data"""
        if not self.simulator.is_connected():
            return
            
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
        
        # Query data
        if rpm_cmd:
            rpm_response = self.simulator.query(rpm_cmd)
            if not rpm_response.is_null():
                rpm = rpm_response.value.magnitude
                self.rpm_gauge.update_value(rpm)
                
        if speed_cmd:
            speed_response = self.simulator.query(speed_cmd)
            if not speed_response.is_null():
                speed = speed_response.value.magnitude
                self.speed_gauge.update_value(speed)
                
        if temp_cmd:
            temp_response = self.simulator.query(temp_cmd)
            if not temp_response.is_null():
                temp = temp_response.value.magnitude
                self.temp_graph.update_value(temp)
                
        if throttle_cmd:
            throttle_response = self.simulator.query(throttle_cmd)
            if not throttle_response.is_null():
                throttle = throttle_response.value.magnitude
                self.throttle_graph.update_value(throttle)
                
                # Update slider if it's not being dragged
                if not self.throttle_slider.state:
                    self.throttle_slider.set(throttle)
                    
        # Schedule next update
        self.after(100, self._update)
        
    def run(self):
        """Run the dashboard"""
        self.mainloop()
        
    def on_closing(self):
        """Handle window closing"""
        # Stop the simulator
        if self.simulator.is_connected():
            self.simulator.close()
            
        # Close the window
        self.destroy()

def run_full_dashboard(simulator=None):
    """
    Run the full dashboard.
    
    Args:
        simulator: OBD-II simulator instance or None to create a new one
    """
    if simulator is None:
        # Create a new simulator
        from obd_simulator.mock_simulator.simulator import Simulator
        simulator = Simulator()
        simulator.connect()
        
    # Create and run dashboard
    dashboard = FullDashboard(simulator)
    dashboard.protocol("WM_DELETE_WINDOW", dashboard.on_closing)
    dashboard.run()