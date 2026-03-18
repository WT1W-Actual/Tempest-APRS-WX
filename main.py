#!/usr/bin/env python3
"""
APRS Weather Sender - Main Application

This application fetches weather data from TempestWX and sends it to Direwolf's
KISS TNC interface in APRS format. It runs every 15 minutes as scheduled.
"""

import yaml
import sys
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

from tempestwx_client import TempestWXClient
from aprs_formatter import APRSWeatherFormatter
from kiss_tnc import KISSTNCClient


def setup_logging(logdir: str = "./logs") -> logging.Logger:
    """
    Setup logging to both console and file.
    
    Args:
        logdir: Directory where log files will be stored. Will be created if it doesn't exist.
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger('aprswx')
    logger.setLevel(logging.DEBUG)
    
    # Console handler (always shows errors)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler for debug logging
    try:
        # Create log directory if it doesn't exist
        log_path = Path(logdir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        log_file = log_path / "aprswx.log"
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    except (PermissionError, OSError) as e:
        # If we can't write to log, just use console
        logger.warning(f"Could not setup log file in {logdir}: {e}")
    
    return logger


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_path}' not found")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing configuration file: {e}")
        sys.exit(1)


def format_aprs_timestamp(dt: datetime) -> str:
    """Format datetime to APRS timestamp (ddhhmmz)."""
    return dt.strftime("%d%H%Mz")


def send_weather_data(config: dict, logger: logging.Logger) -> bool:
    """
    Fetch weather data and send to Direwolf.
    
    Args:
        config: Configuration dictionary
        logger: Logger instance for debug output
        
    Returns:
        True if successful, False otherwise
    """
    # Extract configuration values
    tempest_config = config.get('tempestwx', {})
    direwolf_config = config.get('direwolf', {})
    aprs_config = config.get('aprs', {})
    
    api_key = tempest_config.get('api_key')
    station_id = tempest_config.get('station_id')
    
    host = direwolf_config.get('host', 'localhost')
    port = direwolf_config.get('port', 8001)
    
    callsign = aprs_config.get('callsign')
    ssid = aprs_config.get('ssid', 0)
    symbol_table = aprs_config.get('symbol_table', '/')
    symbol_code = aprs_config.get('symbol_code', '>')
    
    # Validate required configuration
    if not all([api_key, station_id, callsign]):
        logger.error("Missing required configuration values")
        logger.error(f"  API Key: {'✓' if api_key else '✗'}")
        logger.error(f"  Station ID: {'✓' if station_id else '✗'}")
        logger.error(f"  Callsign: {'✓' if callsign else '✗'}")
        return False
    
    # Initialize components
    weather_client = TempestWXClient(api_key)
    formatter = APRSWeatherFormatter(callsign, ssid, symbol_table, symbol_code)
    tnc_client = KISSTNCClient(host, port)
    
    logger.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Fetching weather data...")
    
    # Get weather observation - DO NOT proceed if this fails
    obs = weather_client.get_observation(station_id)
    if not obs:
        logger.error("Failed to fetch weather data from TempestWX")
        logger.debug(f"Station ID: {station_id}")
        return False
    
    logger.info("Weather data successfully fetched")
    
    # Extract coordinates and weather data
    latitude = obs.get('latitude', 0)
    longitude = obs.get('longitude', 0)
    
    logger.info(f"Station: {station_id}")
    logger.info(f"Location: {latitude:.4f}, {longitude:.4f}")
    temp_c = obs.get('air_temperature', 'N/A')
    temp_f = round(temp_c * 9 / 5 + 32, 1) if isinstance(temp_c, (int, float)) else 'N/A'
    logger.info(f"Temperature: {temp_f}°F ({temp_c}°C)")
    wind_ms = obs.get('wind_avg', 'N/A')
    wind_mph = round(wind_ms * 2.23694, 1) if isinstance(wind_ms, (int, float)) else 'N/A'
    logger.info(f"Wind: {obs.get('wind_direction', 'N/A')}° at {wind_mph} mph")
    
    # Format APRS message
    weather_message = formatter.format_weather_message(obs, latitude, longitude)
    aprs_packet = formatter.format_packet(weather_message)
    
    logger.debug(f"APRS Packet: {aprs_packet}")
    
    # Connect to KISS TNC and send - ONLY if we have valid weather data
    if not tnc_client.connect():
        logger.error("Failed to connect to KISS TNC")
        return False
    
    try:
        success = tnc_client.send_aprs_packet(callsign, ssid, weather_message)
        if success:
            logger.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Weather data sent successfully!")
            return True
        else:
            logger.error("Failed to send weather data")
            return False
    finally:
        tnc_client.disconnect()


def main():
    """Main application entry point."""
    # Determine config path
    script_dir = Path(__file__).parent.resolve()
    config_path = script_dir / "config.yaml"
    
    # Load configuration before setting up logging
    config = load_config(str(config_path))
    
    # Get log directory from config
    logdir = config.get('logging', {}).get('logdir', './logs')
    
    # Setup logging with configured directory
    logger = setup_logging(logdir)
    
    logger.info("=" * 60)
    logger.info("APRS Weather Sender")
    logger.info("=" * 60)
    logger.info(f"Config: {config_path}")
    logger.info(f"Logs: {Path(logdir).resolve()}")
    logger.info("")
    
    # Check if we should run once or schedule
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Run once and exit
        success = send_weather_data(config, logger)
        if success:
            logger.info("Weather data sent successfully")
        else:
            logger.error("Failed to send weather data")
        sys.exit(0 if success else 1)
    else:
        # Run on schedule (every 15 minutes)
        update_interval = config.get('update_interval', 15)
        logger.info(f"Running every {update_interval} minutes...")
        logger.info("")
        
        while True:
            start_time = datetime.now()
            
            # Send weather data
            success = send_weather_data(config, logger)
            
            # Calculate next run time
            if success:
                next_run = start_time + timedelta(minutes=update_interval)
                wait_time = (next_run - datetime.now()).total_seconds()
                
                if wait_time > 0:
                    logger.info(f"Next update at: {next_run.strftime('%H:%M:%S')}")
                    logger.info(f"Waiting {wait_time:.0f} seconds...")
                    time.sleep(wait_time)
            else:
                # If failed, retry in 5 minutes
                logger.warning("Retrying in 5 minutes...")
                time.sleep(300)


if __name__ == "__main__":
    main()
