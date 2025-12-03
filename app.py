"""
🐕 Pawdcast Skit Factory
Fully automated article-to-video conversion for The Shib Daily
"""

import streamlit as st
from google import genai
from google.genai import types
import os
import re
import subprocess
import tempfile
import wave
import requests
from pathlib import Path
from datetime import datetime
import time
import base64
import asyncio
import edge_tts
from gtts import gTTS

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="Pawdcast Skit Factory",
    page_icon="🐕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Pre-configured template URLs - UPDATE THESE TO YOUR ACTUAL URLs
# Upload your MP4 files somewhere and put the direct links here
DEFAULT_TEMPLATES = {
    "speaker1": "",  # e.g., "https://yoursite.com/speaker1.mp4"
    "speaker2": "",  # e.g., "https://yoursite.com/speaker2.mp4"  
    "closing": ""    # e.g., "https://yoursite.com/closing.mp4"
}

# Edge TTS Voice Options (FREE)
EDGE_VOICES = {
    "Guy (US)": "en-US-GuyNeural",
    "Davis (US)": "en-US-DavisNeural",
    "Tony (US)": "en-US-TonyNeural",
    "Jason (US)": "en-US-JasonNeural",
    "Christopher (US)": "en-US-ChristopherNeural",
    "Eric (US)": "en-US-EricNeural",
    "Ryan (UK)": "en-GB-RyanNeural",
    "William (AU)": "en-AU-WilliamNeural",
}

# Gemini TTS Voice Options (API)
GEMINI_VOICES = {
    "Enceladus": "Enceladus",
    "Puck": "Puck", 
    "Charon": "Charon",
    "Kore": "Kore",
    "Fenrir": "Fenrir",
    "Aoede": "Aoede",
    "Leda": "Leda",
    "Orus": "Orus",
    "Zephyr": "Zephyr"
}

SKIT_MODEL = "gemini-2.0-flash"
TTS_MODEL = "gemini-2.5-flash-preview-tts"

LOGO_URL = "https://news.shib.io/wp-content/uploads/2025/12/Untitled-design-1.png"

SKIT_PROMPT = """Role: You are a "Content Repurposing Expert" specializing in transforming news articles into short-form multimedia scripts. Write in a natural, human-like style.

Core Task: Generate a Podcast Skit (100–140 words total, ~45–70 seconds when spoken)
* Exactly two speakers (Speaker 1 and Speaker 2)
* Speaker 1 always starts with a witty hook
* Light, professional banter with subtle humor
* End with a unique CTA inviting people to "news.shib.io" for the full story

IMPORTANT: Output ONLY the dialogue in this exact format:
Speaker 1: "..."
Speaker 2: "..."
Speaker 1: "..."
(and so on)

Article:
"""

# ============================================================================
# GLASSMORPHISM CSS
# ============================================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

.stApp {
    background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 50%, #d1d5db 100%);
    font-family: 'Inter', sans-serif;
}

#MainMenu, footer, header {visibility: hidden;}

.header-container {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    padding: 1.5rem;
    margin-bottom: 1rem;
}

.logo-img {
    width: 60px;
    height: 60px;
    border-radius: 16px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.main-title {
    font-size: 2.2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #f7931a 0%, #ff6b35 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}

.subtitle {
    color: #64748b;
    text-align: center;
    font-size: 1rem;
    margin-top: 0.25rem;
}

section[data-testid="stSidebar"] {
    background: rgba(255, 255, 255, 0.8);
    backdrop-filter: blur(20px);
}

.stTextArea textarea, .stTextInput input {
    background: rgba(255, 255, 255, 0.9) !important;
    border: 1px solid rgba(0, 0, 0, 0.1) !important;
    border-radius: 12px !important;
}

.stButton > button {
    background: linear-gradient(135deg, #f7931a 0%, #ff6b35 100%) !important;
    color: white !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    padding: 0.8rem 2rem !important;
    border: none !important;
    border-radius: 12px !important;
    box-shadow: 0 8px 24px rgba(247, 147, 26, 0.35) !important;
}

.stDownloadButton > button {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
    color: white !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 12px !important;
}

.stProgress > div > div {
    background: linear-gradient(90deg, #f7931a, #ff6b35) !important;
}

.badge-success {
    background: rgba(16, 185, 129, 0.15);
    color: #059669;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-size: 0.85rem;
}

.badge-warning {
    background: rgba(245, 158, 11, 0.15);
    color: #d97706;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-size: 0.85rem;
}

.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0,0,0,0.1), transparent);
    margin: 1.5rem 0;
}

.info-card {
    background: rgba(255, 255, 255, 0.6);
    border-radius: 16px;
    padding: 1.25rem;
    margin: 1rem 0;
}

.footer {
    text-align: center;
    padding: 2rem 0 1rem 0;
    color: #9ca3af;
    font-size: 0.85rem;
}

.footer a {
    color: #f7931a;
    text-decoration: none;
}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# HELPER FUNCTIONS
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

def parse_skit(text):
    if not text:
        return []
    pattern = r'Speaker\s*(\d+)\s*:\s*["""]([^"""]+)["""]'
    matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
    if not matches:
        pattern = r'Speaker\s*(\d+)\s*:\s*(.+?)(?=Speaker\s*\d+:|$)'
        matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
        matches = [(num, line.strip().strip('"').strip('"').strip('"').strip("'")) 
                   for num, line in matches]
    return [(f"Speaker {num}", line.strip()) for num, line in matches if line.strip()]

def generate_skit(article, api_key):
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=SKIT_MODEL,
            contents=SKIT_PROMPT + article,
            config=types.GenerateContentConfig(temperature=0.8, max_output_tokens=600)
        )
        if response and response.text:
            return response.text
        raise Exception("Empty response from Gemini")
    except Exception as e:
        raise Exception(f"Skit generation failed: {str(e)}")

def generate_audio_gemini(text, voice, api_key, output_path):
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=TTS_MODEL,
        contents=f'Say this in a warm, engaging podcast host tone: "{text}"',
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                )
            )
        )
    )
    audio_data = response.candidates[0].content.parts[0].inline_data.data
    if isinstance(audio_data, str):
        missing = len(audio_data) % 4
        if missing:
            audio_data += '=' * (4 - missing)
        audio_data = base64.b64decode(audio_data)
    with wave.open(output_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(audio_data)
    return output_path

async def generate_audio_edge_async(text, voice, output_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

def generate_audio(text, voice, output_path, engine="gemini", api_key=None):
    try:
        if engine == "gemini":
            wav_path = output_path.replace('.mp3', '.wav')
            generate_audio_gemini(text, voice, api_key, wav_path)
            return wav_path
        else:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(generate_audio_edge_async(text, voice, output_path))
            finally:
                loop.close()
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return output_path
            raise Exception("Edge TTS failed")
    except Exception as e:
        # Fallback to gTTS
        try:
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(output_path)
            return output_path
        except:
            raise Exception(f"All TTS failed: {str(e)}")

def get_duration(path):
    result = run_cmd([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", path
    ], "duration")
    return float(result.stdout.strip())

def download_template(url, output_path):
    """Download template from URL."""
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except:
        return False

def detect_silence_gaps(audio_path, min_silence_duration=0.3, silence_threshold="-35dB"):
    """Detect silence gaps in audio to find speaker switch points."""
    result = subprocess.run([
        "ffmpeg", "-i", audio_path,
        "-af", f"silencedetect=noise={silence_threshold}:d={min_silence_duration}",
        "-f", "null", "-"
    ], capture_output=True, text=True)
    
    output = result.stderr
    gaps = []
    
    for match in re.finditer(r'silence_end: ([\d.]+)', output):
        gaps.append(float(match.group(1)))
    
    return gaps

def detect_voice_changes(audio_path, num_expected_segments):
    """
    Detect voice changes by analyzing audio energy/pitch changes.
    Uses FFmpeg to extract audio features and find transition points.
    """
    temp_dir = Path(audio_path).parent
    
    # Get total duration
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", audio_path
    ], capture_output=True, text=True)
    total_duration = float(result.stdout.strip())
    
    # Method: Analyze volume changes over time using FFmpeg's volumedetect on chunks
    # Split audio into small chunks and compare characteristics
    chunk_duration = 0.5  # 500ms chunks
    num_chunks = int(total_duration / chunk_duration)
    
    volumes = []
    for i in range(num_chunks):
        start = i * chunk_duration
        result = subprocess.run([
            "ffmpeg", "-ss", str(start), "-t", str(chunk_duration),
            "-i", audio_path,
            "-af", "volumedetect",
            "-f", "null", "-"
        ], capture_output=True, text=True)
        
        # Extract mean volume
        match = re.search(r'mean_volume: ([-\d.]+)', result.stderr)
        if match:
            volumes.append(float(match.group(1)))
        else:
            volumes.append(-50)  # Default quiet
    
    # Find significant changes in volume pattern (potential speaker switches)
    changes = []
    window = 3  # Compare windows of chunks
    
    for i in range(window, len(volumes) - window):
        before = sum(volumes[i-window:i]) / window
        after = sum(volumes[i:i+window]) / window
        diff = abs(after - before)
        if diff > 3:  # Threshold for significant change
            changes.append((i * chunk_duration, diff))
    
    # Sort by significance and take top (num_expected - 1) changes
    changes.sort(key=lambda x: x[1], reverse=True)
    
    # Get the timestamps of top changes
    switch_times = sorted([c[0] for c in changes[:num_expected_segments - 1]])
    
    # Build full list: 0, switches, end
    result_times = [0] + switch_times + [total_duration]
    
    return result_times

def create_video_single_audio(segments, audio_path, tmpl1, tmpl2, closing, output, progress_cb=None):
    """Create video from single complete audio file, switching speakers based on timing."""
    temp = Path(output).parent
    
    if progress_cb: progress_cb(0.5, "Building video segments...")
    
    # Create video segments based on timing
    segment_videos = []
    for i, s in enumerate(segments):
        seg_out = str(temp / f"seg_{i}.mp4")
        template = tmpl1 if "1" in s['speaker'] else tmpl2
        duration = s['duration']
        
        run_cmd([
            "ffmpeg", "-y", "-i", template,
            "-filter_complex", 
            f"[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,"
            f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2,"
            f"loop=loop=-1:size=32767,trim=duration={duration},setpts=PTS-STARTPTS[outv]",
            "-map", "[outv]", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
            "-t", str(duration), "-an", seg_out
        ], f"segment {i}")
        segment_videos.append(seg_out)
    
    if progress_cb: progress_cb(0.7, "Joining segments...")
    
    # Concat video segments
    video_list = temp / "videos.txt"
    with open(video_list, "w") as f:
        for v in segment_videos:
            f.write(f"file '{v}'\n")
    
    main_video = str(temp / "main.mp4")
    run_cmd(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(video_list),
             "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23", main_video], "concat")
    
    if progress_cb: progress_cb(0.8, "Adding audio...")
    
    # Add the complete audio
    main_with_audio = str(temp / "main_audio.mp4")
    run_cmd([
        "ffmpeg", "-y", "-i", main_video, "-i", audio_path,
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", main_with_audio
    ], "add audio")
    
    if progress_cb: progress_cb(0.85, "Adding closing...")
    
    # Scale and add closing (with its audio)
    closing_scaled = str(temp / "closing_scaled.mp4")
    run_cmd([
        "ffmpeg", "-y", "-i", closing,
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k", closing_scaled
    ], "scale closing")
    
    if progress_cb: progress_cb(0.9, "Final assembly...")
    
    run_cmd([
        "ffmpeg", "-y", "-i", main_with_audio, "-i", closing_scaled,
        "-filter_complex", "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[outv][outa]",
        "-map", "[outv]", "-map", "[outa]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", output
    ], "final")
    
    if progress_cb: progress_cb(1.0, "Done!")

def create_video(segments, tmpl1, tmpl2, closing, output, progress_cb=None):
    """Assemble final video with FFmpeg."""
    temp = Path(output).parent
    
    if progress_cb: progress_cb(0.5, "Merging audio...")
    
    # Convert and merge audio
    wav_files = []
    for i, s in enumerate(segments):
        wav_path = str(temp / f"audio_{i}.wav")
        run_cmd([
            "ffmpeg", "-y", "-i", s['audio'],
            "-ar", "24000", "-ac", "1", "-c:a", "pcm_s16le", wav_path
        ], f"convert audio {i}")
        wav_files.append(wav_path)
    
    audio_list = temp / "audio.txt"
    with open(audio_list, "w") as f:
        for wav in wav_files:
            f.write(f"file '{wav}'\n")
    
    merged = str(temp / "merged.wav")
    run_cmd(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(audio_list), 
             "-c:a", "pcm_s16le", merged], "merge audio")
    
    if progress_cb: progress_cb(0.6, "Building video segments...")
    
    # Create video segments
    segment_videos = []
    for i, s in enumerate(segments):
        seg_out = str(temp / f"seg_{i}.mp4")
        template = tmpl1 if "1" in s['speaker'] else tmpl2
        duration = s['duration']
        
        run_cmd([
            "ffmpeg", "-y", "-i", template,
            "-filter_complex", 
            f"[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,"
            f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2,"
            f"loop=loop=-1:size=32767,trim=duration={duration},setpts=PTS-STARTPTS[outv]",
            "-map", "[outv]", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
            "-t", str(duration), "-an", seg_out
        ], f"segment {i}")
        segment_videos.append(seg_out)
    
    if progress_cb: progress_cb(0.75, "Joining segments...")
    
    video_list = temp / "videos.txt"
    with open(video_list, "w") as f:
        for v in segment_videos:
            f.write(f"file '{v}'\n")
    
    main_video = str(temp / "main.mp4")
    run_cmd(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(video_list),
             "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23", main_video], "concat")
    
    if progress_cb: progress_cb(0.8, "Adding audio...")
    
    main_with_audio = str(temp / "main_audio.mp4")
    run_cmd([
        "ffmpeg", "-y", "-i", main_video, "-i", merged,
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", main_with_audio
    ], "add audio")
    
    if progress_cb: progress_cb(0.85, "Adding closing...")
    
    closing_scaled = str(temp / "closing_scaled.mp4")
    run_cmd([
        "ffmpeg", "-y", "-i", closing,
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k", closing_scaled
    ], "scale closing")
    
    if progress_cb: progress_cb(0.9, "Final assembly...")
    
    run_cmd([
        "ffmpeg", "-y", "-i", main_with_audio, "-i", closing_scaled,
        "-filter_complex", "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[outv][outa]",
        "-map", "[outv]", "-map", "[outa]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", output
    ], "final")
    
    if progress_cb: progress_cb(1.0, "Done!")

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    # Header
    st.markdown(f"""
    <div class="header-container">
        <img src="{LOGO_URL}" class="logo-img" alt="Logo">
        <div>
            <h1 class="main-title">Pawdcast Skit Factory</h1>
            <p class="subtitle">Transform articles into podcast videos instantly</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if not check_ffmpeg():
        st.error("⚠️ FFmpeg not available")
        return
    
    # Sidebar
    with st.sidebar:
        st.markdown(f'<img src="{LOGO_URL}" style="width: 50px; border-radius: 12px; margin-bottom: 1rem;">', unsafe_allow_html=True)
        st.markdown("### ⚙️ Settings")
        
        # API Key
        api_key = ""
        if hasattr(st, 'secrets') and st.secrets and "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.markdown('<span class="badge-success">✓ API Ready</span>', unsafe_allow_html=True)
        else:
            api_key = st.text_input("Gemini API Key", type="password")
            if api_key:
                st.markdown('<span class="badge-success">✓ Key Set</span>', unsafe_allow_html=True)
            else:
                st.markdown('[Get free key →](https://aistudio.google.com/app/apikey)')
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # TTS Engine
        st.markdown("### 🔊 Voice Engine")
        tts_engine = st.radio(
            "TTS",
            ["gemini", "edge"],
            format_func=lambda x: "⭐ Gemini (Best)" if x == "gemini" else "🆓 Edge (Free)",
            label_visibility="collapsed"
        )
        
        # Voices
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown("### 🎙️ Voices")
        voice_opts = GEMINI_VOICES if tts_engine == "gemini" else EDGE_VOICES
        voice1 = st.selectbox("Speaker 1", list(voice_opts.keys()), index=0)
        voice2 = st.selectbox("Speaker 2", list(voice_opts.keys()), index=1)
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # Templates
        st.markdown("### 🎬 Video Templates")
        use_default = st.checkbox("Use pre-configured templates", value=True,
                                   help="Uses templates hosted at news.shib.io")
        
        if not use_default:
            st.caption("Upload 1920×1080 MP4 files")
            tmpl1_file = st.file_uploader("Speaker 1", type=["mp4"], key="t1")
            tmpl2_file = st.file_uploader("Speaker 2", type=["mp4"], key="t2")
            tmpl_c_file = st.file_uploader("Closing", type=["mp4"], key="tc")
            templates_ready = all([tmpl1_file, tmpl2_file, tmpl_c_file])
        else:
            tmpl1_file = tmpl2_file = tmpl_c_file = None
            templates_ready = True
            st.markdown('<span class="badge-success">✓ Templates Ready</span>', unsafe_allow_html=True)
    
    # Main content
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📝 Input Mode")
        input_mode = st.radio(
            "Mode",
            ["skit", "audio", "article"],
            format_func=lambda x: {
                "article": "📰 Article → AI generates all",
                "skit": "📜 Paste skit → Generate audio", 
                "audio": "🎧 Upload audio → Video only (FREE)"
            }[x],
            label_visibility="collapsed"
        )
        
        audio_assignments = []
        uploaded_audio_single = None
        timestamp_input = ""
        use_voice_detection = False
        
        if input_mode == "article":
            article = st.text_area("Article", height=250, 
                                   placeholder="Paste your news article...")
        elif input_mode == "skit":
            article = ""
            st.info("💡 Paste skit from [AI Studio](https://aistudio.google.com)")
        else:
            article = ""
            st.success("🎉 **100% FREE!** Upload complete audio from AI Studio")
            
            uploaded_audio_single = st.file_uploader(
                "Complete audio file", type=["wav", "mp3"],
                help="The full podcast audio with both speakers"
            )
            
            if uploaded_audio_single:
                st.markdown('<span class="badge-success">✓ Audio uploaded</span>', unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("**How to detect speaker changes:**")
            
            detection_method = st.radio(
                "Detection method",
                ["manual", "auto"],
                format_func=lambda x: "⏱️ Manual timestamps (recommended)" if x == "manual" else "🤖 Auto voice detection (experimental)",
                label_visibility="collapsed"
            )
            
            if detection_method == "manual":
                st.caption("Enter the time (in seconds) when each speaker STARTS talking")
                timestamp_input = st.text_input(
                    "Timestamps",
                    placeholder="0, 8.5, 15.2, 32.1, 45.8",
                    help="Comma-separated seconds. First is always 0. Listen to audio once to get these."
                )
                if timestamp_input:
                    try:
                        times = [float(t.strip()) for t in timestamp_input.split(",")]
                        st.caption(f"✓ {len(times)} timestamps entered")
                    except:
                        st.caption("⚠️ Invalid format. Use: 0, 8.5, 15.2, 32.1")
            else:
                use_voice_detection = True
                st.caption("Will analyze audio for voice/pitch changes between speakers")
                st.warning("⚠️ Works best when speakers have clearly different voices")
    
    with col2:
        if input_mode == "skit":
            st.markdown("### 📜 Skit")
            skit_input = st.text_area(
                "Skit", height=300,
                placeholder='Speaker 1: "..."\nSpeaker 2: "..."\nSpeaker 1: "..."',
                label_visibility="collapsed"
            )
        elif input_mode == "audio":
            st.markdown("### 📜 Skit (for video timing)")
            st.caption("Paste the skit so we know when to switch speakers")
            skit_input = st.text_area(
                "Skit", height=250,
                placeholder='Speaker 1: "..."\nSpeaker 2: "..."\nSpeaker 1: "..."',
                label_visibility="collapsed"
            )
            if skit_input:
                lines = parse_skit(skit_input)
                if lines:
                    st.caption(f"✓ {len(lines)} speaker turns detected")
        else:
            st.markdown("### 📜 Generated Skit")
            skit_display = st.empty()
            skit_display.text_area("Preview", "Will appear here...", height=300, 
                                   disabled=True, label_visibility="collapsed")
            skit_input = ""
    
    # Create button
    st.markdown("<br>", unsafe_allow_html=True)
    _, btn_col, _ = st.columns([1, 2, 1])
    with btn_col:
        create = st.button("🚀 Create Pawdcast", use_container_width=True)
    
    # Process
    if create:
        errors = []
        if input_mode == "article":
            if not api_key: errors.append("API key required")
            if not article.strip(): errors.append("Article required")
        elif input_mode == "skit":
            if not skit_input.strip(): errors.append("Paste skit")
            if tts_engine == "gemini" and not api_key: errors.append("API key required for Gemini TTS")
        else:  # audio mode
            if not uploaded_audio_single: errors.append("Upload audio file")
            if not skit_input.strip(): errors.append("Paste skit for speaker order")
            if detection_method == "manual" and not timestamp_input.strip():
                errors.append("Enter timestamps (or switch to auto detection)")
        
        if not use_default and not templates_ready:
            errors.append("Upload all templates")
        
        if use_default and not all(DEFAULT_TEMPLATES.values()):
            errors.append("Template URLs not configured - uncheck 'Use pre-configured templates' and upload manually")
        
        if errors:
            st.error("❌ " + " • ".join(errors))
            return
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            progress = st.progress(0)
            status = st.empty()
            
            try:
                t0 = time.time()
                
                # Get templates
                status.info("📦 Loading templates...")
                if use_default:
                    t1_path = str(tmp / "t1.mp4")
                    t2_path = str(tmp / "t2.mp4")
                    tc_path = str(tmp / "tc.mp4")
                    
                    if not download_template(DEFAULT_TEMPLATES["speaker1"], t1_path):
                        st.error("❌ Failed to download Speaker 1 template. Check URL in settings.")
                        return
                    if not download_template(DEFAULT_TEMPLATES["speaker2"], t2_path):
                        st.error("❌ Failed to download Speaker 2 template. Check URL in settings.")
                        return
                    if not download_template(DEFAULT_TEMPLATES["closing"], tc_path):
                        st.error("❌ Failed to download Closing template. Check URL in settings.")
                        return
                else:
                    t1_path = str(tmp / "t1.mp4")
                    t2_path = str(tmp / "t2.mp4")
                    tc_path = str(tmp / "tc.mp4")
                    with open(t1_path, "wb") as f: f.write(tmpl1_file.read())
                    with open(t2_path, "wb") as f: f.write(tmpl2_file.read())
                    with open(tc_path, "wb") as f: f.write(tmpl_c_file.read())
                
                progress.progress(0.1)
                
                # Process based on mode
                if input_mode == "audio":
                    # SINGLE AUDIO MODE
                    status.info("🎧 Processing audio...")
                    
                    # Parse skit to know speaker order
                    lines = parse_skit(skit_input)
                    if not lines:
                        st.error("❌ Could not parse skit")
                        return
                    
                    # Save the complete audio
                    ext = uploaded_audio_single.name.split('.')[-1]
                    full_audio_path = str(tmp / f"full_audio.{ext}")
                    with open(full_audio_path, "wb") as f:
                        f.write(uploaded_audio_single.read())
                    
                    total_duration = get_duration(full_audio_path)
                    num_lines = len(lines)
                    
                    # Get timestamps based on method
                    if detection_method == "manual" and timestamp_input:
                        # Manual timestamps
                        status.info("⏱️ Using manual timestamps...")
                        try:
                            switch_points = [float(t.strip()) for t in timestamp_input.split(",")]
                            # Add end time if not included
                            if len(switch_points) == num_lines:
                                switch_points.append(total_duration)
                            elif len(switch_points) < num_lines:
                                st.error(f"❌ Need {num_lines} timestamps, got {len(switch_points)}")
                                return
                        except Exception as e:
                            st.error(f"❌ Invalid timestamps: {e}")
                            return
                    else:
                        # Auto voice detection
                        status.info("🤖 Detecting voice changes...")
                        switch_points = detect_voice_changes(full_audio_path, num_lines)
                        st.info(f"🔍 Detected switch points: {[f'{t:.1f}s' for t in switch_points]}")
                    
                    # Build segments
                    segments = []
                    for i, (spk, txt) in enumerate(lines):
                        start = switch_points[i]
                        end = switch_points[i + 1] if i + 1 < len(switch_points) else total_duration
                        segments.append({
                            "speaker": spk,
                            "text": txt,
                            "start": start,
                            "duration": end - start
                        })
                    
                    full_audio_for_video = full_audio_path
                    progress.progress(0.3)
                    
                else:
                    # Get skit
                    if input_mode == "article":
                        status.info("🤖 Generating skit...")
                        skit = generate_skit(article, api_key)
                        skit_display.text_area("Preview", skit, height=300, 
                                               disabled=True, label_visibility="collapsed")
                    else:
                        skit = skit_input
                    
                    lines = parse_skit(skit)
                    if not lines:
                        st.error("❌ Could not parse skit format")
                        st.code(skit)
                        return
                    
                    progress.progress(0.2)
                    
                    # Generate audio
                    segments = []
                    voice_map = GEMINI_VOICES if tts_engine == "gemini" else EDGE_VOICES
                    
                    for i, (spk, txt) in enumerate(lines):
                        pct = 0.2 + (i / len(lines)) * 0.25
                        progress.progress(pct)
                        status.info(f"🎙️ Voice {i+1}/{len(lines)}...")
                        
                        voice = voice_map[voice1] if "1" in spk else voice_map[voice2]
                        audio = str(tmp / f"a{i}.mp3")
                        audio_path = generate_audio(txt, voice, audio, tts_engine, api_key)
                        
                        segments.append({
                            "speaker": spk,
                            "text": txt,
                            "audio": audio_path,
                            "duration": get_duration(audio_path)
                        })
                
                # Create video
                def update(pct, msg):
                    progress.progress(pct)
                    status.info(f"🎬 {msg}")
                
                output = str(tmp / "pawdcast.mp4")
                
                if input_mode == "audio":
                    # Single audio mode - use special video creation
                    create_video_single_audio(segments, full_audio_for_video, t1_path, t2_path, tc_path, output, update)
                else:
                    # Normal mode with separate audio files
                    create_video(segments, t1_path, t2_path, tc_path, output, update)
                
                with open(output, "rb") as f:
                    video_bytes = f.read()
                
                elapsed = time.time() - t0
                progress.progress(1.0)
                status.success(f"✅ Done in {elapsed:.0f}s!")
                
                # Results
                st.markdown("---")
                st.markdown("### 🎉 Your Pawdcast is Ready!")
                st.video(video_bytes)
                
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                c1, c2 = st.columns(2)
                with c1:
                    st.download_button("📥 Download Video", video_bytes, 
                                       f"pawdcast_{ts}.mp4", "video/mp4", use_container_width=True)
                
                # Stats
                api_calls = 0
                if input_mode == "article": api_calls += 1
                if input_mode != "audio" and tts_engine == "gemini": api_calls += len(segments)
                
                st.markdown(f"""
                <div class="info-card">
                    <strong>📊 Stats</strong><br>
                    Segments: {len(segments)} • Time: {elapsed:.0f}s • 
                    API calls: {api_calls if api_calls > 0 else "0 (FREE!)"}
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"❌ {e}")
                import traceback
                with st.expander("Details"):
                    st.code(traceback.format_exc())
    
    # Footer
    st.markdown("""
    <div class="footer">
        <div class="divider"></div>
        Made with 🧡 for <a href="https://news.shib.io">The Shib Daily</a>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
