# obd-simulator

"""
Project README file
"""
# OBD-II Simulator

A comprehensive OBD-II vehicle diagnostic simulator that works without requiring physical hardware.

## Features

- **No Hardware Required**: Develop and test OBD-II applications without a real car or adapter
- **Multiple Simulation Methods**: Choose from four different simulation approaches
- **Python-OBD Compatible**: Drop-in replacement for the popular python-OBD library
- **Realistic Vehicle Behavior**: Simulates realistic vehicle parameters and driving scenarios
- **Data Visualization**: Built-in dashboard for visualizing vehicle data

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

## Quick Start

```python
from obd_simulator.mock_simulator import Simulator

# Create and connect to simulator
simulator = Simulator()
simulator.connect()

# Query vehicle data
rpm = simulator.query(simulator.supported_commands[0])
print(f"Engine RPM: {rpm.value}")

# Close the connection
simulator.close()
```

## Dashboard

```bash
# Start the dashboard
python -m obd_simulator.ui.dashboard
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
