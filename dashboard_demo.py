# File: improved_dashboard.py
"""
Improved OBD-II Simulator Dashboard using PyQt5, styled to match the provided image.
"""
import sys
import time
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QSlider, QPushButton, QGridLayout)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QColor, QPalette, QPainter, QBrush, QPen, QPixmap
import pyqtgraph as pg
import numpy as np
import math
# Import the simulator
from obd_simulator.mock_simulator.simulator import Simulator
from obd_simulator.common.obd_command import OBDCommand

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

class CustomGauge(QWidget):
    """Custom circular gauge widget using QPainter"""
    def __init__(self, title, min_value, max_value, units, parent=None):
        super().__init__(parent)
        self.title = title
        self.min_value = min_value
        self.max_value = max_value
        self.units = units
        self.value = min_value
        # Set minimum size
        self.setMinimumSize(200, 200)
        # Create a title label
        self.title_label = QLabel(self.title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.title_label.setStyleSheet("color: white;")
        # Create a value label
        self.value_label = QLabel(f"0 {self.units}")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.value_label.setStyleSheet("color: white;")
        # Set up the layout
        layout = QVBoxLayout()
        layout.addWidget(self.title_label)
        layout.addStretch()
        layout.addWidget(self.value_label)
        self.setLayout(layout)

    def update_value(self, value):
        """Update the gauge value"""
        # Clamp the value to range
        self.value = max(self.min_value, min(self.max_value, value))
        # Update the label
        self.value_label.setText(f"{self.value:.1f} {self.units}")
        # Repaint the widget
        self.update()

    def paintEvent(self, event):
        """Paint the gauge"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # Calculate the center and radius
        rect = self.rect()
        center_x = rect.width() / 2
        center_y = rect.height() / 2
        radius = min(center_x, center_y) * 0.8
        # Draw the outer circle
        painter.setPen(QPen(Qt.white, 2))
        painter.drawEllipse(int(center_x - radius), int(center_y - radius), 
                           int(radius * 2), int(radius * 2))
        # Draw the gauge arc (270 degrees, starting from 135 degrees)
        start_angle = 135 * 16  # QT uses 1/16 of a degree
        span_angle = 270 * 16
        # Draw the background arc
        painter.setPen(QPen(Qt.gray, 3))
        painter.drawArc(int(center_x - radius), int(center_y - radius), 
                       int(radius * 2), int(radius * 2), 
                       start_angle, span_angle)
        # Calculate the angle for the current value
        value_ratio = (self.value - self.min_value) / (self.max_value - self.min_value)
        value_angle = value_ratio * 270
        # Draw the value arc
        painter.setPen(QPen(Qt.red, 4))
        painter.drawArc(int(center_x - radius), int(center_y - radius), 
                       int(radius * 2), int(radius * 2), 
                       start_angle, int(value_angle * 16))
        # Draw the needle
        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(135 + value_angle)
        painter.setPen(QPen(Qt.blue, 2))
        painter.drawLine(0, 0, int(radius * 0.7), 0)
        # Draw the needle center
        painter.setBrush(QBrush(Qt.blue))
        painter.drawEllipse(-5, -5, 10, 10)
        painter.restore()
        # Draw tick marks and labels
        painter.setPen(QPen(Qt.black, 1))
        for i in range(11):  # 11 ticks for 0% to 100%
            tick_value = self.min_value + (self.max_value - self.min_value) * i / 10
            tick_angle = 135 + 270 * i / 10
            # Convert to radians
            rad = math.radians(tick_angle)
            # Calculate tick positions
            inner_x = center_x + int((radius - 10) * math.cos(rad))
            inner_y = center_y + int((radius - 10) * math.sin(rad))
            outer_x = center_x + int(radius * math.cos(rad))
            outer_y = center_y + int(radius * math.sin(rad))
            # Draw tick
            painter.drawLine(inner_x, inner_y, outer_x, outer_y)
            # Draw label
            if i % 2 == 0:  # Only draw labels at even positions to avoid crowding
                label_x = center_x + int((radius - 25) * math.cos(rad))
                label_y = center_y + int((radius - 25) * math.sin(rad))
                # Adjust text alignment based on position
                flags = Qt.AlignCenter
                text_rect = painter.fontMetrics().boundingRect(f"{int(tick_value)}")
                painter.drawText(label_x - text_rect.width() // 2, 
                               label_y + text_rect.height() // 2, 
                               f"{int(tick_value)}")

class LineGraphWidget(QWidget):
    """Widget for displaying a time-series line graph"""
    def __init__(self, title, min_value, max_value, units, history_length=100, parent=None):
        super().__init__(parent)
        self.title = title
        self.min_value = min_value
        self.max_value = max_value
        self.units = units
        self.history_length = history_length
        # Data arrays
        self.time_data = np.linspace(0, self.history_length, self.history_length)
        self.value_data = np.zeros(self.history_length)
        # Set up the layout
        layout = QVBoxLayout()
        # Create a title label
        title_label = QLabel(self.title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setStyleSheet("color: white;")
        # Create the plot widget
        self.plot = pg.PlotWidget()
        self.plot.setBackground(None)
        self.plot.setYRange(self.min_value, self.max_value)
        self.plot.setLabel('left', self.units)
        # Create the line
        self.line = self.plot.plot(self.time_data, self.value_data, pen=pg.mkPen(color='green', width=2))
        # Create a value label
        self.value_label = QLabel(f"0 {self.units}")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.value_label.setStyleSheet("color: white;")
        # Add widgets to layout
        layout.addWidget(title_label)
        layout.addWidget(self.plot)
        layout.addWidget(self.value_label)
        self.setLayout(layout)

    def update_value(self, value):
        """Update the graph with a new value"""
        # Shift data to the left
        self.value_data[:-1] = self.value_data[1:]
        # Add new value at the end
        self.value_data[-1] = value
        # Update the line
        self.line.setData(self.time_data, self.value_data)
        # Update the label
        self.value_label.setText(f"{value:.1f} {self.units}")

class OBDDashboard(QMainWindow):
    """Main dashboard window"""
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

    def init_ui(self):
        """Initialize the user interface"""
        # Set window properties
        self.setWindowTitle("Enhanced OBD-II Simulator Dashboard")
        self.setGeometry(100, 100, 1000, 700)
        # Create central widget and layout
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        # Set dark blue background
        central_widget.setStyleSheet("background-color: #002B5C;")
        # Create gauge layout
        gauge_layout = QHBoxLayout()
        # Create RPM gauge
        self.rpm_gauge = CustomGauge(
            "Engine RPM", 
            0, 8000, 
            "rpm"
        )
        # Create speed gauge
        self.speed_gauge = CustomGauge(
            "Vehicle Speed", 
            0, 200, 
            "km/h"
        )
        # Add gauges to layout
        gauge_layout.addWidget(self.speed_gauge)
        gauge_layout.addWidget(self.rpm_gauge)
        # Create graph layout
        graph_layout = QHBoxLayout()
        # Create temperature graph
        self.temp_graph = LineGraphWidget(
            "Engine Temperature", 
            0, 120, 
            "°C"
        )
        # Create throttle position graph
        self.throttle_graph = LineGraphWidget(
            "Throttle Position", 
            0, 100, 
            "%"
        )
        # Add graphs to layout
        graph_layout.addWidget(self.temp_graph)
        graph_layout.addWidget(self.throttle_graph)
        # Create control layout
        control_layout = QHBoxLayout()
        # Create throttle slider
        throttle_label = QLabel("Throttle:")
        throttle_label.setStyleSheet("color: white;")
        self.throttle_slider = QSlider(Qt.Horizontal)
        self.throttle_slider.setRange(0, 100)
        self.throttle_slider.setValue(0)
        self.throttle_slider.setTickPosition(QSlider.TicksBelow)
        self.throttle_slider.setTickInterval(10)
        self.throttle_slider.valueChanged.connect(self.set_throttle)
        # Create engine control button
        self.engine_button = QPushButton("Stop Engine")
        self.engine_button.clicked.connect(self.toggle_engine)
        self.engine_button.setStyleSheet("background-color: #4CAF50; color: white;")
        # Add widgets to control layout
        control_layout.addWidget(throttle_label)
        control_layout.addWidget(self.throttle_slider)
        control_layout.addWidget(self.engine_button)
        # Create additional parameters layout
        param_layout = QGridLayout()
        # Create parameter labels
        self.param_labels = {}
        params = [
            ("Fuel Level", "fuel", "%"),
            ("Engine Load", "load", "%"),
            ("Intake Temp", "intake", "°C"),
            ("MAF", "maf", "g/s")
        ]
        for i, (name, key, unit) in enumerate(params):
            # Create label with title
            title_label = QLabel(f"{name}:")
            title_label.setFont(QFont("Arial", 10, QFont.Bold))
            title_label.setStyleSheet("color: white;")
            # Create value label
            value_label = QLabel(f"0 {unit}")
            value_label.setFont(QFont("Arial", 10))
            value_label.setStyleSheet("color: white;")
            # Add to grid
            param_layout.addWidget(title_label, i, 0)
            param_layout.addWidget(value_label, i, 1)
            # Store reference
            self.param_labels[key] = value_label
        # Add layouts to main layout
        main_layout.addLayout(gauge_layout, 3)
        main_layout.addLayout(graph_layout, 3)
        main_layout.addLayout(control_layout, 1)
        main_layout.addLayout(param_layout, 2)
        # Set the layout to the central widget
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def apply_theme(self):
        """Apply a dark theme to the dashboard"""
        dark_palette = QPalette()
        # Set color group
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        # Set the palette
        self.setPalette(dark_palette)

    def update_dashboard(self, data):
        """Update the dashboard with new data"""
        # Update RPM gauge
        if 'RPM' in data:
            self.rpm_gauge.update_value(data['RPM'])
        # Update speed gauge
        if 'SPEED' in data:
            self.speed_gauge.update_value(data['SPEED'])
        # Update temperature graph
        if 'COOLANT_TEMP' in data:
            self.temp_graph.update_value(data['COOLANT_TEMP'])
        # Update throttle graph
        if 'THROTTLE_POS' in data:
            self.throttle_graph.update_value(data['THROTTLE_POS'])
        # Update additional parameters
        if 'FUEL_LEVEL' in data:
            self.param_labels['fuel'].setText(f"{data['FUEL_LEVEL']:.1f} %")
        if 'ENGINE_LOAD' in data:
            self.param_labels['load'].setText(f"{data['ENGINE_LOAD']:.1f} %")
        if 'INTAKE_TEMP' in data:
            self.param_labels['intake'].setText(f"{data['INTAKE_TEMP']:.1f} °C")
        if 'MAF' in data:
            self.param_labels['maf'].setText(f"{data['MAF']:.1f} g/s")

    def set_throttle(self, value):
        """Set the throttle position"""
        self.simulator.set_throttle(value)

    def toggle_engine(self):
        """Toggle the engine state"""
        if self.simulator.car.engine_running:
            self.simulator.car.stop_engine()
            self.engine_button.setText("Start Engine")
        else:
            self.simulator.car.start_engine()
            self.engine_button.setText("Stop Engine")

    def closeEvent(self, event):
        """Handle window close event"""
        # Stop the data thread
        if self.data_thread.isRunning():
            self.data_thread.stop()
        # Close the simulator
        self.simulator.close()
        # Accept the event
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Create and show the dashboard
    dashboard = OBDDashboard()
    dashboard.show()
    sys.exit(app.exec_())