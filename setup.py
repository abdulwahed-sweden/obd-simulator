# File: setup.py
"""
OBD-II Simulator - Setup configuration
Setup script for installing the OBD-II simulator package
"""

from setuptools import setup, find_packages

setup(
    name="obd_simulator",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pyserial>=3.5",
        "pint>=0.18",
        "matplotlib>=3.5.2",
        "numpy>=1.21.0",
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="OBD-II vehicle diagnostic simulator without requiring hardware",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/obd-simulator",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "obd-simulator=obd_simulator.ui.cli:main",
        ],
    },
)

# File: requirements.txt
"""
Project dependencies for the OBD-II Simulator
"""
pyserial>=3.5
pint>=0.18
matplotlib>=3.5.2
numpy>=1.21.0
pytest>=7.0.0
pandas>=1.3.0

