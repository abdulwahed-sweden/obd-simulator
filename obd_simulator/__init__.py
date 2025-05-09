"""
OBD-II Simulator Package

A comprehensive OBD-II vehicle diagnostic simulator that works without requiring physical hardware.
This package provides multiple methods to simulate OBD-II interfaces for development, testing, 
and educational purposes.
"""

__version__ = "0.1.0"
__author__ = "Abdulwahed Mansour"

# Import main classes for easy access
from obd_simulator.mock_simulator.simulator import Simulator as MockSimulator
from obd_simulator.virtual_com.elm327_device import ELM327Device as VirtualComSimulator
from obd_simulator.log_playback.log_player import LogPlayer
from obd_simulator.port_detector.auto_detect import OBDPortDetector