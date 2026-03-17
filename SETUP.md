# APRS Weather Sender - Configuration

This directory contains the configuration file for the APRS weather sender application.

## Files

- `config.yaml` - Main configuration file (edit with your settings)
- `main.py` - Main application script
- `tempestwx_client.py` - TempestWX API client
- `aprs_formatter.py` - APRS message formatter
- `kiss_tnc.py` - KISS TNC TCP client

## Setup Instructions

1. Copy all files to your desired directory
2. Edit `config.yaml` with your:
   - TempestWX API key (get from https://api.weather.com/)
   - TempestWX station ID
   - Your amateur radio callsign and SSID
3. Install dependencies: `pip install -r requirements.txt`
4. Test the connection: `python main.py --once`
5. For continuous operation, set up a cron job or systemd service

## Direwolf Setup

Ensure Direwolf is configured with KISS TNC on port 8001:

```
KISSPORT 8001
```

And have an APRS channel configured to accept input from the KISS port.
