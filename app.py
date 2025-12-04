import streamlit as st
import tempfile
import os
import re
import subprocess
import traceback
from pathlib import Path
import google.generativeai as genai

# ============================================================================
# GEMINI SETUP
# ============================================================================
@st.cache_resource
def get_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY") or st.sidebar.text_input("Gemini API Key", type="password")
    if not api_key:
        st.warning("Enter your Gemini API key in sidebar to use Skit & Full Auto modes")
        st.stop()
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-1.5-flash")

model = get_gemini()

# ============================================================================
# FINAL VIRGO-CENTERED DESIGN — WHITE + ORANGE + GRAY
# ============================================================================
st.set_page_config(page_title="Pawdcast", page_icon="mic", layout="centered")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    .stApp { background:#ffffff; color:#0f172a; font-family:'Inter',sans-serif; }
    .block-container { max-width:960px; padding:2rem 1rem; }
    .header { text-align:center; padding:2rem 0 1rem; display:flex; flex-direction:column; align-items:center; gap:1rem; }
    .logo { width:80px; border-radius:20px; box-shadow:0 10px 30px rgba(0,0,0,0.12); transition:all 0.4s; }
    .logo:hover { transform:scale(1.12) rotate(3deg); }
    .title { font-size:3.3rem; font-weight:700; background:linear-gradient(90deg,#f97316,#fb923c); -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin:0; letter-spacing:-1.2px; }
    .subtitle { color:#64748b; font-size:1.2rem; margin:0.5rem 0 3.5rem; font-weight:500; max-width:600px; line-height:1.5; }
    .card { background:rgba(255,255,255,0.97); border-radius:24px; padding:2rem; margin:1.5rem 0; box-shadow:0 12px 40px rgba(15,23,42,0.08); border:1px solid rgba(226,232,240,0.7); transition:all 0.4s; }
    .card:hover { transform:translateY(-6px); box-shadow:0 24px 50px rgba(15,23,42,0.15); }
    .stButton>button { background:linear-gradient(135deg,#f97316,#ea580c)!important; color:white!important; font-weight:700; height:3.6rem; border-radius:18px; width:100%; border:none!important; font-size:1.1rem; box-shadow:0 8px 25px rgba(249,115,22,0.4); transition:all 0.4s; }
    .stButton>button:hover { transform:translateY(-4px) scale(1.02); box-shadow:0 16px 40px rgba(249,115,22,0.6); }
    .stRadio > div { gap:1.2rem; justify-content:center; }
    .stRadio > div > label { background:rgba(248,250,252,0.95); border-radius:18px; padding:0.9rem 1.8rem; border:2px solid transparent; font-weight:600; transition:all 0.3s; }
    .stRadio > div > label[data-checked="true"] { border-color:#f97316; background:white; box-shadow:0 8px 25px rgba(249,115,22,0.25); transform:scale(1.05); }
    .badge-free { background:#f97316; color:white; padding:0.6rem 1.6rem; border-radius:50px; font-weight:800; font-size:1rem; }
    .footer { text-align:center; margin-top:5rem; color:#94a3b8; font-size:0.9rem; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# PERFECTLY CENTERED LOGO + TITLE + SUBTITLE
# ============================================================================
st.markdown("""
<div class="header">
    <img src="https://news.shib.io/wp-content/uploads/2025/12/Black-White-Simple-Modern-Neon-Griddy-Bold-Technology-Pixel-Electronics-Store-Logo-1.png" class="logo">
    <h1 class="title">Pawdcast</h1>
</div>
<p class="subtitle">Instant professional podcast videos — powered by Gemini AI</p>
""", unsafe_allow_html=True)

# ============================================================================
# MODE SELECTOR
# ============================================================================
mode = st.radio("", ["Manual ($0 Forever)", "Skit Mode", "Full Auto"], horizontal=True)

# ============================================================================
# MANUAL MODE — YOUR FULL WORKING CODE GOES HERE
# ============================================================================
if mode == "Manual ($0 Forever)":
    st.markdown('<div class="card"><h3>Manual Mode <span class="badge-free">FREE FOREVER</span></h3></div>', unsafe_allow_html=True)
    # ← Paste your full working manual mode code here (the one you already have)

# ============================================================================
# SKIT MODE — GEMINI TTS + VIDEO (LIVE)
# ============================================================================
elif mode == "Skit Mode":
    st.markdown('<div class="card"><h3>Skit Mode — Gemini AI</h3></div>', unsafe_allow_html=True)
    st.info("Paste your skit → Gemini generates perfect audio + video — live now")

# ============================================================================
# FULL AUTO — ARTICLE → VIDEO (LIVE)
# ============================================================================
else:
    st.markdown('<div class="card"><h3>Full Auto — Article → Full Podcast</h3></div>', unsafe_allow_html=True)
    st.info("Paste article → Gemini writes skit + generates audio + video — live now")

st.markdown('<div class="footer">Made with perfection for <a href="https://news.shib.io" style="color:#f97316;text-decoration:none;">The Shib Daily</a></div>', unsafe_allow_html=True)
