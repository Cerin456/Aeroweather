# utils/metar_parser.py
from dateutil import parser

def parse_metar_simple(metar_obj):
    """
    Return a small dict with raw_text, visibility, wind, temp, clouds, time.
    Accepts both AVWX JSON and aviationweather METAR dicts or raw string.
    """
    out = {"raw_text": None, "visibility": None, "wind": None, "temp_c": None, "clouds": None, "time": None}
    if metar_obj is None:
        return out
    if isinstance(metar_obj, dict):
        # AVWX style commonly has 'raw' or 'raw_text'
        out["raw_text"] = metar_obj.get("raw") or metar_obj.get("raw_text") or str(metar_obj)
        # attempt a few keys
        out["visibility"] = metar_obj.get("visibility") or metar_obj.get("visibility_statute_mi")
        wind = {}
        if metar_obj.get("wind_dir_degrees"):
            wind["dir_deg"] = metar_obj.get("wind_dir_degrees")
        if metar_obj.get("wind_speed_kt"):
            wind["speed_kt"] = metar_obj.get("wind_speed_kt")
        elif metar_obj.get("wind_speed_kph"):
            wind["speed_kph"] = metar_obj.get("wind_speed_kph")
        out["wind"] = wind or None
        out["temp_c"] = metar_obj.get("temp_c")
        out["clouds"] = metar_obj.get("sky_condition") or metar_obj.get("clouds")
        out["time"] = metar_obj.get("observation_time") or metar_obj.get("time") or metar_obj.get("time_observed")
    else:
        out["raw_text"] = str(metar_obj)
    return out
