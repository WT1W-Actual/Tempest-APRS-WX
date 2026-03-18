# APRS Weather Sender

A Python application that fetches real-time weather data from **TempestWX** and broadcasts it via **APRS** (Automatic Packet Reporting System) through **Direwolf's KISS TNC** interface.

## Features

- **TempestWX Integration**: Fetches current weather observations from the TempestWX API (`swd.weatherflow.com`)
- **Proper KISS Protocol**: Implements correct AX.25 UI frame formatting with KISS binary framing (not text mode)
- **APRS Spec Compliance**: Formats weather data according to strict APRS field ordering and unit requirements
- **Comprehensive Weather Data**:
  - Wind direction, speed, and gust (converted m/s → mph)
  - Temperature (converted °C → °F)
  - Barometric pressure (in tenths of millibars)
  - Humidity
  - Rainfall (1-hour, 24-hour, and midnight-to-present)
- **Automatic Scheduling**: Runs continuously with configurable interval (default: 15 minutes)
- **Robust Error Handling**: Only sends packets if weather data fetch succeeds
- **Detailed Logging**: Tracks API calls, conversions, KISS frames, and TNC connections

## Architecture

### Components

- **`tempestwx_client.py`**: Queries the TempestWX API at `https://swd.weatherflow.com/swd/rest/observations/station/{station_id}` with your token
- **`aprs_formatter.py`**: Converts raw weather data to APRS format with proper unit conversions (metric → imperial/APRS units)
- **`kiss_tnc.py`**: Builds AX.25 UI frames and wraps them in proper KISS framing for Direwolf's TCP interface
- **`main.py`**: Orchestrates the workflow, loading config, fetching weather, formatting, and sending

### Data Flow

```
TempestWX API
    ↓ (raw observation in metric units)
aprs_formatter.py
    ↓ (convert units, build APRS packet)
kiss_tnc.py
    ↓ (build AX.25 frame, KISS framing)
Direwolf KISS TCP (port 8001)
    ↓ (transmit on RF)
APRS Network
```

## Configuration

Edit `config.yaml`:

```yaml
tempestwx:
  api_key: "YOUR_TEMPEST_API_TOKEN"    # From WeatherFlow
  station_id: "YOUR_STATION_ID"         # Your Tempest station ID

direwolf:
  host: "172.16.2.201"                  # Direwolf system IP
  port: 8001                            # KISS TCP port (must match Direwolf config)

aprs:
  callsign: "YOUR_CALLSIGN"            # e.g., W1AW
  ssid: 5                               # APRS SSID (0-15, typically 5 for weather)
  symbol_table: "/"                     # "/" = weather station
  symbol_code: ">"                      # ">" = weather station symbol

update_interval: 15                     # Minutes between updates
```

## Installation & Setup

### Prerequisites

- Python 3.7+
- Direwolf with KISS TCP enabled: `KISSPORT 8001`
- TempestWX API key and station ID
- Amateur radio license and valid callsign

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/WT1W-Actual/Tempest-APRS-WX.git
   cd Tempest-APRS-WX
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your settings**:
   ```bash
   cp config.yaml.example config.yaml
   # Edit config.yaml with your API key, station ID, callsign, etc.
   ```

4. **Test the setup** (send one packet and exit):
   ```bash
   python main.py --once
   ```

5. **Check the logs**:
   ```bash
   tail -f /var/log/aprswx.log
   ```

## Usage

### One-Time Send (for testing)
```bash
python main.py --once
```

### Continuous Operation (recommended)
```bash
python main.py
```
Runs in an infinite loop, sending weather updates every 15 minutes (or your configured interval).

### Cron Job (recommended for reliability)
Add to your crontab (`crontab -e`):
```bash
# Send weather data every 15 minutes
*/15 * * * * /usr/bin/python3 /path/to/aprswx/main.py --once >> /var/log/aprswx.log 2>&1
```

### Systemd Service
Create `/etc/systemd/system/aprswx.service`:
```ini
[Unit]
Description=APRS Weather Sender
After=network.target

[Service]
Type=simple
User=weather
WorkingDirectory=/home/weather/aprswx
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

Then enable and start:
```bash
sudo systemctl enable aprswx.service
sudo systemctl start aprswx.service
```

## APRS Weather Format

The application broadcasts weather data in strict APRS format. Example output on APRS.fi:

```
WT1W>APRS,WIDE1-1:_090/025g035t068r000p000P000h75b10215
```

Field breakdown:
- `_` = Weather report identifier
- `090` = Wind direction (degrees)
- `/025` = Wind speed (mph)
- `g035` = Gust (mph)
- `t068` = Temperature (°F)
- `r000` = Rain last hour (hundredths inch)
- `p000` = Rain last 24 hours (hundredths inch)
- `P000` = Rain since midnight (hundredths inch)
- `h75` = Humidity (00-99, where 00 = 100%)
- `b10215` = Barometer (tenths of millibars)

## Logging

All operations logged to `/var/log/aprswx.log`:

- **INFO**: Fetch success/failure, connection status, data sent
- **DEBUG**: API responses, field conversions, KISS frame bytes
- **ERROR**: Config/connection/API errors

View logs in real-time:
```bash
tail -f /var/log/aprswx.log
```

## Troubleshooting

### "Connection refused" on port 8001
- Verify Direwolf is running with `KISSPORT 8001` configured
- Check firewall allows localhost:8001 or your network connectivity

### "No observations found"
- Verify TempestWX API key and station ID in config.yaml
- Test the API directly: `curl "https://swd.weatherflow.com/swd/rest/observations/station/{ID}?token={TOKEN}"`

### "Something unexpected from client application"
- This means Direwolf is receiving text instead of proper KISS binary frames
- Verify you're using the latest code with proper KISS framing (not text mode)

### Packets not appearing on APRS.fi
- Check that your callsign and SSID are correct
- Verify Direwolf is outputting to a channel with APRS filtering enabled
- Allow 5-10 minutes for APRS.fi to update

## License

MIT

## Contributing

Pull requests welcome! Please ensure code follows the existing style and includes appropriate error handling and logging.

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
