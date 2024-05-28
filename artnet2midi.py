import socket
import mido
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon
import sys 

class ConfigWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.start_artnet_listener()

    def initUI(self):
        self.setWindowTitle('Configuration')
        self.setGeometry(100, 100, 300, 200)

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        self.label = QLabel("Configuration Panel", self)
        layout.addWidget(self.label)

        self.button = QPushButton("Click Me", self)
        self.button.clicked.connect(self.on_click)
        layout.addWidget(self.button)

        self.setCentralWidget(central_widget)

    def on_click(self):
        QMessageBox.information(self, "Information", "Button clicked!")

    def start_artnet_listener(self):
        # Configurer la réception Art-Net
        self.UDP_IP = "0.0.0.0"
        self.UDP_PORT = 6454
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.UDP_IP, self.UDP_PORT))
        self.sock.setblocking(False)
        self.timer = self.startTimer(10)  # Appel périodique pour vérifier les paquets

    def timerEvent(self, event):
        try:
            data, addr = self.sock.recvfrom(1024)
            dmx_data = self.parse_artnet_packet(data)
            if dmx_data:
                for channel in range(1, 513):
                    dmx_value = dmx_data[channel - 1]
                    msc_params = self.dmx_to_msc(channel, dmx_value)
                    self.send_msc_set_message(*msc_params)
        except BlockingIOError:
            pass

    def parse_artnet_packet(self, packet):
        if packet[:8] == b'Art-Net\x00':
            opcode = int.from_bytes(packet[8:10], byteorder='little')
            if opcode == 0x5000:  # OpOutput / ArtDMX
                dmx_data = packet[18:]  # DMX data starts at byte 18
                return dmx_data
        return None

    def dmx_to_msc(self, dmx_channel, dmx_value):
        msc_control_number = dmx_channel  # Mapping 1-to-1
        return [0x7F, 0x01, msc_control_number, dmx_value]

    def send_msc_set_message(self, device_id, command_format, control_number, value):
        sysex_start = [0xF0, 0x7F, device_id, 0x02, command_format, 0x06, 0x01]
        control_value_pair = [control_number & 0x7F, value & 0x7F]
        sysex_end = [0xF7]
        sysex_message = sysex_start + control_value_pair + sysex_end
        
        msg = mido.Message('sysex', data=sysex_message)
        
        with mido.open_output() as outport:
            outport.send(msg)


def create_tray_icon(app):
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

    return tray_icon

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    window = ConfigWindow()
    
    tray_icon = create_tray_icon(app)
    
    sys.exit(app.exec_())