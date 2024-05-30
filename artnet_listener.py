import socket
import logging

class ArtNetListener:
    def __init__(self, ip="0.0.0.0", port=6454, universe=0):
        self.UDP_IP = ip
        self.UDP_PORT = port
        self.universe = universe
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.UDP_IP, self.UDP_PORT))
        self.sock.setblocking(False)
        self.received_universes = set()
        logging.info("Art-Net listener started on IP %s, port %d, universe %d", self.UDP_IP, self.UDP_PORT, self.universe)

    def set_universe(self, universe):
        self.universe = universe
        logging.info("Art-Net listener universe changed to %d", self.universe)

    def receive_packet(self):
        try:
            data, addr = self.sock.recvfrom(1024)
            return data, addr
        except BlockingIOError:
            return None, None

    def parse_artnet_packet(self, packet):
        if packet and packet[:8] == b'Art-Net\x00':
            opcode = int.from_bytes(packet[8:10], byteorder='little')
            if opcode == 0x5000:  # OpOutput / ArtDMX
                universe = int.from_bytes(packet[14:16], byteorder='little')
                #logging.debug("Received packet from universe %d", universe)
                self.received_universes.add(universe)
                if universe == self.universe:
                    dmx_data = packet[18:]  # DMX data starts at byte 18
                    #logging.debug("Parsed Art-Net DMX data: %s", dmx_data)
                    return dmx_data
        return None
