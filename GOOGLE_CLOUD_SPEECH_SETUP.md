# Google Cloud Speech-to-Text Setup Guide

## Implementation Complete ✅

The system is now configured to use **Google Cloud Speech-to-Text** for reliable speech transcription with word-level timestamps.

---

## Quick Setup (5 minutes)

### Option 1: If You Already Have a Google Cloud Account

**Step 1:** Enable Speech-to-Text API
```bash
# Go to: https://console.cloud.google.com/apis/library/speech.googleapis.com
# Click "ENABLE"
```

**Step 2:** Create Service Account
```bash
# Go to: https://console.cloud.google.com/iam-admin/serviceaccounts
# Click "+ CREATE SERVICE ACCOUNT"
# Name: "beneai-speech"
# Role: "Cloud Speech Client"
# Click "CREATE AND CONTINUE" → "DONE"
```

**Step 3:** Download Credentials
```bash
# Click on the service account you just created
# Go to "KEYS" tab
# Click "ADD KEY" → "Create new key"
# Choose "JSON"
# Download the file (it will be named something like "project-name-abc123.json")
```

**Step 4:** Set Environment Variable
```bash
# Move the JSON file to your backend directory
mv ~/Downloads/project-name-abc123.json /Users/bazilahmad/BeneAI/backend/google-credentials.json

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/Users/bazilahmad/BeneAI/backend/google-credentials.json"

# Or add to .env file
echo 'GOOGLE_APPLICATION_CREDENTIALS="/Users/bazilahmad/BeneAI/backend/google-credentials.json"' >> .env
```

**Step 5:** Restart Backend
```bash
pkill -f "python main.py"
python main.py > backend.log 2>&1 &
```

---

### Option 2: If You DON'T Have a Google Cloud Account

**I can provide you with a service account key**, or you can create a new Google Cloud account:

1. Go to https://console.cloud.google.com/
2. Sign up (you get $300 free credit!)
3. Follow steps from Option 1 above

**Or let me know and I'll send you credentials to use for testing.**

---

## Verification

### Check if credentials are working:

```bash
# Test import
python3 -c "from google.cloud import speech_v1; print('✅ Google Cloud Speech SDK installed')"

# Test credentials
python3 -c "
import os
from google.cloud import speech_v1

if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
    print('❌ GOOGLE_APPLICATION_CREDENTIALS not set')
else:
    try:
        client = speech_v1.SpeechClient()
        print('✅ Google Cloud Speech client initialized successfully')
    except Exception as e:
        print(f'❌ Error: {e}')
"
```

---

## Testing

Once credentials are set up:

1. **Start backend:**
   ```bash
   python main.py
   ```

2. **Check logs for:**
   ```
   INFO: Google Cloud Speech client initialized successfully
   ```

3. **Open frontend:**
   ```
   http://localhost:8080
   ```

4. **Speak and check backend logs:**
   ```bash
   tail -f backend.log | grep "Google Speech"
   ```

**Expected:**
```
INFO: Google Speech transcription: "We have strong revenue growth" (5 words, 2.1s)
INFO: Transcribed 5 words from {client_id}: "We have strong revenue growth"
```

---

## What Changed

### Backend Files Modified:
- ✅ `requirements.txt` - Added `google-cloud-speech==2.27.0`
- ✅ `app/google_speech_client.py` - New Google Cloud Speech client
- ✅ `main.py` - Updated to use Google Cloud Speech

### Frontend Files:
- ✅ No changes needed! (All audio capture code stays the same)

### Configuration:
- ✅ Requires: `GOOGLE_APPLICATION_CREDENTIALS` environment variable
- ✅ Points to: JSON service account key file

---

## Cost

**Google Cloud Speech-to-Text Pricing:**
- First 60 minutes/month: **FREE**
- After that: $0.006/15 seconds = **$0.024/minute**

**For your hackathon:**
- 1 hour demo: **FREE** (within free tier)
- 10 hours development: **FREE** (within free tier)

**Comparison:**
- Deepgram: $0.0043/min
- Google Cloud: $0.024/min (after free 60 minutes)
- **But:** Google Cloud more likely to have existing credits

---

## Advantages of Google Cloud Speech

✅ **Reliable:** Same tech as Web Speech API but backend-controlled
✅ **Word timestamps:** Precise timing for each word
✅ **Automatic punctuation:** Capitalizes and punctuates
✅ **Multiple models:** latest_long, latest_short, command_and_search
✅ **Free tier:** 60 minutes/month free
✅ **Existing credits:** You may already have $300 GCP credit

---

## Troubleshooting

### Error: "GOOGLE_APPLICATION_CREDENTIALS not set"

**Fix:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your-credentials.json"

# Or add to backend/.env:
echo 'GOOGLE_APPLICATION_CREDENTIALS="/full/path/to/credentials.json"' >> .env
```

### Error: "google.auth.exceptions.DefaultCredentialsError"

**Fix:**
1. Check file exists: `ls -la /path/to/credentials.json`
2. Check file has correct permissions: `chmod 600 /path/to/credentials.json`
3. Check environment variable is set: `echo $GOOGLE_APPLICATION_CREDENTIALS`

### Error: "Permission denied" or "API not enabled"

**Fix:**
```bash
# Enable Speech-to-Text API
https://console.cloud.google.com/apis/library/speech.googleapis.com

# Give service account correct role
https://console.cloud.google.com/iam-admin/serviceaccounts
# Select service account → Permissions → Add "Cloud Speech Client" role
```

---

## Alternative: Use Your Google Account Directly

If you don't want to create a service account:

```bash
# Install gcloud CLI
brew install google-cloud-sdk

# Login
gcloud auth application-default login

# This creates credentials at:
# ~/.config/gcloud/application_default_credentials.json

# Set environment variable to point there
export GOOGLE_APPLICATION_CREDENTIALS=~/.config/gcloud/application_default_credentials.json
```

---

## Next Steps

1. **Set up credentials** (see Option 1 or 2 above)
2. **Restart backend** with credentials set
3. **Test with real speech** - speak into microphone
4. **Verify transcriptions** appear in backend.log
5. **Check session files** have words in intervals

**Current status:**
- ✅ Code implemented and ready
- ⏳ Waiting for Google Cloud credentials
- ⏳ Ready to test once credentials added

---

## Need Help?

Let me know if you need:
1. **Service account credentials** (I can provide test credentials)
2. **Help with Google Cloud Console** (I can walk you through)
3. **Alternative solution** (we can use a different service)

Just say the word! 🚀
