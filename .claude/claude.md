# BeneAI - AI-Powered Video Call Assistant

## Project Overview

BeneAI is an AI-powered real-time video call assistant designed for high-stakes meetings. The system analyzes visual and audio cues during video calls to assess participant engagement metrics (interest, confusion, agreement, etc.) and provides real-time coaching advice to help users navigate critical conversations effectively.

## Current Status

**Stage:** Hackathon Development
**Phase:** MVP Implementation & Documentation
**Timeline:** Fast-track development for hackathon demo
**Deployment:** Developer mode Chrome extension + Cloud Run backend

## Core Architecture Components

### 1. Visual Analysis Pipeline
- **Component:** Facial expression and emotion detection
- **Input:** Video stream from meetings (WebRTC chrome.tabCapture)
- **Output:** Emotional state parameters (positive, negative, neutral, concerned, surprised)
- **Tech Stack:** MediaPipe Face Mesh (via CDN) with rule-based emotion detection
- **Latency:** ~30-50ms per frame

### 2. Audio Analysis Pipeline
- **Component:** Speech and pacing analysis
- **Input:** Audio stream from meetings
- **Output:** Speech rate, pauses, filler words, volume levels
- **Tech Stack:** Web Audio API + Web Speech API
- **Latency:** ~100-200ms for speech recognition

### 3. Parameter Extraction (MVP Scope)
- **Primary Metrics:**
  - Emotional tone (happy, concerned, neutral, surprised)
  - Speech pacing (words per minute, pause frequency)
  - Filler word usage ("um", "uh", "like")
  - Volume/energy levels
  - Speaking time tracking

### 4. LLM Wrapper & Advice Engine
- **Component:** Real-time coaching system with streaming
- **Input:** Aggregated parameters from video + audio analysis
- **Output:** Actionable coaching advice (streamed word-by-word)
- **Tech Stack:** GPT-4-turbo via OpenAI API, Python FastAPI backend
- **Latency:** ~300-500ms to first token, streaming thereafter

### 5. User Interface
- **Component:** Non-intrusive overlay during video calls
- **UI Elements:**
  - Corner widget showing current emotional state
  - Expandable advice panel with real-time suggestions
  - Minimal design to avoid distraction
- **Tech Stack:** Vanilla HTML/CSS/JS (no build step for hackathon speed)
- **Deployment:** Chrome extension (developer mode)

## Hackathon Tech Stack (Finalized)

### Frontend: Chrome Extension
- **Capture:** WebRTC `chrome.tabCapture` API
- **Facial Detection:** MediaPipe Face Mesh (CDN: https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh)
- **Emotion:** Rule-based Action Unit (AU) detection
- **Audio:** Web Audio API + Web Speech API
- **UI:** Vanilla JS/HTML/CSS (no build tools)
- **Target:** Chrome (developer mode installation)

### Backend: Python + Cloud Run
- **Framework:** FastAPI with WebSocket support
- **LLM:** OpenAI GPT-4-turbo (streaming)
- **Deployment:** Google Cloud Run (serverless)
- **Memory:** In-memory caching for demo (no database)
- **Config:** `--min-instances 1` during demo to prevent cold starts

### Development Priorities (Hackathon Timeline)

**Phase 1: Infrastructure (Days 1-2)**
1. Set up Cloud Run backend with FastAPI + WebSocket
2. OpenAI integration with streaming responses
3. Basic extension scaffold with manifest.json
4. End-to-end "hello world" test (extension ↔ backend)

**Phase 2: Analysis Pipeline (Days 3-4)**
5. MediaPipe face detection in extension
6. Simple emotion detection (smile, frown, neutral)
7. Web Speech API for speech-to-text
8. Audio feature extraction (speech rate, pauses, volume)

**Phase 3: Integration & UI (Days 5-6)**
9. Prompt engineering for GPT-4 coaching advice
10. Build overlay UI (corner widget + expandable panel)
11. Connect analysis → backend → LLM → UI
12. End-to-end testing with real video calls

**Phase 4: Demo Polish (Day 7)**
13. Record backup demo video
14. Create judge installation guide (INSTALL.md)
15. Prepare demo script and presentation
16. Final testing and bug fixes

## Technical Considerations

### Real-Time Processing (Optimized for Hackathon)
- **Target Latency:** <500ms from capture to advice display
- **Video Processing:** 5-10 fps (reduce from 30fps to save CPU)
- **Audio Buffering:** 2-3 second windows for speech analysis
- **Optimization:** Process every 3rd frame for face detection (still smooth)
- **Expected Total Latency:** 400-700ms end-to-end

### Privacy & Security (MVP Approach)
- **On-Device:** Face detection runs entirely in browser (MediaPipe)
- **Server-Sent:** Only aggregated parameters sent to backend (not raw video/audio)
- **No Storage:** Zero data persistence for hackathon demo
- **OpenAI:** Audio transcripts sent to OpenAI API (document in privacy notice)
- **Demo Consent:** Clear messaging that it's a prototype

### Hackathon Workarounds & Risks

**Challenge: Extension Installation**
- **Solution:** Developer mode instructions (5 min setup)
- **Backup:** Have 2-3 laptops pre-configured for judges
- **Alternative:** Bookmarklet fallback (limited features)

**Challenge: Cloud Run Cold Starts**
- **Solution:** Use `--min-instances 1` during demo day ($5 cost, worth it)
- **Backup:** Pre-warm instance 5 mins before demo

**Challenge: OpenAI Rate Limits**
- **Solution:** Upgrade to Tier 2 ($50 budget)
- **Backup:** Implement simple caching for common scenarios

**Challenge: WiFi Reliability**
- **Solution:** Use phone hotspot as backup
- **Backup:** Pre-recorded demo video with live voiceover

**Challenge: Browser Permissions**
- **Solution:** Test permission flow extensively
- **Backup:** Clear troubleshooting guide in INSTALL.md

## Architecture Decisions (Finalized)

1. **Deployment Model:** Hybrid - Face detection client-side, LLM reasoning server-side
2. **Target Platform:** Chrome extension (developer mode for hackathon)
3. **Video Platforms:** Any WebRTC-based platform (Google Meet, Zoom Web, Teams)
4. **Model Selection:** Pre-trained MediaPipe (no custom training needed)
5. **Advice Delivery:** Non-intrusive corner widget + expandable panel
6. **User Customization:** Minimal for MVP (on/off toggle only)

## File Structure (Hackathon-Optimized)

```
BeneAI/
├── extension/                  # Chrome extension
│   ├── manifest.json          # Extension configuration (Manifest V3)
│   ├── background.js          # Service worker for background tasks
│   ├── content.js             # Injected into video call pages
│   ├── popup.html             # Extension popup UI
│   ├── popup.js               # Popup logic
│   ├── overlay.html           # Advice overlay template
│   ├── overlay.css            # Overlay styles
│   ├── overlay.js             # Overlay UI controller
│   ├── analysis/
│   │   ├── video-analyzer.js  # MediaPipe face detection
│   │   ├── audio-analyzer.js  # Web Audio API + Speech API
│   │   └── emotion-detector.js # Rule-based emotion from landmarks
│   ├── utils/
│   │   ├── websocket.js       # WebSocket connection to backend
│   │   └── storage.js         # Chrome storage helpers
│   └── icons/                 # Extension icons (16, 48, 128px)
│
├── backend/                    # Python FastAPI backend
│   ├── main.py                # FastAPI app + WebSocket handler
│   ├── llm.py                 # OpenAI GPT-4 integration
│   ├── prompts.py             # Prompt templates for coaching
│   ├── cache.py               # Simple in-memory cache
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile             # Cloud Run container
│   ├── .env.example           # Environment variables template
│   └── tests/                 # Backend unit tests
│
├── docs/                       # Documentation
│   ├── architecture.md        # System architecture & data flow
│   ├── api-specs.md           # WebSocket protocol & message formats
│   ├── deployment.md          # Cloud Run deployment guide
│   ├── demo-guide.md          # Hackathon demo script
│   ├── INSTALL.md             # Extension installation for judges
│   └── QUICKSTART.md          # Team onboarding guide
│
├── demo/
│   ├── backup-demo.mp4        # Pre-recorded fallback demo
│   └── slides.pdf             # Presentation deck
│
├── .gitignore
├── README.md                   # Project overview
└── .claude/
    └── claude.md              # Claude Code configuration (this file)
```

## Development Guidelines

### Code Style
- **Python:** Follow PEP 8, use type hints, docstrings for all functions
- **JavaScript:** ES6+ syntax, async/await for promises, JSDoc comments
- **Comments:** Explain "why" not "what" (code should be self-documenting)
- **Git:** Feature branches, clear commit messages, squash before merge

### Hackathon Best Practices
- **Move Fast:** Working prototype > perfect code
- **Test Often:** Test end-to-end every few hours
- **Document Live:** Update docs as you build, not after
- **Backup Everything:** Commit frequently, record demo early
- **Plan for Failure:** Always have fallback (pre-recorded demo, backup internet)

### Privacy & Ethics (MVP)
- **Minimal Data:** Only send aggregated metrics to backend (no raw video/audio)
- **No Persistence:** Zero storage of user data for hackathon
- **Clear Consent:** Display privacy notice on first use
- **Transparency:** Open about what data goes to OpenAI API

## Resources & References

### MediaPipe (Face Detection)
- **CDN:** https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh
- **Docs:** https://google.github.io/mediapipe/solutions/face_mesh.html
- **Landmarks:** 468 3D facial landmarks, including eyes, mouth, eyebrows
- **Emotion Mapping:** Use landmark distances for smile/frown/surprise detection

### Web APIs
- **Web Audio API:** https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API
- **Web Speech API:** https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API
- **Chrome Extensions:** https://developer.chrome.com/docs/extensions/mv3/

### OpenAI
- **GPT-4 Turbo API:** https://platform.openai.com/docs/api-reference/chat
- **Streaming:** https://platform.openai.com/docs/api-reference/streaming
- **Best Practices:** https://platform.openai.com/docs/guides/prompt-engineering

### FastAPI
- **WebSocket:** https://fastapi.tiangolo.com/advanced/websockets/
- **Docs:** https://fastapi.tiangolo.com/

### Cloud Run
- **Deploy Python:** https://cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-service
- **WebSocket Support:** https://cloud.google.com/run/docs/triggering/websockets

## Hackathon Demo Strategy

### Pre-Demo Checklist
- [ ] Extension pre-installed on 2-3 laptops
- [ ] Backend deployed with `--min-instances 1`
- [ ] Pre-warm Cloud Run 5 mins before demo
- [ ] Backup demo video ready to play
- [ ] Phone hotspot configured as backup internet
- [ ] OpenAI API key working, rate limits checked
- [ ] INSTALL.md printed for judges
- [ ] Demo script practiced 3+ times

### Demo Flow (5-7 minutes)
1. **Hook (30 sec):** "Imagine having an AI coach during every high-stakes call"
2. **Problem (1 min):** Stats on remote work, importance of video presence
3. **Live Demo (3-4 min):**
   - Show extension in Chrome
   - Start Google Meet call with teammate
   - Demonstrate real-time emotion detection
   - Show pacing feedback (speak fast → get advice to slow down)
   - Display coaching suggestions as they stream in
4. **Technical Deep Dive (1 min):** Show architecture diagram
5. **Future Vision (30 sec):** Sales coaching, interview prep, therapy
6. **Q&A (1 min)**

### Backup Plans
- **Plan A:** Live demo with real video call
- **Plan B:** Pre-recorded video with live voiceover
- **Plan C:** Slides + architecture walkthrough if tech fails

## Cost Estimates (Hackathon)

- **Development:** 0 days × team size = free (your time)
- **OpenAI API:** ~$30-50 (testing + demo day)
- **Cloud Run:** ~$5-10 (with min-instances during demo)
- **Total:** ~$40-60

## Success Metrics (for Judging)

- **Technical Innovation:** Real-time multi-modal AI (video + audio + LLM)
- **Demo Impact:** Live, working prototype that judges can try
- **Market Fit:** Clear use case (sales, interviews, investor pitches)
- **Execution Quality:** <500ms latency, clean UI, reliable performance
- **Wow Factor:** Emotional tone detection that actually works in real-time
