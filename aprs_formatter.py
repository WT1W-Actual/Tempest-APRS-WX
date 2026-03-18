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

        APRS Weather Message Format (strict field order per spec):
        _ccc/sssgggtttrrrrppppPPPPhhbbbbb
        """
        # Position
        position = self.format_position(latitude, longitude)

        # Wind direction (degrees)
        wind_dir = int(obs.get("wind_direction", 0) or 0)

        # Wind speed (Tempest returns m/s, APRS needs mph)
        wind_speed_ms = obs.get("wind_avg", 0) or 0
        wind_speed = int(round(wind_speed_ms * 2.23694))

        # Gust speed (m/s → mph)
        gust_ms = obs.get("wind_gust", 0) or wind_speed_ms
        gust = int(round(gust_ms * 2.23694))

        # Temperature (Tempest returns °C, APRS needs °F)
        temp_c = obs.get("air_temperature", 0) or 0
        temp_f = int(round(temp_c * 9 / 5 + 32))
        if temp_f >= 0:
            temp_str = f"t{temp_f:03d}"
        else:
            temp_str = f"t-{abs(temp_f):02d}"

        # Rainfall (Tempest returns mm, APRS needs hundredths of an inch)
        # r = last 1 hour, p = last 24 hours, P = since midnight
        rain_1h_mm = obs.get("precip", 0) or 0
        rain_1h = int(round(rain_1h_mm * 3.93701))

        rain_24h_mm = obs.get("precip_accum_last_1hr", 0) or 0  # fallback; Tempest uses 1hr field
        rain_24h = int(round(rain_24h_mm * 3.93701))

        rain_midnight_mm = obs.get("precip_accum_local_day", 0) or 0
        rain_midnight = int(round(rain_midnight_mm * 3.93701))

        # Humidity (0-99; 00 means 100%)
        humidity = int(obs.get("relative_humidity", 0) or 0)
        humidity_str = f"h{humidity % 100:02d}"

        # Pressure (Tempest returns mb/hPa, APRS needs tenths of mb, 5 digits)
        pressure_mb = obs.get("sea_level_pressure", 0) or 0
        pressure_str = f"b{int(round(pressure_mb * 10)):05d}"

        # Build weather data in strict APRS field order:
        # _ccc/sssgggtttrrrrppppPPPPhhbbbbb
        weather_data = (
            f"_{wind_dir:03d}/{wind_speed:03d}"
            f"g{gust:03d}"
            f"{temp_str}"
            f"r{rain_1h:03d}"
            f"p{rain_24h:03d}"
            f"P{rain_midnight:03d}"
            f"{humidity_str}"
            f"{pressure_str}"
        )

        return f"{position}{self.symbol_code}{weather_data}"
    
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
        
        return f"{dst_addr}<{src_addr},WIDE1-1>:{message}"
