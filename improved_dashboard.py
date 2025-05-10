# File: minimal_car_dashboard.py
"""
محاكي لوحة قيادة سيارة بسيطة باستخدام PyQt5
تصميم بسيط مع التركيز على النصوص والقيم
"""

import sys
import time
import random
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QSlider, QPushButton, QGridLayout,
                            QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QColor, QPalette, QFontDatabase
import numpy as np

# Import the simulator
from obd_simulator.mock_simulator.simulator import Simulator
from obd_simulator.common.obd_command import OBDCommand

# Define theme colors
COLORS = {
    'background': QColor('#192445'),      # Dark blue background
    'panel_bg': QColor('#1A2851'),        # Slightly lighter for panels
    'text': QColor('#CCCCCC'),            # Light gray text
    'value': QColor('#FFFFFF'),           # White for values
    'warning': QColor('#FF3B30'),         # Red for warnings
    'active': QColor('#26E07F'),          # Green for active indicators
    'inactive': QColor('#555555'),        # Dark gray for inactive elements
    'slider_bg': QColor('#333333'),       # Dark for slider background
    'slider_fg': QColor('#26E07F')        # Green for slider foreground
}

class DataCollectorThread(QThread):
    """Thread for collecting data from the simulator"""
    data_updated = pyqtSignal(dict)
    
    def __init__(self, simulator):
        super().__init__()
        self.simulator = simulator
        self.running = True
        
    def run(self):
        while self.running:
            if self.simulator.is_connected():
                data = {}
                # Query all supported commands
                for cmd in self.simulator.supported_commands:
                    response = self.simulator.query(cmd)
                    if not response.is_null():
                        data[cmd.name] = response.value.magnitude
                
                # Emit the data
                self.data_updated.emit(data)
            
            # Sleep to control update rate
            time.sleep(0.1)
            
    def stop(self):
        self.running = False
        self.wait()

class ValueDisplay(QFrame):
    """Simple display for a value with label"""
    
    def __init__(self, title, units="", warning_threshold=None, parent=None):
        super().__init__(parent)
        self.title = title
        self.units = units
        self.warning_threshold = warning_threshold
        self.value = 0
        self.warning_active = False
        
        # Set frame style
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet(f"""
            background-color: {COLORS['panel_bg'].name()};
            border-radius: 5px;
            padding: 10px;
        """)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(5)
        
        # Create label for title
        self.title_label = QLabel(self.title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont("Arial", 12))
        self.title_label.setStyleSheet(f"color: {COLORS['text'].name()};")
        
        # Create label for value
        self.value_label = QLabel("0")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setFont(QFont("Arial", 36, QFont.Bold))
        self.value_label.setStyleSheet(f"color: {COLORS['value'].name()};")
        
        # Create label for units
        self.units_label = QLabel(self.units)
        self.units_label.setAlignment(Qt.AlignCenter)
        self.units_label.setFont(QFont("Arial", 12))
        self.units_label.setStyleSheet(f"color: {COLORS['text'].name()};")
        
        # Add to layout
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label, 1)  # Give it more space
        if self.units:
            layout.addWidget(self.units_label)
        
    def update_value(self, value):
        """Update the displayed value"""
        self.value = value
        
        # Format value
        if abs(value) >= 1000:
            formatted_value = f"{value/1000:.1f}k"
        else:
            formatted_value = f"{int(value)}"
            
        self.value_label.setText(formatted_value)
        
        # Check warning threshold
        if self.warning_threshold is not None:
            is_warning = value >= self.warning_threshold
            if is_warning != self.warning_active:
                self.warning_active = is_warning
                color = COLORS['warning'].name() if is_warning else COLORS['value'].name()
                self.value_label.setStyleSheet(f"color: {color};")

class WarningIndicator(QFrame):
    """Simple text-based warning indicator"""
    
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        self.active = False
        
        # Set frame style
        self.setFrameShape(QFrame.NoFrame)
        self.setFixedHeight(40)
        self.setStyleSheet(f"""
            background-color: {COLORS['inactive'].name()};
            border-radius: 5px;
            padding: 5px;
        """)
        
        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        
        # Create label
        self.label = QLabel(self.title)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFont(QFont("Arial", 10))
        self.label.setStyleSheet(f"color: {COLORS['text'].name()};")
        
        # Add to layout
        layout.addWidget(self.label)
        
    def set_active(self, active):
        """Set whether the warning is active"""
        if active != self.active:
            self.active = active
            bg_color = COLORS['warning'].name() if active else COLORS['inactive'].name()
            text_color = COLORS['value'].name() if active else COLORS['text'].name()
            self.setStyleSheet(f"""
                background-color: {bg_color};
                border-radius: 5px;
                padding: 5px;
            """)
            self.label.setStyleSheet(f"color: {text_color};")

class MinimalDashboard(QMainWindow):
    """Minimalist car dashboard window"""
    
    def __init__(self):
        super().__init__()
        
        # Create and connect to the simulator
        self.simulator = Simulator()
        self.simulator.connect()
        
        # Set up the UI
        self.init_ui()
        
        # Start data collection
        self.data_thread = DataCollectorThread(self.simulator)
        self.data_thread.data_updated.connect(self.update_dashboard)
        self.data_thread.start()
        
        # Set timer for random warning lights (for demonstration)
        self.warning_timer = QTimer()
        self.warning_timer.timeout.connect(self.update_random_warning)
        self.warning_timer.start(5000)  # 5 seconds
        
    def init_ui(self):
        """Initialize the user interface"""
        # Set window properties
        self.setWindowTitle("Minimal Car Dashboard")
        self.setGeometry(100, 100, 900, 500)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Apply theme
        self.apply_theme()
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Create warning indicators panel
        warnings_panel = QFrame()
        warnings_panel.setFrameShape(QFrame.NoFrame)
        warnings_panel.setMaximumHeight(50)
        
        warnings_layout = QHBoxLayout(warnings_panel)
        warnings_layout.setSpacing(10)
        
        # Create warning indicators
        self.warnings = {
            'engine': WarningIndicator("ENGINE"),
            'oil': WarningIndicator("OIL"),
            'battery': WarningIndicator("BATTERY"),
            'brake': WarningIndicator("BRAKE"),
            'airbag': WarningIndicator("AIRBAG"),
            'steering': WarningIndicator("POWER STEERING")
        }
        
        # Add warning indicators to layout
        for warning in self.warnings.values():
            warnings_layout.addWidget(warning)
        
        # Create main values display layout
        values_layout = QGridLayout()
        values_layout.setSpacing(15)
        
        # Create value displays
        self.speed_display = ValueDisplay("SPEED", "km/h")
        self.rpm_display = ValueDisplay("RPM", "", warning_threshold=6000)
        self.temp_display = ValueDisplay("TEMPERATURE", "°C", warning_threshold=100)
        self.fuel_display = ValueDisplay("FUEL", "%")
        
        # Add value displays to layout - 2 columns
        values_layout.addWidget(self.speed_display, 0, 0)
        values_layout.addWidget(self.rpm_display, 0, 1)
        values_layout.addWidget(self.temp_display, 1, 0)
        values_layout.addWidget(self.fuel_display, 1, 1)
        
        # Create info panel
        info_panel = QFrame()
        info_panel.setFrameShape(QFrame.NoFrame)
        info_panel.setMaximumHeight(80)
        info_panel.setStyleSheet(f"""
            background-color: {COLORS['panel_bg'].name()};
            border-radius: 5px;
            padding: 10px;
        """)
        
        info_layout = QHBoxLayout(info_panel)
        info_layout.setSpacing(30)
        
        # Create info items
        self.info_items = {}
        info_configs = [
            ("TRIP", "trip", "1049 km"),
            ("AMBIENT", "ambient", "20.5 °C"),
            ("ENGINE LOAD", "load", "0 %")
        ]
        
        for title, key, initial_value in info_configs:
            container = QFrame()
            layout = QVBoxLayout(container)
            
            # Title label
            title_label = QLabel(title)
            title_label.setAlignment(Qt.AlignCenter)
            title_label.setFont(QFont("Arial", 10))
            title_label.setStyleSheet(f"color: {COLORS['text'].name()};")
            
            # Value label
            value_label = QLabel(initial_value)
            value_label.setAlignment(Qt.AlignCenter)
            value_label.setFont(QFont("Arial", 16, QFont.Bold))
            value_label.setStyleSheet(f"color: {COLORS['value'].name()};")
            
            # Add to layout
            layout.addWidget(title_label)
            layout.addWidget(value_label)
            
            # Add to info layout
            info_layout.addWidget(container)
            
            # Store reference
            self.info_items[key] = value_label
        
        # Create controls panel
        controls_panel = QFrame()
        controls_panel.setFrameShape(QFrame.NoFrame)
        controls_panel.setMaximumHeight(70)
        controls_panel.setStyleSheet(f"""
            background-color: {COLORS['panel_bg'].name()};
            border-radius: 5px;
            padding: 10px;
        """)
        
        controls_layout = QHBoxLayout(controls_panel)
        controls_layout.setSpacing(20)
        
        # Create throttle label
        throttle_label = QLabel("THROTTLE")
        throttle_label.setFont(QFont("Arial", 12))
        throttle_label.setStyleSheet(f"color: {COLORS['text'].name()};")
        
        # Create throttle slider
        self.throttle_slider = QSlider(Qt.Horizontal)
        self.throttle_slider.setRange(0, 100)
        self.throttle_slider.setValue(0)
        self.throttle_slider.valueChanged.connect(self.set_throttle)
        self.throttle_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {COLORS['slider_bg'].name()};
                height: 8px;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {COLORS['value'].name()};
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }}
            QSlider::sub-page:horizontal {{
                background: {COLORS['slider_fg'].name()};
                border-radius: 4px;
            }}
        """)
        
        # Create engine button
        self.engine_button = QPushButton("STOP ENGINE")
        self.engine_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.engine_button.clicked.connect(self.toggle_engine)
        self.engine_button.setMinimumWidth(150)
        self.engine_button.setMinimumHeight(40)
        self.engine_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['warning'].name()};
                color: {COLORS['value'].name()};
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['warning'].lighter(120).name()};
            }}
        """)
        
        # Add to controls layout
        controls_layout.addWidget(throttle_label)
        controls_layout.addWidget(self.throttle_slider, 1)
        controls_layout.addWidget(self.engine_button)
        
        # Add all panels to main layout
        main_layout.addWidget(warnings_panel)
        main_layout.addLayout(values_layout, 3)
        main_layout.addWidget(info_panel)
        main_layout.addWidget(controls_panel)
        
    def apply_theme(self):
        """Apply a minimal dark theme to the window"""
        # Set application font
        default_font = QFont("Arial", 10)
        QApplication.setFont(default_font)
        
        # Set color palette
        palette = QPalette()
        palette.setColor(QPalette.Window, COLORS['background'])
        palette.setColor(QPalette.WindowText, COLORS['text'])
        palette.setColor(QPalette.Base, COLORS['panel_bg'])
        palette.setColor(QPalette.Text, COLORS['text'])
        palette.setColor(QPalette.Button, COLORS['panel_bg'])
        palette.setColor(QPalette.ButtonText, COLORS['text'])
        
        self.setPalette(palette)
        
        # Set window style
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {COLORS['background'].name()};
            }}
            QLabel {{
                color: {COLORS['text'].name()};
            }}
        """)
        
    def update_dashboard(self, data):
        """Update the dashboard with new data"""
        # Update RPM display
        if 'RPM' in data:
            self.rpm_display.update_value(data['RPM'])
        
        # Update speed display
        if 'SPEED' in data:
            self.speed_display.update_value(data['SPEED'])
        
        # Update temperature display
        if 'COOLANT_TEMP' in data:
            temp = data['COOLANT_TEMP']
            self.temp_display.update_value(temp)
            
            # Update warning light if temperature is too high
            self.warnings['engine'].set_active(temp > 100)
        
        # Update fuel display
        if 'FUEL_LEVEL' in data:
            self.fuel_display.update_value(data['FUEL_LEVEL'])
        
        # Update engine load info
        if 'ENGINE_LOAD' in data:
            self.info_items['load'].setText(f"{data['ENGINE_LOAD']:.1f} %")
        
    def update_random_warning(self):
        """Randomly toggle warning indicators for demonstration"""
        # Skip engine warning as it's controlled by temperature
        warning_types = ['oil', 'battery', 'brake', 'airbag', 'steering']
        for warning_type in warning_types:
            # 10% chance to toggle
            if random.random() < 0.1:
                indicator = self.warnings[warning_type]
                indicator.set_active(not indicator.active)
        
    def set_throttle(self, value):
        """Set the throttle position"""
        self.simulator.set_throttle(value)
        
    def toggle_engine(self):
        """Toggle the engine state"""
        if self.simulator.car.engine_running:
            self.simulator.car.stop_engine()
            self.engine_button.setText("START ENGINE")
            self.engine_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['active'].name()};
                    color: {COLORS['value'].name()};
                    border: none;
                    border-radius: 5px;
                    padding: 8px 15px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['active'].lighter(120).name()};
                }}
            """)
            
            # Reset displays to zero
            self.rpm_display.update_value(0)
            self.speed_display.update_value(0)
        else:
            self.simulator.car.start_engine()
            self.engine_button.setText("STOP ENGINE")
            self.engine_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['warning'].name()};
                    color: {COLORS['value'].name()};
                    border: none;
                    border-radius: 5px;
                    padding: 8px 15px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['warning'].lighter(120).name()};
                }}
            """)
            
    def closeEvent(self, event):
        """Handle window close event"""
        # Stop the data thread
        if self.data_thread.isRunning():
            self.data_thread.stop()
            
        # Stop the warning timer
        self.warning_timer.stop()
            
        # Close the simulator
        self.simulator.close()
        
        # Accept the event
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Create and show the dashboard
    dashboard = MinimalDashboard()
    dashboard.show()
    
    sys.exit(app.exec_())