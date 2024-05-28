import sys
import logging
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox, QComboBox, QRadioButton, QButtonGroup, QGroupBox, QHBoxLayout
from PyQt5.QtGui import QIcon, QFont

from config_window import ConfigWindow

# Configurer le logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler("artnet_msc.log"),
    logging.StreamHandler()
])

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
    
    window.show()  # Show the configuration window at launch

    exit_code = app.exec_()
    if window.midi_outport:
        window.midi_outport.close()  # Fermer correctement le port MIDI
    sys.exit(exit_code)
