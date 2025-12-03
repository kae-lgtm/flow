"""
🐕 Pawdcast Skit Factory - Fully Automated Edition
One-click article to video conversion, just like MakeReels.ai

User Flow:
1. Paste article text
2. Click "Create Pawdcast"
3. Download ready-to-publish 16:9 video

Tech Stack:
- Streamlit Cloud (free hosting with server-side FFmpeg)
- Gemini 3 Pro Preview (skit generation)
- Gemini 2.5 Flash Preview TTS (multi-speaker audio)
- FFmpeg (fast server-side video rendering)
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
import zipfile
import io

# ============================================================================
# PAGE CONFIG & THEME
# ============================================================================

st.set_page_config(
    page_title="Pawdcast Skit Factory",
    page_icon="🐕",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
/* Dark Shib theme */
.stApp {
    background: linear-gradient(135deg, #0a0a14 0%, #12121f 50%, #0f1018 100%);
}

/* Title styling */
.main-title {
    font-size: 2.6rem;
    font-weight: 800;
    text-align: center;
    background: linear-gradient(90deg, #f7931a 0%, #ff6b35 50%, #f7931a 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem;
}

.subtitle {
    color: #888;
    text-align: center;
    font-size: 1rem;
    margin-bottom: 1.5rem;
}

/* Big orange CTA button */
.stButton > button {
    background: linear-gradient(90deg, #f7931a, #ff6b35) !important;
    color: white !important;
    font-size: 1.3rem !important;
    font-weight: bold !important;
    padding: 0.8rem 2rem !important;
    border: none !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 15px rgba(247, 147, 26, 0.4) !important;
    transition: all 0.2s ease !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(247, 147, 26, 0.5) !important;
}

/* Status badges */
.badge-success {
    display: inline-block;
    background: rgba(34, 197, 94, 0.2);
    border: 1px solid #22c55e;
    color: #22c55e;
    padding: 0.3rem 0.7rem;
    border-radius: 20px;
    font-size: 0.85rem;
}

.badge-warning {
    display: inline-block;
    background: rgba(251, 191, 36, 0.2);
    border: 1px solid #fbbf24;
    color: #fbbf24;
    padding: 0.3rem 0.7rem;
    border-radius: 20px;
    font-size: 0.85rem;
}

/* Info cards */
.info-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 1rem;
    margin: 0.5rem 0;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%);
}

/* Download buttons */
.stDownloadButton > button {
    background: linear-gradient(90deg, #22c55e, #16a34a) !important;
}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CONFIGURATION
# ============================================================================

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

# Voice options
VOICE_OPTIONS = {
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

# Models - using stable versions
SKIT_MODEL = "gemini-2.0-flash"  # Stable and fast
TTS_MODEL = "gemini-2.5-flash-preview-tts"

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
    
    # Try standard quote format
    pattern = r'Speaker\s*(\d+)\s*:\s*["""]([^"""]+)["""]'
    matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
    
    if not matches:
        # Try alternate format without quotes
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
        
        # Check if response has text
        if response and response.text:
            return response.text
        elif response and response.candidates:
            # Try to get text from candidates
            for candidate in response.candidates:
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, 'text') and part.text:
                            return part.text
        
        raise Exception("Gemini returned empty response. Try again.")
        
    except Exception as e:
        raise Exception(f"Skit generation failed: {str(e)}")

def generate_audio(text, voice, api_key, output_path):
    """Generate TTS audio using Gemini."""
    try:
        client = genai.Client(api_key=api_key)
        
        response = client.models.generate_content(
            model=TTS_MODEL,
            contents=f'Say this in a warm, engaging podcast host tone: "{text}"',
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice
                        )
                    )
                )
            )
        )
        
        # Get the audio data from response
        audio_part = response.candidates[0].content.parts[0]
        audio_data = audio_part.inline_data.data
        
        # Handle if data is already bytes or needs decoding
        if isinstance(audio_data, bytes):
            pcm_data = audio_data
        elif isinstance(audio_data, str):
            # Fix padding if needed
            missing_padding = len(audio_data) % 4
            if missing_padding:
                audio_data += '=' * (4 - missing_padding)
            pcm_data = base64.b64decode(audio_data)
        else:
            raise Exception(f"Unexpected audio data type: {type(audio_data)}")
        
        # Save as WAV (24kHz, 16-bit, mono)
        with wave.open(output_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(pcm_data)
        
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

def escape_ffmpeg(text):
    """Escape text for FFmpeg drawtext."""
    for char in ["\\", "'", ":", ",", "[", "]", ";", "="]:
        text = text.replace(char, f"\\{char}")
    return text

def wrap_text(text, max_len=40):
    """Word wrap for captions."""
    words = text.split()
    lines, line = [], []
    for word in words:
        line.append(word)
        if len(" ".join(line)) > max_len:
            lines.append(" ".join(line[:-1]))
            line = [word]
    if line:
        lines.append(" ".join(line))
    return "\\n".join(lines)

def create_video(segments, tmpl1, tmpl2, closing, output, progress_cb=None):
    """Assemble final video with FFmpeg."""
    temp = Path(output).parent
    
    # 1. Merge all audio
    if progress_cb: progress_cb(0.5, "Merging audio...")
    
    audio_list = temp / "audio.txt"
    with open(audio_list, "w") as f:
        for s in segments:
            f.write(f"file '{s['audio']}'\n")
    
    merged = str(temp / "merged.wav")
    run_cmd(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(audio_list), 
             "-c:a", "pcm_s16le", merged], "merge audio")
    
    total_dur = get_duration(merged)
    
    # Calculate timestamps
    t = 0
    for s in segments:
        s['start'], s['end'] = t, t + s['duration']
        t = s['end']
    
    # 2. Build filter graph - using simpler approach
    if progress_cb: progress_cb(0.6, "Building video...")
    
    # Create individual video segments for each speaker line
    segment_videos = []
    
    for i, s in enumerate(segments):
        seg_out = str(temp / f"seg_{i}.mp4")
        template = tmpl1 if "1" in s['speaker'] else tmpl2
        duration = s['duration']
        caption = s['text'].replace("'", "'\\''").replace(":", "\\:")
        
        # Word wrap caption
        words = caption.split()
        lines = []
        line = []
        for word in words:
            line.append(word)
            if len(" ".join(line)) > 40:
                lines.append(" ".join(line[:-1]))
                line = [word]
        if line:
            lines.append(" ".join(line))
        caption_wrapped = "\\n".join(lines)
        
        # Create segment with caption
        filter_str = (
            f"[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,"
            f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2,"
            f"loop=loop=-1:size=32767,trim=duration={duration},setpts=PTS-STARTPTS,"
            f"drawtext=text='{caption_wrapped}':fontsize=64:fontcolor=white:"
            f"borderw=3:bordercolor=black:x=(w-text_w)/2:y=h*0.75[outv]"
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
    
    # 3. Create concat list for video segments
    video_list = temp / "videos.txt"
    with open(video_list, "w") as f:
        for v in segment_videos:
            f.write(f"file '{v}'\n")
    
    # Concat all video segments
    main_video = str(temp / "main.mp4")
    run_cmd([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(video_list),
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
        main_video
    ], "concat videos")
    
    # 4. Add closing template
    if progress_cb: progress_cb(0.85, "Adding closing...")
    
    # Scale closing
    closing_scaled = str(temp / "closing_scaled.mp4")
    run_cmd([
        "ffmpeg", "-y", "-i", closing,
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
        "-an",
        closing_scaled
    ], "scale closing")
    
    # Concat main + closing
    final_video_list = temp / "final_videos.txt"
    with open(final_video_list, "w") as f:
        f.write(f"file '{main_video}'\n")
        f.write(f"file '{closing_scaled}'\n")
    
    video_no_audio = str(temp / "video_no_audio.mp4")
    run_cmd([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(final_video_list),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        video_no_audio
    ], "concat final")
    
    # 5. Create silent audio for closing and merge
    if progress_cb: progress_cb(0.9, "Adding audio...")
    
    close_dur = get_duration(closing)
    silent = str(temp / "silent.wav")
    run_cmd(["ffmpeg", "-y", "-f", "lavfi", 
             "-i", f"anullsrc=r=24000:cl=mono:d={close_dur}",
             "-c:a", "pcm_s16le", silent], "silent")
    
    # Concat all audio
    final_audio_list = temp / "final_audio.txt"
    with open(final_audio_list, "w") as f:
        f.write(f"file '{merged}'\n")
        f.write(f"file '{silent}'\n")
    
    final_audio = str(temp / "final_audio.wav")
    run_cmd(["ffmpeg", "-y", "-f", "concat", "-safe", "0", 
             "-i", str(final_audio_list),
             "-c:a", "pcm_s16le", final_audio], "concat audio")
    
    # 6. Merge video and audio
    run_cmd([
        "ffmpeg", "-y",
        "-i", video_no_audio,
        "-i", final_audio,
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        output
    ], "final merge")
    
    if progress_cb: progress_cb(1.0, "Done!")

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    # Header
    st.markdown('<h1 class="main-title">🐕 Pawdcast Skit Factory</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Paste article → Get video • Fully automated like MakeReels.ai</p>', unsafe_allow_html=True)
    
    # Check FFmpeg
    if not check_ffmpeg():
        st.error("⚠️ FFmpeg not available. Contact administrator.")
        return
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # API Key
        api_key = ""
        if hasattr(st, 'secrets') and st.secrets and "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.markdown('<span class="badge-success">✅ API Key Ready</span>', unsafe_allow_html=True)
        else:
            api_key = st.text_input("Gemini API Key", type="password",
                                    help="Get free at aistudio.google.com")
            if api_key:
                st.markdown('<span class="badge-success">✅ Key entered</span>', unsafe_allow_html=True)
            else:
                st.markdown('[Get free API key →](https://aistudio.google.com/app/apikey)')
        
        st.divider()
        
        # Voices
        st.subheader("🎙️ Voices")
        voice1 = st.selectbox("Speaker 1", list(VOICE_OPTIONS.keys()), index=0)
        voice2 = st.selectbox("Speaker 2", list(VOICE_OPTIONS.keys()), index=1)
        
        st.divider()
        
        # Templates
        st.subheader("🎬 Templates (16:9)")
        tmpl1 = st.file_uploader("Speaker 1 video", type=["mp4"], key="t1")
        tmpl2 = st.file_uploader("Speaker 2 video", type=["mp4"], key="t2")
        tmpl_c = st.file_uploader("Closing video", type=["mp4"], key="tc")
        
        ready = all([tmpl1, tmpl2, tmpl_c])
        if ready:
            st.markdown('<span class="badge-success">✅ Templates ready</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="badge-warning">⚠️ Upload all 3</span>', unsafe_allow_html=True)
    
    # Main area
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📝 Article")
        article = st.text_area("Paste article", height=350, 
                               placeholder="Paste your news article here...",
                               label_visibility="collapsed")
    
    with col2:
        st.subheader("📜 Skit Preview")
        skit_area = st.empty()
        skit_area.text_area("Skit", "Skit will appear here...", height=350,
                           disabled=True, label_visibility="collapsed")
    
    # Create button
    st.markdown("<br>", unsafe_allow_html=True)
    _, btn_col, _ = st.columns([1, 2, 1])
    with btn_col:
        create = st.button("🚀 CREATE PAWDCAST", use_container_width=True)
    
    # Process
    if create:
        # Validate
        errors = []
        if not api_key: errors.append("API key required")
        if not article.strip(): errors.append("Article required")
        if not ready: errors.append("All templates required")
        
        if errors:
            st.error("❌ " + " • ".join(errors))
            return
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            progress = st.progress(0)
            status = st.empty()
            
            try:
                t0 = time.time()
                
                # 1. Generate skit
                status.info("🤖 Generating skit...")
                progress.progress(0.1)
                
                skit = generate_skit(article, api_key)
                skit_area.text_area("Skit", skit, height=350, label_visibility="collapsed")
                
                lines = parse_skit(skit)
                if not lines:
                    st.error("❌ Could not parse skit. Try again.")
                    st.code(skit)
                    return
                
                progress.progress(0.15)
                
                # 2. Save templates
                status.info("💾 Processing templates...")
                t1_path = str(tmp / "t1.mp4")
                t2_path = str(tmp / "t2.mp4")
                tc_path = str(tmp / "tc.mp4")
                
                with open(t1_path, "wb") as f: f.write(tmpl1.read())
                with open(t2_path, "wb") as f: f.write(tmpl2.read())
                with open(tc_path, "wb") as f: f.write(tmpl_c.read())
                
                progress.progress(0.2)
                
                # 3. Generate TTS
                segments = []
                for i, (spk, txt) in enumerate(lines):
                    pct = 0.2 + (i / len(lines)) * 0.25
                    progress.progress(pct)
                    status.info(f"🎙️ Voice {i+1}/{len(lines)}...")
                    
                    voice = VOICE_OPTIONS[voice1] if "1" in spk else VOICE_OPTIONS[voice2]
                    audio = str(tmp / f"a{i}.wav")
                    generate_audio(txt, voice, api_key, audio)
                    
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
                status.success(f"✅ Done in {elapsed:.0f}s!")
                
                # Show results
                st.header("🎉 Your Pawdcast")
                st.video(video_bytes)
                
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                c1, c2 = st.columns(2)
                with c1:
                    st.download_button("📥 Download MP4", video_bytes,
                                      f"pawdcast_{ts}.mp4", "video/mp4",
                                      use_container_width=True)
                with c2:
                    st.download_button("📥 Download Script", skit,
                                      f"pawdcast_{ts}.txt", "text/plain",
                                      use_container_width=True)
                
                st.info(f"📊 {len(lines)} lines • {elapsed:.0f}s • 1920×1080")
                
            except Exception as e:
                st.error(f"❌ {e}")
                import traceback
                with st.expander("Details"):
                    st.code(traceback.format_exc())
    
    # Footer
    st.markdown("---")
    st.caption("Made for [The Shib Daily](https://news.shib.io) • Powered by Gemini AI")

if __name__ == "__main__":
    main()
