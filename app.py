import streamlit as st
from PIL import Image
from PIL.ExifTags import TAGS
from geopy.geocoders import Nominatim
import requests
import numpy as np

st.set_page_config(page_title="Canada Wildfire Risk AI", page_icon="🔥")

st.title("🔥 Canada Wildfire Risk AI")
st.write("Upload a GPS-tagged photo to estimate wildfire risk using image analysis and weather data.")

uploaded_file = st.file_uploader(
    "Upload a photo",
    type=["jpg", "jpeg", "png"]
)

# Historical wildfire hotspot factors
fire_hotspots = {
    "British Columbia": 15,
    "Alberta": 12,
    "Saskatchewan": 10,
    "Northwest Territories": 18,
    "Yukon": 16,
    "Ontario": 8,
    "Quebec": 7,
    "Manitoba": 9,
    "New Brunswick": 5,
    "Nova Scotia": 5,
    "Prince Edward Island": 3,
    "Newfoundland and Labrador": 4
}

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

    return (
        current["temperature_2m"],
        current["relative_humidity_2m"],
        current["wind_speed_10m"]
    )

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

def detect_water(image):
    img = np.array(image.convert("RGB"))

    red = img[:, :, 0]
    green = img[:, :, 1]
    blue = img[:, :, 2]

    water_pixels = np.sum(
        (blue > red) &
        (blue > green)
    )

    total_pixels = img.shape[0] * img.shape[1]

    return (water_pixels / total_pixels) * 100

def estimate_ndvi(image):
    img = np.array(image.convert("RGB"))

    red = img[:, :, 0].astype(float)
    green = img[:, :, 1].astype(float)

    ndvi = (green - red) / (green + red + 1)

    return float(np.mean(ndvi))

def vegetation_density(green_percent):

    if green_percent > 70:
        return "Very Dense"

    elif green_percent > 50:
        return "Dense"

    elif green_percent > 30:
        return "Moderate"

    else:
        return "Sparse"

if uploaded_file:

    try:

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

        lat = dms_to_decimal(gps[2], gps[1])
        lon = dms_to_decimal(gps[4], gps[3])

        geolocator = Nominatim(
            user_agent="canada_wildfire_ai"
        )

        location = geolocator.reverse(
            f"{lat}, {lon}"
        )

        town = "Unknown"
        province = "Unknown"

        if location:

            address = location.raw["address"]

            town = (
                address.get("city")
                or address.get("town")
                or address.get("village")
                or address.get("municipality")
                or "Unknown"
            )

            province = address.get("state", "Unknown")

        st.success(
            f"📍 Photo Location: {town}, {province}"
        )

        green_percent, brown_percent = analyze_vegetation(image)

        water_percent = detect_water(image)

        ndvi = estimate_ndvi(image)

        density = vegetation_density(
            green_percent
        )

        st.subheader("🛰 Satellite Analysis")

        st.write(f"🌿 Green Vegetation: {green_percent:.1f}%")
        st.write(f"🍂 Dry Vegetation: {brown_percent:.1f}%")
        st.write(f"🌊 Water Detected: {water_percent:.1f}%")
        st.write(f"🌳 Forest Density: {density}")
        st.write(f"🛰 Estimated NDVI: {ndvi:.3f}")

        if water_percent > 20:
            water_effect = "Strong Natural Fire Barrier"
        elif water_percent > 10:
            water_effect = "Moderate Natural Fire Barrier"
        else:
            water_effect = "Little Water Protection"

        st.write(f"💧 Water Impact: {water_effect}")

        temp, humidity, wind = get_weather(
            lat,
            lon
        )

        st.subheader("🌤 Weather Conditions")

        st.write(f"🌡 Temperature: {temp}°C")
        st.write(f"💧 Humidity: {humidity}%")
        st.write(f"💨 Wind Speed: {wind} km/h")

        hotspot_factor = fire_hotspots.get(
            province,
            5
        )

        # AI-style wildfire score

        risk_score = 0

        risk_score += min(temp, 40) / 40 * 30
        risk_score += (100 - humidity) / 100 * 20
        risk_score += min(wind, 50) / 50 * 15
        risk_score += min(brown_percent, 100) / 100 * 15
        risk_score += min(green_percent, 100) / 100 * 10

        # NDVI contribution
        if ndvi < 0:
            risk_score += 10
        elif ndvi < 0.1:
            risk_score += 5

        # Historical wildfire factor
        risk_score += hotspot_factor * 0.5

        # Water protection
        risk_score -= min(water_percent, 20) / 20 * 10

        risk_score = max(
            0,
            min(100, risk_score)
        )

        if risk_score < 25:
            level = "LOW"

        elif risk_score < 50:
            level = "MODERATE"

        elif risk_score < 75:
            level = "HIGH"

        else:
            level = "EXTREME"

        st.subheader("🔥 AI Wildfire Assessment")

        st.metric(
            "Wildfire Risk Score",
            f"{risk_score:.1f}/100"
        )

        st.metric(
            "Risk Level",
            level
        )

        st.write(
            f"📚 Historical Fire Factor: {hotspot_factor}"
        )

        st.markdown("## AI Analysis Summary")

        st.write(
            f"""
            Location: {town}, {province}

            Temperature: {temp}°C

            Humidity: {humidity}%

            Wind Speed: {wind} km/h

            Green Vegetation: {green_percent:.1f}%

            Dry Vegetation: {brown_percent:.1f}%

            Water Coverage: {water_percent:.1f}%

            Vegetation Density: {density}

            Estimated NDVI: {ndvi:.3f}

            Historical Fire Factor: {hotspot_factor}

            Final Wildfire Risk Score:
            {risk_score:.1f}/100

            Estimated Wildfire Risk:
            {level}
            """
        )

    except Exception as e:
        st.error(f"Error: {e}")
