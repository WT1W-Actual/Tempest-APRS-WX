"""
TempestWX API Client for fetching weather data.
"""

import requests
import logging
from typing import Dict, Any, Optional


logger = logging.getLogger('aprswx')


class TempestWXClient:
    """Client for interacting with the TempestWX API."""
    
    BASE_URL = "https://api.weather.com/v1"
    
    def __init__(self, api_key: str):
        """
        Initialize the TempestWX client.
        
        Args:
            api_key: Your TempestWX API key
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "TempestWX-APRS-Weather-Sender/1.0"
        })
    
    def get_station_data(self, station_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current weather data for a specific station.
        
        Args:
            station_id: The TempestWX station ID
            
        Returns:
            Dictionary containing weather data or None if request fails
        """
        url = f"https://api.weather.com/v1/stations/{station_id}/observations/current"
        params = {
            "apiKey": self.api_key,
            "units": "e"  # Use imperial units for APRS compatibility
        }
        
        try:
            logger.debug(f"Fetching weather data from TempestWX API for station {station_id}")
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching weather data: {e}")
            logger.debug(f"API URL: {url}, Params: {params}")
            return None
    
    def get_observation(self, station_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current observation from a station.
        
        Args:
            station_id: The TempestWX station ID
            
        Returns:
            Dictionary containing the observation data
        """
        data = self.get_station_data(station_id)
        if data and "observations" in data:
            logger.debug(f"Successfully retrieved observation for station {station_id}")
            return data["observations"][0]
        else:
            logger.warning(f"No observations found in response for station {station_id}")
        return None
