import streamlit as st
from PIL import Image
from PIL.ExifTags import TAGS
from geopy.geocoders import Nominatim
import requests

st.title("Wildfire Risk Detector")

uploaded_file = st.file_uploader(
    "Upload an image",
    type=["jpg", "jpeg", "png"]
)

def get_exif_data(image):
    exif = {}
    info = image._getexif()

    if info:
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            exif[decoded] = value

    return exif

def dms_to_decimal(dms, ref):
    degrees = float(dms[0])
    minutes = float(dms[1])
    seconds = float(dms[2])

    decimal = degrees + minutes / 60 + seconds / 3600

    if ref in ["S", "W"]:
        decimal *= -1

    return decimal

def get_weather(lat, lon):
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m"
    )

    data = requests.get(url).json()

    current = data["current"]

    temp = current["temperature_2m"]
    humidity = current["relative_humidity_2m"]
    wind = current["wind_speed_10m"]

    return temp, humidity, wind

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image)

    exif = get_exif_data(image)

    if "GPSInfo" in exif:

        gps = exif["GPSInfo"]

        lat = dms_to_decimal(gps[2], gps[1])
        lon = dms_to_decimal(gps[4], gps[3])

        geolocator = Nominatim(user_agent="fire_risk_app")
        location = geolocator.reverse(f"{lat}, {lon}")

        if location:

            address = location.raw["address"]

            town = (
                address.get("city")
                or address.get("town")
                or address.get("village")
                or address.get("municipality")
                or "Unknown"
            )

            st.success(f"📍 Photo was taken near: {town}")

            temp, humidity, wind = get_weather(lat, lon)

            st.write(f"🌡 Temperature: {temp}°C")
            st.write(f"💧 Humidity: {humidity}%")
            st.write(f"💨 Wind Speed: {wind} km/h")

            risk = 0

            if temp > 30:
                risk += 3

            if humidity < 30:
                risk += 3

            if wind > 20:
                risk += 2

            if risk <= 3:
                level = "LOW"
            elif risk <= 6:
                level = "MODERATE"
            elif risk <= 8:
                level = "HIGH"
            else:
                level = "EXTREME"

            st.subheader(f"🔥 Fire Risk: {level}")

            st.write(
                f"""
                Summary:

                The photo was taken near {town}.

                Current temperature is {temp}°C.

                Relative humidity is {humidity}%.

                Wind speed is {wind} km/h.

                Estimated wildfire risk is {level}.
                """
            )

        else:
            st.error("Could not determine location.")

    else:
        st.error("No GPS location found in this image.")
