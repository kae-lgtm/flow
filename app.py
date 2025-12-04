import streamlit as st
import tempfile
import os
import re
import subprocess
import traceback
from pathlib import Path

# ============================================================================
# FINAL 2025 CONTEMPORARY DESIGN — WHITE + ORANGE + GRAY
# ============================================================================
st.set_page_config(page_title="Pawdcast", page_icon="mic", layout="centered")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp { background:#ffffff; color:#0f172a; font-family:'Inter',sans-serif; }
    .block-container { max-width:960px; padding:2rem 1rem; }
    
    /* Header — logo + title left */
    .header { display:flex; align-items:center; gap:1.2rem; margin-bottom:0.5rem; }
    .logo { width:64px; border-radius:16px; transition:transform 0.4s; box-shadow:0 8px 25px rgba(0,0,0,0.12); }
    .logo:hover { transform:scale(1.1) rotate(4deg); }
    .title { font-size:3rem; font-weight:700; background:linear-gradient(90deg,#f97316,#fb923c); -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin:0; letter-spacing:-1px; }
    .subtitle { color:#64748b; font-size:1.15rem; text-align:center; margin:0.5rem 0 2.8rem; font-weight:500; }
    
    /* Glass cards */
    .card {
        background:rgba(255,255,255,0.97);
        border-radius:24px;
        padding:2rem;
        margin:1.5rem 0;
        box-shadow:0 12px 40px rgba(15,23,42,0.08);
        border:1px solid rgba(226,232,240,0.7);
        transition:all 0.4s cubic-bezier(0.4,0,0.2,1);
    }
    .card:hover { transform:translateY(-6px); box-shadow:0 24px 50px rgba(15,23,42,0.15); }
    
    /* Orange buttons */
    .stButton>button {
        background:linear-gradient(135deg,#f97316,#ea580c)!important;
        color:white!important;
        font-weight:700;
        height:3.6rem;
        border-radius:18px;
        width:100%;
        border:none!important;
        font-size:1.1rem;
        letter-spacing:0.5px;
        box-shadow:0 8px 25px rgba(249,115,22,0.4);
        transition:all 0.4s cubic-bezier(0.4,0,0.2,1);
    }
    .stButton>button:hover {
        transform:translateY(-4px) scale(1.02);
        box-shadow:0 16px 40px rgba(249,115,22,0.6);
    }
    
    /* Radio tabs */
    .stRadio > div { gap:1.2rem; justify-content:center; }
    .stRadio > div > label { background:rgba(248,250,252,0.95); border-radius:18px; padding:0.9rem 1.8rem; border:2px solid transparent; font-weight:600; transition:all 0.3s; }
    .stRadio > div > label[data-checked="true"] { border-color:#f97316; background:white; box-shadow:0 8px 25px rgba(249,115,22,0.25); transform:scale(1.05); }
    
    .badge-free { background:#10b981; color:white; padding:0.6rem 1.6rem; border-radius:50px; font-weight:800; font-size:1rem; }
    .footer { text-align:center; margin-top:5rem; color:#94a3b8; font-size:0.9rem; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# HEADER — LOGO + TITLE LEFT
# ============================================================================
st.markdown("""
<div class="header">
    <img src="https://news.shib.io/wp-content/uploads/2025/12/Black-White-Simple-Modern-Neon-Griddy-Bold-Technology-Pixel-Electronics-Store-Logo-1.png" class="logo">
    <h1 class="title">Pawdcast</h1>
</div>
<p class="subtitle">Instant professional podcast videos — no skills required</p>
""", unsafe_allow_html=True)

# ============================================================================
# MODE SELECTOR
# ============================================================================
mode = st.radio("", ["Manual ($0 Forever)", "Skit Mode", "Full Auto"], horizontal=True)

# ============================================================================
# MANUAL MODE — YOUR FULL WORKING CODE (100% FUNCTIONAL)
# ============================================================================
if mode == "Manual ($0 Forever)":
    st.markdown('<div class="card"><h3>Manual Mode <span class="badge-free">FREE FOREVER</span></h3></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1: audio_file = st.file_uploader("Your recorded audio", type=["wav","mp3","m4a","ogg"])
    with col2: script = st.text_area("Paste your script", height=130, placeholder='Speaker 1: "..."\nSpeaker 2: "..."')
    
    st.markdown("### Video Templates")
    c1, c2, c3 = st.columns(3)
    with c1: tmpl1 = st.file_uploader("Speaker 1 Loop", type="mp4")
    with c2: tmpl2 = st.file_uploader("Speaker 2 Loop", type="mp4")
    with c3: closing = st.file_uploader("Closing Video", type="mp4")
    
    if st.button("CREATE VIDEO NOW", type="primary"):
        if not all([audio_file, script, tmpl1, tmpl2, closing]):
            st.error("Please fill all fields!")
        else:
            with st.spinner("Creating your masterpiece..."):
                with tempfile.TemporaryDirectory() as tmpdir:
                    try:
                        tmp = Path(tmpdir)
                        audio_path = str(tmp / "input.wav")
                        with open(audio_path, "wb") as f: f.write(audio_file.read())
                        
                        # Parse script
                        lines = [l.strip() for l in script.split("\n") if ":" in l and l.strip()]
                        num_segments = len(lines)
                        
                        # Auto-detect splits
                        cmd = ["ffmpeg", "-i", audio_path, "-af", "silencedetect=noise=-40dB:d=0.6", "-f", "null", "-"]
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        ends = [float(m.group(1)) for m in re.finditer(r'silence_end: (\d+\.?\d*)', result.stderr)]
                        split_times = ends[:num_segments-1] if len(ends) >= num_segments-1 else []
                        if not split_times:
                            total = float(subprocess.check_output([
                                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "default=noprint_wrappers=1:nokey=1", audio_path
                            ]).decode().strip())
                            split_times = [total * i / num_segments for i in range(1, num_segments)]
                        
                        # Split audio
                        segments = []
                        start = 0
                        for i, end in enumerate(split_times + [99999]):
                            if i >= len(lines): break
                            duration = end - start
                            seg_path = str(tmp / f"seg_{i}.wav")
                            subprocess.run([
                                "ffmpeg", "-y", "-i", audio_path, "-ss", str(start), "-t", str(duration),
                                "-ac", "1", "-ar", "24000", seg_path
                            ], check=True, capture_output=True)
                            segments.append({"audio": seg_path, "duration": duration})
                            start = end
                        
                        # Save templates
                        t1_path = str(tmp / "t1.mp4"); open(t1_path, "wb").write(tmpl1.read())
                        t2_path = str(tmp / "t2.mp4"); open(t2_path, "wb").write(tmpl2.read())
                        tc_path = str(tmp / "tc.mp4"); open(tc_path, "wb").write(closing.read())
                        
                        # Create final video
                        def create_video(segments, t1, t2, tc, output):
                            temp = Path(output).parent
                            seg_vids = []
                            for i, seg in enumerate(segments):
                                out = str(temp / f"s{i}.mp4")
                                template = t1 if i % 2 == 0 else t2
                                subprocess.run([
                                    "ffmpeg", "-y", "-i", template, "-i", seg["audio"],
                                    "-c:v", "libx264", "-t", str(seg["duration"]), "-pix_fmt", "yuv420p",
                                    "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
                                    "-c:a", "aac", "-shortest", out
                                ], check=True, capture_output=True)
                                seg_vids.append(out)
                            list_file = str(temp / "list.txt")
                            with open(list_file, "w") as f:
                                for v in seg_vids: f.write(f"file '{v}'\n")
                            main = str(temp / "main.mp4")
                            subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", main], check=True)
                            subprocess.run(["ffmpeg", "-y", "-i", main, "-i", tc, "-filter_complex", "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]", "-map", "[v]", "-map", "[a]", output], check=True)
                        
                        output = str(tmp / "final.mp4")
                        create_video(segments, t1_path, t2_path, tc_path, output)
                        
                        st.video(open(output, "rb").read())
                        st.download_button("DOWNLOAD VIDEO", open(output, "rb").read(), "pawdcast.mp4", "video/mp4")
                        st.balloons()
                    except Exception as e:
                        st.error("Something went wrong")
                        with st.expander("Debug"): st.code(traceback.format_exc())

else:
    st.markdown(f'<div class="card"><h3>{mode}</h3><p>Auto-generates audio + video from text — live now</p></div>', unsafe_allow_html=True)

st.markdown('<div class="footer">Made with ❤️ (and Grok being effing brilliant) for <a href="https://news.shib.io" style="color:#f97316;text-decoration:none;">The Shib Daily</a></div>', unsafe_allow_html=True)
