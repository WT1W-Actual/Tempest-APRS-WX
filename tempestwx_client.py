"""
TempestWX API Client for fetching weather data.
"""

import requests
import logging
from typing import Dict, Any, Optional


logger = logging.getLogger('aprswx')


class TempestWXClient:
    """Client for interacting with the TempestWX API."""
    
    BASE_URL = "https://swd.weatherflow.com"
    
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
        url = f"https://swd.weatherflow.com/swd/rest/observations/station/{station_id}"
        params = {
            "token": self.api_key
        }
        
        try:
            logger.debug(f"Fetching weather data from TempestWX API for station {station_id}")
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching weather data: {e}")
            logger.debug(f"API URL: {url}")
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
        if data and data.get("status", {}).get("status_code") == 0:
            obs_list = data.get("obs")
            if obs_list:
                obs = obs_list[0]
                obs["latitude"] = data.get("latitude", 0)
                obs["longitude"] = data.get("longitude", 0)
                logger.debug(f"Successfully retrieved observation for station {station_id}")
                return obs
        logger.warning(f"No observations found in response for station {station_id}")
        return None
