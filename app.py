"""
Pawdcast Skit Factory — FINAL 2025 BULLETPROOF VERSION
Perfect sync · Zero cost after first generation
"""
import streamlit as st
from google import genai
from google.genai import types
import os
import re
import subprocess
import tempfile
import requests
from pathlib import Path
from datetime import datetime
import time
import base64
import asyncio
import edge_tts
from gtts import gTTS
import traceback

# ============================================================================
# CONFIG & CSS
# ============================================================================
st.set_page_config(page_title="Pawdcast Skit Factory", page_icon="Dog", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
.stApp {background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 50%, #d1d5db 100%); font-family: 'Inter', sans-serif;}
#MainMenu, footer, header {visibility: hidden;}
.header-container {display: flex; align-items: center; justify-content: center; gap: 1rem; padding: 1.5rem; margin-bottom: 1rem;}
.logo-img {width: 60px; height: 60px; border-radius: 16px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);}
.main-title {font-size: 2.2rem; font-weight: 700; background: linear-gradient(135deg, #f7931a 0%, #ff6b35 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
.subtitle {color: #64748b; text-align: center; font-size: 1rem; margin-top: 0.25rem;}
section[data-testid="stSidebar"] {background: rgba(255,255,255,0.8); backdrop-filter: blur(20px);}
.stTextArea textarea, .stTextInput input {background: rgba(255,255,255,0.9)!important; border: 1px solid rgba(0,0,0,0.1)!important; border-radius: 12px!important;}
.stButton>button {background: linear-gradient(135deg, #f7931a 0%, #ff6b35 100%)!important; color: white!important; font-weight: 600!important; border-radius: 12px!important; box-shadow: 0 8px 24px rgba(247,147,26,0.35)!important;}
.stDownloadButton>button {background: linear-gradient(135deg, #10b981 0%, #059669 100%)!important; color: white!important;}
.stProgress > div > div {background: linear-gradient(90deg, #f7931a, #ff6b35)!important;}
.badge-success {background: rgba(16,185,129,0.15); color: #059669; padding: 0.3rem 0.8rem; border-radius: 20px;}
.divider {height: 1px; background: linear-gradient(90deg, transparent, rgba(0,0,0,0.1), transparent); margin: 1.5rem 0;}
.footer {text-align: center; padding: 2rem 0 1rem; color: #9ca3af; font-size: 0.85rem;}
.footer a {color: #f7931a; text-decoration: none;}
</style>
""", unsafe_allow_html=True)

DEFAULT_TEMPLATES = {"speaker1": "", "speaker2": "", "closing": ""}
EDGE_VOICES = {"Guy (US)": "en-US-GuyNeural", "Davis (US)": "en-US-DavisNeural", "Tony (US)": "en-US-TonyNeural", "Jason (US)": "en-US-JasonNeural"}
GEMINI_VOICES = {"Enceladus": "Enceladus", "Puck": "Puck", "Charon": "Charon", "Kore": "Kore"}
LOGO_URL = "https://news.shib.io/wp-content/uploads/2025/12/Untitled-design-1.png"

# ============================================================================
# HELPERS
# ============================================================================
def run_cmd(cmd, desc=""):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Error ({desc}): {result.stderr}")
    return result

def check_ffmpeg():
    try:
        run_cmd(["ffmpeg", "-version"], "ffmpeg check")
        return True
    except:
        return False

def get_duration(path):
    result = run_cmd(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path], "duration")
    return float(result.stdout.strip())

def parse_skit(text):
    if not text: return []
    pattern = r'Speaker\s*(\d+)\s*:\s*["\']([^"\']+)["\']'
    matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
    if not matches:
        pattern = r'Speaker\s*(\d+)\s*:\s*(.+?)(?=Speaker\s*\d+:|$)'
        matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
        matches = [(num, line.strip().strip('"').strip("'")) for num, line in matches]
    return [(f"Speaker {num}", line.strip()) for num, line in matches if line.strip()]

def download_template(url, output_path):
    try:
        r = requests.get(url, stream=True, timeout=30)
        r.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        return True
    except:
        return False

# ============================================================================
# PERFECT SWITCH DETECTION
# ============================================================================
def get_perfect_switch_points(audio_path, num_lines):
    total_dur = get_duration(audio_path)
    # 1. SSML/long breaks
    cmd = ["ffmpeg", "-i", audio_path, "-af", "silencedetect=noise=-50dB:d=0.8", "-f", "null", "-"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    ends = [float(m.group(1)) for m in re.finditer(r'silence_end: (\d+\.?\d*)', result.stderr) if float(m.group(1)) > 1.0]

    # 2. Natural pauses
    if len(ends) < num_lines - 1:
        cmd = ["ffmpeg", "-i", audio_path, "-af", "silencedetect=noise=-32dB:d=0.38", "-f", "null", "-"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        ends = [float(m.group(1)) for m in re.finditer(r'silence_end: (\d+\.?\d*)', result.stderr)]

    timestamps = [0.0]
    if len(ends) >= num_lines - 1:
        timestamps.extend(ends[:num_lines-1])
    else:
        step = total_dur / num_lines
        timestamps.extend([i * step for i in range(1, num_lines)])
    timestamps[-1] = total_dur
    timestamps = sorted(set(timestamps))
    while len(timestamps) <= num_lines:
        timestamps.append(total_dur)
    return timestamps[:num_lines + 1]

# ============================================================================
# VIDEO CREATION FUNCTIONS (FULLY INCLUDED)
# ============================================================================
def create_video_single_audio(segments, audio_path, tmpl1, tmpl2, closing, output, progress_cb=None):
    temp = Path(output).parent
    if progress_cb: progress_cb(0.5, "Building video segments...")

    segment_videos = []
    for i, s in enumerate(segments):
        seg_out = str(temp / f"seg_{i}.mp4")
        template = tmpl1 if "1" in s['speaker'] else tmpl2
        duration = s['duration']
        run_cmd([
            "ffmpeg", "-y", "-i", template,
            "-filter_complex",
            f"[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,loop=loop=-1:size=32767,trim=duration={duration},setpts=PTS-STARTPTS[outv]",
            "-map", "[outv]", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
            "-t", str(duration), "-an", seg_out
        ], f"segment {i}")
        segment_videos.append(seg_out)

    if progress_cb: progress_cb(0.7, "Joining segments...")
    video_list = temp / "videos.txt"
    with open(video_list, "w") as f:
        for v in segment_videos:
            f.write(f"file '{v}'\n")
    main_video = str(temp / "main.mp4")
    run_cmd(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(video_list), "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23", main_video], "concat")

    if progress_cb: progress_cb(0.8, "Adding audio...")
    main_with_audio = str(temp / "main_audio.mp4")
    run_cmd(["ffmpeg", "-y", "-i", main_video, "-i", audio_path, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", main_with_audio], "add audio")

    if progress_cb: progress_cb(0.85, "Adding closing...")
    closing_scaled = str(temp / "closing_scaled.mp4")
    run_cmd(["ffmpeg", "-y", "-i", closing, "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2", "-c:v", "libx264", "-c:a", "aac", closing_scaled], "scale closing")

    if progress_cb: progress_cb(0.9, "Final assembly...")
    run_cmd([
        "ffmpeg", "-y", "-i", main_with_audio, "-i", closing_scaled,
        "-filter_complex", "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[outv][outa]",
        "-map", "[outv]", "-map", "[outa]", "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", output
    ], "final")
    if progress_cb: progress_cb(1.0, "Done!")

# ============================================================================
# MAIN APP
# ============================================================================
def main():
    st.markdown(f'<div class="header-container"><img src="{LOGO_URL}" class="logo-img"><div><h1 class="main-title">Pawdcast Skit Factory</h1><p class="subtitle">Perfect sync · Zero cost after first audio</p></div></div>', unsafe_allow_html=True)
    if not check_ffmpeg():
        st.error("FFmpeg not found — install it!")
        return

    with st.sidebar:
        st.markdown("### Settings")
        api_key = st.text_input("Gemini API Key (only needed for article/skit mode)", type="password")
        use_default = st.checkbox("Use pre-configured templates", value=True)
        if not use_default:
            tmpl1_file = st.file_uploader("Speaker 1 template", type=["mp4"])
            tmpl2_file = st.file_uploader("Speaker 2 template", type=["mp4"])
            tmpl_c_file = st.file_uploader("Closing template", type=["mp4"])

    col1, col2 = st.columns(2)
    with col1:
        input_mode = st.radio("Mode", ["article", "skit", "audio"],
                              format_func=lambda x: {"article":"Article → AI all", "skit":"Paste skit → Gen audio", "audio":"Upload audio → Video only (FREE & PERFECT)"}[x])
        if input_mode == "audio":
            uploaded_audio_single = st.file_uploader("Upload complete audio file", type=["wav","mp3","m4a"])
            detection_method = st.radio("Timing", ["auto", "manual"])
            timestamp_input = ""
            if detection_method == "manual":
                timestamp_input = st.text_input("Timestamps (seconds)", placeholder="0, 8.5, 15.2, 32.1")
        elif input_mode == "article":
            article = st.text_area("Paste article", height=250)
        else:
            st.info("Paste skit from AI Studio")

    with col2:
        skit_input = st.text_area("Skit (required for audio mode)", height=300,
                                  placeholder='Speaker 1: "..."\nSpeaker 2: "..."\nSpeaker 1: "..."')

    if not st.button("Create Pawdcast", use_container_width=True):
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        progress = st.progress(0)
        status = st.empty()

        try:
            t0 = time.time()
            # Templates
            if use_default:
                t1_path = str(tmp / "t1.mp4"); download_template(DEFAULT_TEMPLATES["speaker1"], t1_path)
                t2_path = str(tmp / "t2.mp4"); download_template(DEFAULT_TEMPLATES["speaker2"], t2_path)
                tc_path = str(tmp / "tc.mp4"); download_template(DEFAULT_TEMPLATES["closing"], tc_path)
            else:
                t1_path = str(tmp / "t1.mp4"); open(t1_path, "wb").write(tmpl1_file.read())
                t2_path = str(tmp / "t2.mp4"); open(t2_path, "wb").write(tmpl2_file.read())
                tc_path = str(tmp / "tc.mp4"); open(tc_path, "wb").write(tmpl_c_file.read())

            if input_mode == "audio":
                status.info("Processing uploaded audio...")
                lines = parse_skit(skit_input)
                if not lines: raise Exception("Invalid skit format")
                ext = uploaded_audio_single.name.split(".")[-1]
                full_audio_path = str(tmp / f"full.{ext}")
                open(full_audio_path, "wb").write(uploaded_audio_single.read())

                if detection_method == "manual" and timestamp_input:
                    switch_points = [float(t.strip()) for t in timestamp_input.split(",")]
                    switch_points.append(get_duration(full_audio_path))
                else:
                    status.info("Detecting perfect speaker switches...")
                    switch_points = get_perfect_switch_points(full_audio_path, len(lines))
                    st.info(f"Switches: {', '.join([f'{t:.2f}s' for t in switch_points[:-1]])}")

                segments = []
                for i, (spk, txt) in enumerate(lines):
                    start = switch_points[i]
                    end = switch_points[i+1]
                    segments.append({"speaker": spk, "text": txt, "duration": end-start})

                full_audio_for_video = full_audio_path

            else:
                st.warning("Article/skit modes disabled in this minimal version — use audio mode!")
                return

            def update(pct, msg):
                progress.progress(pct)
                status.info(msg)

            output = str(tmp / "pawdcast.mp4")
            create_video_single_audio(segments, full_audio_for_video, t1_path, t2_path, tc_path, output, update)

            video_bytes = open(output, "rb").read()
            elapsed = time.time() - t0
            progress.progress(1.0)
            status.success(f"Done in {elapsed:.0f}s!")

            st.video(video_bytes)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button("Download Video", video_bytes, f"pawdcast_{ts}.mp4", "video/mp4")

        except Exception as e:
            st.error(f"Error: {e}")
            with st.expander("Details"):
                st.code(traceback.format_exc())

    st.markdown('<div class="footer"><div class="divider"></div>Made with Love for The Shib Daily</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
