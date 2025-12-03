# 🐕 Pawdcast Skit Factory

**Fully automated article-to-video conversion** - just like MakeReels.ai!

Paste article → Click button → Download ready-to-publish 16:9 video

---

## ✨ Features

- **One-Click Generation**: Paste article, get video
- **AI-Powered Skits**: Gemini 3 creates witty podcast dialogues
- **Natural Voices**: Gemini TTS with multiple voice options
- **Auto Speaker Switching**: Video switches between templates based on who's talking
- **Synced Captions**: Big white text with black outline
- **100% Free**: Hosted on Streamlit Community Cloud

---

## 🚀 Deploy in 5 Minutes

### Step 1: Create GitHub Repo
1. Go to [github.com/new](https://github.com/new)
2. Name: `pawdcast-skit-factory`
3. Set to **Public**
4. Upload these files

### Step 2: Deploy to Streamlit
1. Go to [streamlit.io/cloud](https://streamlit.io/cloud)
2. Click **New app**
3. Select your repo
4. Main file: `app.py`
5. Click **Deploy**

### Step 3: Add API Key
1. In your deployed app, click **⋮** → **Settings**
2. Go to **Secrets**
3. Add:
```toml
GEMINI_API_KEY = "your-key-here"
```

### Step 4: Share URL with Team! 🎉

---

## 📁 Files

```
├── app.py              # Main app
├── requirements.txt    # Python packages
├── packages.txt        # System packages (FFmpeg)
├── .streamlit/
│   └── config.toml     # Theme config
└── README.md
```

---

## 🎬 Template Requirements

| Property | Value |
|----------|-------|
| Resolution | 1920×1080 (16:9) |
| Format | MP4 |
| Size | Under 200MB each |

**You need 3 templates:**
1. Speaker 1 (Shiba 1 talking)
2. Speaker 2 (Shiba 2 talking)
3. Closing (Logo/outro)

---

## 🎙️ Voices

| Voice | Style |
|-------|-------|
| Enceladus | Deep, authoritative |
| Puck | Warm, friendly |
| Charon | Professional |
| Kore | Bright, energetic |

---

## 💰 Cost

**$0** - Everything is free!

---

Made with 🧡 for [The Shib Daily](https://news.shib.io)
