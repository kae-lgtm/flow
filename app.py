"""
🐕 Pawdcast Skit Factory
Fully automated article-to-video conversion for The Shib Daily

Features:
- Paste article → Get video
- AI-powered skit generation (Gemini)
- Natural TTS voices
- Auto speaker switching
- 16:9 output (1920x1080)
"""

import streamlit as st
from google import genai
from google.genai import types
import os
import re
import subprocess
import tempfile
import wave
from pathlib import Path
from datetime import datetime
import time
import base64
import asyncio
import edge_tts

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
# GLASSMORPHISM THEME - White/Gray with Glass Effects
# ============================================================================

st.markdown("""
<style>
/* Import Google Font */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Main background - light gradient */
.stApp {
    background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 50%, #d1d5db 100%);
    font-family: 'Inter', sans-serif;
}

/* Hide default Streamlit elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Glass card effect */
.glass-card {
    background: rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.8);
    border-radius: 24px;
    padding: 2rem;
    box-shadow: 
        0 8px 32px rgba(0, 0, 0, 0.08),
        inset 0 0 0 1px rgba(255, 255, 255, 0.5);
}

/* Header with logo */
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
    font-weight: 400;
    margin-top: 0.25rem;
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background: rgba(255, 255, 255, 0.8);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
}

section[data-testid="stSidebar"] .stMarkdown {
    color: #374151;
}

/* Input fields */
.stTextArea textarea {
    background: rgba(255, 255, 255, 0.9) !important;
    border: 1px solid rgba(0, 0, 0, 0.1) !important;
    border-radius: 16px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.95rem !important;
    color: #1f2937 !important;
    padding: 1rem !important;
}

.stTextArea textarea:focus {
    border-color: #f7931a !important;
    box-shadow: 0 0 0 3px rgba(247, 147, 26, 0.1) !important;
}

.stTextArea textarea::placeholder {
    color: #9ca3af !important;
}

/* File uploader */
.stFileUploader {
    background: rgba(255, 255, 255, 0.5);
    border-radius: 12px;
    padding: 0.5rem;
}

/* Select boxes */
.stSelectbox > div > div {
    background: rgba(255, 255, 255, 0.9) !important;
    border: 1px solid rgba(0, 0, 0, 0.1) !important;
    border-radius: 12px !important;
}

/* Big orange CTA button */
.stButton > button {
    background: linear-gradient(135deg, #f7931a 0%, #ff6b35 100%) !important;
    color: white !important;
    font-size: 1.2rem !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    padding: 1rem 2.5rem !important;
    border: none !important;
    border-radius: 16px !important;
    box-shadow: 0 8px 24px rgba(247, 147, 26, 0.35) !important;
    transition: all 0.3s ease !important;
    text-transform: none !important;
}

.stButton > button:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 12px 32px rgba(247, 147, 26, 0.45) !important;
}

.stButton > button:active {
    transform: translateY(-1px) !important;
}

/* Download buttons */
.stDownloadButton > button {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
    color: white !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3) !important;
}

.stDownloadButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4) !important;
}

/* Progress bar */
.stProgress > div > div {
    background: linear-gradient(90deg, #f7931a, #ff6b35) !important;
    border-radius: 10px;
}

/* Status badges */
.badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.4rem 0.9rem;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 500;
}

.badge-success {
    background: rgba(16, 185, 129, 0.15);
    color: #059669;
    border: 1px solid rgba(16, 185, 129, 0.3);
}

.badge-warning {
    background: rgba(245, 158, 11, 0.15);
    color: #d97706;
    border: 1px solid rgba(245, 158, 11, 0.3);
}

.badge-info {
    background: rgba(59, 130, 246, 0.15);
    color: #2563eb;
    border: 1px solid rgba(59, 130, 246, 0.3);
}

/* Section headers */
.section-header {
    font-size: 1.1rem;
    font-weight: 600;
    color: #374151;
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* Info cards */
.info-card {
    background: rgba(255, 255, 255, 0.6);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.8);
    border-radius: 16px;
    padding: 1.25rem;
    margin: 1rem 0;
}

/* Video container */
.video-container {
    background: rgba(0, 0, 0, 0.03);
    border-radius: 20px;
    padding: 1rem;
    border: 1px solid rgba(0, 0, 0, 0.05);
}

/* Footer */
.footer {
    text-align: center;
    padding: 2rem 0 1rem 0;
    color: #9ca3af;
    font-size: 0.85rem;
}

.footer a {
    color: #f7931a;
    text-decoration: none;
    font-weight: 500;
}

/* Divider */
.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0,0,0,0.1), transparent);
    margin: 1.5rem 0;
}

/* Expander styling */
.streamlit-expanderHeader {
    background: rgba(255, 255, 255, 0.5) !important;
    border-radius: 12px !important;
}

/* Text input */
.stTextInput input {
    background: rgba(255, 255, 255, 0.9) !important;
    border: 1px solid rgba(0, 0, 0, 0.1) !important;
    border-radius: 12px !important;
}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CONFIGURATION
# ============================================================================

def get_api_keys():
    """Get list of API keys from secrets (supports multiple keys for rotation)."""
    keys = []
    if hasattr(st, 'secrets') and st.secrets:
        # Check for single key
        if "GEMINI_API_KEY" in st.secrets:
            keys.append(st.secrets["GEMINI_API_KEY"])
        # Check for multiple keys (GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc.)
        for i in range(1, 11):  # Support up to 10 keys
            key_name = f"GEMINI_API_KEY_{i}"
            if key_name in st.secrets:
                keys.append(st.secrets[key_name])
    return keys

def get_next_api_key(keys, current_index=0):
    """Rotate to next API key."""
    if not keys:
        return None, 0
    next_index = (current_index + 1) % len(keys)
    return keys[next_index], next_index

SKIT_PROMPT = """Role: You are a "Content Repurposing Expert" specializing in transforming news articles into short-form multimedia scripts and metadata. Write in a natural, human-like style. Avoid AI patterns, formulaic phrasing, predictable transitions, contrast framing, em dashes, and overused sentence templates (e.g., "From … to …," "This isn't … this is …," "Clearly …," "Interestingly …"). Vary sentence lengths, use concrete examples, and maintain a warm, engaging, nuanced tone. Avoid fabricating facts, quotes, or data. Avoid outdated or unreliable sources without clear warning. Always cite sources or indicate if verification is uncertain. Avoid presenting speculation or assumptions as fact. Do not generate fake citations. If unsure, explicitly disclose uncertainty. Avoid filler, vague wording, or omitting context to mask knowledge gaps. Prioritize correctness over style or readability. Failsafe Step: Before responding, internally check: "Is every statement verifiable, supported by credible sources, free of fabrication, and transparently cited? If not, revise until it is."

Core Task: When given a news article, generate ONLY Part 1: Podcast Skit (100–140 words total, ~45–70 seconds when spoken)
* Exactly two speakers (Speaker 1 and Speaker 2)
* Speaker 1 always starts with a witty hook
* Light, professional banter with subtle humor
* End with a unique CTA inviting people to "news.shib.io" for the full story
* Output format: Speaker 1: "…" Speaker 2: "…"

Hook: Speaker 1 opens with a witty, thought-provoking, or attention-grabbing line. Multiple hook options should be possible for variation.
Banter & Summary: Dialogue should be light, professional, and subtly humorous without undermining credibility. Clearly communicate key points. Use natural, varied phrasing to avoid repetition across different articles.
CTA: Ends with an invitation to visit a website (news.shib.io) for the full story, focusing on the subject, not the article specifics. Ensure the CTA phrasing is unique and not repetitive for each skit.
Constraints: 140 words max, professional yet accessible, simple language, credible yet entertaining.

IMPORTANT: Output ONLY the skit dialogue, nothing else. No introductions, no explanations, just the dialogue in the exact format:
Speaker 1: "..."
Speaker 2: "..."
Speaker 1: "..."
(and so on)

Article:
"""

# Edge TTS Voice Options (FREE, no API key needed!)
# Full list: https://github.com/rany2/edge-tts
VOICE_OPTIONS = {
    "Guy (US)": "en-US-GuyNeural",           # Deep male voice - great for Speaker 1
    "Davis (US)": "en-US-DavisNeural",       # Warm male voice - great for Speaker 2
    "Tony (US)": "en-US-TonyNeural",         # Casual male voice
    "Jason (US)": "en-US-JasonNeural",       # Professional male
    "Christopher (US)": "en-US-ChristopherNeural",  # News anchor style
    "Eric (US)": "en-US-EricNeural",         # Friendly male
    "Ryan (UK)": "en-GB-RyanNeural",         # British male
    "William (AU)": "en-AU-WilliamNeural",   # Australian male
    "Jenny (US)": "en-US-JennyNeural",       # Friendly female
    "Aria (US)": "en-US-AriaNeural",         # Professional female
}

SKIT_MODEL = "gemini-2.0-flash"

LOGO_URL = "https://news.shib.io/wp-content/uploads/2025/12/Untitled-design-1.png"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def run_cmd(cmd, desc=""):
    """Run shell command."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Error ({desc}): {result.stderr}")
    return result

def check_ffmpeg():
    """Verify FFmpeg is available."""
    try:
        run_cmd(["ffmpeg", "-version"], "ffmpeg check")
        return True
    except:
        return False

def parse_skit(text):
    """Parse skit into [(speaker, dialogue), ...]"""
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
    """Generate podcast skit from article using Gemini."""
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=SKIT_MODEL,
            contents=SKIT_PROMPT + article,
            config=types.GenerateContentConfig(
                temperature=0.8,
                max_output_tokens=600
            )
        )
        
        if response and response.text:
            return response.text
        elif response and response.candidates:
            for candidate in response.candidates:
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, 'text') and part.text:
                            return part.text
        
        raise Exception("Gemini returned empty response. Try again.")
        
    except Exception as e:
        raise Exception(f"Skit generation failed: {str(e)}")

async def generate_audio_async(text, voice, output_path):
    """Generate TTS audio using Edge TTS (FREE, unlimited)."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)
    return output_path

def generate_audio(text, voice, output_path):
    """Wrapper to run async Edge TTS."""
    try:
        # Run the async function
        asyncio.run(generate_audio_async(text, voice, output_path))
        return output_path
    except Exception as e:
        raise Exception(f"Audio generation failed: {str(e)}")

def get_duration(path):
    """Get media file duration."""
    result = run_cmd([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", path
    ], "duration")
    return float(result.stdout.strip())

def create_video(segments, tmpl1, tmpl2, closing, output, progress_cb=None):
    """Assemble final video with FFmpeg - NO CAPTIONS, WITH CLOSING AUDIO."""
    temp = Path(output).parent
    
    # 1. Convert and merge all skit audio (Edge TTS outputs MP3)
    if progress_cb: progress_cb(0.5, "Merging audio...")
    
    # First convert each MP3 to WAV with consistent format
    wav_files = []
    for i, s in enumerate(segments):
        wav_path = str(temp / f"audio_{i}.wav")
        run_cmd([
            "ffmpeg", "-y", "-i", s['audio'],
            "-ar", "24000", "-ac", "1", "-c:a", "pcm_s16le",
            wav_path
        ], f"convert audio {i}")
        wav_files.append(wav_path)
        s['audio_wav'] = wav_path
    
    audio_list = temp / "audio.txt"
    with open(audio_list, "w") as f:
        for wav in wav_files:
            f.write(f"file '{wav}'\n")
    
    merged = str(temp / "merged.wav")
    run_cmd(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(audio_list), 
             "-c:a", "pcm_s16le", merged], "merge audio")
    
    # 2. Create individual video segments for each speaker line (NO CAPTIONS)
    if progress_cb: progress_cb(0.6, "Building video segments...")
    
    segment_videos = []
    
    for i, s in enumerate(segments):
        seg_out = str(temp / f"seg_{i}.mp4")
        template = tmpl1 if "1" in s['speaker'] else tmpl2
        duration = s['duration']
        
        # Simple filter - just scale, loop, and trim (no captions)
        filter_str = (
            f"[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,"
            f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2,"
            f"loop=loop=-1:size=32767,trim=duration={duration},setpts=PTS-STARTPTS[outv]"
        )
        
        run_cmd([
            "ffmpeg", "-y",
            "-i", template,
            "-filter_complex", filter_str,
            "-map", "[outv]",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
            "-t", str(duration),
            "-an",
            seg_out
        ], f"segment {i}")
        
        segment_videos.append(seg_out)
    
    if progress_cb: progress_cb(0.75, "Joining segments...")
    
    # 3. Concat all video segments
    video_list = temp / "videos.txt"
    with open(video_list, "w") as f:
        for v in segment_videos:
            f.write(f"file '{v}'\n")
    
    main_video = str(temp / "main.mp4")
    run_cmd([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(video_list),
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
        main_video
    ], "concat videos")
    
    # 4. Add skit audio to main video
    if progress_cb: progress_cb(0.8, "Adding skit audio...")
    
    main_with_audio = str(temp / "main_with_audio.mp4")
    run_cmd([
        "ffmpeg", "-y",
        "-i", main_video,
        "-i", merged,
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        main_with_audio
    ], "add skit audio")
    
    # 5. Scale closing template (KEEP ITS AUDIO)
    if progress_cb: progress_cb(0.85, "Adding closing...")
    
    closing_scaled = str(temp / "closing_scaled.mp4")
    run_cmd([
        "ffmpeg", "-y", "-i", closing,
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        closing_scaled
    ], "scale closing")
    
    # 6. Concat main (with skit audio) + closing (with its own audio)
    if progress_cb: progress_cb(0.9, "Final assembly...")
    
    # Use ffmpeg concat filter for videos with different audio
    run_cmd([
        "ffmpeg", "-y",
        "-i", main_with_audio,
        "-i", closing_scaled,
        "-filter_complex", 
        "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[outv][outa]",
        "-map", "[outv]",
        "-map", "[outa]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        output
    ], "final concat")
    
    if progress_cb: progress_cb(1.0, "Done!")

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    # Header with logo
    st.markdown(f"""
    <div class="header-container">
        <img src="{LOGO_URL}" class="logo-img" alt="Pawdcast Logo">
        <div>
            <h1 class="main-title">Pawdcast Skit Factory</h1>
            <p class="subtitle">Transform articles into podcast videos instantly</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Check FFmpeg
    if not check_ffmpeg():
        st.error("⚠️ FFmpeg not available. Please contact administrator.")
        return
    
    # Sidebar
    with st.sidebar:
        st.markdown(f'<img src="{LOGO_URL}" style="width: 50px; border-radius: 12px; margin-bottom: 1rem;">', unsafe_allow_html=True)
        st.markdown("### ⚙️ Settings")
        
        # API Key
        api_key = ""
        if hasattr(st, 'secrets') and st.secrets and "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.markdown('<span class="badge badge-success">✓ API Ready</span>', unsafe_allow_html=True)
        else:
            api_key = st.text_input("Gemini API Key", type="password")
            if api_key:
                st.markdown('<span class="badge badge-success">✓ Key Set</span>', unsafe_allow_html=True)
            else:
                st.markdown('[Get free key →](https://aistudio.google.com/app/apikey)')
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # Voices
        st.markdown("### 🎙️ Voices")
        voice1 = st.selectbox("Speaker 1", list(VOICE_OPTIONS.keys()), index=0)
        voice2 = st.selectbox("Speaker 2", list(VOICE_OPTIONS.keys()), index=1)
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # Templates
        st.markdown("### 🎬 Video Templates")
        st.caption("Upload 1920×1080 MP4 files")
        
        tmpl1 = st.file_uploader("Speaker 1", type=["mp4"], key="t1")
        tmpl2 = st.file_uploader("Speaker 2", type=["mp4"], key="t2")
        tmpl_c = st.file_uploader("Closing", type=["mp4"], key="tc")
        
        ready = all([tmpl1, tmpl2, tmpl_c])
        if ready:
            st.markdown('<span class="badge badge-success">✓ Templates Ready</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="badge badge-warning">⚠ Upload all 3</span>', unsafe_allow_html=True)
    
    # Main content
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<p class="section-header">📝 Article</p>', unsafe_allow_html=True)
        
        # Option to skip skit generation
        skip_skit = st.checkbox("⚡ Skip AI generation (paste your own skit)", 
                                help="Check this to paste a pre-written skit and skip the API call - 100% FREE!")
        
        if skip_skit:
            st.info("💡 Paste your skit in the right panel. Format: `Speaker 1: \"...\"` and `Speaker 2: \"...\"`")
            article = ""
        else:
            article = st.text_area(
                "Article",
                height=280,
                placeholder="Paste your news article here...\n\nThe AI will transform it into a podcast dialogue.",
                label_visibility="collapsed"
            )
            if article:
                word_count = len(article.split())
                st.caption(f"📊 {word_count} words")
    
    with col2:
        st.markdown('<p class="section-header">📜 Skit</p>', unsafe_allow_html=True)
        
        if skip_skit:
            # Editable skit area when skipping AI generation
            skit_input = st.text_area(
                "Skit",
                height=320,
                placeholder='''Paste your skit here in this format:

Speaker 1: "Your opening line here..."
Speaker 2: "Response line here..."
Speaker 1: "Next line..."
Speaker 2: "And so on..."''',
                label_visibility="collapsed"
            )
        else:
            # Read-only preview when using AI generation
            skit_input = ""
            skit_area = st.empty()
            skit_area.text_area(
                "Skit",
                value="Your skit will appear here after AI generation...",
                height=320,
                disabled=True,
                label_visibility="collapsed"
            )
    
    # Create button
    st.markdown("<br>", unsafe_allow_html=True)
    _, btn_col, _ = st.columns([1, 2, 1])
    with btn_col:
        create = st.button("🚀 Create Pawdcast", use_container_width=True)
    
    # Process
    if create:
        # Validation - different requirements based on mode
        errors = []
        if skip_skit:
            if not skit_input.strip():
                errors.append("Paste your skit in the right panel")
        else:
            if not api_key:
                errors.append("API key required (or use 'Skip AI generation' option)")
            if not article.strip():
                errors.append("Article required")
        if not ready:
            errors.append("All templates required")
        
        if errors:
            st.error("❌ " + " • ".join(errors))
            return
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            progress = st.progress(0)
            status = st.empty()
            
            try:
                t0 = time.time()
                
                # 1. Get skit (either from AI or pasted)
                if skip_skit:
                    # Use pasted skit directly - NO API CALL!
                    status.info("📜 Using your pasted skit...")
                    progress.progress(0.15)
                    skit = skit_input
                else:
                    # Generate with AI
                    status.info("🤖 Generating skit...")
                    progress.progress(0.1)
                    skit = generate_skit(article, api_key)
                    skit_area.text_area("Skit", skit, height=320, label_visibility="collapsed")
                
                lines = parse_skit(skit)
                if not lines:
                    st.error("❌ Could not parse skit. Make sure format is: Speaker 1: \"...\" Speaker 2: \"...\"")
                    st.code(skit)
                    return
                
                progress.progress(0.2)
                
                # 2. Save templates
                status.info("💾 Processing templates...")
                t1_path = str(tmp / "t1.mp4")
                t2_path = str(tmp / "t2.mp4")
                tc_path = str(tmp / "tc.mp4")
                
                with open(t1_path, "wb") as f: f.write(tmpl1.read())
                with open(t2_path, "wb") as f: f.write(tmpl2.read())
                with open(tc_path, "wb") as f: f.write(tmpl_c.read())
                
                progress.progress(0.2)
                
                # 3. Generate TTS (FREE with Edge TTS!)
                segments = []
                for i, (spk, txt) in enumerate(lines):
                    pct = 0.2 + (i / len(lines)) * 0.25
                    progress.progress(pct)
                    status.info(f"🎙️ Generating voice {i+1}/{len(lines)}...")
                    
                    voice = VOICE_OPTIONS[voice1] if "1" in spk else VOICE_OPTIONS[voice2]
                    audio = str(tmp / f"a{i}.mp3")
                    generate_audio(txt, voice, audio)
                    
                    segments.append({
                        "speaker": spk,
                        "text": txt,
                        "audio": audio,
                        "duration": get_duration(audio)
                    })
                
                # 4. Create video
                def update(pct, msg):
                    progress.progress(pct)
                    status.info(f"🎬 {msg}")
                
                output = str(tmp / "pawdcast.mp4")
                create_video(segments, t1_path, t2_path, tc_path, output, update)
                
                # Read result
                with open(output, "rb") as f:
                    video_bytes = f.read()
                
                elapsed = time.time() - t0
                progress.progress(1.0)
                status.success(f"✅ Created in {elapsed:.0f} seconds!")
                
                # Results
                st.markdown("---")
                st.markdown("### 🎉 Your Pawdcast is Ready!")
                
                st.markdown('<div class="video-container">', unsafe_allow_html=True)
                st.video(video_bytes)
                st.markdown('</div>', unsafe_allow_html=True)
                
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                c1, c2 = st.columns(2)
                with c1:
                    st.download_button(
                        "📥 Download Video",
                        video_bytes,
                        f"pawdcast_{ts}.mp4",
                        "video/mp4",
                        use_container_width=True
                    )
                with c2:
                    st.download_button(
                        "📄 Download Script",
                        skit,
                        f"pawdcast_{ts}.txt",
                        "text/plain",
                        use_container_width=True
                    )
                
                st.markdown(f"""
                <div class="info-card">
                    <strong>📊 Video Stats</strong><br>
                    Resolution: 1920×1080 • Lines: {len(lines)} • Time: {elapsed:.0f}s<br>
                    <span style="color: {'#10b981' if skip_skit else '#f7931a'}">
                        {'✓ 100% FREE (no API used)' if skip_skit else '• 1 API call (skit generation)'}
                    </span>
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"❌ {e}")
                import traceback
                with st.expander("Show details"):
                    st.code(traceback.format_exc())
    
    # Footer
    st.markdown("""
    <div class="footer">
        <div class="divider"></div>
        Made with 🧡 for <a href="https://news.shib.io" target="_blank">The Shib Daily</a><br>
        Powered by Gemini AI
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
