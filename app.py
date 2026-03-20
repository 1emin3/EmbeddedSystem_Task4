import sys
import time
import serial
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QMessageBox, QFrame, QGridLayout
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont


PORT = "COM8"       # Change if needed
BAUDRATE = 115200


class JoystickPlot(QWidget):
    def __init__(self):
        super().__init__()
        self.x_val = 512
        self.y_val = 512
        self.setMinimumSize(280, 280)

    def update_position(self, x_val, y_val):
        self.x_val = x_val
        self.y_val = y_val
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        margin = 20
        left = margin
        top = margin
        width = w - 2 * margin
        height = h - 2 * margin

        painter.setPen(QPen(Qt.GlobalColor.black, 2))
        painter.drawRect(left, top, width, height)

        center_x = left + width // 2
        center_y = top + height // 2

        painter.setPen(QPen(Qt.GlobalColor.gray, 1))
        painter.drawLine(center_x, top, center_x, top + height)
        painter.drawLine(left, center_y, left + width, center_y)

        px = left + int((self.x_val / 1023) * width)
        py = top + height - int((self.y_val / 1023) * height)

        painter.setBrush(QBrush(QColor("red")))
        painter.setPen(QPen(Qt.GlobalColor.red, 2))
        painter.drawEllipse(px - 7, py - 7, 14, 14)


class DirectionPad(QWidget):
    def __init__(self):
        super().__init__()
        self.direction = "CENTER"
        self.setMinimumSize(220, 220)

    def set_direction(self, direction):
        self.direction = direction
        self.update()

    def draw_box(self, painter, x, y, size, active, label):
        if active:
            painter.setBrush(QBrush(QColor(0, 200, 120)))
        else:
            painter.setBrush(QBrush(QColor(230, 230, 230)))

        painter.setPen(QPen(QColor(80, 120, 100), 2))
        painter.drawRect(x, y, size, size)

        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.drawText(x, y, size, size, Qt.AlignmentFlag.AlignCenter, label)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        size = 55
        gap = 4

        total = size * 3 + gap * 2
        start_x = (self.width() - total) // 2
        start_y = (self.height() - total) // 2

        center_x = start_x + size + gap
        center_y = start_y + size + gap

        self.draw_box(painter, center_x, start_y, size, self.direction == "UP", "UP")
        self.draw_box(painter, start_x, center_y, size, self.direction == "LEFT", "LEFT")
        self.draw_box(painter, center_x, center_y, size, self.direction == "CENTER", "C")
        self.draw_box(painter, center_x + size + gap, center_y, size, self.direction == "RIGHT", "RIGHT")
        self.draw_box(painter, center_x, center_y + size + gap, size, self.direction == "DOWN", "DOWN")


class Window(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Lab Task 4 - Joystick Tester")
        self.resize(980, 620)

        self.ser = None
        self.running = False

        self.x_val = 512
        self.y_val = 512
        self.direction = "CENTER"

        self.last_time = None
        self.sample_rate = 0.0

        self.build_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.read_serial)
        self.timer.start(20)

    def build_ui(self):
        main_layout = QVBoxLayout()

        title = QLabel("LAB TASK 4 - Joystick Tester")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        main_layout.addWidget(title)

        top_row = QHBoxLayout()

        self.start_stop_button = QPushButton("Start Test")
        self.start_stop_button.setFixedHeight(45)
        self.start_stop_button.clicked.connect(self.toggle_test)

        self.status_box = QLabel("OFF")
        self.status_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_box.setFixedSize(90, 45)
        self.update_status_box()

        top_row.addWidget(self.start_stop_button)
        top_row.addWidget(self.status_box)
        top_row.addStretch()

        main_layout.addLayout(top_row)

        middle_layout = QHBoxLayout()

        left_panel = QVBoxLayout()
        left_title = QLabel("Data Visualization")
        left_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.plot_widget = JoystickPlot()

        left_panel.addWidget(left_title)
        left_panel.addWidget(self.plot_widget)

        right_panel = QVBoxLayout()
        right_title = QLabel("Button Mapping")
        right_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.direction_pad = DirectionPad()

        right_panel.addWidget(right_title)
        right_panel.addWidget(self.direction_pad)

        middle_layout.addLayout(left_panel, 1)
        middle_layout.addLayout(right_panel, 1)

        main_layout.addLayout(middle_layout)

        data_frame = QFrame()
        data_frame.setFrameShape(QFrame.Shape.Box)
        data_layout = QGridLayout()

        self.x_raw_label = QLabel("X Raw: ---")
        self.y_raw_label = QLabel("Y Raw: ---")
        self.x_volt_label = QLabel("X Voltage: ---")
        self.y_volt_label = QLabel("Y Voltage: ---")
        self.dir_label = QLabel("Direction: ---")
        self.sample_label = QLabel("Sample Rate: --- Hz")

        data_layout.addWidget(self.x_raw_label, 0, 0)
        data_layout.addWidget(self.y_raw_label, 0, 1)
        data_layout.addWidget(self.x_volt_label, 1, 0)
        data_layout.addWidget(self.y_volt_label, 1, 1)
        data_layout.addWidget(self.dir_label, 2, 0)
        data_layout.addWidget(self.sample_label, 2, 1)

        data_frame.setLayout(data_layout)
        main_layout.addWidget(data_frame)

        self.setLayout(main_layout)

    def update_status_box(self):
        if self.running:
            self.status_box.setText("ON")
            self.status_box.setStyleSheet(
                "background-color: #00c853; color: white; font-weight: bold; border: 1px solid black;"
            )
            self.start_stop_button.setText("Stop Test")
        else:
            self.status_box.setText("OFF")
            self.status_box.setStyleSheet(
                "background-color: #d32f2f; color: white; font-weight: bold; border: 1px solid black;"
            )
            self.start_stop_button.setText("Start Test")

    def toggle_test(self):
        if not self.running:
            self.connect_serial()
            if self.ser and self.ser.is_open:
                self.running = True
        else:
            self.running = False
            self.disconnect_serial()

        self.update_status_box()

    def connect_serial(self):
        try:
            if not self.ser or not self.ser.is_open:
                self.ser = serial.Serial(PORT, BAUDRATE, timeout=0.1)
                time.sleep(1.5)
                self.last_time = None
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", str(e))

    def disconnect_serial(self):
        if self.ser and self.ser.is_open:
            self.ser.close()

    def read_serial(self):
        if not self.running:
            return

        if self.ser and self.ser.in_waiting:
            try:
                line = self.ser.readline().decode(errors="ignore").strip()
                parts = line.split(",")

                x_val = None
                y_val = None
                direction = None

                for part in parts:
                    if part.startswith("x="):
                        x_val = int(part[2:])
                    elif part.startswith("y="):
                        y_val = int(part[2:])
                    elif part.startswith("dir="):
                        direction = part[4:]

                if x_val is not None and y_val is not None and direction is not None:
                    now = time.time()
                    if self.last_time is not None:
                        dt = now - self.last_time
                        if dt > 0:
                            self.sample_rate = 1.0 / dt
                    self.last_time = now

                    self.x_val = x_val
                    self.y_val = y_val
                    self.direction = direction

                    x_voltage = (self.x_val / 1023.0) * 5.0
                    y_voltage = (self.y_val / 1023.0) * 5.0

                    self.x_raw_label.setText(f"X Raw: {self.x_val}")
                    self.y_raw_label.setText(f"Y Raw: {self.y_val}")
                    self.x_volt_label.setText(f"X Voltage: {x_voltage:.2f} V")
                    self.y_volt_label.setText(f"Y Voltage: {y_voltage:.2f} V")
                    self.dir_label.setText(f"Direction: {self.direction}")
                    self.sample_label.setText(f"Sample Rate: {self.sample_rate:.1f} Hz")

                    self.plot_widget.update_position(self.x_val, self.y_val)
                    self.direction_pad.set_direction(self.direction)

            except Exception as e:
                QMessageBox.critical(self, "Read Error", str(e))
                self.running = False
                self.disconnect_serial()
                self.update_status_box()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())