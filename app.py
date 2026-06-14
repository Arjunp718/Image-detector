import streamlit as st
from PIL import Image
from PIL.ExifTags import TAGS
from geopy.geocoders import Nominatim

st.title("Photo Location Detector")

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

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image)

    exif = get_exif_data(image)

    if "GPSInfo" in exif:
        gps = exif["GPSInfo"]

        lat = dms_to_decimal(gps[2], gps[1])
        lon = dms_to_decimal(gps[4], gps[3])

        geolocator = Nominatim(user_agent="photo_locator")
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

        else:
            st.warning("Location found but town could not be determined.")

    else:
        st.error("No GPS location found in this image.")
