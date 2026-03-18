# APRS Weather Sender - Setup Guide

This guide covers the complete setup process for the Tempest-to-APRS weather broadcaster.

## Requirements

- Python 3.7+
- TempestWX weather station with API access
- Direwolf running with KISS TCP interface on port 8001
- Amateur radio license and valid FCC callsign
- Network connectivity between this machine and Direwolf

## Files Overview

| File | Purpose |
|------|---------|
| `config.yaml` | Configuration (API keys, callsign, network settings) |
| `main.py` | Application entry point |
| `tempestwx_client.py` | TempestWX API client (queries `swd.weatherflow.com`) |
| `aprs_formatter.py` | Converts weather data to APRS format with unit conversions |
| `kiss_tnc.py` | Builds AX.25 UI frames and KISS protocol framing |
| `requirements.txt` | Python dependencies |

## Step 1: Install Dependencies

```bash
cd /path/to/aprswx
pip install -r requirements.txt
```

Required packages:
- `PyYAML` - Configuration file parsing
- `requests` - HTTP client for TempestWX API

## Step 2: Get Your TempestWX API Token

1. Log into your WeatherFlow account at https://tempestwx.com/
2. Go to Settings → API → Token
3. Generate or copy your API token
4. Note your station ID (visible in the app or API documentation)

## Step 3: Configure Direwolf

Ensure Direwolf is configured to accept KISS connections:

**In your Direwolf configuration file** (typically `/etc/direwolf.conf`):

```
# Enable KISS protocol on TCP port 8001
KISSPORT 8001

# Configure an APRS channel (adjust as needed)
CHANNEL 0
    DESCRIPTION   "APRS Receive"
    FREQUENCY     144.39
    # ... other settings ...
```

Then start Direwolf:
```bash
direwolf -c /etc/direwolf.conf
```

Verify KISS is listening:
```bash
netstat -tuln | grep 8001
# Should show: tcp  0  0 127.0.0.1:8001  0.0.0.0:*  LISTEN
```

## Step 4: Configure the Application

Copy and edit `config.yaml`:

```yaml
tempestwx:
  api_key: "YOUR_TOKEN_FROM_STEP_2"
  station_id: "YOUR_STATION_ID"

direwolf:
  host: "127.0.0.1"              # localhost or 172.16.x.x for remote
  port: 8001                     # Must match Direwolf KISSPORT

aprs:
  callsign: "YOUR_CALLSIGN"      # e.g., W1AW
  ssid: 5                        # 5 for weather TX is standard
  symbol_table: "/"              # "/" = primary symbol table
  symbol_code: ">"               # ">" = weather station symbol

update_interval: 15              # Send update every 15 minutes
```

## Step 5: Test the Setup

Test everything before deploying:

```bash
# Run once, sending a single weather packet
python main.py --once
```

Expected output:
```
============================================================
APRS Weather Sender
============================================================
Config: /path/to/aprswx/config.yaml

Station: 164104
Location: 42.3601, -71.0589
Temperature: 68.5°F (20.3°C)
Wind: 090° at 12.3 mph
```

Check logs for any errors:
```bash
tail -20 /var/log/aprswx.log
```

Common issues to look for:
- "Error connecting to KISS TNC" → Direwolf not running or wrong port
- "Error fetching weather data" → Invalid API key or station ID
- "Something unexpected from client" → Direwolf received text instead of binary (old code issue)

## Step 6: Deploy for Continuous Operation

### Option A: Cron Job (Recommended - simple, reliable)

Add to crontab (`crontab -e`):
```bash
# Run weather sender every 15 minutes
*/15 * * * * /usr/bin/python3 /path/to/aprswx/main.py --once >> /var/log/aprswx.log 2>&1
```

### Option B: Systemd Service (Recommended - for servers)

Create `/etc/systemd/system/aprswx.service`:
```ini
[Unit]
Description=TempestWX APRS Weather Sender
After=network.target direwolf.service
Wants=direwolf.service

[Service]
Type=simple
User=weather
WorkingDirectory=/home/weather/aprswx
ExecStart=/usr/bin/python3 /home/weather/aprswx/main.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable aprswx.service
sudo systemctl start aprswx.service
sudo systemctl status aprswx.service
```

View logs:
```bash
sudo journalctl -u aprswx.service -f
```

### Option C: Manual Continuous Run

```bash
python main.py
```
This runs in an infinite loop. For persistent operation, use `screen`, `tmux`, or a process manager.

## Verification

Check that data is being transmitted:

1. **Monitor Direwolf output**: Should show packets being digipeated
2. **Check APRS.fi**: After 5-10 minutes, search for your callsign on https://aprs.fi/
3. **Monitor logs**: `tail -f /var/log/aprswx.log`

Example log output:
```
[2026-03-18 14:30:00] Fetching weather data...
[2026-03-18 14:30:01] Station: 164104
[2026-03-18 14:30:01] Location: 42.3601, -71.0589
[2026-03-18 14:30:01] Temperature: 68.5°F (20.3°C)
[2026-03-18 14:30:01] Wind: 090° at 12.3 mph
[2026-03-18 14:30:01] Weather data sent successfully!
```

## Unit Conversions

The application automatically converts from TempestWX (metric) to APRS (imperial/barometric):

| Field | TempestWX → APRS |
|-------|------------------|
| Wind Speed | m/s → mph (×2.23694) |
| Wind Gust | m/s → mph (×2.23694) |
| Temperature | °C → °F |
| Rainfall | mm → hundredths inch (÷25.4 ×100) |
| Pressure | mb/hPa → tenths of mb (×10, 5 digits) |

## Troubleshooting

### Connection Issues

**"Error connecting to KISS TNC"**
```bash
# Verify Direwolf is running
ps aux | grep direwolf

# Verify port is open
netstat -tuln | grep 8001

# Test connectivity
python3 -c "import socket; s = socket.socket(); s.connect(('127.0.0.1', 8001)); print('OK'); s.close()"
```

### API Issues

**"No observations found"**
```bash
# Test the API directly
curl "https://swd.weatherflow.com/swd/rest/observations/station/YOUR_ID?token=YOUR_TOKEN"

# Should return JSON with an "obs" array
```

### Data Not Appearing on APRS.fi

1. Verify your callsign and SSID are correct
2. Check Direwolf configuration includes an APRS beacon/transmit channel
3. Wait 5-10 minutes for APRS.fi to update
4. Check local packet monitoring tools (Xastir, etc.)

## Next Steps

- Set up a monitoring script to detect sending failures
- Configure Direwolf to beacon on multiple frequencies if desired
- Integrate with home weather station monitoring dashboards
- Contribute improvements back to the project!

