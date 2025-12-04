import streamlit as st
import tempfile
import os
import subprocess
import traceback
from pathlib import Path

# ============================================================================
# PAWDCAST — CONTEMPORARY MINIMALIST DESIGN
# ============================================================================
st.set_page_config(page_title="Pawdcast", page_icon="🎙️", layout="centered")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* Base */
    .stApp { 
        background: linear-gradient(180deg, #fafafa 0%, #ffffff 100%); 
        color: #1a1a2e; 
        font-family: 'Inter', -apple-system, sans-serif; 
    }
    .block-container { max-width: 720px; padding: 2rem 1.5rem; }
    
    /* Hide Streamlit defaults */
    #MainMenu, footer, header { visibility: hidden; }
    .stDeployButton { display: none; }
    
    /* Header — Logo LEFT of Title */
    .header-container {
        display: flex;
        flex-direction: row;
        align-items: center;
        justify-content: center;
        text-align: left;
        padding: 2.5rem 0 1.5rem;
        gap: 1.25rem;
    }
    
    .logo-wrapper {
        width: 72px;
        height: 72px;
        min-width: 72px;
        border-radius: 18px;
        overflow: hidden;
        box-shadow: 0 16px 50px rgba(249, 115, 22, 0.25), 0 6px 16px rgba(0,0,0,0.08);
        transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1);
    }
    .logo-wrapper:hover {
        transform: translateY(-3px) scale(1.05);
        box-shadow: 0 24px 60px rgba(249, 115, 22, 0.35), 0 10px 25px rgba(0,0,0,0.12);
    }
    .logo-wrapper img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    
    .header-text {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }
    
    .brand-title {
        font-size: 2.75rem;
        font-weight: 800;
        background: linear-gradient(135deg, #f97316 0%, #ea580c 50%, #c2410c 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        letter-spacing: -1.5px;
        line-height: 1;
    }
    
    .brand-subtitle {
        font-size: 1rem;
        color: #64748b;
        font-weight: 500;
        margin: 0;
        letter-spacing: -0.2px;
    }
    
    /* Mode Pills */
    .stRadio > div { 
        display: flex; 
        gap: 0.75rem; 
        justify-content: center;
        flex-wrap: wrap;
        padding: 0.5rem 0;
    }
    .stRadio > div > label { 
        background: #ffffff; 
        border-radius: 100px; 
        padding: 0.75rem 1.5rem; 
        border: 1.5px solid #e2e8f0; 
        font-weight: 600; 
        font-size: 0.9rem;
        transition: all 0.3s cubic-bezier(0.23, 1, 0.32, 1);
        cursor: pointer;
    }
    .stRadio > div > label:hover { 
        border-color: #f97316; 
        background: #fff7ed;
    }
    .stRadio > div > label[data-checked="true"] { 
        border-color: #f97316; 
        background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%);
        box-shadow: 0 4px 15px rgba(249, 115, 22, 0.2);
    }
    
    /* Cards */
    .card {
        background: #ffffff;
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
        border: 1px solid #f1f5f9;
        box-shadow: 0 4px 20px rgba(0,0,0,0.04);
        transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
    }
    .card:hover {
        box-shadow: 0 12px 40px rgba(0,0,0,0.08);
        transform: translateY(-2px);
    }
    
    .card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid #f1f5f9;
    }
    
    .card-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #1a1a2e;
        margin: 0;
    }
    
    .badge {
        background: linear-gradient(135deg, #f97316, #ea580c);
        color: white;
        padding: 0.4rem 1rem;
        border-radius: 100px;
        font-weight: 700;
        font-size: 0.75rem;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    
    .badge-coming {
        background: linear-gradient(135deg, #6366f1, #4f46e5);
    }
    
    /* Inputs */
    .stTextArea textarea, .stTextInput input {
        border-radius: 14px !important;
        border: 1.5px solid #e2e8f0 !important;
        padding: 1rem !important;
        font-size: 0.95rem !important;
        transition: all 0.3s !important;
        background: #fafafa !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #f97316 !important;
        box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.1) !important;
        background: #ffffff !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #f97316 0%, #ea580c 100%) !important;
        color: white !important;
        font-weight: 700 !important;
        height: 3.25rem !important;
        border-radius: 14px !important;
        width: 100% !important;
        border: none !important;
        font-size: 1rem !important;
        letter-spacing: -0.3px !important;
        box-shadow: 0 8px 25px rgba(249, 115, 22, 0.35) !important;
        transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1) !important;
    }
    .stButton > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 16px 40px rgba(249, 115, 22, 0.45) !important;
    }
    .stButton > button:active {
        transform: translateY(-1px) !important;
    }
    
    /* File Uploader */
    .stFileUploader {
        border-radius: 14px;
    }
    .stFileUploader > div > div {
        border-radius: 14px !important;
        border: 2px dashed #e2e8f0 !important;
        background: #fafafa !important;
        transition: all 0.3s !important;
    }
    .stFileUploader > div > div:hover {
        border-color: #f97316 !important;
        background: #fff7ed !important;
    }
    
    /* Select boxes */
    .stSelectbox > div > div {
        border-radius: 14px !important;
        border: 1.5px solid #e2e8f0 !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        border-radius: 14px !important;
        background: #fafafa !important;
        font-weight: 600 !important;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        margin-top: 4rem;
        padding: 2rem 0;
        border-top: 1px solid #f1f5f9;
    }
    .footer-text {
        color: #94a3b8;
        font-size: 0.85rem;
        font-weight: 500;
    }
    .footer-link {
        color: #f97316;
        text-decoration: none;
        font-weight: 600;
        transition: color 0.3s;
    }
    .footer-link:hover {
        color: #ea580c;
    }
    
    /* Progress */
    .stProgress > div > div {
        background: linear-gradient(135deg, #f97316, #ea580c) !important;
        border-radius: 100px !important;
    }
    
    /* Success/Info boxes */
    .stSuccess, .stInfo {
        border-radius: 14px !important;
    }
    
    /* Divider */
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# HEADER — LOGO LEFT OF TITLE
# ============================================================================
st.markdown("""
<div class="header-container">
    <div class="logo-wrapper">
        <img src="https://news.shib.io/wp-content/uploads/2025/12/Black-White-Simple-Modern-Neon-Griddy-Bold-Technology-Pixel-Electronics-Store-Logo-1.png" alt="Pawdcast">
    </div>
    <div class="header-text">
        <h1 class="brand-title">Pawdcast</h1>
        <p class="brand-subtitle">Create professional podcast videos in seconds</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# MODE SELECTOR
# ============================================================================
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
mode = st.radio("Choose your mode", ["Manual", "Skit Mode", "Full Auto"], horizontal=True, label_visibility="collapsed")
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ============================================================================
# MANUAL MODE — FULLY WORKING
# ============================================================================
if mode == "Manual":
    st.markdown("""
    <div class="card">
        <div class="card-header">
            <h3 class="card-title">Manual Mode</h3>
            <span class="badge">FREE FOREVER</span>
        </div>
        <p style="color:#64748b; margin:0; font-size:0.95rem;">Upload your own audio and background — full creative control</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        audio_file = st.file_uploader("🎵 Audio File", type=["mp3", "wav", "m4a"], help="Your podcast audio")
    
    with col2:
        bg_file = st.file_uploader("🖼️ Background", type=["mp4", "jpg", "png", "gif"], help="Video or image background")
    
    # Advanced options
    with st.expander("⚙️ Advanced Settings"):
        col_a, col_b = st.columns(2)
        with col_a:
            output_format = st.selectbox("Output Format", ["mp4", "mov", "webm"])
        with col_b:
            quality = st.selectbox("Quality", ["High (1080p)", "Medium (720p)", "Low (480p)"])
    
    if st.button("🚀 Generate Video", use_container_width=True):
        if audio_file and bg_file:
            with st.spinner("Creating your masterpiece..."):
                try:
                    with tempfile.TemporaryDirectory() as tmp_dir:
                        audio_path = os.path.join(tmp_dir, f"audio.{audio_file.name.split('.')[-1]}")
                        bg_path = os.path.join(tmp_dir, f"bg.{bg_file.name.split('.')[-1]}")
                        output_path = os.path.join(tmp_dir, f"output.{output_format}")
                        
                        with open(audio_path, "wb") as f:
                            f.write(audio_file.read())
                        with open(bg_path, "wb") as f:
                            f.write(bg_file.read())
                        
                        probe_cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{audio_path}"'
                        duration = float(subprocess.check_output(probe_cmd, shell=True).decode().strip())
                        
                        quality_map = {
                            "High (1080p)": "1920:1080",
                            "Medium (720p)": "1280:720",
                            "Low (480p)": "854:480"
                        }
                        resolution = quality_map.get(quality, "1920:1080")
                        
                        bg_ext = bg_file.name.split('.')[-1].lower()
                        
                        if bg_ext in ['mp4', 'mov', 'webm', 'gif']:
                            ffmpeg_cmd = f'''ffmpeg -y -stream_loop -1 -i "{bg_path}" -i "{audio_path}" \
                                -vf "scale={resolution}:force_original_aspect_ratio=decrease,pad={resolution}:(ow-iw)/2:(oh-ih)/2" \
                                -c:v libx264 -preset fast -crf 23 \
                                -c:a aac -b:a 192k \
                                -t {duration} -shortest \
                                "{output_path}"'''
                        else:
                            ffmpeg_cmd = f'''ffmpeg -y -loop 1 -i "{bg_path}" -i "{audio_path}" \
                                -vf "scale={resolution}:force_original_aspect_ratio=decrease,pad={resolution}:(ow-iw)/2:(oh-ih)/2" \
                                -c:v libx264 -preset fast -crf 23 \
                                -c:a aac -b:a 192k \
                                -t {duration} -shortest \
                                "{output_path}"'''
                        
                        result = subprocess.run(ffmpeg_cmd, shell=True, capture_output=True, text=True)
                        
                        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                            with open(output_path, "rb") as f:
                                video_bytes = f.read()
                            
                            st.success("✨ Video created successfully!")
                            st.video(video_bytes)
                            st.download_button(
                                label="📥 Download Video",
                                data=video_bytes,
                                file_name=f"pawdcast_output.{output_format}",
                                mime=f"video/{output_format}",
                                use_container_width=True
                            )
                        else:
                            st.error("Video generation failed. Check your files.")
                            if result.stderr:
                                with st.expander("Error details"):
                                    st.code(result.stderr)
                                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    with st.expander("Debug info"):
                        st.code(traceback.format_exc())
        else:
            st.warning("Please upload both an audio file and a background.")

# ============================================================================
# SKIT MODE
# ============================================================================
elif mode == "Skit Mode":
    st.markdown("""
    <div class="card">
        <div class="card-header">
            <h3 class="card-title">Skit Mode</h3>
            <span class="badge">LIVE</span>
        </div>
        <p style="color:#64748b; margin:0; font-size:0.95rem;">Write a script, we'll generate the conversation</p>
    </div>
    """, unsafe_allow_html=True)
    
    script = st.text_area(
        "Your Script",
        placeholder="HOST: Welcome to the show!\nGUEST: Thanks for having me!\nHOST: Let's dive in...",
        height=200,
        label_visibility="collapsed"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        host_voice = st.selectbox("Host Voice", ["Professional Male", "Professional Female", "Casual Male", "Casual Female"])
    with col2:
        guest_voice = st.selectbox("Guest Voice", ["Professional Female", "Professional Male", "Casual Female", "Casual Male"])
    
    bg_file = st.file_uploader("🖼️ Background (optional)", type=["mp4", "jpg", "png", "gif"])
    
    if st.button("🎬 Generate Skit", use_container_width=True):
        if script.strip():
            st.info("🎙️ Skit Mode requires TTS integration. Connect your preferred TTS API in settings.")
            
            lines = [l.strip() for l in script.split('\n') if l.strip()]
            
            with st.expander("📜 Script Preview"):
                for line in lines:
                    if ':' in line:
                        speaker, text = line.split(':', 1)
                        st.markdown(f"**{speaker.strip()}:** {text.strip()}")
                    else:
                        st.markdown(line)
            
            st.success("Script parsed! Connect TTS to generate audio.")
        else:
            st.warning("Please write a script first.")

# ============================================================================
# FULL AUTO MODE
# ============================================================================
else:
    st.markdown("""
    <div class="card">
        <div class="card-header">
            <h3 class="card-title">Full Auto Mode</h3>
            <span class="badge badge-coming">PRO</span>
        </div>
        <p style="color:#64748b; margin:0; font-size:0.95rem;">AI generates everything from a single topic</p>
    </div>
    """, unsafe_allow_html=True)
    
    topic = st.text_input(
        "Topic",
        placeholder="e.g., The future of cryptocurrency in 2025",
        label_visibility="collapsed"
    )
    
    col1, col2, col3 = st.columns(3)
    with col1:
        duration = st.selectbox("Duration", ["1-2 minutes", "3-5 minutes", "5-10 minutes"])
    with col2:
        style = st.selectbox("Style", ["Professional", "Casual", "Educational", "Entertainment"])
    with col3:
        voices = st.selectbox("Voices", ["Solo Host", "Two Hosts", "Interview Style"])
    
    with st.expander("🎨 Customize"):
        tone = st.select_slider("Tone", options=["Serious", "Balanced", "Light", "Fun"])
        include_music = st.checkbox("Include background music", value=True)
        include_sfx = st.checkbox("Include sound effects", value=False)
    
    if st.button("✨ Generate Full Podcast", use_container_width=True):
        if topic.strip():
            progress = st.progress(0)
            status = st.empty()
            
            steps = [
                ("🧠 Generating script...", 20),
                ("🎙️ Creating voiceover...", 40),
                ("🎨 Preparing visuals...", 60),
                ("🎬 Rendering video...", 80),
                ("✅ Finalizing...", 100)
            ]
            
            for step_text, step_progress in steps:
                status.text(step_text)
                progress.progress(step_progress)
                import time
                time.sleep(0.8)
            
            st.success("🎉 Full Auto requires AI + TTS integration. Connect your APIs in settings!")
            
            st.markdown("""
            <div class="card" style="background: #f8fafc;">
                <p style="margin:0; color:#64748b; font-size:0.9rem;"><strong>Preview of what will be generated:</strong></p>
                <ul style="color:#64748b; font-size:0.9rem; margin-top:0.5rem;">
                    <li>AI-written script based on your topic</li>
                    <li>Professional voiceover with selected voices</li>
                    <li>Auto-generated or stock visuals</li>
                    <li>Background music and transitions</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("Please enter a topic.")

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("""
<div class="footer">
    <p class="footer-text">
        Crafted with precision for 
        <a href="https://news.shib.io" class="footer-link" target="_blank">The Shib Daily</a>
    </p>
</div>
""", unsafe_allow_html=True)
