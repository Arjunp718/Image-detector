import streamlit as st

st.title("Image Origin Detector")

uploaded_file = st.file_uploader(
    "Upload an image",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file:
    st.image(uploaded_file)

    st.success("Image uploaded!")

    st.write("Analysis will go here.")
