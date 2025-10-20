# BeneAI Quickstart Guide

Welcome to the BeneAI team! This guide will get you up and running in under 15 minutes.

## Prerequisites

Before you start, make sure you have:

- [ ] Python 3.11+ installed (`python --version`)
- [ ] Node.js 18+ installed (optional, for extension build tools)
- [ ] Google Chrome browser
- [ ] Git installed
- [ ] OpenAI API key ([get one here](https://platform.openai.com/api-keys))
- [ ] Google Cloud account ([sign up here](https://console.cloud.google.com/))

## Quick Setup (15 minutes)

### Step 1: Clone Repository

```bash
# Clone the repo
git clone https://github.com/your-org/BeneAI.git
cd BeneAI

# Check structure
ls -la
# Should see: extension/, backend/, docs/, demo/, .claude/
```

### Step 2: Backend Setup (5 minutes)

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Mac/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
# Use nano, vim, or your favorite editor:
nano .env
# Add: OPENAI_API_KEY=sk-proj-...your-key-here...
```

### Step 3: Run Backend Locally (2 minutes)

```bash
# Make sure you're in backend/ and venv is activated
cd backend  # if not already there
source venv/bin/activate  # if not already activated

# Run the server
uvicorn main:app --reload --port 8000

# You should see:
# INFO:     Uvicorn running on http://127.0.0.1:8000
# INFO:     Application startup complete
```

**Test it:**
```bash
# In a new terminal:
curl http://localhost:8000/
# Expected: {"status":"healthy","version":"1.0.0"}
```

### Step 4: Extension Setup (3 minutes)

```bash
# In a new terminal, navigate to extension directory
cd extension

# Update backend URL for local development
# Edit extension/utils/websocket.js
# Change: const BACKEND_URL = "ws://localhost:8000/ws";
```

### Step 5: Load Extension in Chrome (2 minutes)

1. Open Chrome
2. Go to `chrome://extensions`
3. Enable "Developer mode" (toggle in top-right corner)
4. Click "Load unpacked"
5. Select the `BeneAI/extension` directory
6. You should see "BeneAI" extension appear with a green icon

### Step 6: Test End-to-End (3 minutes)

1. Open a new tab in Chrome
2. Go to https://meet.google.com/new
3. Join the test call
4. Open Chrome DevTools (F12 or Cmd+Option+I)
5. Check Console tab for logs like:
   ```
   [BeneAI] Initializing...
   [BeneAI] MediaPipe loaded
   [BeneAI] WebSocket connected
   [BeneAI] Starting face detection...
   ```
6. You should see a small overlay widget in the corner
7. Try smiling or frowning - check if emotion is detected
8. Speak and watch for pacing feedback

**If you see the overlay and it updates, you're good to go! 🎉**

---

## Development Workflow

### Daily Routine

**1. Start Backend**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

**2. Make Changes**
- Backend: Edit Python files in `backend/`
- Extension: Edit JS files in `extension/`
- FastAPI auto-reloads on file changes
- Extension requires manual reload (click reload button in chrome://extensions)

**3. Test Changes**
- Refresh Google Meet page
- Check console logs
- Verify overlay behavior

**4. Commit Changes**
```bash
git add .
git commit -m "Add feature X"
git push origin your-branch-name
```

---

## Project Structure

```
BeneAI/
├── extension/              # Chrome extension (frontend)
│   ├── manifest.json      # Extension config
│   ├── background.js      # Service worker
│   ├── content.js         # Injected into video pages
│   ├── popup.html/js      # Extension popup
│   ├── overlay.*          # UI overlay on calls
│   ├── analysis/          # Video & audio analysis
│   │   ├── video-analyzer.js
│   │   ├── audio-analyzer.js
│   │   └── emotion-detector.js
│   └── utils/             # Helpers (WebSocket, storage)
│
├── backend/               # FastAPI backend
│   ├── main.py           # FastAPI app + WebSocket
│   ├── llm.py            # OpenAI integration
│   ├── prompts.py        # GPT-4 prompts
│   ├── cache.py          # In-memory cache
│   ├── requirements.txt  # Python dependencies
│   └── Dockerfile        # Cloud Run container
│
├── docs/                 # Documentation
│   ├── architecture.md   # System design
│   ├── api-specs.md      # WebSocket protocol
│   ├── deployment.md     # Cloud Run guide
│   ├── demo-guide.md     # Hackathon demo script
│   ├── QUICKSTART.md     # This file
│   └── INSTALL.md        # Judge installation guide
│
└── demo/                 # Demo materials
    └── backup-demo.mp4   # Pre-recorded fallback
```

---

## Common Tasks

### Adding a New Feature

**Example: Add "energy level" detection**

1. **Extension side** (`extension/analysis/audio-analyzer.js`):
   ```javascript
   function analyzeEnergy(audioData) {
     // Calculate RMS energy
     const energy = calculateRMS(audioData);
     return energy;
   }
   ```

2. **Update message format** (`extension/content.js`):
   ```javascript
   const payload = {
     // ... existing fields
     speech: {
       // ... existing metrics
       energyLevel: analyzeEnergy(audioData)
     }
   };
   ```

3. **Backend side** (`backend/prompts.py`):
   ```python
   def build_prompt(parameters):
       energy = parameters["speech"]["energyLevel"]
       # Use energy in prompt
       return f"User energy level: {energy}..."
   ```

4. **Test it:**
   - Reload extension
   - Restart backend (if needed)
   - Join test call
   - Check console logs for new field

### Debugging

**Check Extension Logs:**
```javascript
// In Chrome DevTools console:
// Extension logs are prefixed with [BeneAI]
```

**Check Backend Logs:**
```bash
# Backend terminal shows all requests
# Look for errors or WebSocket messages
```

**Test WebSocket Connection:**
```bash
# Install wscat
npm install -g wscat

# Connect to local backend
wscat -c ws://localhost:8000/ws

# Send test message
{"type":"ping","timestamp":1697745123456}

# Should receive pong
```

**Check OpenAI API:**
```bash
# Test your API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Updating Dependencies

**Backend:**
```bash
cd backend
pip install new-package
pip freeze > requirements.txt
```

**Extension:**
```bash
# Extension has no build step for hackathon
# Just edit JS files directly
```

---

## Environment Variables

### Backend `.env`

```env
# Required
OPENAI_API_KEY=sk-proj-...        # Your OpenAI API key

# Optional (with defaults)
OPENAI_MODEL=gpt-4-turbo          # Model to use
OPENAI_MAX_TOKENS=100             # Max tokens per response
OPENAI_TEMPERATURE=0.7            # Creativity (0-1)
ENVIRONMENT=development           # development | production
LOG_LEVEL=info                    # debug | info | warning | error
ALLOWED_ORIGINS=*                 # CORS origins
MAX_CONNECTIONS=100               # Max WebSocket connections
RATE_LIMIT_MESSAGES_PER_SECOND=10 # Rate limit per client
CACHE_TTL_SECONDS=300             # Cache time-to-live
```

---

## Troubleshooting

### Backend won't start

**Error:** `ModuleNotFoundError: No module named 'fastapi'`
```bash
# Activate virtual environment
source venv/bin/activate
pip install -r requirements.txt
```

**Error:** `Port 8000 already in use`
```bash
# Kill existing process
lsof -ti:8000 | xargs kill -9
# Or use different port
uvicorn main:app --reload --port 8001
```

### Extension not loading

**Error:** "Manifest file is missing or unreadable"
```bash
# Check manifest.json syntax
cat extension/manifest.json | python -m json.tool
```

**Error:** "Service worker registration failed"
```bash
# Chrome Manifest V3 issue - check background.js
# Ensure it's listed in manifest.json
```

### WebSocket connection fails

**Error:** `WebSocket connection to 'ws://localhost:8000/ws' failed`

1. Check backend is running: `curl http://localhost:8000/`
2. Check firewall isn't blocking port 8000
3. Check CORS settings in backend
4. Look at backend logs for errors

### No emotion detected

**Problem:** Face detected but emotion always "neutral"

1. Check console logs for MediaPipe errors
2. Verify good lighting (webcam needs clear face view)
3. Test emotion rules in `emotion-detector.js`
4. Try exaggerated expressions (big smile, deep frown)

### No advice appearing

**Problem:** Everything seems to work but no advice shows up

1. Check backend logs - is LLM being called?
2. Check OpenAI API key is valid
3. Check rate limits (upgrade to Tier 2 if needed)
4. Test with curl:
   ```bash
   curl -X POST http://localhost:8000/test-llm \
     -H "Content-Type: application/json" \
     -d '{"emotion":"concerned","wpm":180}'
   ```

---

## Git Workflow

### Branching Strategy

```bash
# Create feature branch
git checkout -b feature/add-energy-detection

# Make changes
git add .
git commit -m "Add energy level detection"

# Push to remote
git push origin feature/add-energy-detection

# Create pull request on GitHub
# Get review, merge to main
```

### Commit Message Style

```bash
# Good commit messages:
git commit -m "Add emotion detection for surprised state"
git commit -m "Fix WebSocket reconnection logic"
git commit -m "Optimize MediaPipe frame processing"

# Bad commit messages:
git commit -m "stuff"
git commit -m "changes"
git commit -m "idk lol"
```

---

## Testing

### Manual Testing Checklist

Before pushing code, test:

- [ ] Backend starts without errors
- [ ] Extension loads in Chrome
- [ ] WebSocket connection establishes
- [ ] Face detection works (try smiling/frowning)
- [ ] Speech analysis works (speak and check WPM)
- [ ] Advice streams in real-time
- [ ] No console errors in DevTools
- [ ] Backend logs look normal

### Automated Tests (Future)

```bash
# Backend unit tests
cd backend
pytest

# Extension tests (future)
cd extension
npm test
```

---

## Useful Commands

```bash
# Backend
cd backend && source venv/bin/activate && uvicorn main:app --reload

# View logs
tail -f backend/logs/app.log

# Check Python version
python --version

# Install package
pip install package-name

# Freeze dependencies
pip freeze > requirements.txt

# Extension
# Reload: Go to chrome://extensions and click reload icon

# Test WebSocket
wscat -c ws://localhost:8000/ws

# Check Chrome version
chrome --version

# Clear extension data
# Go to chrome://extensions, click "Details", then "Clear storage"
```

---

## Resources

### Documentation
- **Architecture:** See `docs/architecture.md`
- **API Specs:** See `docs/api-specs.md`
- **Deployment:** See `docs/deployment.md`

### External Resources
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **MediaPipe:** https://google.github.io/mediapipe/
- **Chrome Extensions:** https://developer.chrome.com/docs/extensions/
- **OpenAI API:** https://platform.openai.com/docs/

### Team Communication
- **Slack:** #beneai channel
- **GitHub:** https://github.com/your-org/BeneAI
- **Stand-ups:** Daily at 9am

---

## Need Help?

### Quick Questions
- Check documentation in `docs/`
- Search existing GitHub issues
- Ask in team Slack

### Bugs
- Open GitHub issue with:
  - Steps to reproduce
  - Expected vs actual behavior
  - Console logs / error messages
  - Screenshots if relevant

### New Features
- Discuss in team meeting first
- Create GitHub issue with proposal
- Get approval before starting work

---

## Next Steps

Now that you're set up:

1. **Read the docs:** Understand the architecture (`docs/architecture.md`)
2. **Pick a task:** Check GitHub issues for "good first issue" label
3. **Make a change:** Start with something small to learn the codebase
4. **Ask questions:** No question is too small!

**Welcome to the team! Let's build something amazing! 🚀**
