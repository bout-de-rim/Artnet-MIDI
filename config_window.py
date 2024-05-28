from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QRadioButton, QButtonGroup, QMessageBox, QSystemTrayIcon, QGroupBox, QHBoxLayout, QSpinBox, QListWidget
from PyQt5.QtGui import QIcon, QFont, QPainter, QColor
from PyQt5.QtCore import Qt
import mido
import logging
from config import load_config, save_config
from midi_output import MidiOutput
from artnet_listener import ArtNetListener
import webbrowser

class StatusIndicator(QLabel):
    def __init__(self):
        super().__init__()
        self.setFixedSize(100, 100)
        self.status = "OFF"
        self.setToolTip("Red: OFF\nOrange: ON, no Art-Net message\nGreen: Received Art-Net message")
        self.update_status("OFF")

    def update_status(self, status):
        self.status = status
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.contentsRect()

        if self.status == "OFF":
            color = QColor(Qt.red)
        elif self.status == "ON":
            color = QColor(255, 165, 0)  # Orange color
        elif self.status == "RECEIVED":
            color = QColor(Qt.green)

        painter.setBrush(color)
        painter.drawEllipse(rect)
        painter.end()

class ConfigWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.midi_output = MidiOutput()
        self.artnet_listener = None
        self.tray_icon = None
        self.config = load_config()
        self.status_indicator = StatusIndicator()
        self.previous_dmx_values = [0] * 512  # Initialiser les valeurs précédentes des canaux DMX
        self.initUI()

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()


    def initUI(self):
        self.setWindowTitle('Configuration')
        self.setGeometry(100, 100, 400, 700)

        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        # Section MIDI Output
        midi_group = QGroupBox("Select MIDI Output Port")
        midi_layout = QVBoxLayout()

        self.midi_ports_combo = QComboBox(self)
        self.midi_ports_combo.addItems(mido.get_output_names())
        midi_layout.addWidget(self.midi_ports_combo)

        self.update_midi_button = QPushButton("Update MIDI Output", self)
        self.update_midi_button.setStyleSheet("padding: 10px; font-size: 14px;")
        self.update_midi_button.clicked.connect(self.update_midi_output)
        midi_layout.addWidget(self.update_midi_button)

        midi_group.setLayout(midi_layout)

        # Section Mode Selection
        mode_group = QGroupBox("Select Mode")
        mode_layout = QVBoxLayout()

        self.msc_mode = QRadioButton("MSC", self)
        self.noteon_mode = QRadioButton("NoteOn", self)

        self.mode_group = QButtonGroup()
        self.mode_group.addButton(self.msc_mode)
        self.mode_group.addButton(self.noteon_mode)

        mode_layout.addWidget(self.msc_mode)
        mode_layout.addWidget(self.noteon_mode)

        mode_group.setLayout(mode_layout)

        # Section NoteOn Conversion Type
        conversion_group = QGroupBox("NoteOn Conversion Type")
        conversion_layout = QVBoxLayout()

        self.noteon_conversion_combo = QComboBox(self)
        self.noteon_conversion_combo.addItems(["Proportionate", "Truncated"])
        conversion_layout.addWidget(self.noteon_conversion_combo)

        conversion_group.setLayout(conversion_layout)

        # Art-Net Universe Selection
        universe_group = QGroupBox("Select Art-Net Universe")
        universe_layout = QVBoxLayout()

        self.universe_spinbox = QSpinBox(self)
        self.universe_spinbox.setRange(0, 32767)  # Art-Net supports up to 32767 universes
        self.universe_spinbox.valueChanged.connect(self.change_universe)
        universe_layout.addWidget(self.universe_spinbox)

        universe_group.setLayout(universe_layout)

        # Received Universes
        received_group = QGroupBox("Received Art-Net Universes")
        received_layout = QVBoxLayout()

        self.received_list = QListWidget(self)
        received_layout.addWidget(self.received_list)

        received_group.setLayout(received_layout)

        # Start Button
        self.start_button = QPushButton("Start Art-Net Listener", self)
        self.start_button.setStyleSheet("padding: 10px; font-size: 14px;")
        self.start_button.clicked.connect(self.start_artnet_listener)
        self.start_button.setEnabled(True)

        # Status Indicator
        status_group = QGroupBox("Server Status")
        status_layout = QVBoxLayout()
        status_layout.addWidget(self.status_indicator)
        status_group.setLayout(status_layout)

        # Donation Section
        donation_group = QGroupBox("Donation")
        donation_layout = QVBoxLayout()

        donation_message = QLabel("If you use this soft for professional purpose, please consider making a donation.")
        donation_layout.addWidget(donation_message)

        name_label = QLabel("Rémi Dubot")
        donation_layout.addWidget(name_label)

        paypal_button = QPushButton("Donate via PayPal")
        paypal_button.setStyleSheet("padding: 10px; font-size: 14px;")
        paypal_button.clicked.connect(lambda: webbrowser.open("https://paypal.me/Rdbt82"))
        donation_layout.addWidget(paypal_button)

        donation_group.setLayout(donation_layout)

        # Add groups to main layout
        main_layout.addWidget(midi_group)
        main_layout.addWidget(mode_group)
        main_layout.addWidget(conversion_group)
        main_layout.addWidget(universe_group)
        main_layout.addWidget(received_group)
        main_layout.addWidget(self.start_button)
        main_layout.addWidget(status_group)
        main_layout.addWidget(donation_group)

        self.setCentralWidget(central_widget)

        self.load_ui_settings()

    def load_ui_settings(self):
        if 'midi_output' in self.config:
            index = self.midi_ports_combo.findText(self.config['midi_output'])
            if index != -1:
                self.midi_ports_combo.setCurrentIndex(index)

        if 'mode' in self.config:
            if self.config['mode'] == 'MSC':
                self.msc_mode.setChecked(True)
            else:
                self.noteon_mode.setChecked(True)

        if 'conversion_type' in self.config:
            index = self.noteon_conversion_combo.findText(self.config['conversion_type'])
            if index != -1:
                self.noteon_conversion_combo.setCurrentIndex(index)

        if 'universe' in self.config:
            self.universe_spinbox.setValue(self.config['universe'])

    def save_config(self):
        self.config['midi_output'] = self.midi_ports_combo.currentText()
        self.config['mode'] = 'MSC' if self.msc_mode.isChecked() else 'NoteOn'
        self.config['conversion_type'] = self.noteon_conversion_combo.currentText()
        self.config['universe'] = self.universe_spinbox.value()
        save_config(self.config)

    def update_midi_output(self):
        selected_port = self.midi_ports_combo.currentText()
        if selected_port and self.midi_output.open_output(selected_port):
            self.save_config()
            QMessageBox.information(self, "MIDI Output Updated", f"MIDI output port updated to: {selected_port}")
    
    def start_artnet_listener(self):
        selected_port = self.midi_ports_combo.currentText()
        if selected_port and self.midi_output.open_output(selected_port):
            self.save_config()
            logging.info("Selected MIDI output port: %s", selected_port)
            universe = self.universe_spinbox.value()
            self.artnet_listener = ArtNetListener(universe=universe)
            self.timer = self.startTimer(10)  # Appel périodique pour vérifier les paquets
            logging.info("Art-Net listener started on IP %s, port %d, universe %d", self.artnet_listener.UDP_IP, self.artnet_listener.UDP_PORT, universe)
            self.start_button.setEnabled(False)  # Désactiver le bouton après démarrage
            self.status_indicator.update_status("ON")

    def change_universe(self):
        if self.artnet_listener:
            new_universe = self.universe_spinbox.value()
            self.artnet_listener.set_universe(new_universe)
            self.save_config()
            logging.info("Changed Art-Net universe to %d", new_universe)

    def timerEvent(self, event):
        data, addr = self.artnet_listener.receive_packet()
        dmx_data = self.artnet_listener.parse_artnet_packet(data)
        if dmx_data:
            self.status_indicator.update_status("RECEIVED")
            self.update_received_universes()
            for channel in range(1, 513):
                dmx_value = dmx_data[channel - 1]
                if dmx_value != self.previous_dmx_values[channel - 1]:  # Vérifier le changement d'état
                    self.previous_dmx_values[channel - 1] = dmx_value  # Mettre à jour l'état précédent
                    if self.msc_mode.isChecked():
                        msc_params = self.dmx_to_msc(channel, dmx_value)
                        self.midi_output.send_msc_set_message(*msc_params)
                    elif self.noteon_mode.isChecked():
                        conversion_type = self.noteon_conversion_combo.currentText()
                        self.midi_output.send_noteon_message(channel, dmx_value, conversion_type)

    def update_received_universes(self):
        self.received_list.clear()
        for universe in sorted(self.artnet_listener.received_universes):
            self.received_list.addItem(str(universe))

    def dmx_to_msc(self, dmx_channel, dmx_value):
        msc_control_number = 512 + (dmx_channel - 1)  # Mapping 512-1023 for DMX channels 1-512
        logging.debug("Mapping DMX channel %d to MSC control number %d with value %d", dmx_channel, msc_control_number, dmx_value)
        return [msc_control_number, dmx_value]

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        if self.tray_icon:
            self.tray_icon.showMessage("Artnet2MIDI", "The application is still running in the system tray.", QSystemTrayIcon.Information)
