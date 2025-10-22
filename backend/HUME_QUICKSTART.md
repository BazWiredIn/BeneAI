# Hume AI Quick Start Guide

Get Hume AI running in BeneAI in 5 minutes.

## 1. Get API Key

Visit https://platform.hume.ai/ → API Keys → Create New Key

## 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

## 3. Configure

Add to `backend/.env`:

```bash
HUME_API_KEY=your-hume-api-key-here
HUME_USE_PRIMARY=true  # Use Hume instead of Luxand
```

## 4. Test

```bash
cd backend
python test_hume.py
```

Expected: ✅ Successfully connected to Hume AI WebSocket

## 5. Run

```bash
uvicorn main:app --reload --port 8000
```

Visit: http://localhost:8000 → Should show `"hume": true` in services

## Done! 🎉

Your backend now uses Hume AI for:
- **Facial expressions** (53 emotions vs Luxand's 7)
- **Speech prosody** (from audio)
- **Emotional language** (from text)

## Switching Between Hume and Luxand

**Use Hume as primary:**
```bash
HUME_USE_PRIMARY=true
```

**Use Luxand as primary (Hume as fallback):**
```bash
HUME_USE_PRIMARY=false
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Connection failed | Check API key in `.env` |
| No emotions detected | Verify image quality (good lighting) |
| Slow performance | Reduce `HUME_FRAME_RATE=2.0` |

## What's Different?

### Before (Luxand only):
```json
{
  "emotion": "happiness",
  "confidence": 0.78,
  "investor_state": "positive"
}
```

### After (Hume AI):
```json
{
  "emotion": "Admiration",
  "confidence": 0.78,
  "investor_state": "positive",
  "top_emotions": [
    {"name": "Admiration", "score": 0.78},
    {"name": "Interest", "score": 0.65},
    {"name": "Concentration", "score": 0.52}
  ],
  "service": "hume"
}
```

## Resources

- Full docs: `HUME_SETUP.md`
- Test script: `test_hume.py`
- Hume docs: https://dev.hume.ai/docs

---

Need help? Check `HUME_SETUP.md` for detailed troubleshooting.
