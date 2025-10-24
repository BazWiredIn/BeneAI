# Quick Test Guide - After Implementation

## 🔴 CRITICAL: Fix OpenAI Key First!

```bash
# 1. Get key from: https://platform.openai.com/api-keys
# 2. Edit backend/.env:
vim backend/.env
# Change: OPENAI_API_KEY=sk-YOUR-NEW-KEY-HERE

# 3. Restart backend
lsof -ti:8000 | xargs kill
cd backend
python main.py
```

---

## ✅ Quick Test (3 minutes)

### 1. Open Frontend
```
http://localhost:8080
```

### 2. Open Browser Console (F12)

### 3. Click "Start Session"

### 4. Wait 10-20 seconds
Look for these logs in console:

```
📊 Frame sent: {"count":1}           ← Frames being captured
📊 Emotion received: {...}            ← Hume AI working
📊 Interval complete: {...}           ← Aggregation working
📊 Coaching advice: {...}             ← LLM working! ✅
```

**If you see "Coaching advice" → SUCCESS!** 🎉

### 5. Stop Session

### 6. Visualize Data
```bash
cd backend
./visualize_session.sh
```

---

## 🎯 What to Check

### Backend Terminal:
```
✅ HTTP/1.1 200 OK  (good - OpenAI working)
❌ HTTP/1.1 401 Unauthorized (bad - fix key!)
```

### Browser Console:
```
✅ "Coaching advice" messages (GPT-4 responses)
❌ Only emotions/intervals (LLM not triggering)
```

### Visualization:
```
✅ Purple dashed lines on emotion plot (LLM updates)
✅ LLM Updates timeline plot appears
✅ Coaching advice printed in terminal
```

---

## 📊 Expected Output

### Successful Test Session:
- **10-20 frames** sent
- **3-6 emotions** detected
- **3-6 intervals** completed
- **1-2 LLM updates** generated ✅

### Data File:
```bash
ls -lh backend/session_data.json
# Should be 2-10 KB
```

### Plots Generated:
1. Emotion timeseries (with LLM markers)
2. Investor state timeline
3. LLM updates timeline
4. Emotion trends (if --trends)

---

## 🐛 Common Issues

### Issue: "401 Unauthorized"
**Fix**: Update OpenAI key in `.env` and restart

### Issue: No coaching advice in console
**Check**:
- Did you wait 5+ seconds? (LLM triggers after 5 intervals)
- Is OpenAI key valid? (check backend logs for 200 OK)

### Issue: "session_data.json not found"
**Fix**: Backend not started or session not run
```bash
cd backend
python main.py
# Then run session in browser
```

### Issue: Speech recognition errors
**Status**: Non-critical, emotion detection still works

---

## 🚀 All Commands in One Place

```bash
# Fix OpenAI key (do this first!)
vim backend/.env
# OPENAI_API_KEY=sk-YOUR-NEW-KEY-HERE

# Restart backend
lsof -ti:8000 | xargs kill
cd backend
python main.py

# Open frontend (in browser)
# http://localhost:8080

# After session, visualize
cd backend
./visualize_session.sh

# Or with all options:
python visualize_emotions.py session_data.json --trends --prompts --output ./plots/
```

---

## ✅ Success Criteria

You'll know it's working when you see:

1. ✅ Purple "LLM #1" markers on emotion plot
2. ✅ "Coaching advice" in browser console
3. ✅ "HTTP/1.1 200 OK" in backend logs
4. ✅ LLM prompts and responses printed

**If all 4 appear → FULLY WORKING!** 🎊

---

**Read `IMPLEMENTATION_COMPLETE.md` for full details.**
