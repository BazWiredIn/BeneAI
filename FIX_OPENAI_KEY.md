# OpenAI API Key Issue - FIX REQUIRED

## Problem

Backend logs show:
```
HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 401 Unauthorized"
```

**This means your OpenAI API key is either expired, invalid, or missing.**

---

## Current Status

✅ **OpenAI key exists** in `backend/.env`
❌ **Key is getting 401 Unauthorized** from OpenAI API
⚠️ **System is using fallback advice** instead of GPT-4

---

## How to Fix

### 1. Get a Valid OpenAI API Key

Go to: https://platform.openai.com/api-keys

- Sign in to your OpenAI account
- Click "Create new secret key"
- Copy the key (starts with `sk-proj-...` or `sk-...`)

### 2. Update `.env` File

Edit `backend/.env`:

```bash
# Replace the existing key with your new key
OPENAI_API_KEY=sk-YOUR-NEW-KEY-HERE
```

### 3. Restart Backend

```bash
# Stop current backend (Ctrl+C)

# Restart
cd backend
python main.py
```

---

## How to Verify It's Working

After restart, backend logs should show:

**Before fix (BROKEN):**
```
INFO: HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 401 Unauthorized" ❌
INFO: Coaching advice sent: Close strong. Discuss next steps. (fallback advice)
```

**After fix (WORKING):**
```
INFO: HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK" ✅
INFO: Coaching advice sent: Great engagement! They're showing strong interest... (actual GPT-4 response)
```

**In browser console:**
```
📊 [time] Coaching advice: {"advice":"Great engagement!..."} ✅
```

---

## Temporary Workaround

The system works without a valid OpenAI key but will only provide generic fallback advice:
- "Close strong. Discuss next steps." (for positive states)
- "Slow down. Emphasize key wins clearly." (for evaluative states)
- etc.

To get real GPT-4 coaching, you **must** fix the API key.

---

## Cost Warning

OpenAI API usage is **not free**. GPT-4 Turbo costs approximately:
- **$0.01 per 1,000 input tokens** (~750 words)
- **$0.03 per 1,000 output tokens**

Each 5-second coaching update sends ~200-300 tokens and receives ~30 tokens.

**Estimated cost:**
- 1-minute session: ~$0.005 (half a cent)
- 10-minute session: ~$0.05 (5 cents)
- 1-hour session: ~$0.30 (30 cents)

Make sure you have credits on your OpenAI account!

---

## Test After Fixing

1. **Restart backend** with new key
2. **Open frontend**: http://localhost:8080
3. **Click "Start Session"**
4. **Wait for 5-10 seconds** (until first LLM update)
5. **Check browser console** for:
   ```
   📊 Coaching advice: {...}
   ```
6. **Check backend logs** for:
   ```
   HTTP/1.1 200 OK ✅
   ```

If you see 200 OK, it's working! 🎉

---

**Fix this before testing the visualization system!**
