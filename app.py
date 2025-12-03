"""
🐕 Pawdcast Skit Factory
Fully automated article-to-video conversion for The Shib Daily

Modes:
- Article: Full auto (API)
- Skit: Paste skit, generate audio (API for TTS)
- Audio: Upload + split audio (100% FREE!)
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
import json

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

DEFAULT_TEMPLATES = {
    "speaker1": "",
    "speaker2": "",
    "closing": ""
}

EDGE_VOICES = {
    "Guy (US)": "en-US-GuyNeural",
    "Davis (US)": "en-US-DavisNeural",
    "Tony (US)": "en-US-TonyNeural",
    "Jason (US)": "en-US-JasonNeural",
}

GEMINI_VOICES = {
    "Enceladus": "Enceladus",
    "Puck": "Puck",
    "Charon": "Charon",
    "Kore": "Kore",
    "Fenrir": "Fenrir",
    "Aoede": "Aoede",
}

SKIT_MODEL = "gemini-2.0-flash"
TTS_MODEL = "gemini-2.5-flash-preview-tts"
LOGO_URL = "https://news.shib.io/wp-content/uploads/2025/12/Untitled-design-1.png"

SKIT_PROMPT = """You are a Content Repurposing Expert. Transform this article into a podcast skit.

Requirements:
- 100-140 words total (~45-70 seconds)
- Exactly two speakers (Speaker 1 and Speaker 2)
- Speaker 1 starts with a witty hook
- Light, professional banter
- End with CTA to "news.shib.io"

Output ONLY dialogue in this format:
Speaker 1: "..."
Speaker 2: "..."

Article:
"""

# ============================================================================
# CSS
# ============================================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
.stApp { background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%); font-family: 'Inter', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.header-container { display: flex; align-items: center; justify-content: center; gap: 1rem; padding: 1.5rem; }
.logo-img { width: 60px; height: 60px; border-radius: 16px; }
.main-title { font-size: 2rem; font-weight: 700; background: linear-gradient(135deg, #f7931a, #ff6b35); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0; }
.subtitle { color: #64748b; font-size: 0.95rem; }
section[data-testid="stSidebar"] { background: rgba(255,255,255,0.9); }
.stButton > button { background: linear-gradient(135deg, #f7931a, #ff6b35) !important; color: white !important; font-weight: 600 !important; border: none !important; border-radius: 12px !important; }
.stDownloadButton > button { background: linear-gradient(135deg, #10b981, #059669) !important; color: white !important; border: none !important; border-radius: 12px !important; }
.badge-success { background: rgba(16,185,129,0.15); color: #059669; padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.8rem; }
.badge-warning { background: rgba(245,158,11,0.15); color: #d97706; padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.8rem; }
.badge-free { background: rgba(16,185,129,0.2); color: #059669; padding: 0.4rem 1rem; border-radius: 20px; font-size: 0.9rem; font-weight: 600; }
.divider { height: 1px; background: linear-gradient(90deg, transparent, rgba(0,0,0,0.1), transparent); margin: 1.5rem 0; }
.split-item { background: rgba(255,255,255,0.8); border-radius: 12px; padding: 1rem; margin: 0.5rem 0; border-left: 4px solid #f7931a; }
.split-item-s2 { border-left-color: #3b82f6; }
.info-card { background: rgba(255,255,255,0.7); border-radius: 12px; padding: 1rem; margin: 1rem 0; }
.footer { text-align: center; padding: 2rem 0; color: #9ca3af; font-size: 0.85rem; }
.footer a { color: #f7931a; text-decoration: none; }
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
        run_cmd(["ffmpeg", "-version"], "ffmpeg")
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
        matches = [(n, l.strip().strip('"\'""')) for n, l in matches]
    return [(f"Speaker {n}", l.strip()) for n, l in matches if l.strip()]

def get_duration(path):
    result = run_cmd([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", path
    ], "duration")
    return float(result.stdout.strip())

def generate_skit(article, api_key):
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=SKIT_MODEL,
        contents=SKIT_PROMPT + article,
        config=types.GenerateContentConfig(temperature=0.8, max_output_tokens=600)
    )
    if response and response.text:
        return response.text
    raise Exception("Empty response")

def generate_audio_gemini(text, voice, api_key, output_path):
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=TTS_MODEL,
        contents=f'Say in a warm podcast tone: "{text}"',
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                )
            )
        )
    )
    data = response.candidates[0].content.parts[0].inline_data.data
    if isinstance(data, str):
        pad = len(data) % 4
        if pad:
            data += '=' * (4 - pad)
        data = base64.b64decode(data)
    with wave.open(output_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(data)
    return output_path

async def generate_audio_edge_async(text, voice, output_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

def generate_audio(text, voice, output_path, engine="gemini", api_key=None):
    try:
        if engine == "gemini":
            return generate_audio_gemini(text, voice, api_key, output_path.replace('.mp3', '.wav'))
        else:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(generate_audio_edge_async(text, voice, output_path))
            loop.close()
            return output_path
    except Exception as e:
        tts = gTTS(text=text, lang='en')
        tts.save(output_path)
        return output_path

# ============================================================================
# AUDIO SPLITTER FUNCTIONS
# ============================================================================

def analyze_audio_for_splits(audio_path, num_segments):
    """
    Analyze audio to find optimal split points using energy/volume analysis.
    Returns list of timestamps where speakers likely change.
    """
    total_duration = get_duration(audio_path)
    
    # Analyze volume in small chunks
    chunk_size = 0.25  # 250ms chunks
    num_chunks = int(total_duration / chunk_size)
    
    volumes = []
    for i in range(num_chunks):
        start = i * chunk_size
        result = subprocess.run([
            "ffmpeg", "-ss", str(start), "-t", str(chunk_size),
            "-i", audio_path, "-af", "volumedetect", "-f", "null", "-"
        ], capture_output=True, text=True)
        
        match = re.search(r'mean_volume: ([-\d.]+)', result.stderr)
        vol = float(match.group(1)) if match else -60
        volumes.append(vol)
    
    # Find dips in volume (potential speaker transitions)
    dips = []
    window = 2
    for i in range(window, len(volumes) - window):
        before = sum(volumes[i-window:i]) / window
        current = volumes[i]
        after = sum(volumes[i+1:i+1+window]) / window
        
        # Look for dips (current is quieter than surroundings)
        if current < before - 2 and current < after - 2:
            dips.append((i * chunk_size, before - current + after - current))
    
    # Sort by significance and get top (num_segments - 1) dips
    dips.sort(key=lambda x: x[1], reverse=True)
    split_times = sorted([d[0] for d in dips[:num_segments - 1]])
    
    # If not enough dips found, fall back to equal division
    if len(split_times) < num_segments - 1:
        segment_dur = total_duration / num_segments
        split_times = [segment_dur * i for i in range(1, num_segments)]
    
    return split_times, total_duration

def split_audio_file(audio_path, split_times, total_duration, output_dir):
    """
    Split audio file at given timestamps.
    Returns list of output file paths.
    """
    output_files = []
    
    # Add start and end
    times = [0] + split_times + [total_duration]
    
    for i in range(len(times) - 1):
        start = times[i]
        duration = times[i + 1] - start
        output_path = os.path.join(output_dir, f"segment_{i:02d}.wav")
        
        run_cmd([
            "ffmpeg", "-y",
            "-ss", str(start),
            "-t", str(duration),
            "-i", audio_path,
            "-c:a", "pcm_s16le",
            "-ar", "24000",
            "-ac", "1",
            output_path
        ], f"split segment {i}")
        
        output_files.append({
            "path": output_path,
            "start": start,
            "duration": duration
        })
    
    return output_files

# ============================================================================
# VIDEO CREATION
# ============================================================================

def create_video_from_segments(segments, tmpl1, tmpl2, closing, output, progress_cb=None):
    """Create video from audio segments with proper speaker switching."""
    temp = Path(output).parent
    
    if progress_cb:
        progress_cb(0.4, "Building video segments...")
    
    segment_videos = []
    
    for i, seg in enumerate(segments):
        seg_out = str(temp / f"seg_{i}.mp4")
        template = tmpl1 if "1" in seg['speaker'] else tmpl2
        duration = seg['duration']
        
        run_cmd([
            "ffmpeg", "-y", "-i", template,
            "-filter_complex",
            f"[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,"
            f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2,"
            f"loop=loop=-1:size=32767,trim=duration={duration},setpts=PTS-STARTPTS[outv]",
            "-map", "[outv]",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
            "-t", str(duration), "-an",
            seg_out
        ], f"video segment {i}")
        
        # Add audio to this segment
        seg_with_audio = str(temp / f"seg_audio_{i}.mp4")
        run_cmd([
            "ffmpeg", "-y",
            "-i", seg_out,
            "-i", seg['audio'],
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            seg_with_audio
        ], f"add audio {i}")
        
        segment_videos.append(seg_with_audio)
    
    if progress_cb:
        progress_cb(0.7, "Joining segments...")
    
    # Concat all segments
    concat_list = temp / "concat.txt"
    with open(concat_list, "w") as f:
        for v in segment_videos:
            f.write(f"file '{v}'\n")
    
    main_video = str(temp / "main.mp4")
    run_cmd([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        main_video
    ], "concat segments")
    
    if progress_cb:
        progress_cb(0.85, "Adding closing...")
    
    # Add closing
    closing_scaled = str(temp / "closing_scaled.mp4")
    run_cmd([
        "ffmpeg", "-y", "-i", closing,
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        closing_scaled
    ], "scale closing")
    
    if progress_cb:
        progress_cb(0.9, "Final assembly...")
    
    # Final concat
    final_list = temp / "final.txt"
    with open(final_list, "w") as f:
        f.write(f"file '{main_video}'\n")
        f.write(f"file '{closing_scaled}'\n")
    
    run_cmd([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(final_list),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        output
    ], "final output")
    
    if progress_cb:
        progress_cb(1.0, "Done!")

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    # Header
    st.markdown(f"""
    <div class="header-container">
        <img src="{LOGO_URL}" class="logo-img">
        <div>
            <h1 class="main-title">Pawdcast Skit Factory</h1>
            <p class="subtitle">Transform articles into podcast videos</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if not check_ffmpeg():
        st.error("⚠️ FFmpeg not available")
        return
    
    # Sidebar
    with st.sidebar:
        st.markdown(f'<img src="{LOGO_URL}" style="width: 40px; border-radius: 10px;">', unsafe_allow_html=True)
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
                st.markdown('[Get key →](https://aistudio.google.com/app/apikey)')
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # TTS Engine (only shown for non-audio modes)
        st.markdown("### 🔊 TTS Engine")
        tts_engine = st.radio(
            "Engine",
            ["gemini", "edge"],
            format_func=lambda x: "⭐ Gemini" if x == "gemini" else "🆓 Edge",
            label_visibility="collapsed"
        )
        
        voice_opts = GEMINI_VOICES if tts_engine == "gemini" else EDGE_VOICES
        voice1 = st.selectbox("Voice 1", list(voice_opts.keys()), index=0)
        voice2 = st.selectbox("Voice 2", list(voice_opts.keys()), index=1)
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # Templates
        st.markdown("### 🎬 Templates")
        tmpl1 = st.file_uploader("Speaker 1 video", type=["mp4"], key="t1")
        tmpl2 = st.file_uploader("Speaker 2 video", type=["mp4"], key="t2")
        tmpl_c = st.file_uploader("Closing video", type=["mp4"], key="tc")
        
        templates_ready = all([tmpl1, tmpl2, tmpl_c])
        if templates_ready:
            st.markdown('<span class="badge-success">✓ Ready</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="badge-warning">⚠ Upload all 3</span>', unsafe_allow_html=True)
    
    # Main content - Mode selection
    st.markdown("### 📌 Select Mode")
    
    mode = st.radio(
        "Mode",
        ["audio", "skit", "article"],
        format_func=lambda x: {
            "article": "📰 Article Mode (Full Auto - uses API)",
            "skit": "📜 Skit Mode (Paste skit - uses API for TTS)",
            "audio": "🎧 Audio Mode (Upload from AI Studio - 100% FREE!)"
        }[x],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # ========== AUDIO MODE (FREE) ==========
    if mode == "audio":
        st.markdown('<span class="badge-free">💰 $0 API COST</span>', unsafe_allow_html=True)
        st.markdown("#### 🎧 Audio Splitter Mode")
        st.caption("Upload complete audio from AI Studio → Auto-split by speaker → Perfect video!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Step 1: Upload Audio**")
            audio_file = st.file_uploader("Complete audio (both speakers)", type=["wav", "mp3"])
            
            if audio_file:
                st.audio(audio_file)
                st.markdown('<span class="badge-success">✓ Audio loaded</span>', unsafe_allow_html=True)
        
        with col2:
            st.markdown("**Step 2: Paste Skit**")
            st.caption("So we know speaker order")
            skit_text = st.text_area(
                "Skit",
                height=200,
                placeholder='Speaker 1: "..."\nSpeaker 2: "..."\nSpeaker 1: "..."',
                label_visibility="collapsed"
            )
            
            if skit_text:
                lines = parse_skit(skit_text)
                if lines:
                    st.caption(f"✓ {len(lines)} speaker turns")
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # Timestamp input option
        st.markdown("**Step 3: Set Split Points**")
        
        split_method = st.radio(
            "How to split?",
            ["manual", "auto"],
            format_func=lambda x: "⏱️ Manual timestamps" if x == "manual" else "🤖 Auto-detect",
            horizontal=True,
            label_visibility="collapsed"
        )
        
        manual_timestamps = ""
        if split_method == "manual":
            st.caption("Enter seconds when each speaker STARTS (first is always 0)")
            manual_timestamps = st.text_input(
                "Timestamps",
                placeholder="0, 8.5, 12.3, 28.7, 35.2",
                help="Listen to audio once, note when each line starts"
            )
        else:
            st.caption("Will analyze audio volume patterns to find speaker changes")
        
        # Create button
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        if st.button("🚀 Split & Create Video", use_container_width=True):
            # Validation
            errors = []
            if not audio_file:
                errors.append("Upload audio")
            if not skit_text.strip():
                errors.append("Paste skit")
            if not templates_ready:
                errors.append("Upload all templates")
            if split_method == "manual" and not manual_timestamps.strip():
                errors.append("Enter timestamps")
            
            if errors:
                st.error("❌ " + " • ".join(errors))
            else:
                with tempfile.TemporaryDirectory() as tmpdir:
                    tmp = Path(tmpdir)
                    progress = st.progress(0)
                    status = st.empty()
                    
                    try:
                        t0 = time.time()
                        
                        # Parse skit
                        lines = parse_skit(skit_text)
                        num_segments = len(lines)
                        
                        # Save audio
                        status.info("📁 Processing audio...")
                        ext = audio_file.name.split('.')[-1]
                        audio_path = str(tmp / f"input.{ext}")
                        with open(audio_path, "wb") as f:
                            f.write(audio_file.read())
                        
                        total_duration = get_duration(audio_path)
                        progress.progress(0.1)
                        
                        # Get split points
                        if split_method == "manual":
                            status.info("⏱️ Using manual timestamps...")
                            try:
                                split_times = [float(t.strip()) for t in manual_timestamps.split(",")]
                                # Remove first if it's 0
                                if split_times and split_times[0] == 0:
                                    split_times = split_times[1:]
                            except:
                                st.error("Invalid timestamp format")
                                return
                        else:
                            status.info("🔍 Analyzing audio for splits...")
                            split_times, _ = analyze_audio_for_splits(audio_path, num_segments)
                        
                        progress.progress(0.2)
                        
                        # Show detected splits
                        st.info(f"📍 Split points: {', '.join([f'{t:.1f}s' for t in [0] + split_times])}")
                        
                        # Split audio
                        status.info("✂️ Splitting audio...")
                        split_files = split_audio_file(audio_path, split_times, total_duration, str(tmp))
                        progress.progress(0.3)
                        
                        # Build segments with speaker info
                        segments = []
                        for i, (speaker, text) in enumerate(lines):
                            if i < len(split_files):
                                segments.append({
                                    "speaker": speaker,
                                    "text": text,
                                    "audio": split_files[i]["path"],
                                    "duration": split_files[i]["duration"]
                                })
                        
                        # Save templates
                        status.info("📦 Loading templates...")
                        t1_path = str(tmp / "t1.mp4")
                        t2_path = str(tmp / "t2.mp4")
                        tc_path = str(tmp / "tc.mp4")
                        with open(t1_path, "wb") as f: f.write(tmpl1.read())
                        with open(t2_path, "wb") as f: f.write(tmpl2.read())
                        with open(tc_path, "wb") as f: f.write(tmpl_c.read())
                        
                        # Create video
                        output = str(tmp / "pawdcast.mp4")
                        
                        def update(pct, msg):
                            progress.progress(pct)
                            status.info(f"🎬 {msg}")
                        
                        create_video_from_segments(segments, t1_path, t2_path, tc_path, output, update)
                        
                        # Read result
                        with open(output, "rb") as f:
                            video_bytes = f.read()
                        
                        elapsed = time.time() - t0
                        progress.progress(1.0)
                        status.success(f"✅ Done in {elapsed:.0f}s!")
                        
                        # Show result
                        st.markdown("---")
                        st.markdown("### 🎉 Your Pawdcast!")
                        st.video(video_bytes)
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.download_button(
                                "📥 Download Video",
                                video_bytes,
                                f"pawdcast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                                "video/mp4",
                                use_container_width=True
                            )
                        
                        st.markdown(f"""
                        <div class="info-card">
                            <strong>📊 Stats</strong><br>
                            Segments: {len(segments)} • Duration: {total_duration:.1f}s • 
                            <span style="color: #059669; font-weight: 600;">API Cost: $0.00 🎉</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    except Exception as e:
                        st.error(f"❌ {e}")
                        import traceback
                        with st.expander("Details"):
                            st.code(traceback.format_exc())
    
    # ========== SKIT MODE ==========
    elif mode == "skit":
        st.markdown("#### 📜 Skit Mode")
        st.caption("Paste your skit → App generates audio and video")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Paste Skit**")
            skit_text = st.text_area(
                "Skit",
                height=300,
                placeholder='Speaker 1: "..."\nSpeaker 2: "..."\nSpeaker 1: "..."',
                label_visibility="collapsed"
            )
            if skit_text:
                lines = parse_skit(skit_text)
                if lines:
                    st.caption(f"✓ {len(lines)} lines detected")
        
        with col2:
            st.markdown("**Preview**")
            if skit_text:
                lines = parse_skit(skit_text)
                for i, (spk, txt) in enumerate(lines):
                    cls = "split-item" if "1" in spk else "split-item split-item-s2"
                    st.markdown(f'<div class="{cls}"><strong>{spk}</strong><br>{txt[:50]}...</div>', unsafe_allow_html=True)
        
        if st.button("🚀 Generate Video", use_container_width=True):
            errors = []
            if not api_key and tts_engine == "gemini":
                errors.append("API key needed for Gemini TTS")
            if not skit_text.strip():
                errors.append("Paste skit")
            if not templates_ready:
                errors.append("Upload templates")
            
            if errors:
                st.error("❌ " + " • ".join(errors))
            else:
                with tempfile.TemporaryDirectory() as tmpdir:
                    tmp = Path(tmpdir)
                    progress = st.progress(0)
                    status = st.empty()
                    
                    try:
                        t0 = time.time()
                        lines = parse_skit(skit_text)
                        
                        # Generate TTS
                        segments = []
                        voice_map = GEMINI_VOICES if tts_engine == "gemini" else EDGE_VOICES
                        
                        for i, (spk, txt) in enumerate(lines):
                            progress.progress(0.1 + (i / len(lines)) * 0.3)
                            status.info(f"🎙️ Generating voice {i+1}/{len(lines)}...")
                            
                            voice = voice_map[voice1] if "1" in spk else voice_map[voice2]
                            audio_path = str(tmp / f"audio_{i}.mp3")
                            audio_path = generate_audio(txt, voice, audio_path, tts_engine, api_key)
                            
                            segments.append({
                                "speaker": spk,
                                "text": txt,
                                "audio": audio_path,
                                "duration": get_duration(audio_path)
                            })
                        
                        # Save templates
                        t1_path = str(tmp / "t1.mp4")
                        t2_path = str(tmp / "t2.mp4")
                        tc_path = str(tmp / "tc.mp4")
                        with open(t1_path, "wb") as f: f.write(tmpl1.read())
                        with open(t2_path, "wb") as f: f.write(tmpl2.read())
                        with open(tc_path, "wb") as f: f.write(tmpl_c.read())
                        
                        # Create video
                        output = str(tmp / "pawdcast.mp4")
                        
                        def update(pct, msg):
                            progress.progress(pct)
                            status.info(f"🎬 {msg}")
                        
                        create_video_from_segments(segments, t1_path, t2_path, tc_path, output, update)
                        
                        with open(output, "rb") as f:
                            video_bytes = f.read()
                        
                        elapsed = time.time() - t0
                        status.success(f"✅ Done in {elapsed:.0f}s!")
                        
                        st.markdown("---")
                        st.markdown("### 🎉 Your Pawdcast!")
                        st.video(video_bytes)
                        
                        st.download_button(
                            "📥 Download",
                            video_bytes,
                            f"pawdcast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                            "video/mp4",
                            use_container_width=True
                        )
                        
                    except Exception as e:
                        st.error(f"❌ {e}")
    
    # ========== ARTICLE MODE ==========
    else:
        st.markdown("#### 📰 Article Mode")
        st.caption("Paste article → AI generates everything")
        
        article = st.text_area(
            "Article",
            height=300,
            placeholder="Paste your news article here...",
            label_visibility="collapsed"
        )
        
        if st.button("🚀 Generate Everything", use_container_width=True):
            errors = []
            if not api_key:
                errors.append("API key required")
            if not article.strip():
                errors.append("Paste article")
            if not templates_ready:
                errors.append("Upload templates")
            
            if errors:
                st.error("❌ " + " • ".join(errors))
            else:
                with tempfile.TemporaryDirectory() as tmpdir:
                    tmp = Path(tmpdir)
                    progress = st.progress(0)
                    status = st.empty()
                    
                    try:
                        t0 = time.time()
                        
                        # Generate skit
                        status.info("🤖 Generating skit...")
                        progress.progress(0.1)
                        skit = generate_skit(article, api_key)
                        
                        st.markdown("**Generated Skit:**")
                        st.code(skit)
                        
                        lines = parse_skit(skit)
                        if not lines:
                            st.error("Failed to parse skit")
                            return
                        
                        # Generate TTS
                        segments = []
                        voice_map = GEMINI_VOICES if tts_engine == "gemini" else EDGE_VOICES
                        
                        for i, (spk, txt) in enumerate(lines):
                            progress.progress(0.15 + (i / len(lines)) * 0.25)
                            status.info(f"🎙️ Voice {i+1}/{len(lines)}...")
                            
                            voice = voice_map[voice1] if "1" in spk else voice_map[voice2]
                            audio_path = str(tmp / f"audio_{i}.mp3")
                            audio_path = generate_audio(txt, voice, audio_path, tts_engine, api_key)
                            
                            segments.append({
                                "speaker": spk,
                                "text": txt,
                                "audio": audio_path,
                                "duration": get_duration(audio_path)
                            })
                        
                        # Templates
                        t1_path = str(tmp / "t1.mp4")
                        t2_path = str(tmp / "t2.mp4")
                        tc_path = str(tmp / "tc.mp4")
                        with open(t1_path, "wb") as f: f.write(tmpl1.read())
                        with open(t2_path, "wb") as f: f.write(tmpl2.read())
                        with open(tc_path, "wb") as f: f.write(tmpl_c.read())
                        
                        output = str(tmp / "pawdcast.mp4")
                        
                        def update(pct, msg):
                            progress.progress(pct)
                            status.info(f"🎬 {msg}")
                        
                        create_video_from_segments(segments, t1_path, t2_path, tc_path, output, update)
                        
                        with open(output, "rb") as f:
                            video_bytes = f.read()
                        
                        elapsed = time.time() - t0
                        status.success(f"✅ Done in {elapsed:.0f}s!")
                        
                        st.markdown("---")
                        st.markdown("### 🎉 Your Pawdcast!")
                        st.video(video_bytes)
                        
                        st.download_button(
                            "📥 Download",
                            video_bytes,
                            f"pawdcast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                            "video/mp4",
                            use_container_width=True
                        )
                        
                    except Exception as e:
                        st.error(f"❌ {e}")
    
    # Footer
    st.markdown("""
    <div class="footer">
        <div class="divider"></div>
        Made with 🧡 for <a href="https://news.shib.io">The Shib Daily</a>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
