"""
APRS Weather Message Formatter.
Formats weather data for transmission via APRS protocol.
"""

import math
from typing import Dict, Any


class APRSWeatherFormatter:
    """Formatter for converting weather data to APRS messages."""
    
    def __init__(self, callsign: str, ssid: int = 0, symbol_table: str = "/", symbol_code: str = ">"):
        """
        Initialize the APRS formatter.
        
        Args:
            callsign: Your amateur radio callsign
            ssid: APRS SSID (typically 0-15)
            symbol_table: Symbol table character ("/" for weather station)
            symbol_code: Symbol code character (">" for weather station)
        """
        self.callsign = callsign
        self.ssid = ssid
        self.symbol_table = symbol_table
        self.symbol_code = symbol_code
    
    def format_position(self, latitude: float, longitude: float) -> str:
        """
        Format coordinates to APRS position format.
        
        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            
        Returns:
            Formatted APRS position string (e.g., "3723.45N/12212.34W")
        """
        # Format latitude
        lat_deg = int(abs(latitude))
        lat_min = (abs(latitude) - lat_deg) * 60
        lat_hemisphere = "N" if latitude >= 0 else "S"
        lat_str = f"{lat_deg:02d}{lat_min:05.2f}{lat_hemisphere}"
        
        # Format longitude
        lon_deg = int(abs(longitude))
        lon_min = (abs(longitude) - lon_deg) * 60
        lon_hemisphere = "E" if longitude >= 0 else "W"
        lon_str = f"{lon_deg:03d}{lon_min:05.2f}{lon_hemisphere}"
        
        return f"{lat_str}{self.symbol_table}{lon_str}"
    
    def format_weather_message(self, obs: Dict[str, Any], latitude: float, longitude: float) -> str:
        """
        Format weather observation data to APRS weather message format.
        
        APRS Weather Message Format:
        !llll.llN/ssss.ssSYsym<tab>hhhmm/sssss/gggg/tttt/rPPPP/pPPPP/bBBB/dDDD
        
        Args:
            obs: Weather observation dictionary
            latitude: Station latitude
            longitude: Station longitude
            
        Returns:
            Formatted APRS weather message string
        """
        # Position
        position = self.format_position(latitude, longitude)
        
        # Wind direction (degrees)
        wind_dir = obs.get("windDirection", 0) or 0
        
        # Wind speed (mph)
        wind_speed = obs.get("windSpeed", 0) or 0
        
        # Gust speed (mph)
        gust = obs.get("gust", 0) or wind_speed
        
        # Temperature (Fahrenheit)
        temp_f = obs.get("airTemperature", 0) or 0
        # Format temperature as 4-digit with leading zeros and sign
        if temp_f >= 0:
            temp_str = f"t{temp_f:03d}"
        else:
            temp_str = f"t{abs(temp_f):03d}"  # Negative temps handled differently in APRS
        
        # Rainfall (inches - today's total)
        rain_in = obs.get("precipTotal", 0) or 0
        if rain_in > 0:
            rain_str = f"r{rain_in * 100:03d}"  # Convert to hundredths of an inch
        else:
            rain_str = "r000"
        
        # Pressure (millibars or inches Hg)
        pressure = obs.get("pressure", 0) or 0
        if pressure > 0:
            # Convert to millibars if in hPa, or keep as is
            pressure_str = f"b{int(pressure)}"
        else:
            pressure_str = "b000"
        
        # Build the message
        # Note: APRS weather format uses tab character between position and data
        weather_data = f"{wind_dir:03d}/{int(wind_speed):03d}/{int(gust):03d}{temp_str}{rain_str}b{pressure_str}"
        
        return f"{position}{self.symbol_table}\t{weather_data}"
    
    def format_packet(self, message: str) -> str:
        """
        Format complete APRS packet with source and destination addresses.
        
        Args:
            message: The weather message content
            
        Returns:
            Complete APRS packet string
        """
        # APRS packets use AX.25 framing
        # Format: dstaddr<srcaddr,path:message
        dst_addr = "APRS"
        src_addr = f"{self.callsign}-{self.ssid}"
        
        return f"{dst_addr}<{src_addr},WIDE1-1}:{message}"
