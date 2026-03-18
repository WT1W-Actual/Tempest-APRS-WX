"""
KISS TNC Client for sending APRS packets to Direwolf.
"""

import socket
import logging
from typing import Optional


logger = logging.getLogger('aprswx')

# KISS special bytes
FEND = 0xC0   # Frame End (frame delimiter)
FESC = 0xDB   # Frame Escape
TFEND = 0xDC  # Transposed FEND
TFESC = 0xDD  # Transposed FESC


def _encode_ax25_address(callsign: str, ssid: int, end: bool = False, c_bit: bool = False) -> bytes:
    """Encode a callsign+SSID into a 7-byte AX.25 address field."""
    padded = callsign.upper().ljust(6)[:6]
    addr = bytes(ord(ch) << 1 for ch in padded)
    ssid_byte = (0x80 if c_bit else 0x00) | 0x60 | ((ssid & 0x0F) << 1) | (0x01 if end else 0x00)
    return addr + bytes([ssid_byte])


def _build_ax25_ui_frame(src_call: str, src_ssid: int, info: str) -> bytes:
    """Build an AX.25 UI frame suitable for APRS."""
    dest  = _encode_ax25_address("APRS",  0,        end=False, c_bit=True)
    source = _encode_ax25_address(src_call, src_ssid, end=False, c_bit=False)
    digi  = _encode_ax25_address("WIDE1", 1,        end=True,  c_bit=False)
    control = bytes([0x03])  # UI frame
    pid     = bytes([0xF0])  # No layer 3 protocol
    return dest + source + digi + control + pid + info.encode('ascii', errors='replace')


def _kiss_escape(data: bytes) -> bytes:
    """Apply KISS byte stuffing to frame payload."""
    result = bytearray()
    for byte in data:
        if byte == FEND:
            result.extend([FESC, TFEND])
        elif byte == FESC:
            result.extend([FESC, TFESC])
        else:
            result.append(byte)
    return bytes(result)


def _kiss_wrap(ax25_frame: bytes) -> bytes:
    """Wrap an AX.25 frame in a KISS data frame (port 0)."""
    payload = bytes([0x00]) + ax25_frame  # 0x00 = data command, port 0
    return bytes([FEND]) + _kiss_escape(payload) + bytes([FEND])


class KISSTNCClient:
    """Client for connecting to a KISS TNC via TCP."""

    def __init__(self, host: str = "localhost", port: int = 8001):
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None

    def connect(self) -> bool:
        """Connect to the KISS TNC. Returns True on success."""
        try:
            logger.debug(f"Connecting to KISS TNC at {self.host}:{self.port}")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.host, self.port))
            logger.debug("Successfully connected to KISS TNC")
            return True
        except (socket.error, socket.timeout) as e:
            logger.error(f"Error connecting to KISS TNC: {e}")
            self.socket = None
            return False

    def disconnect(self):
        """Disconnect from the KISS TNC."""
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                logger.debug(f"Error closing socket: {e}")
            finally:
                self.socket = None

    def send_aprs_packet(self, src_callsign: str, src_ssid: int, info: str) -> bool:
        """
        Build a proper AX.25 UI frame, wrap it in KISS framing, and send it.

        Args:
            src_callsign: Source amateur radio callsign (e.g. "WT1W")
            src_ssid:     Source SSID (0-15)
            info:         APRS information field string

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.socket:
            logger.error("Cannot send packet - not connected to KISS TNC")
            return False

        try:
            ax25_frame = _build_ax25_ui_frame(src_callsign, src_ssid, info)
            kiss_frame = _kiss_wrap(ax25_frame)
            logger.debug(f"Sending APRS packet ({src_callsign}-{src_ssid}): {info}")
            self.socket.sendall(kiss_frame)
            logger.debug("Packet sent successfully")
            return True
        except (socket.error, socket.timeout) as e:
            logger.error(f"Error sending packet: {e}")
            return False

    def is_connected(self) -> bool:
        """Check if connected to the KISS TNC."""
        return self.socket is not None

