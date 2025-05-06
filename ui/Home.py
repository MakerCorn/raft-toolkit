import streamlit as st
from pathlib import Path

# Set the page to wide mode
st.set_page_config(layout="wide")

st.title('RAFT Data Browser')
st.write('Browse the RAFT data used for model training/testing.')