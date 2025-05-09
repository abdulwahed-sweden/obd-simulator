# File: obd_simulator/mock_simulator/vehicle_parameters.py
"""
Default vehicle parameter definitions.
"""

# Standard vehicle profiles
VEHICLE_PROFILES = {
    "sedan": {
        "idle_rpm": 800,
        "redline_rpm": 6500,
        "max_speed": 200,
        "rpm_per_throttle": 50,
        "speed_per_rpm": 0.03,
        "normal_coolant_temp": 90
    },
    "sports_car": {
        "idle_rpm": 900,
        "redline_rpm": 8500,
        "max_speed": 300,
        "rpm_per_throttle": 70,
        "speed_per_rpm": 0.035,
        "normal_coolant_temp": 95
    },
    "truck": {
        "idle_rpm": 700,
        "redline_rpm": 5500,
        "max_speed": 160,
        "rpm_per_throttle": 40,
        "speed_per_rpm": 0.025,
        "normal_coolant_temp": 85
    },
    "electric": {
        "idle_rpm": 0,        # Electric motors don't idle
        "redline_rpm": 15000,  # Higher RPM for electric motors
        "max_speed": 200,
        "rpm_per_throttle": 100,
        "speed_per_rpm": 0.01,
        "normal_coolant_temp": 60  # Lower temp for electric
    }
}

def get_vehicle_profile(profile_name):
    """
    Get a vehicle profile by name.
    
    Args:
        profile_name: Name of the profile
        
    Returns:
        dict: Vehicle parameters or None if not found
    """
    return VEHICLE_PROFILES.get(profile_name.lower())