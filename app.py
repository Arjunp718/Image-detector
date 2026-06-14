import streamlit as st
from PIL import Image
from PIL.ExifTags import TAGS
from geopy.geocoders import Nominatim
import requests
import numpy as np

st.title("🔥 Wildfire Risk Detector")

uploaded_file = st.file_uploader(
    "Upload a photo",
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

def analyze_vegetation(image):
    img = np.array(image.convert("RGB"))

    red = img[:, :, 0]
    green = img[:, :, 1]
    blue = img[:, :, 2]

    green_pixels = np.sum(
        (green > red) &
        (green > blue)
    )

    brown_pixels = np.sum(
        (red > green) &
        (green > blue)
    )

    total_pixels = img.shape[0] * img.shape[1]

    green_percent = (green_pixels / total_pixels) * 100
    brown_percent = (brown_pixels / total_pixels) * 100

    return green_percent, brown_percent

if uploaded_file:

    image = Image.open(uploaded_file)

    st.image(
        image,
        caption="Uploaded Photo",
        use_container_width=True
    )

    exif = get_exif_data(image)

    if "GPSInfo" not in exif:
        st.error("No GPS location found in this image.")
        st.stop()

    gps = exif["GPSInfo"]

    try:
        lat = dms_to_decimal(gps[2], gps[1])
        lon = dms_to_decimal(gps[4], gps[3])

        geolocator = Nominatim(user_agent="wildfire_risk_detector")
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
        else:
            town = "Unknown"

        st.success(f"📍 Photo was taken near: {town}")

        green_percent, brown_percent = analyze_vegetation(image)

        st.write(f"🌿 Green Vegetation: {green_percent:.1f}%")
        st.write(f"🍂 Dry Vegetation: {brown_percent:.1f}%")

        temp, humidity, wind = get_weather(lat, lon)

        st.write(f"🌡 Temperature: {temp}°C")
        st.write(f"💧 Humidity: {humidity}%")
        st.write(f"💨 Wind Speed: {wind} km/h")

        risk = 0

        # Weather
        if temp > 30:
            risk += 3
        elif temp > 25:
            risk += 2

        if humidity < 30:
            risk += 3
        elif humidity < 50:
            risk += 1

        if wind > 20:
            risk += 2
        elif wind > 10:
            risk += 1

        # Vegetation
        if brown_percent > 20:
            risk += 2
        elif brown_percent > 10:
            risk += 1

        if green_percent > 50:
            risk -= 1

        # Risk level
        if risk <= 2:
            level = "LOW"
        elif risk <= 5:
            level = "MODERATE"
        elif risk <= 8:
            level = "HIGH"
        else:
            level = "EXTREME"

        st.subheader(f"🔥 Fire Risk: {level}")

        st.markdown("### Wildfire Risk Summary")

        st.write(
            f"""
            The photo was taken near **{town}**.

            Current weather conditions:
            - Temperature: {temp}°C
            - Humidity: {humidity}%
            - Wind Speed: {wind} km/h

            Vegetation detected:
            - Green Vegetation: {green_percent:.1f}%
            - Dry Vegetation: {brown_percent:.1f}%

            Based on both the photo and current weather conditions,
            the estimated wildfire risk is **{level}**.
            """
        )

    except Exception as e:
        st.error(f"Error: {e}")
