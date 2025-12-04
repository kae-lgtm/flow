"""
Pawdcast Skit Factory — Enhanced Modern Design
Audio Mode: Perfect sync with Google TTS / any audio
"""
import streamlit as st
import google.generativeai as genai
import os
import re
import subprocess
import tempfile
import wave
from pathlib import Path
import base64
import traceback

# ============================================================================
# PAGE CONFIG & MODERN CSS
# ============================================================================
st.set_page_config(page_title="Pawdcast", page_icon="🎙️", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* Base */
.stApp { 
    background: linear-gradient(160deg, #ffffff 0%, #f8fafc 100%); 
    font-family: 'Inter', -apple-system, sans-serif; 
    color: #1e293b;
}

/* Hide defaults */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* Header — Logo LEFT of Title */
.header-container { 
    display: flex; 
    align-items: center; 
    justify-content: center; 
    gap: 1rem; 
    padding: 1.5rem 0; 
}
.logo-img { 
    width: 48px; 
    height: 48px; 
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(249, 115, 22, 0.2);
}
.header-text {
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
}
.main-title { 
    font-size: 1.75rem; 
    font-weight: 800; 
    background: linear-gradient(135deg, #f97316, #ea580c); 
    -webkit-background-clip: text; 
    -webkit-text-fill-color: transparent; 
    margin: 0;
    letter-spacing: -0.5px;
}
.subtitle { 
    color: #64748b; 
    font-size: 0.85rem;
    font-weight: 500;
    margin: 0;
}

/* Sidebar */
section[data-testid="stSidebar"] { 
    background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
    border-right: 1px solid #e2e8f0;
}
section[data-testid="stSidebar"] .block-container {
    padding: 1rem;
}

/* All Buttons — Orange Theme */
.stButton > button,
.stDownloadButton > button {
    background: linear-gradient(135deg, #f97316 0%, #ea580c 100%) !important;
    color: white !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.6rem 1.2rem !important;
    box-shadow: 0 4px 14px rgba(249, 115, 22, 0.3) !important;
    transition: all 0.25s ease !important;
}
.stButton > button:hover,
.stDownloadButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(249, 115, 22, 0.4) !important;
}

/* Badges */
.badge-free { 
    display: inline-block;
    background: linear-gradient(135deg, #f97316, #ea580c);
    color: white;
    padding: 0.4rem 1rem; 
    border-radius: 50px; 
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.5px;
}
.badge-ready {
    display: inline-block;
    background: linear-gradient(135deg, #10b981, #059669);
    color: white;
    padding: 0.3rem 0.8rem;
    border-radius: 50px;
    font-size: 0.7rem;
    font-weight: 600;
}
.badge-waiting {
    display: inline-block;
    background: linear-gradient(135deg, #f59e0b, #d97706);
    color: white;
    padding: 0.3rem 0.8rem;
    border-radius: 50px;
    font-size: 0.7rem;
    font-weight: 600;
}

/* Cards */
.card {
    background: white;
    border-radius: 16px;
    padding: 1.25rem;
    margin: 1rem 0;
    border: 1px solid #e2e8f0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.card-title {
    font-size: 1rem;
    font-weight: 700;
    color: #1e293b;
    margin: 0 0 0.25rem 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.card-desc {
    color: #64748b;
    font-size: 0.85rem;
    margin: 0;
}

/* Mode Pills */
.stRadio > div { 
    display: flex; 
    gap: 0.5rem; 
    justify-content: center;
    flex-wrap: wrap;
}
.stRadio > div > label { 
    background: white; 
    border-radius: 50px; 
    padding: 0.5rem 1rem; 
    border: 1.5px solid #e2e8f0; 
    font-weight: 600; 
    font-size: 0.85rem;
    transition: all 0.2s ease;
    cursor: pointer;
}
.stRadio > div > label:hover { 
    border-color: #f97316; 
    background: #fff7ed;
}

/* Inputs */
.stTextArea textarea, .stTextInput input {
    border-radius: 10px !important;
    border: 1.5px solid #e2e8f0 !important;
    font-size: 0.9rem !important;
    background: #fafafa !important;
    transition: all 0.2s !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: #f97316 !important;
    box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.1) !important;
    background: white !important;
}

/* File Uploader */
.stFileUploader > div > div {
    border-radius: 10px !important;
    border: 2px dashed #e2e8f0 !important;
    background: #fafafa !important;
}
.stFileUploader > div > div:hover {
    border-color: #f97316 !important;
    background: #fff7ed !important;
}

/* Progress */
.stProgress > div > div {
    background: linear-gradient(135deg, #f97316, #ea580c) !important;
    border-radius: 50px !important;
}

/* Expander */
.streamlit-expanderHeader {
    background: #f8fafc !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}

/* Divider */
.divider { 
    height: 1px; 
    background: linear-gradient(90deg, transparent, #e2e8f0, transparent); 
    margin: 1.5rem 0; 
}

/* Footer */
.footer { 
    text-align: center; 
    padding: 2rem 0; 
    color: #94a3b8; 
    font-size: 0.8rem;
    margin-top: 2rem;
    border-top: 1px solid #e2e8f0;
}
.footer a { 
    color: #f97316; 
    text-decoration: none;
    font-weight: 600;
}

/* Section headers */
.section-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 700;
    color: #475569;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin: 1rem 0 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CONFIG
# ============================================================================
GEMINI_VOICES = {
    "Puck": "Puck",
    "Charon": "Charon", 
    "Kore": "Kore",
    "Fenrir": "Fenrir",
    "Aoede": "Aoede",
    "Enceladus": "Enceladus"
}
SKIT_MODEL = "gemini-2.0-flash"
TTS_MODEL = "gemini-2.5-flash-preview-tts"
LOGO_URL = "https://news.shib.io/wp-content/uploads/2025/12/Black-White-Simple-Modern-Neon-Griddy-Bold-Technology-Pixel-Electronics-Store-Logo-1.png"

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
        run_cmd(["ffmpeg", "-version"], "ffmpeg")
        return True
    except:
        return False

def get_duration(path):
    result = run_cmd(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path])
    return float(result.stdout.strip())

def parse_skit(text):
    if not text: return []
    pattern = r'Speaker\s*(\d+)\s*:\s*["""]([^"""]+)["""]'
    matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
    if not matches:
        pattern = r'Speaker\s*(\d+)\s*:\s*(.+?)(?=Speaker\s*\d+:|$)'
        matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
        matches = [(n, l.strip().strip('"\'""')) for n, l in matches]
    return [(f"Speaker {n}", l.strip()) for n, l in matches if l.strip()]

# ============================================================================
# AUDIO SPLITTER
# ============================================================================
def analyze_audio_for_splits(audio_path, num_segments):
    total_duration = get_duration(audio_path)
    
    # Try detecting silence gaps
    cmd = ["ffmpeg", "-i", audio_path, "-af", "silencedetect=noise=-50dB:d=0.8", "-f", "null", "-"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    ends = [float(m.group(1)) for m in re.finditer(r'silence_end: (\d+\.?\d*)', result.stderr) if float(m.group(1)) > 1.0]
    
    if len(ends) < num_segments - 1:
        cmd = ["ffmpeg", "-i", audio_path, "-af", "silencedetect=noise=-32dB:d=0.38", "-f", "null", "-"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        ends = [float(m.group(1)) for m in re.finditer(r'silence_end: (\d+\.?\d*)', result.stderr)]
    
    if len(ends) >= num_segments - 1:
        split_times = ends[:num_segments - 1]
    else:
        step = total_duration / num_segments
        split_times = [step * i for i in range(1, num_segments)]
    
    return split_times, total_duration

def split_audio_file(audio_path, split_times, total_duration, output_dir):
    output_files = []
    times = [0] + split_times + [total_duration]
    
    for i in range(len(times) - 1):
        start = times[i]
        end = times[i + 1]
        duration = max(0.1, end - start)
        output_path = os.path.join(output_dir, f"segment_{i:02d}.wav")
        
        run_cmd([
            "ffmpeg", "-y",
            "-i", audio_path,
            "-ss", str(start),
            "-t", str(duration),
            "-c:a", "pcm_s16le",
            "-ar", "24000",
            "-ac", "1",
            output_path
        ], f"split {i}")
        
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
    temp = Path(output).parent
    
    if progress_cb: progress_cb(0.4, "🎬 Building video segments...")
    
    segment_videos = []
    for i, seg in enumerate(segments):
        seg_out = str(temp / f"seg_{i}.mp4")
        template = tmpl1 if "1" in seg['speaker'] else tmpl2
        duration = seg['duration']
        
        run_cmd([
            "ffmpeg", "-y", "-i", template,
            "-filter_complex",
            f"[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,loop=loop=-1:size=32767,trim=duration={duration},setpts=PTS-STARTPTS[outv]",
            "-map", "[outv]", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
            "-t", str(duration), "-an", seg_out
        ], f"video segment {i}")
        
        seg_with_audio = str(temp / f"seg_audio_{i}.mp4")
        run_cmd([
            "ffmpeg", "-y", "-i", seg_out, "-i", seg['audio'],
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", seg_with_audio
        ], f"add audio {i}")
        segment_videos.append(seg_with_audio)
    
    if progress_cb: progress_cb(0.7, "🔗 Joining segments...")
    
    concat_list = temp / "concat.txt"
    with open(concat_list, "w") as f:
        for v in segment_videos: 
            f.write(f"file '{v}'\n")
    
    main_video = str(temp / "main.mp4")
    run_cmd(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c:v", "libx264", "-preset", "fast", "-crf", "23", main_video], "concat")
    
    if progress_cb: progress_cb(0.85, "🎵 Adding outro with audio...")
    
    # Keep closing video's original audio
    run_cmd([
        "ffmpeg", "-y",
        "-i", main_video,
        "-i", closing,
        "-filter_complex", "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-preset", "fast",
        "-crf", "23",
        "-movflags", "+faststart",
        output
    ], "final with closing audio preserved")
    
    if progress_cb: progress_cb(1.0, "✅ Done!")

# ============================================================================
# GEMINI TTS
# ============================================================================
def generate_audio_gemini(text, voice, api_key, output_path):
    """Generate TTS audio using Gemini."""
    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel(TTS_MODEL)
    
    response = model.generate_content(
        f'Say this naturally: "{text}"',
        generation_config=genai.types.GenerationConfig(
            response_mime_type="audio/wav",
        )
    )
    
    # Handle audio response
    if hasattr(response, 'candidates') and response.candidates:
        audio_part = response.candidates[0].content.parts[0]
        if hasattr(audio_part, 'inline_data'):
            audio_data = audio_part.inline_data.data
            
            if isinstance(audio_data, str):
                missing_padding = len(audio_data) % 4
                if missing_padding:
                    audio_data += '=' * (4 - missing_padding)
                audio_data = base64.b64decode(audio_data)
            
            # Write as WAV
            with wave.open(output_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(24000)
                wf.writeframes(audio_data)
            
            return output_path
    
    raise Exception("No audio generated")

def generate_skit(article, api_key):
    """Generate podcast skit from article."""
    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel(SKIT_MODEL)
    
    prompt = f"""Transform this article into a short podcast conversation between two hosts.

Rules:
- 4-6 exchanges total
- Speaker 1 leads, Speaker 2 reacts
- Natural, conversational tone
- Format: Speaker 1: "text" or Speaker 2: "text"

Article:
{article}

Write the skit:"""
    
    response = model.generate_content(prompt)
    return response.text

# ============================================================================
# MAIN APP
# ============================================================================
def main():
    # Header
    st.markdown(f'''
    <div class="header-container">
        <img src="{LOGO_URL}" class="logo-img">
        <div class="header-text">
            <h1 class="main-title">Pawdcast</h1>
            <p class="subtitle">Transform articles into podcast videos</p>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    if not check_ffmpeg():
        st.error("⚠️ FFmpeg not available")
        return
    
    # Sidebar
    with st.sidebar:
        st.markdown(f'<img src="{LOGO_URL}" style="width:36px; border-radius:10px; margin-bottom:0.5rem;">', unsafe_allow_html=True)
        
        st.markdown('<div class="section-header">🔑 API</div>', unsafe_allow_html=True)
        api_key = st.text_input(
            "Gemini API Key",
            type="password",
            value=st.secrets.get("GEMINI_API_KEY", "") if hasattr(st, 'secrets') and "GEMINI_API_KEY" in st.secrets else "",
            label_visibility="collapsed",
            placeholder="Enter your Gemini API key"
        )
        
        st.markdown('<div class="section-header">🎙️ Voices</div>', unsafe_allow_html=True)
        voice1 = st.selectbox("Speaker 1", list(GEMINI_VOICES.keys()), index=0, label_visibility="collapsed")
        voice2 = st.selectbox("Speaker 2", list(GEMINI_VOICES.keys()), index=1, label_visibility="collapsed")
        
        st.markdown('<div class="section-header">🎬 Templates</div>', unsafe_allow_html=True)
        tmpl1 = st.file_uploader("Speaker 1 video", type=["mp4"], key="t1", label_visibility="collapsed")
        tmpl2 = st.file_uploader("Speaker 2 video", type=["mp4"], key="t2", label_visibility="collapsed")
        tmpl_c = st.file_uploader("Outro video", type=["mp4"], key="tc", label_visibility="collapsed")
        
        templates_ready = all([tmpl1, tmpl2, tmpl_c])
        
        if templates_ready:
            st.markdown('<span class="badge-ready">✓ Ready</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="badge-waiting">⏳ Upload 3 videos</span>', unsafe_allow_html=True)
    
    # Mode selector
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    mode = st.radio(
        "Mode",
        ["audio", "skit", "article"],
        horizontal=True,
        format_func=lambda x: {
            "audio": "🎧 Audio Mode",
            "skit": "📝 Skit Mode", 
            "article": "📰 Article Mode"
        }[x],
        label_visibility="collapsed"
    )
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # ========================================================================
    # AUDIO MODE — FREE
    # ========================================================================
    if mode == "audio":
        st.markdown('''
        <div class="card">
            <div class="card-title">🎧 Audio Mode <span class="badge-free">FREE FOREVER</span></div>
            <p class="card-desc">Upload your audio from AI Studio + paste the skit</p>
        </div>
        ''', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            audio_file = st.file_uploader("🎵 Upload audio", type=["wav", "mp3", "m4a"])
        with col2:
            skit_text = st.text_area("📝 Paste skit", height=180, placeholder='Speaker 1: "Welcome!"\nSpeaker 2: "Thanks!"')
        
        with st.expander("⚙️ Split Settings"):
            split_method = st.radio("Method", ["auto", "manual"], horizontal=True, format_func=lambda x: "🤖 Auto-detect" if x == "auto" else "✏️ Manual")
            manual_timestamps = ""
            if split_method == "manual":
                manual_timestamps = st.text_input("Timestamps (seconds)", placeholder="0, 8.5, 15.2, 22.0")
        
        if st.button("🚀 Create Video", use_container_width=True):
            if not all([audio_file, skit_text, templates_ready]):
                st.error("Please upload audio, paste skit, and add all 3 templates")
            else:
                with tempfile.TemporaryDirectory() as tmpdir:
                    tmp = Path(tmpdir)
                    progress = st.progress(0)
                    status = st.empty()
                    
                    try:
                        lines = parse_skit(skit_text)
                        if not lines:
                            st.error("Could not parse skit. Use: Speaker 1: \"text\"")
                            return
                        
                        num_segments = len(lines)
                        audio_path = str(tmp / "input.wav")
                        with open(audio_path, "wb") as f:
                            f.write(audio_file.read())
                        
                        total_duration = get_duration(audio_path)
                        progress.progress(0.1)
                        
                        if split_method == "manual" and manual_timestamps:
                            split_times = [float(t.strip()) for t in manual_timestamps.split(",") if t.strip()]
                            if split_times and split_times[0] == 0:
                                split_times = split_times[1:]
                        else:
                            status.info("🔍 Detecting speaker changes...")
                            split_times, _ = analyze_audio_for_splits(audio_path, num_segments)
                        
                        st.info(f"📍 Splits: 0, {', '.join([f'{t:.2f}' for t in split_times])}")
                        progress.progress(0.2)
                        
                        split_files = split_audio_file(audio_path, split_times, total_duration, str(tmp))
                        
                        segments = []
                        for i, (spk, txt) in enumerate(lines):
                            if i < len(split_files):
                                segments.append({
                                    "speaker": spk,
                                    "text": txt,
                                    "audio": split_files[i]["path"],
                                    "duration": split_files[i]["duration"]
                                })
                        
                        t1_path = str(tmp / "t1.mp4")
                        t2_path = str(tmp / "t2.mp4")
                        tc_path = str(tmp / "tc.mp4")
                        
                        with open(t1_path, "wb") as f: f.write(tmpl1.read())
                        with open(t2_path, "wb") as f: f.write(tmpl2.read())
                        with open(tc_path, "wb") as f: f.write(tmpl_c.read())
                        
                        output = str(tmp / "final.mp4")
                        create_video_from_segments(
                            segments, t1_path, t2_path, tc_path, output,
                            lambda p, m: (progress.progress(p), status.info(m))
                        )
                        
                        st.success("✨ Video created!")
                        with open(output, "rb") as f:
                            video_bytes = f.read()
                        st.video(video_bytes)
                        st.download_button("📥 Download Video", video_bytes, "pawdcast.mp4", "video/mp4", use_container_width=True)
                        
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                        with st.expander("Details"):
                            st.code(traceback.format_exc())
    
    # ========================================================================
    # SKIT MODE
    # ========================================================================
    elif mode == "skit":
        st.markdown('''
        <div class="card">
            <div class="card-title">📝 Skit Mode</div>
            <p class="card-desc">Paste your skit, we generate audio with Gemini TTS</p>
        </div>
        ''', unsafe_allow_html=True)
        
        skit_text = st.text_area("📝 Paste skit", height=200, placeholder='Speaker 1: "Hey everyone!"\nSpeaker 2: "Welcome back!"')
        
        if st.button("🎬 Generate Video", use_container_width=True):
            if not api_key:
                st.error("Please add your Gemini API key")
            elif not skit_text:
                st.error("Please paste a skit")
            elif not templates_ready:
                st.error("Please upload all 3 templates")
            else:
                with tempfile.TemporaryDirectory() as tmpdir:
                    tmp = Path(tmpdir)
                    progress = st.progress(0)
                    status = st.empty()
                    
                    try:
                        lines = parse_skit(skit_text)
                        if not lines:
                            st.error("Could not parse skit")
                            return
                        
                        status.info(f"🎙️ Generating audio for {len(lines)} lines...")
                        
                        segments = []
                        for i, (spk, txt) in enumerate(lines):
                            voice = GEMINI_VOICES[voice1] if "1" in spk else GEMINI_VOICES[voice2]
                            audio_path = str(tmp / f"line_{i}.wav")
                            
                            generate_audio_gemini(txt, voice, api_key, audio_path)
                            duration = get_duration(audio_path)
                            
                            segments.append({
                                "speaker": spk,
                                "text": txt,
                                "audio": audio_path,
                                "duration": duration
                            })
                            progress.progress((i + 1) / len(lines) * 0.5)
                        
                        t1_path = str(tmp / "t1.mp4")
                        t2_path = str(tmp / "t2.mp4")
                        tc_path = str(tmp / "tc.mp4")
                        
                        with open(t1_path, "wb") as f: f.write(tmpl1.read())
                        with open(t2_path, "wb") as f: f.write(tmpl2.read())
                        with open(tc_path, "wb") as f: f.write(tmpl_c.read())
                        
                        output = str(tmp / "final.mp4")
                        create_video_from_segments(
                            segments, t1_path, t2_path, tc_path, output,
                            lambda p, m: (progress.progress(0.5 + p * 0.5), status.info(m))
                        )
                        
                        st.success("✨ Video created!")
                        with open(output, "rb") as f:
                            video_bytes = f.read()
                        st.video(video_bytes)
                        st.download_button("📥 Download Video", video_bytes, "pawdcast.mp4", "video/mp4", use_container_width=True)
                        
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                        with st.expander("Details"):
                            st.code(traceback.format_exc())
    
    # ========================================================================
    # ARTICLE MODE
    # ========================================================================
    else:
        st.markdown('''
        <div class="card">
            <div class="card-title">📰 Article Mode</div>
            <p class="card-desc">Paste an article, AI writes skit + generates audio</p>
        </div>
        ''', unsafe_allow_html=True)
        
        article_text = st.text_area("📰 Paste article", height=200, placeholder="Paste your article here...")
        
        if st.button("✨ Create Pawdcast", use_container_width=True):
            if not api_key:
                st.error("Please add your Gemini API key")
            elif not article_text:
                st.error("Please paste an article")
            elif not templates_ready:
                st.error("Please upload all 3 templates")
            else:
                with tempfile.TemporaryDirectory() as tmpdir:
                    tmp = Path(tmpdir)
                    progress = st.progress(0)
                    status = st.empty()
                    
                    try:
                        status.info("🧠 Writing skit...")
                        skit_text = generate_skit(article_text, api_key)
                        progress.progress(0.2)
                        
                        with st.expander("📜 Generated Skit"):
                            st.text(skit_text)
                        
                        lines = parse_skit(skit_text)
                        if not lines:
                            st.error("Failed to parse skit")
                            return
                        
                        status.info(f"🎙️ Generating audio...")
                        segments = []
                        
                        for i, (spk, txt) in enumerate(lines):
                            voice = GEMINI_VOICES[voice1] if "1" in spk else GEMINI_VOICES[voice2]
                            audio_path = str(tmp / f"line_{i}.wav")
                            
                            generate_audio_gemini(txt, voice, api_key, audio_path)
                            duration = get_duration(audio_path)
                            
                            segments.append({
                                "speaker": spk,
                                "text": txt,
                                "audio": audio_path,
                                "duration": duration
                            })
                            progress.progress(0.2 + (i + 1) / len(lines) * 0.4)
                        
                        t1_path = str(tmp / "t1.mp4")
                        t2_path = str(tmp / "t2.mp4")
                        tc_path = str(tmp / "tc.mp4")
                        
                        with open(t1_path, "wb") as f: f.write(tmpl1.read())
                        with open(t2_path, "wb") as f: f.write(tmpl2.read())
                        with open(tc_path, "wb") as f: f.write(tmpl_c.read())
                        
                        output = str(tmp / "final.mp4")
                        create_video_from_segments(
                            segments, t1_path, t2_path, tc_path, output,
                            lambda p, m: (progress.progress(0.6 + p * 0.4), status.info(m))
                        )
                        
                        st.success("✨ Video created!")
                        with open(output, "rb") as f:
                            video_bytes = f.read()
                        st.video(video_bytes)
                        st.download_button("📥 Download Video", video_bytes, "pawdcast.mp4", "video/mp4", use_container_width=True)
                        
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                        with st.expander("Details"):
                            st.code(traceback.format_exc())
    
    # Footer
    st.markdown('''
    <div class="footer">
        Made with ❤️ for <a href="https://news.shib.io" target="_blank">The Shib Daily</a>
    </div>
    ''', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
