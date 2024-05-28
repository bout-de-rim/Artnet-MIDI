import mido
import logging
from PyQt5.QtWidgets import QMessageBox, QSystemTrayIcon

class MidiOutput:
    def __init__(self):
        self.midi_outport = None
        self.tray_icon = None

    def open_output(self, selected_port):
        try:
            if self.midi_outport:
                self.midi_outport.close()
            self.midi_outport = mido.open_output(selected_port)
            logging.info("Updated MIDI output port to: %s", selected_port)
        except IOError as e:
            logging.error("Failed to open MIDI output port: %s", e)
            if self.tray_icon:
                self.tray_icon.showMessage("MIDI Output Error", f"Failed to open MIDI output port: {e}", QSystemTrayIcon.Critical)
            QMessageBox.critical(None, "MIDI Output Error", f"Failed to open MIDI output port: {e}")
            return False
        return True

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
