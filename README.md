# APRS Weather Sender

A Python application that fetches weather data from TempestWX and sends it to Direwolf's KISS TNC interface in APRS format.

## Features

- Fetches current weather observations from TempestWX API
- Formats data according to APRS weather message specification
- Sends packets via TCP connection to Direwolf's KISS TNC on port 8001
- Runs automatically every 15 minutes (configurable)
- Handles wind speed, direction, temperature, and pressure data
- Comprehensive logging to system log file (`/var/log/aprswx.log`)
- Only sends data to Direwolf if weather fetch succeeds

## Logging

The application logs all operations to `/var/log/aprswx.log`:
- **INFO**: Weather data fetch success/failure, connection status, send status
- **DEBUG**: Detailed API responses, packet contents, connection details
- **ERROR**: Configuration errors, connection failures, API errors

Only successful weather data fetches result in packets being sent to Direwolf.

## Requirements

- Python 3.7+
- PyYAML library
- Access to a running Direwolf instance with KISS TNC enabled on port 8001

## Installation

1. Clone or copy the files to your desired directory
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Edit `config.yaml` with your settings:
   - TempestWX API key and station ID
   - Your amateur radio callsign and SSID
   - Direwolf connection details (default: localhost:8001)

## Configuration

Edit `config.yaml` to customize:

```yaml
tempestwx:
  api_key: "YOUR_TEMPESTWX_API_KEY"
  station_id: "YOUR_STATION_ID"

direwolf:
  host: "localhost"  # KISS TNC host
  port: 8001         # KISS TNC port

aprs:
  callsign: "YOUR_CALLSIGN"
  ssid: 5           # APRS SSID (0-15)
  symbol_table: "/" # "/" for weather station
  symbol_code: ">"  # ">" for weather station

update_interval: 15 # Minutes between updates
```

## Usage

### Run once (for testing):
```bash
python main.py --once
```

### Run as scheduled service:
```bash
python main.py
```

This will run continuously, fetching and sending weather data every 15 minutes.

### Using with cron:

Add to your crontab to run every 15 minutes:
```bash
*/15 * * * * /usr/bin/python3 /path/to/aprswx/main.py --once >> /var/log/aprswx.log 2>&1
```

## Log File

All operations are logged to `/var/log/aprswx.log`:
- **INFO**: Weather data fetch success/failure, connection status, send status
- **DEBUG**: Detailed API responses, packet contents, connection details
- **ERROR**: Configuration errors, connection failures, API errors

To view logs in real-time:
```bash
tail -f /var/log/aprswx.log
```

## APRS Weather Message Format

The application sends weather data in the standard APRS format:
```
!llll.llN/ssss.ssSYsym<tab>hhhmm/sssss/gggg/tttt/rPPPP/pPPPP/bBBB/dDDD
```

Where:
- `llll.llN` - Latitude
- `ssss.ssY` - Longitude with symbol
- `hhhmm` - Wind direction and speed
- `ssss` - Gust speed
- `gggg` - Wind gust direction
- `tttt` - Temperature (°F)
- `rPPPP` - Rainfall (hundredths of an inch)
- `pPPPP` - Pressure (millibars)

## Troubleshooting

1. **Connection refused**: Ensure Direwolf is running and KISS TNC is enabled on port 8001
2. **API errors**: Verify your TempestWX API key and station ID are correct
3. **No data sent**: Check the logs at `/var/log/aprswx.log` for error messages

## License

This project is provided as-is for amateur radio use.
