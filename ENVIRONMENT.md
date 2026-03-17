# Python Environment for APRS Weather Sender

This directory contains the Python application for fetching weather data from TempestWX and sending it to Direwolf's KISS TNC.

## Project Structure

```
aprswx/
├── config.yaml          # Configuration file (edit with your settings)
├── main.py             # Main application script
├── tempestwx_client.py # TempestWX API client
├── aprs_formatter.py   # APRS message formatter
├── kiss_tnc.py         # KISS TNC TCP client
├── requirements.txt    # Python dependencies
├── README.md           # Project documentation
└── SETUP.md            # Setup instructions
```

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Edit `config.yaml` with your settings:
   - TempestWX API key and station ID
   - Your amateur radio callsign and SSID
   - Direwolf connection details (default: localhost:8001)

3. Test the application:
   ```bash
   python main.py --once
   ```

4. For continuous operation, run:
   ```bash
   python main.py
   ```

## Configuration

The `config.yaml` file contains all settings:

```yaml
tempestwx:
  api_key: "YOUR_TEMPESTWX_API_KEY"
  station_id: "YOUR_STATION_ID"

direwolf:
  host: "localhost"
  port: 8001

aprs:
  callsign: "YOUR_CALLSIGN"
  ssid: 5
  symbol_table: "/"
  symbol_code: ">"

update_interval: 15
```

## Usage Examples

### Run once (for testing)
```bash
python main.py --once
```

### Run continuously (every 15 minutes by default)
```bash
python main.py
```

### Using with cron (add to crontab)
```bash
# Run every 15 minutes
*/15 * * * * /usr/bin/python3 /path/to/aprswx/main.py --once >> /var/log/aprswx.log 2>&1
```

## Requirements

- Python 3.7+
- PyYAML
- requests

See `requirements.txt` for complete list.
