
# Artnet2MIDI

Artnet2MIDI is a Python application that listens for Art-Net DMX data and converts it to MIDI Show Control (MSC) or MIDI Note On messages. It features a GUI for configuration, supports hot-swapping MIDI output ports and Art-Net universes, and includes a status indicator to show the state of the Art-Net listener.

## Features

- **Art-Net to MIDI Conversion**: Converts Art-Net DMX data to MSC or MIDI Note On messages.
- **Hot-Swappable MIDI Output**: Change MIDI output ports without restarting the application.
- **Hot-Swappable Art-Net Universe**: Change the Art-Net universe on the fly.
- **Status Indicator**: Visual indicator showing the status of the Art-Net listener.
- **Received Universes List**: Displays a list of Art-Net universes for which values have been received.
- **System Tray Integration**: Runs in the system tray with a context menu for easy access.
- **Donation Link**: Includes a donation link for supporting the developer.

## Installation

### Prerequisites

- Python 3.6+
- pip (Python package installer)
- Virtual environment (optional but recommended)

### Clone the Repository

```sh
git clone https://github.com/bout-de-rim/Artnet-MIDI.git
cd Artnet2MIDI
```

### Create and Activate a Virtual Environment

```sh
python -m venv .venv
source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
```

### Install Dependencies

```sh
pip install -r requirements.txt
```

## Usage

### Running the Application

To start the application, run:

```sh
python artnet2midi.py
```

### Configuration

1. **MIDI Output Port**: Select the desired MIDI output port and click "Update MIDI Output".
2. **Mode Selection**: Choose between MSC or NoteOn mode.
3. **NoteOn Conversion Type**: Select between "Proportionate" and "Truncated" for NoteOn conversion.
4. **Art-Net Universe**: Select the Art-Net universe to listen to.
5. **Start Listener**: Click "Start Art-Net Listener" to begin listening for Art-Net DMX data.

### Status Indicator

- **Red**: The server is OFF.
- **Orange**: The server is ON but hasn't received any Art-Net messages.
- **Green**: The server has received an Art-Net message.

### System Tray

- **Open Configuration**: Double-click the tray icon or select "Open Configuration" from the context menu to open the configuration window.
- **Exit**: Select "Exit" from the context menu to close the application.

## Donations

If you use this software for professional purposes, please consider making a donation.

**Rémi Dubot**  
[Donate via PayPal](https://paypal.me/Rdbt82)

## Contributing

Contributions are welcome! Please fork the repository and submit pull requests for new features, bug fixes, or improvements.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

Special thanks to the developers of the libraries used in this project:

- [mido](https://github.com/mido/mido)
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/intro)

## Contact

For any questions or issues, please open an issue on GitHub or contact the project maintainer.

---

© 2024 Rémi Dubot
