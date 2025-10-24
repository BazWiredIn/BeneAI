# BeneAI Quick Reference Card

## 🚀 Start the System

```bash
./start_demo.sh
```

Then open: **http://localhost:8080**

---

## 🔧 Stop the System

```bash
# Kill backend on port 8000
lsof -ti:8000 | xargs kill

# Kill frontend on port 8080
lsof -ti:8080 | xargs kill
```

Or:
```bash
killall python python3
```

---

## 📊 See Collected Data

### 1. Browser Console (F12) - Most Detail
```
📊 [3:45:12 PM] Frame sent: {"count":125}
📊 [3:45:13 PM] Emotion received: {"state":"receptive","emotion":"Joy","confidence":"0.85","count":42}
📊 [3:45:20 PM] Coaching advice: {"advice":"Great momentum!...","count":3}
```

### 2. Status Bar - Quick Stats
```
Active - Frames:125 | Emotions:42 | Intervals:15 | Advice:3
```

### 3. Debug Panel - Live Log
Expand "📊 Data Collection Log (Live)" at bottom of page

### 4. Backend Terminal - Server Logs
```
INFO: Emotion detected: receptive (Joy: 0.85)
INFO: Interval complete: receptive, 3 frames
INFO: Coaching advice sent: "Great momentum!..."
```

---

## ⏱️ Expected Timeline

| Time | Event | What to See |
|------|-------|-------------|
| 0s | Press "Start Session" | Video starts, webcam permission |
| 0.3s | First frame sent | Console: `📊 Frame sent: {"count":1}` |
| 0.8s | First emotion received | Console: `📊 Emotion received: ...` |
| 1.0s | First interval complete | Console: `📊 Interval complete: ...` |
| 5.0s | First coaching advice | Console: `📊 Coaching advice: ...` |
| 9.5s | Second coaching advice | UI updates with new advice |

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `frontend/js/app.js` | Main application logic (FIXED) |
| `frontend/index.html` | UI with debug panel |
| `backend/main.py` | FastAPI server + WebSocket |
| `backend/.env` | API keys (OPENAI_API_KEY, HUME_API_KEY) |

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| TypeError crash | ✅ FIXED in latest app.js |
| No data visible | Open console (F12) + debug panel |
| Backend not running | `python backend/main.py` |
| Port 8000 in use | `lsof -ti:8000 \| xargs kill` |
| No emotions received | Check HUME_API_KEY in .env |
| No coaching advice | Check OPENAI_API_KEY in .env |
| Speech errors | Known issue, non-critical |

---

## 🎯 Data Flow Summary

```
Video Frame (every 333ms)
    ↓
Backend (WebSocket)
    ↓
Hume AI (48 emotions)
    ↓
Investor State Mapping (6 states)
    ↓
1-Second Interval (EMA smoothing)
    ↓
5-Second Buffer (rolling window)
    ↓
GPT-4 Coaching (every 4.5s)
    ↓
UI Display (real-time)
```

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| **QUICK_START.md** | How to run & test |
| **WHERE_IS_DATA.md** | Where to see collected data |
| **DATA_FLOW.md** | Technical pipeline details |
| **FIXED_ISSUES.md** | What was fixed |
| **USAGE_GUIDE.md** | Comprehensive setup guide |

---

## 💡 Pro Tips

1. **Keep console open** (F12) while running for best visibility
2. **Debug panel shows last 20 events** - auto-refreshes
3. **Status bar updates every event** - watch counters increase
4. **Wait 5 seconds** for first coaching advice
5. **Good lighting + centered face** = better emotion detection

---

## ✅ Current Status

**Working:**
- ✅ Video frame capture (3 FPS)
- ✅ Hume AI emotion detection
- ✅ Investor state mapping
- ✅ 1-second interval aggregation
- ✅ 5-second buffer + trends
- ✅ GPT-4 coaching advice
- ✅ Real-time UI updates
- ✅ Data collection logging

**Known Issues:**
- ⚠️ Speech recognition network errors (non-critical)
- ⚠️ Speech metrics not updating (depends on above)

---

**Last Updated:** October 22, 2025
**System Version:** 1.0 (Post-Fix)
