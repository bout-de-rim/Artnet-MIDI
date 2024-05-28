import sys
import socket
import mido
import logging
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox, QComboBox
from PyQt5.QtGui import QIcon

# Configurer le logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler("artnet_msc.log"),
    logging.StreamHandler()
])

class ConfigWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.midi_outport = None
        self.initUI()
        self.previous_dmx_values = [0] * 512  # Initialiser les valeurs précédentes des canaux DMX

    def initUI(self):
        self.setWindowTitle('Configuration')
        self.setGeometry(100, 100, 300, 200)

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        self.label = QLabel("Select MIDI Output Port", self)
        layout.addWidget(self.label)

        self.midi_ports_combo = QComboBox(self)
        self.midi_ports_combo.addItems(mido.get_output_names())
        layout.addWidget(self.midi_ports_combo)

        self.button = QPushButton("Start Art-Net Listener", self)
        self.button.clicked.connect(self.start_artnet_listener)
        layout.addWidget(self.button)

        self.setCentralWidget(central_widget)

    def start_artnet_listener(self):
        selected_port = self.midi_ports_combo.currentText()
        if selected_port:
            self.midi_outport = mido.open_output(selected_port)
            logging.info("Selected MIDI output port: %s", selected_port)
            self.UDP_IP = "0.0.0.0"
            self.UDP_PORT = 6454
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind((self.UDP_IP, self.UDP_PORT))
            self.sock.setblocking(False)
            self.timer = self.startTimer(10)  # Appel périodique pour vérifier les paquets
            logging.info("Art-Net listener started on IP %s, port %d", self.UDP_IP, self.UDP_PORT)
            self.button.setEnabled(False)  # Désactiver le bouton après démarrage

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
                        msc_params = self.dmx_to_msc(channel, dmx_value)
                        self.send_msc_set_message(*msc_params)
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

def create_tray_icon(app, window):
    tray_icon = QSystemTrayIcon(QIcon("artnet2midi.png"), app)
    
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
