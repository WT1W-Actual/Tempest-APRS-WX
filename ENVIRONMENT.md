# APRS Weather Sender - Development Environment

This document describes the project structure, components, and development setup.

## Project Structure

```
aprswx/
├── README.md              # User-facing documentation
├── SETUP.md              # Installation and deployment guide
├── ENVIRONMENT.md        # This file - development info
├── config.yaml           # User configuration (API keys, callsign, etc.)
├── requirements.txt      # Python dependencies
│
├── main.py              # Application entry point
├── tempestwx_client.py  # TempestWX API integration
├── aprs_formatter.py    # Weather data → APRS format conversion
├── kiss_tnc.py          # KISS protocol framing and TNC interface
│
└── __pycache__/         # Python bytecode cache (gitignored)
```

## Component Architecture

### Data Flow

```
┌─────────────────────┐
│   TempestWX API     │
│  (REST, JSON)       │
└──────────┬──────────┘
           │ obs: {wind_direction, wind_avg, wind_gust, 
           │        air_temperature, relative_humidity,
           │        sea_level_pressure, ...}
           ↓
┌─────────────────────────────┐
│ tempestwx_client.py         │
│ - Query swd.weatherflow.com │
│ - Parse JSON response       │
│ - Extract obs array [0]     │
└──────────┬──────────────────┘
           │ raw_obs
           ↓
┌─────────────────────────────────────┐
│ aprs_formatter.py                   │
│ - Convert °C → °F                   │
│ - Convert m/s → mph                 │
│ - Convert mm → hundredths inch      │
│ - Build APRS format string          │
│ - Strict field ordering             │
└──────────┬──────────────────────────┘
           │ "090/025g035t068r000p000P000h75b10215"
           ↓
┌──────────────────────────────────────────────┐
│ kiss_tnc.py                                  │
│ - Build AX.25 UI frame (binary)              │
│ - Apply KISS byte-stuffing (0xC0, 0xDB)     │
│ - Wrap in FEND delimiters (0xC0)            │
│ - TCP send to Direwolf:8001                 │
└──────────┬───────────────────────────────────┘
           │ KISS frame (binary)
           ↓
┌────────────────────────┐
│   Direwolf KISS TCP    │
│   (port 8001)          │
└──────────┬─────────────┘
           │ RF Transmission
           ↓
┌────────────────────────┐
│   APRS Network         │
│   (APRS.fi visible)    │
└────────────────────────┘
```

## Component Details

### tempestwx_client.py

**Purpose**: Fetch current weather observations from TempestWX API

**Key Methods**:
- `__init__(api_key)` - Initialize with API token
- `get_station_data(station_id)` - Query API at `https://swd.weatherflow.com/swd/rest/observations/station/{id}?token={token}`
- `get_observation(station_id)` - Parse response and return first observation with lat/lon injected

**Response Structure** (from Tempest API):
```json
{
  "status": {"status_code": 0},
  "latitude": 42.3601,
  "longitude": -71.0589,
  "obs": [
    {
      "air_temperature": 20.3,
      "wind_direction": 090,
      "wind_avg": 5.5,
      "wind_gust": 8.2,
      "relative_humidity": 75,
      "sea_level_pressure": 1013.2,
      "precip": 0.0,
      "precip_accum_last_1hr": 0.0,
      "precip_accum_local_day": 0.0
    }
  ]
}
```

### aprs_formatter.py

**Purpose**: Convert metric weather data to APRS format with proper field ordering

**Key Methods**:
- `format_position(lat, lon)` - Convert decimal degrees to APRS format (e.g., "4221.36N/07124.56W")
- `format_weather_message(obs, lat, lon)` - Build complete APRS weather string with strict field ordering
- `format_packet(message)` - *Deprecated; APRS message now generated without this*

**APRS Weather Format** (strict order required by APRS.fi and clients):
```
_ccc/sss g... t... r... p... P... h.. b.....

_        = Weather symbol
ccc      = Wind direction (000-360°)
/sss     = Wind speed (mph)
g###     = Gust (mph)
t###     = Temperature (°F, -99 to 999)
r###     = Rain 1 hour (hundredths inch)
p###     = Rain 24 hours (hundredths inch)  
P###     = Rain since midnight (hundredths inch)
h##      = Humidity (00-99, where 00=100%)
b#####   = Barometer (tenths of millibars, 5 digits)
```

**Unit Conversions**:
- Wind: m/s × 2.23694 = mph
- Temp: (°C × 9/5) + 32 = °F
- Rain: mm × (100/25.4) = hundredths inch  
- Pressure: mb × 10 = tenths of mb (formatted to 5 digits)

### kiss_tnc.py

**Purpose**: Build proper AX.25 UI frames and wrap in KISS protocol for Direwolf

**Key Components**:

1. **KISS Framing Constants**:
   - `FEND = 0xC0` - Frame delimiter
   - `FESC = 0xDB` - Frame escape
   - `TFEND = 0xDC` - Transposed FEND
   - `TFESC = 0xDD` - Transposed FESC

2. **Key Functions**:
   - `_encode_ax25_address(callsign, ssid, end, c_bit)` - Encode 7-byte AX.25 address with SSID
   - `_build_ax25_ui_frame(src_call, src_ssid, info)` - Build complete frame: DEST + SOURCE + DIGI + CONTROL + PID + INFO
   - `_kiss_escape(data)` - Apply byte-stuffing: 0xC0→0xDB 0xDC, 0xDB→0xDB 0xDD
   - `_kiss_wrap(ax25_frame)` - Wrap frame with FEND delimiters and data-command byte

3. **KISSTNCClient**:
   - `connect()` - Establish TCP connection to Direwolf
   - `send_aprs_packet(callsign, ssid, info)` - Full pipeline: build frame → escape → wrap → send

**Frame Structure**:
```
FEND | <escaped: CMD|DEST|SOURCE|DIGI|CTRL|PID|INFO> | FEND

DEST:    APRS-0 (address shifted << 1, SSID byte with C-bit set)
SOURCE:  W1AW-5 (address shifted << 1, SSID byte)
DIGI:    WIDE1-1 (repeater path, end flag set)
CTRL:    0x03 (UI frame - unconnected information)
PID:     0xF0 (no layer 3 protocol)
INFO:    APRS weather string from formatter
```

### main.py

**Purpose**: Orchestrate the full workflow

**Workflow**:
1. Setup logging (console + file)
2. Load config.yaml
3. Initialize clients (TempestWX, APRS formatter, KISS TNC)
4. Fetch weather observation from API
5. Convert to APRS format
6. Connect to Direwolf and send packet
7. Handle errors gracefully, only send if weather fetch succeeds
8. Schedule: either once (`--once`) or continuous loop (default 15min interval)

**Logging Levels**:
- **DEBUG**: API URLs, parsed fields, unit conversions, KISS frame bytes
- **INFO**: Fetch status, connection events, final send confirmation
- **ERROR**: API failures, connection errors, config validation

## Development Setup

### Clone and Install

```bash
git clone https://github.com/WT1W-Actual/Tempest-APRS-WX.git
cd Tempest-APRS-WX
pip install -r requirements.txt
```

### Configuration for Testing

Create a local `config.yaml` with test values (see SETUP.md).

### Running Tests

```bash
# One-time send with verbose output
python main.py --once

# Continuous mode
python main.py

# Check specific component
python -c "from tempestwx_client import TempestWXClient; print('Import OK')"
```

### Common Development Tasks

**Debug API parsing**:
```python
from tempestwx_client import TempestWXClient
client = TempestWXClient("YOUR_TOKEN")
obs = client.get_observation("YOUR_STATION_ID")
print(obs)
```

**Debug APRS formatting**:
```python
from aprs_formatter import APRSWeatherFormatter
fmt = APRSWeatherFormatter("W1AW", 5, "/", ">")
msg = fmt.format_weather_message(obs, 42.3601, -71.0589)
print(msg)
```

**Debug KISS framing**:
```python
from kiss_tnc import _build_ax25_ui_frame, _kiss_wrap
frame = _build_ax25_ui_frame("W1AW", 5, "090/025g035t068...")
kiss = _kiss_wrap(frame)
print(kiss.hex())  # Inspect bytes
```

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| PyYAML | 6.0+ | Parse config.yaml |
| requests | 2.28+ | HTTP queries to TempestWX API |

## Testing Checklist

- [ ] API key and station ID are valid
- [ ] Direwolf running with `KISSPORT 8001`
- [ ] Can connect to `localhost:8001`
- [ ] Weather data fetches successfully
- [ ] Unit conversions produce reasonable values
- [ ] APRS packet format validates using online tools
- [ ] Data appears on APRS.fi within 5-10 minutes

## Common Issues & Solutions

| Issue | Root Cause | Solution |
|-------|-----------|----------|
| "KISS client has gone away" | Text sent instead of binary | Ensure using `send_aprs_packet()` not old text mode |
| No data on APRS.fi | Direwolf config issue | Check Direwolf channel is transmitting, check frequency |
| "Connection refused" | Direwolf not running | `ps aux \| grep direwolf` and verify port 8001 |
| API errors | Invalid token/ID | Test curl request directly against swd.weatherflow.com |

## References

- [APRS Specification](http://www.aprs.org/aprs11/aprs.txt)
- [AX.25 Protocol](http://www.ax25.net/)
- [KISS TNC Protocol](http://www.ka9q.net/papers/kiss.html)
- [Direwolf Documentation](https://github.com/wb2osz/direwolf)
- [TempestWX API](https://weatherflow.github.io/Tempest/api.html)
- [APRS.fi](https://aprs.fi/)

