# app.py
import streamlit as st
from utils.auth import verify_user, create_user, ensure_demo_user
from utils.storage import load_aircrafts, add_aircraft, csv_export_string
from utils.api_client import fetch_metar_avwx, fetch_metar_aviationweather, fetch_open_meteo
from utils.metar_parser import parse_metar_simple
import pandas as pd
import csv
from pathlib import Path
import io

st.set_page_config(page_title="AeroWeather", layout="wide")
ensure_demo_user()  # creates demo/demo123 if not present

# Session login state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

def login_box():
    st.title("AeroWeather — Login")
    with st.form("login_form"):
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            if verify_user(user.strip(), pwd.strip()):
                st.session_state.logged_in = True
                st.session_state.username = user.strip()
                st.success(f"Logged in as {user.strip()}")
                st.rerun()
            else:
                st.error("Invalid username or password")

if not st.session_state.logged_in:
    login_box()
    st.info("Demo user: `demo` / `demo123`")
    st.stop()

# Sidebar navigation
page = st.sidebar.selectbox("Page", ["Aircrafts", "Weather", "Admin", "Logout"])

if page == "Logout":
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()

if page == "Aircrafts":
    st.header("Aircraft details")
    with st.form("add_aircraft"):
        ac_no = st.text_input("Aircraft number", placeholder="e.g. VT-ABC")
        origin = st.text_input("Origin ICAO (e.g. VIDP)")
        dest = st.text_input("Destination ICAO (e.g., EGLL)")
        dep_date = st.date_input("Departure date")
        dep_time = st.time_input("Departure time")
        submit = st.form_submit_button("Add Aircraft")
        if submit:
            rec = {
                "aircraft_no": ac_no.strip(),
                "origin": origin.strip().upper(),
                "dest": dest.strip().upper(),
                "departure": f"{dep_date} {dep_time}"
            }
            add_aircraft(rec)
            st.success("Aircraft record saved")

    ac_list = load_aircrafts()
    if ac_list:
        df = pd.DataFrame(ac_list)
        st.dataframe(df)
        csv_bytes = csv_export_string().encode("utf-8")
        st.download_button("Export CSV", csv_bytes, "aircrafts.csv")
    else:
        st.info("No aircrafts recorded yet.")

elif page == "Weather":
    st.header("Weather & Flight Safety")
    col1, col2 = st.columns([1, 2])
    with col1:
        icao = st.text_input("Airport ICAO", value="KJFK")
        lookup = st.button("Lookup")
    with col2:
        st.write("Enter ICAO and press Lookup. Uses AVWX (if available) -> AviationWeather -> Open-Meteo fallback.")

    if lookup and icao.strip():
        icao = icao.strip().upper()
        st.info(f"Fetching METAR for {icao}...")
        metar = None
        # Try AVWX first (structured)
        try:
            metar = fetch_metar_avwx(icao)
        except Exception:
            metar = None
        # If AVWX failed, try AviationWeather
        if not metar:
            try:
                metar = fetch_metar_aviationweather(icao)
            except Exception:
                metar = None

        if metar:
            parsed = parse_metar_simple(metar)
            st.subheader("METAR / Observation (parsed)")
            st.json(parsed)
            st.markdown("**Raw METAR / decoded:**")
            st.code(parsed.get("raw_text") or str(metar))
            # Very basic heuristic for flight safety
            vis = parsed.get("visibility")
            if vis is not None:
                try:
                    # many sources give miles or meters; try numeric parse
                    v = float(vis)
                except Exception:
                    v = None
            else:
                v = None
            # fetch wind info
            wind = parsed.get("wind") or {}
            # Heuristic:
            status = "OK"
            reasons = []
            if v is not None and v < 2:  # less than 2 statute miles -> caution
                status = "DELAY"
                reasons.append(f"Low visibility ({v})")
            if wind and (wind.get("speed_kt") and wind.get("speed_kt") > 40):
                status = "DELAY"
                reasons.append(f"High wind speed ({wind.get('speed_kt')} kt)")
            if status == "OK" and (v is not None and v < 5):
                status = "CAUTION"
                reasons.append("Visibility below recommended VFR minima")
            st.markdown(f"**Quick safety heuristic:** **{status}**")
            if reasons:
                for r in reasons:
                    st.warning(r)
        else:
            st.warning("No METAR found. Falling back to Open-Meteo using airports.csv coordinates.")
            # try airports.csv lookup
            airports_path = Path("airports.csv")
            if not airports_path.exists():
                st.error("airports.csv missing; add coordinates for the ICAO in airports.csv")
            else:
                df = pd.read_csv(airports_path)
                row = df[df["icao"].str.upper() == icao]
                if row.empty:
                    st.error("ICAO not found in airports.csv. Add it (icao,lat,lon,...).")
                else:
                    lat = float(row.iloc[0]["lat"])
                    lon = float(row.iloc[0]["lon"])
                    st.info(f"Fetching Open-Meteo for {icao} at {lat},{lon}")
                    try:
                        forecast = fetch_open_meteo(lat, lon)
                        st.subheader("Open-Meteo (hourly sample keys)")
                        # show small sample table of hourly variables if present
                        hourly = forecast.get("hourly")
                        if hourly:
                            sample = {k: hourly.get(k)[:8] for k in list(hourly.keys())[:4] if hourly.get(k)}
                            st.json(sample)
                        st.json({k: forecast.get(k) for k in ["latitude", "longitude", "generationtime_ms"]})
                    except Exception as e:
                        st.error(f"Open-Meteo request failed: {e}")

elif page == "Admin":
    st.header("Admin")
    st.write("Create users (demo only). For production use proper auth.")
    with st.form("create_user"):
        uname = st.text_input("New username")
        pwd = st.text_input("New password", type="password")
        create = st.form_submit_button("Create user")
        if create:
            try:
                create_user(uname.strip(), pwd.strip())
                st.success("User created")
            except Exception as e:
                st.error(str(e))
