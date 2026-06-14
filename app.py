import streamlit as st
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

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

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image)

    exif = get_exif_data(image)

    if "GPSInfo" in exif:
        st.success("GPS data found!")
        st.write(exif["GPSInfo"])
    else:
        st.error("No GPS location found in this image.")
