# Testing Hume AI with Photos - Quick Guide

## Quick Start

### Test with an Image File

```bash
cd backend
python test_with_photo.py path/to/your/photo.jpg
```

**Example:**
```bash
python test_with_photo.py ~/Pictures/selfie.jpg
```

---

## Usage Options

### 1️⃣ Test with Image File (Recommended)

```bash
python test_with_photo.py photo.jpg
```

**What happens:**
- ✅ Loads your image
- ✅ Sends to Hume AI
- ✅ Shows emotion analysis results
- ✅ Displays top 10 emotions with visualization
- ✅ Gives investor state interpretation

**Best for:** Testing with existing photos

---

### 2️⃣ Test with Webcam (Interactive)

```bash
python test_with_photo.py --webcam
```

**What happens:**
- ✅ Opens your webcam
- ✅ Shows live video feed
- ✅ Press **SPACE** to capture
- ✅ Analyzes captured frame

**Requires:** `opencv-python` package
```bash
pip install opencv-python
```

**Best for:** Quick testing with your face

---

### 3️⃣ Test Language Analysis

```bash
python test_with_photo.py --text "I'm really excited about this opportunity!"
```

**What happens:**
- ✅ Analyzes emotional content of text
- ✅ Shows emotion for each word
- ✅ Displays confidence scores

**Best for:** Testing language emotion detection

---

## Example Output

### Facial Emotion Analysis

```
============================================================
Testing Facial Emotion Analysis
============================================================
Image: selfie.jpg

📸 Encoding image...
✅ Image encoded (234567 bytes)

🔌 Connecting to Hume AI...
✅ Connected successfully

🧠 Analyzing facial emotions...

============================================================
✅ RESULTS
============================================================

🎯 Primary Emotion: Joy
📊 Confidence: 78.5%
💼 Investor State: POSITIVE

🔝 Top 10 Emotions:
────────────────────────────────────────────────────────────
 1. Joy                      ████████████████████████████████ 78.5%
 2. Admiration               ████████████████████████ 61.2%
 3. Interest                 ███████████████████ 52.3%
 4. Excitement               ████████████████ 45.1%
 5. Calmness                 ████████████ 34.2%
 6. Satisfaction             ██████████ 28.7%
 7. Concentration            ████████ 23.5%
 8. Amusement                ███████ 19.8%
 9. Contemplation            █████ 15.2%
10. Curiosity                ████ 11.6%

============================================================
📝 Interpretation:
============================================================
🎉 Great! The person appears engaged and positive.
   Coaching: Continue with your current approach, move toward close.

============================================================
```

---

## Tips for Best Results

### For Photos:

✅ **Good lighting** - Face should be well-lit
✅ **Clear face** - Face should be visible and in focus
✅ **Forward-facing** - Best results when facing camera
✅ **Close-up** - Face should fill a good portion of frame

❌ **Avoid:**
- Very dark or backlit photos
- Blurry images
- Face too small in frame
- Sunglasses covering eyes

### Supported Image Formats:
- ✅ JPG/JPEG
- ✅ PNG
- ✅ BMP
- ✅ WebP

---

## Troubleshooting

### Error: "No face detected"

**Causes:**
- Face not visible or too small
- Poor lighting
- Face at extreme angle

**Fix:**
- Use a clearer photo
- Try the webcam option to capture a new photo
- Ensure good lighting

---

### Error: "File not found"

**Cause:** Image path is incorrect

**Fix:**
```bash
# Use absolute path
python test_with_photo.py /Users/yourname/Pictures/photo.jpg

# Or relative path from backend directory
python test_with_photo.py ../photos/selfie.jpg
```

---

### Error: "Failed to connect to Hume AI"

**Causes:**
- API key not set in `.env`
- No internet connection
- Invalid API key

**Fix:**
1. Check your `.env` file has `HUME_API_KEY`
2. Verify internet connection
3. Test basic connection: `python test_hume.py`

---

### Webcam not working

**Error:** `opencv-python not installed`

**Fix:**
```bash
pip install opencv-python
```

**Error:** `Could not open webcam`

**Fixes:**
- Check webcam permissions
- Close other apps using webcam
- Try different camera index (if multiple cameras)

---

## Understanding Results

### Investor States

| State | Meaning | Coaching Advice |
|-------|---------|----------------|
| **positive** | 🎉 Engaged, enthusiastic | Move toward close |
| **receptive** | 👂 Open, interested | Share more details |
| **evaluative** | 🤔 Thinking, analyzing | Give time for questions |
| **skeptical** | ⚠️  Doubtful, concerned | Address concerns directly |
| **neutral** | 😐 No strong emotion | Engage with a question |

### Top Emotions Explained

**High Scores (>60%):**
- **Joy** - Happy, pleased
- **Admiration** - Impressed, respectful
- **Excitement** - Energetic, enthusiastic
- **Interest** - Curious, engaged

**Medium Scores (30-60%):**
- **Concentration** - Focused, attentive
- **Contemplation** - Thoughtful, considering
- **Calmness** - Relaxed, composed
- **Curiosity** - Inquisitive, wondering

**Low Scores (<30%):**
- Generally background emotions
- Less dominant in expression

---

## Next Steps

### After Testing with Photos

1. ✅ **Verified it works?** → Start the full backend
   ```bash
   uvicorn main:app --reload --port 8000
   ```

2. ✅ **Want real-time analysis?** → Run the frontend
   ```bash
   cd frontend
   python -m http.server 8080
   # Open http://localhost:8080
   ```

3. ✅ **Integration working?** → Test with Chrome extension

---

## Quick Commands Reference

```bash
# Test with photo
python test_with_photo.py photo.jpg

# Test with webcam
python test_with_photo.py --webcam

# Test language
python test_with_photo.py --text "Your text here"

# Show help
python test_with_photo.py --help
```

---

## Need More Help?

- **Full docs:** See `HUME_SETUP.md`
- **API issues:** See `HUME_QUICKSTART.md`
- **Backend setup:** See `RUN_HUME_LOCALLY.md`

**Happy testing! 🚀**
