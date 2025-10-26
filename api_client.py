# utils/api_client.py
import requests
from urllib.parse import urlencode

# NOTE: If you have an AVWX API key, set it here or via environment variables.
AVWX_API_KEY = None  # Example: "your_avwx_key_here"

AWC_DATASERVER = "https://aviationweather.gov/adds/dataserver_current/httpparam"
OPEN_METEO = "https://api.open-meteo.com/v1/forecast"
AVWX_BASE = "https://avwx.rest/api/metar/"

def fetch_metar_aviationweather(station: str):
    """Try the NOAA/AviationWeather data server for METAR (json)."""
    params = {
        "datasource": "metars",
        "requestType": "retrieve",
        "format": "json",
        "stationString": station,
        "hoursBeforeNow": 4,
        "mostRecentForEachStation": "true"
    }
    url = AWC_DATASERVER + "?" + urlencode(params)
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    j = r.json()
    # j['METAR'] may be inside j['data']['METAR'] depending on response
    data = j.get("data", {})
    # aviationweather returns key 'METAR' inside 'data' in many cases
    if isinstance(data, dict):
        metars = data.get("METAR") or []
        if len(metars) > 0:
            return metars[0]
    return None

def fetch_metar_avwx(station: str):
    """Try AVWX (structured JSON). Returns JSON or None. Requires key for higher limits."""
    url = AVWX_BASE + station
    headers = {}
    if AVWX_API_KEY:
        headers["Authorization"] = f"Bearer {AVWX_API_KEY}"
    try:
        r = requests.get(url, headers=headers, params={"options":"info"}, timeout=8)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception:
        return None

def fetch_open_meteo(lat: float, lon: float, hourly_vars=None):
    """Open-Meteo fallback for forecast / hourly variables."""
    if hourly_vars is None:
        hourly_vars = ["temperature_2m", "windspeed_10m", "winddirection_10m", "visibility"]
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ",".join(hourly_vars),
        "timezone": "UTC"
    }
    r = requests.get(OPEN_METEO, params=params, timeout=10)
    r.raise_for_status()
    return r.json()
