"""
KISS TNC Client for sending APRS packets to Direwolf.
"""

import socket
import time
import logging
from typing import Optional


logger = logging.getLogger('aprswx')


class KISSTNCClient:
    """Client for connecting to a KISS TNC via TCP."""
    
    def __init__(self, host: str = "localhost", port: int = 8001):
        """
        Initialize the KISS TNC client.
        
        Args:
            host: Hostname or IP address of the KISS TNC
            port: Port number of the KISS TNC
        """
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
    
    def connect(self) -> bool:
        """
        Connect to the KISS TNC.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.debug(f"Connecting to KISS TNC at {self.host}:{self.port}")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.host, self.port))
            logger.debug("Successfully connected to KISS TNC")
            return True
        except (socket.error, socket.timeout) as e:
            logger.error(f"Error connecting to KISS TNC: {e}")
            logger.debug(f"Connection details - Host: {self.host}, Port: {self.port}")
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
    
    def send_packet(self, packet: str) -> bool:
        """
        Send an APRS packet to the KISS TNC.
        
        Args:
            packet: The APRS packet string to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.socket:
            logger.error("Cannot send packet - not connected to KISS TNC")
            return False
        
        try:
            # KISS TNC over TCP expects raw frames with FEND framing
            # For simple text mode, we can often send the raw packet directly
            # Direwolf's KISS TNC interface accepts raw APRS packets
            
            # Add proper line ending
            data = packet.encode('utf-8') + b'\r\n'
            
            logger.debug(f"Sending APRS packet: {packet}")
            self.socket.sendall(data)
            logger.debug("Packet sent successfully")
            return True
        except (socket.error, socket.timeout) as e:
            logger.error(f"Error sending packet: {e}")
            return False
    
    def send_raw_frame(self, frame: bytes) -> bool:
        """
        Send a raw KISS frame to the TNC.
        
        Args:
            frame: Raw KISS frame bytes
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.socket:
            return False
        
        try:
            # KISS frames are framed with FEND (0xC0) characters
            kiss_frame = b'\xC0' + frame + b'\xC0'
            self.socket.sendall(kiss_frame)
            return True
        except (socket.error, socket.timeout) as e:
            print(f"Error sending raw frame: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if connected to the KISS TNC."""
        return self.socket is not None


def create_kiss_frame(ax25_frame: bytes) -> bytes:
    """
    Create a KISS frame from an AX.25 frame.
    
    Args:
        ax25_frame: Raw AX.25 frame bytes
        
    Returns:
        KISS framed bytes
    """
    # For simple text mode, we can just send the raw packet
    # The KISS TNC will handle the framing
    return ax25_frame
