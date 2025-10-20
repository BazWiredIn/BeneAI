# BeneAI - AI-Powered Video Call Coach

<div align="center">

![BeneAI Logo](https://via.placeholder.com/400x100?text=BeneAI)

**Real-time AI coaching for high-stakes video calls**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Chrome Extension](https://img.shields.io/badge/Chrome-Extension-green.svg)](https://chrome.google.com/webstore)

[Demo](#demo) • [Features](#features) • [Installation](#installation) • [Documentation](#documentation) • [Contributing](#contributing)

</div>

---

## Overview

BeneAI is an AI-powered Chrome extension that provides real-time coaching during video calls. It analyzes your facial expressions, speech patterns, and emotional tone to give you actionable advice as you speak.

Perfect for:
- 💼 Sales calls
- 👔 Job interviews
- 💰 Investor pitches
- 🎤 Presentations
- 🧑‍⚕️ Therapy sessions
- 📞 Important meetings

## Demo

![BeneAI Demo](https://via.placeholder.com/800x450?text=Demo+GIF)

**Watch the full demo:** [YouTube Link](#)

### What It Does

- **Emotion Detection:** Analyzes facial expressions in real-time (happy, concerned, surprised, neutral)
- **Speech Analysis:** Tracks speaking pace, pauses, and filler words
- **AI Coaching:** GPT-4 generates personalized advice based on your performance
- **Privacy-First:** All video processing happens in your browser, nothing is recorded

## Features

### 🎭 Real-Time Emotion Detection
- Detects happiness, concern, surprise, and neutral states
- Uses Google MediaPipe (468 facial landmarks)
- Updates every 2-3 seconds
- Visual indicator in corner overlay

### 🗣️ Speech & Pacing Analysis
- **Words Per Minute:** Tracks speaking rate (target: 120-150 WPM)
- **Pause Frequency:** Monitors natural pauses
- **Filler Words:** Counts "um," "uh," "like," etc.
- **Volume Levels:** Ensures you're speaking loud enough

### 🤖 AI-Powered Coaching
- GPT-4 Turbo generates personalized advice
- Streams responses word-by-word (feels instant)
- Context-aware suggestions
- Adapts to your communication style

### 🔒 Privacy & Security
- **On-device processing:** Video never leaves your browser
- **Zero recording:** No audio or video files stored
- **Minimal data:** Only sends aggregated metrics (e.g., "user looks concerned")
- **Open source:** Audit the code yourself

### ⚡ Performance
- **Sub-second latency:** <500ms from detection to advice
- **Lightweight:** ~100-150MB memory usage
- **Efficient:** Processes 5-10 FPS (optimized for battery life)

## Installation

### For Users (5 minutes)

**See detailed instructions:** [INSTALL.md](docs/INSTALL.md)

**Quick steps:**
1. Download `beneai-extension.zip` from [Releases](#)
2. Extract the ZIP file
3. Go to `chrome://extensions` in Chrome
4. Enable "Developer mode"
5. Click "Load unpacked" and select the `extension` folder
6. Join a Google Meet call to test!

### For Developers (15 minutes)

**See full guide:** [QUICKSTART.md](docs/QUICKSTART.md)

```bash
# Clone repository
git clone https://github.com/your-org/BeneAI.git
cd BeneAI

# Set up backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Run backend
uvicorn main:app --reload --port 8000

# In Chrome:
# 1. Go to chrome://extensions
# 2. Enable Developer mode
# 3. Load unpacked extension from /extension folder
```

## Architecture

```
Extension (Browser)          Backend (Cloud Run)          OpenAI API
┌─────────────────┐         ┌──────────────────┐         ┌─────────┐
│                 │         │                  │         │         │
│  Video Stream   │         │                  │         │         │
│       ↓         │         │                  │         │         │
│  MediaPipe      │         │                  │         │         │
│  Face Detection │         │                  │         │         │
│       ↓         │         │                  │         │         │
│  Emotion Rules  │         │                  │         │         │
│                 │         │                  │         │         │
│  Audio Stream   │         │                  │         │         │
│       ↓         │         │                  │         │         │
│  Web Speech API │         │                  │         │         │
│       ↓         │         │                  │         │         │
│  Aggregate      │─────────→  FastAPI         │─────────→ GPT-4   │
│  Parameters     │ WebSocket│  WebSocket      │  HTTPS  │ Turbo   │
│                 │←─────────│  Handler        │←─────────│         │
│                 │         │                  │         │         │
│  Display Advice │         │  Cache & Queue   │         │         │
│  in Overlay     │         │                  │         │         │
└─────────────────┘         └──────────────────┘         └─────────┘
```

**Learn more:** [docs/architecture.md](docs/architecture.md)

## Technology Stack

### Frontend (Chrome Extension)
- **Video Analysis:** Google MediaPipe (Face Mesh)
- **Audio Analysis:** Web Audio API + Web Speech API
- **UI:** Vanilla JavaScript (no framework for speed)
- **Communication:** WebSocket to backend

### Backend (Cloud Run)
- **Framework:** FastAPI (Python)
- **LLM:** OpenAI GPT-4 Turbo (streaming)
- **Deployment:** Google Cloud Run (serverless)
- **Caching:** In-memory (for cost optimization)

### Infrastructure
- **Hosting:** Google Cloud Run
- **CI/CD:** GitHub Actions
- **Monitoring:** Cloud Run Logs

## Documentation

- **[Architecture](docs/architecture.md)** - System design and data flow
- **[API Specifications](docs/api-specs.md)** - WebSocket protocol
- **[Deployment Guide](docs/deployment.md)** - Deploy to Cloud Run
- **[Quickstart](docs/QUICKSTART.md)** - Get started developing
- **[Installation](docs/INSTALL.md)** - Install the extension
- **[Demo Guide](docs/demo-guide.md)** - Hackathon presentation script

## Supported Platforms

| Platform | Status | Notes |
|----------|--------|-------|
| Google Meet | ✅ Full Support | Best experience |
| Zoom Web | ✅ Full Support | Must use web version |
| Microsoft Teams Web | ✅ Full Support | Web version only |
| Zoom Desktop | ⚠️ Limited | Requires screen sharing |
| Teams Desktop | ⚠️ Limited | Requires screen sharing |

## Performance

- **Latency:** <500ms from capture to advice display
- **Accuracy:** 70-80% emotion detection (rule-based)
- **CPU Usage:** ~10-15% during calls
- **Memory:** ~100-150MB
- **Network:** ~1KB per update (minimal bandwidth)

## Roadmap

### MVP (Current - Week 1)
- [x] Basic emotion detection (5 states)
- [x] Speech pacing analysis
- [x] GPT-4 coaching integration
- [x] Chrome extension
- [x] Cloud Run backend

### v1.1 (Post-Hackathon)
- [ ] Multi-person tracking
- [ ] Historical analytics
- [ ] Custom coaching profiles
- [ ] Mobile app for second screen

### v2.0 (Future)
- [ ] Fine-tuned local LLM (cost reduction)
- [ ] Advanced emotions (ML model)
- [ ] Team collaboration features
- [ ] Calendar integration

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Good first issues:** Look for the `good-first-issue` label on GitHub.

### Development Setup

```bash
# Fork and clone
git clone https://github.com/your-username/BeneAI.git
cd BeneAI

# Create feature branch
git checkout -b feature/your-feature-name

# Make changes, commit, push
git add .
git commit -m "Add your feature"
git push origin feature/your-feature-name

# Open pull request on GitHub
```

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Extension Tests
```bash
# Manual testing for now
# Load extension in Chrome and test on Google Meet
```

### End-to-End Tests
See [docs/QUICKSTART.md#testing](docs/QUICKSTART.md#testing) for manual test checklist.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **MediaPipe** by Google - Face detection
- **OpenAI** - GPT-4 Turbo API
- **FastAPI** - Backend framework
- **Google Cloud Run** - Serverless hosting

## Team

Built for [Hackathon Name] by:
- [Your Name] - [@github](https://github.com/username)
- [Teammate 2] - [@github](https://github.com/username)
- [Teammate 3] - [@github](https://github.com/username)

## Contact

- **Website:** https://beneai.com
- **Email:** team@beneai.com
- **GitHub Issues:** https://github.com/your-org/BeneAI/issues
- **Twitter:** [@BeneAI](https://twitter.com/beneai)

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=your-org/BeneAI&type=Date)](https://star-history.com/#your-org/BeneAI&Date)

---

<div align="center">

**Made with ❤️ by the BeneAI team**

[⬆ Back to top](#beneai---ai-powered-video-call-coach)

</div>
