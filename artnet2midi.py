import sys
import socket
import mido
import logging
import json
import os
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox, QComboBox, QRadioButton, QButtonGroup
from PyQt5.QtGui import QIcon

# Configurer le logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler("artnet_msc.log"),
    logging.StreamHandler()
])

CONFIG_FILE = 'config.json'

class ConfigWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.midi_outport = None
        self.tray_icon = None
        self.config = self.load_config()
        self.initUI()
        self.previous_dmx_values = [0] * 512  # Initialiser les valeurs précédentes des canaux DMX

    def initUI(self):
        self.setWindowTitle('Configuration')
        self.setGeometry(100, 100, 300, 400)

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        self.label = QLabel("Select MIDI Output Port", self)
        layout.addWidget(self.label)

        self.midi_ports_combo = QComboBox(self)
        self.midi_ports_combo.addItems(mido.get_output_names())
        layout.addWidget(self.midi_ports_combo)

        self.update_midi_button = QPushButton("Update MIDI Output", self)
        self.update_midi_button.clicked.connect(self.update_midi_output)
        layout.addWidget(self.update_midi_button)

        self.mode_label = QLabel("Select Mode", self)
        layout.addWidget(self.mode_label)

        self.msc_mode = QRadioButton("MSC", self)
        self.noteon_mode = QRadioButton("NoteOn", self)

        self.mode_group = QButtonGroup()
        self.mode_group.addButton(self.msc_mode)
        self.mode_group.addButton(self.noteon_mode)

        layout.addWidget(self.msc_mode)
        layout.addWidget(self.noteon_mode)

        self.noteon_conversion_label = QLabel("NoteOn Conversion Type", self)
        layout.addWidget(self.noteon_conversion_label)

        self.noteon_conversion_combo = QComboBox(self)
        self.noteon_conversion_combo.addItems(["Proportionate", "Truncated"])
        layout.addWidget(self.noteon_conversion_combo)

        self.start_button = QPushButton("Start Art-Net Listener", self)
        self.start_button.clicked.connect(self.start_artnet_listener)
        layout.addWidget(self.start_button)

        self.setCentralWidget(central_widget)

        self.load_ui_settings()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        else:
            return {}

    def save_config(self):
        self.config['midi_output'] = self.midi_ports_combo.currentText()
        self.config['mode'] = 'MSC' if self.msc_mode.isChecked() else 'NoteOn'
        self.config['conversion_type'] = self.noteon_conversion_combo.currentText()
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f)

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

    def open_midi_output(self, selected_port):
        try:
            if self.midi_outport:
                self.midi_outport.close()
            self.midi_outport = mido.open_output(selected_port)
            logging.info("Updated MIDI output port to: %s", selected_port)
        except IOError as e:
            logging.error("Failed to open MIDI output port: %s", e)
            if self.tray_icon:
                self.tray_icon.showMessage("MIDI Output Error", f"Failed to open MIDI output port: {e}", QSystemTrayIcon.Critical)
            QMessageBox.critical(self, "MIDI Output Error", f"Failed to open MIDI output port: {e}")
            return False
        return True
    
    def update_midi_output(self):
        selected_port = self.midi_ports_combo.currentText()
        if selected_port and self.open_midi_output(selected_port):
            self.save_config()
            QMessageBox.information(self, "MIDI Output Updated", f"MIDI output port updated to: {selected_port}")
    
    def start_artnet_listener(self):
        selected_port = self.midi_ports_combo.currentText()
        if selected_port and self.open_midi_output(selected_port):
            self.save_config()
            logging.info("Selected MIDI output port: %s", selected_port)
            self.UDP_IP = "0.0.0.0"
            self.UDP_PORT = 6454
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind((self.UDP_IP, self.UDP_PORT))
            self.sock.setblocking(False)
            self.timer = self.startTimer(10)  # Appel périodique pour vérifier les paquets
            logging.info("Art-Net listener started on IP %s, port %d", self.UDP_IP, self.UDP_PORT)
            self.start_button.setEnabled(False)  # Désactiver le bouton après démarrage

    def timerEvent(self, event):
        try:
            data, addr = self.sock.recvfrom(1024)
            dmx_data = self.parse_artnet_packet(data)
            if dmx_data:
                #logging.debug("Received Art-Net data from %s: %s", addr, dmx_data)
                for channel in range(1, 513):
                    dmx_value = dmx_data[channel - 1]
                    if dmx_value != self.previous_dmx_values[channel - 1]:  # Vérifier le changement d'état
                        self.previous_dmx_values[channel - 1] = dmx_value  # Mettre à jour l'état précédent
                        if self.msc_mode.isChecked():
                            msc_params = self.dmx_to_msc(channel, dmx_value)
                            self.send_msc_set_message(*msc_params)
                        elif self.noteon_mode.isChecked():
                            conversion_type = self.noteon_conversion_combo.currentText()
                            self.send_noteon_message(channel, dmx_value, conversion_type)
        except BlockingIOError:
            pass

    def parse_artnet_packet(self, packet):
        if packet[:8] == b'Art-Net\x00':
            opcode = int.from_bytes(packet[8:10], byteorder='little')
            if opcode == 0x5000:  # OpOutput / ArtDMX
                dmx_data = packet[18:]  # DMX data starts at byte 18
                #logging.debug("Parsed Art-Net DMX data: %s", dmx_data)
                return dmx_data
        return None

    def dmx_to_msc(self, dmx_channel, dmx_value):
        msc_control_number = 512 + (dmx_channel - 1)  # Mapping 512-1023 for DMX channels 1-512
        logging.debug("Mapping DMX channel %d to MSC control number %d with value %d", dmx_channel, msc_control_number, dmx_value)
        return [msc_control_number, dmx_value]

    def send_msc_set_message(self, control_number, value):
        # Convertir les numéros de contrôle et les valeurs en 14 bits (LSB first)
        control_number_lsb = control_number & 0x7F
        control_number_msb = (control_number >> 7) & 0x7F
        value_lsb = value & 0x7F
        value_msb = (value >> 7) & 0x7F

        sysex_data = [0x7F, 0x7F, 0x02, 0x01, 0x06, control_number_lsb, control_number_msb, value_lsb, value_msb]

        msg = mido.Message('sysex', data=sysex_data)
        
        self.midi_outport.send(msg)
        logging.info("Sent MSC message: %s", msg)

    def send_noteon_message(self, channel, value, conversion_type):
        # Envoyer un message NoteOn avec la valeur DMX
        note = channel % 128  # Limiter les notes à 128

        if conversion_type == "Proportionate":
            velocity = int((value / 255) * 127)  # Conversion proportionnelle
        elif conversion_type == "Truncated":
            velocity = min(value, 127)  # Troncation (la valeur reste 127 pour DMX > 127)

        msg = mido.Message('note_on', channel=(channel - 1) % 16, note=note, velocity=velocity)
        
        self.midi_outport.send(msg)
        logging.info("Sent NoteOn message: %s", msg)

def create_tray_icon(app, window):
    tray_icon = QSystemTrayIcon(QIcon("artnet2midi.png"), app)
    window.tray_icon = tray_icon
    
    tray_menu = QMenu()
    
    open_action = QAction("Open Configuration", tray_icon)
    open_action.triggered.connect(lambda: window.show())
    tray_menu.addAction(open_action)

    exit_action = QAction("Exit", tray_icon)
    exit_action.triggered.connect(app.quit)
    tray_menu.addAction(exit_action)

    tray_icon.setContextMenu(tray_menu)
    tray_icon.show()
    logging.info("System tray icon created")

    return tray_icon

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    window = ConfigWindow()
    
    tray_icon = create_tray_icon(app, window)
    
    exit_code = app.exec_()
    if window.midi_outport:
        window.midi_outport.close()  # Fermer correctement le port MIDI
    sys.exit(exit_code)
