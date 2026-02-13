import os
import requests
import streamlit as st

BACKEND_URL = "http://backend:8000"

st.set_page_config(page_title="Streamlit Base", layout="centered")
st.title("🚀 Streamlit Base App")

st.write("Backend URL:", BACKEND_URL)
