# BeneAI Deployment Guide

## Overview

This guide covers deploying the BeneAI backend to Google Cloud Run and packaging the Chrome extension for distribution.

## Prerequisites

### Required Accounts
- [x] Google Cloud Platform account
- [x] OpenAI API account
- [x] GitHub account (for version control)

### Required Tools
```bash
# Install Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Install Python 3.11+
python --version  # Should be 3.11 or higher

# Install Node.js (optional, for extension build tools)
node --version  # Should be 18+
```

### Cost Estimate
- **Cloud Run:** $0-10/month (free tier covers development)
- **OpenAI API:** ~$30-50 for hackathon
- **Total:** ~$40-60

---

## Part 1: Backend Deployment (Cloud Run)

### Step 1: Set Up Google Cloud Project

```bash
# Login to Google Cloud
gcloud auth login

# Create new project (or use existing)
gcloud projects create beneai-hackathon --name="BeneAI"

# Set as active project
gcloud config set project beneai-hackathon

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### Step 2: Configure Environment Variables

Create `.env` file in `backend/` directory:

```bash
cd backend
cp .env.example .env
```

Edit `.env`:
```env
# OpenAI Configuration
OPENAI_API_KEY=sk-proj-...your-key-here...
OPENAI_MODEL=gpt-4-turbo
OPENAI_MAX_TOKENS=100
OPENAI_TEMPERATURE=0.7

# Server Configuration
ENVIRONMENT=production
LOG_LEVEL=info
ALLOWED_ORIGINS=*
MAX_CONNECTIONS=100

# Rate Limiting
RATE_LIMIT_MESSAGES_PER_SECOND=10
RATE_LIMIT_BURST=3

# Cache Configuration
CACHE_TTL_SECONDS=300
CACHE_MAX_SIZE=1000
```

### Step 3: Test Locally

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Run locally
uvicorn main:app --reload --port 8000

# Test WebSocket connection (in another terminal)
python test_websocket.py
```

### Step 4: Deploy to Cloud Run

#### Option A: Deploy from Source (Easiest)

```bash
cd backend

# Deploy (will build and deploy in one command)
gcloud run deploy beneai-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY=$OPENAI_API_KEY \
  --set-env-vars ENVIRONMENT=production \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0

# Note: Use --min-instances 1 during demo to avoid cold starts
```

#### Option B: Deploy with Docker (More Control)

```bash
cd backend

# Build Docker image
docker build -t gcr.io/beneai-hackathon/backend:latest .

# Test locally
docker run -p 8000:8080 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  gcr.io/beneai-hackathon/backend:latest

# Push to Google Container Registry
docker push gcr.io/beneai-hackathon/backend:latest

# Deploy to Cloud Run
gcloud run deploy beneai-backend \
  --image gcr.io/beneai-hackathon/backend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY=$OPENAI_API_KEY
```

### Step 5: Configure for Demo Day

**Important:** Set min instances to 1 on demo day to eliminate cold starts.

```bash
# Update service with min instances
gcloud run services update beneai-backend \
  --region us-central1 \
  --min-instances 1

# This keeps one instance warm at all times
# Cost: ~$5/day (only enable during demo)
```

### Step 6: Get Service URL

```bash
# Get the deployed URL
gcloud run services describe beneai-backend \
  --region us-central1 \
  --format='value(status.url)'

# Example output: https://beneai-backend-abc123-uc.a.run.app
```

**Save this URL!** You'll need it for the Chrome extension configuration.

### Step 7: Test Deployment

```bash
# Test health endpoint
curl https://beneai-backend-abc123-uc.a.run.app/

# Expected response:
# {"status": "healthy", "version": "1.0.0"}

# Test WebSocket (requires wscat or similar)
npm install -g wscat
wscat -c wss://beneai-backend-abc123-uc.a.run.app/ws
```

---

## Part 2: Chrome Extension Packaging

### Step 1: Update Backend URL

Edit `extension/utils/websocket.js`:

```javascript
// Update this line with your Cloud Run URL
const BACKEND_URL = "wss://beneai-backend-abc123-uc.a.run.app/ws";
```

### Step 2: Validate Extension Files

Ensure all required files exist:

```bash
cd extension

# Check manifest
cat manifest.json

# Verify icons exist
ls icons/icon-16.png icons/icon-48.png icons/icon-128.png

# Check main files
ls background.js content.js popup.html overlay.html
```

### Step 3: Create ZIP Package

```bash
cd extension

# Create zip (exclude unnecessary files)
zip -r ../beneai-extension.zip . \
  -x "*.DS_Store" \
  -x "node_modules/*" \
  -x ".git/*" \
  -x "*.md"

# Verify zip contents
unzip -l ../beneai-extension.zip
```

### Step 4: Test Extension Locally

1. Open Chrome
2. Navigate to `chrome://extensions`
3. Enable "Developer mode" (toggle in top right)
4. Click "Load unpacked"
5. Select the `extension/` directory
6. Verify extension appears in toolbar

### Step 5: Test End-to-End

1. Open Google Meet (https://meet.google.com/new)
2. Start a test call
3. Open Chrome DevTools (F12)
4. Check console for logs
5. Verify overlay appears
6. Test advice streaming

---

## Part 3: CI/CD Setup (Optional but Recommended)

### GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - id: auth
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Deploy to Cloud Run
        uses: google-github-actions/deploy-cloudrun@v1
        with:
          service: beneai-backend
          region: us-central1
          source: ./backend
          env_vars: |
            ENVIRONMENT=production
          secrets: |
            OPENAI_API_KEY=OPENAI_API_KEY:latest
```

### Set Up Secrets

```bash
# Create service account
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions"

# Grant permissions
gcloud projects add-iam-policy-binding beneai-hackathon \
  --member="serviceAccount:github-actions@beneai-hackathon.iam.gserviceaccount.com" \
  --role="roles/run.admin"

# Create key
gcloud iam service-accounts keys create key.json \
  --iam-account=github-actions@beneai-hackathon.iam.gserviceaccount.com

# Add to GitHub secrets as GCP_SA_KEY
```

---

## Part 4: Monitoring & Debugging

### View Logs

```bash
# Stream logs in real-time
gcloud run services logs tail beneai-backend \
  --region us-central1

# Filter for errors only
gcloud run services logs read beneai-backend \
  --region us-central1 \
  --filter='severity>=ERROR' \
  --limit 50
```

### Monitor Metrics

```bash
# Open Cloud Run dashboard
gcloud run services describe beneai-backend \
  --region us-central1 \
  --format='value(status.url)' | \
  xargs -I {} open "https://console.cloud.google.com/run/detail/us-central1/beneai-backend"
```

### Check OpenAI Usage

```bash
# Visit OpenAI dashboard
open https://platform.openai.com/usage

# Check rate limits
curl https://api.openai.com/v1/usage \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

---

## Part 5: Pre-Demo Checklist

### 24 Hours Before Demo

- [ ] Deploy latest backend version
- [ ] Test WebSocket connection
- [ ] Verify OpenAI API key is working
- [ ] Check rate limits (upgrade to Tier 2 if needed)
- [ ] Package extension ZIP file
- [ ] Test extension on fresh Chrome profile
- [ ] Record backup demo video
- [ ] Print INSTALL.md for judges

### 1 Hour Before Demo

- [ ] Set `--min-instances 1` (keep backend warm)
- [ ] Pre-warm Cloud Run (make a few test requests)
- [ ] Install extension on 2-3 demo laptops
- [ ] Test on real Google Meet call
- [ ] Check internet connection (have phone hotspot ready)
- [ ] Open Cloud Run logs dashboard (for debugging)

### During Demo

- [ ] Monitor Cloud Run logs for errors
- [ ] Have backup demo video ready to play
- [ ] Keep OpenAI dashboard open (check for rate limits)

---

## Part 6: Troubleshooting

### Problem: Cold Start Latency

**Symptom:** First request takes 5-10 seconds

**Solution:**
```bash
# Set min instances to 1
gcloud run services update beneai-backend \
  --min-instances 1 \
  --region us-central1
```

### Problem: WebSocket Connection Fails

**Symptom:** `WebSocket connection failed` in console

**Check:**
1. Verify Cloud Run URL is correct in `websocket.js`
2. Ensure Cloud Run service is deployed
3. Check CORS settings in backend
4. Test with `wscat`:
   ```bash
   wscat -c wss://your-cloud-run-url/ws
   ```

### Problem: OpenAI Rate Limit

**Symptom:** Error `RATE_LIMIT_EXCEEDED` from OpenAI

**Solution:**
1. Upgrade to Tier 2 (requires $50 prepaid)
2. Implement caching (already in backend)
3. Reduce request frequency (increase aggregation window)

### Problem: Extension Not Detecting Video

**Symptom:** No emotion data, overlay not appearing

**Check:**
1. Verify permissions in `manifest.json` include `tabCapture`
2. Check console for permission errors
3. Ensure video call is using WebRTC (Google Meet, Zoom Web)
4. Grant camera/microphone permissions

### Problem: High Latency

**Symptom:** Advice appears >2 seconds after speaking

**Debug:**
```javascript
// Add timing logs in content.js
console.time('capture-to-advice');
// ... send to backend
// ... receive advice
console.timeEnd('capture-to-advice');
```

**Optimize:**
- Reduce video processing FPS (5 instead of 10)
- Increase aggregation window (3s instead of 2s)
- Enable caching on backend
- Use GPT-3.5-turbo for faster responses (less accurate)

---

## Part 7: Cost Optimization

### Development Phase
```bash
# Use min-instances 0 (default)
gcloud run services update beneai-backend \
  --min-instances 0 \
  --region us-central1

# Use GPT-3.5-turbo for testing
# Edit backend/llm.py: model="gpt-3.5-turbo"
```

### Demo Day
```bash
# Enable min-instances 1 (only for demo hours)
gcloud run services update beneai-backend \
  --min-instances 1 \
  --region us-central1

# After demo, revert to 0
gcloud run services update beneai-backend \
  --min-instances 0 \
  --region us-central1
```

### Budget Alerts

```bash
# Set up budget alert
gcloud billing budgets create \
  --billing-account=YOUR_BILLING_ACCOUNT \
  --display-name="BeneAI Budget" \
  --budget-amount=50 \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100
```

---

## Part 8: Rollback Procedure

### If deployment fails:

```bash
# List revisions
gcloud run revisions list \
  --service=beneai-backend \
  --region us-central1

# Rollback to previous revision
gcloud run services update-traffic beneai-backend \
  --region us-central1 \
  --to-revisions=beneai-backend-00001-abc=100
```

### If you need to delete everything:

```bash
# Delete Cloud Run service
gcloud run services delete beneai-backend \
  --region us-central1

# Delete project (CAUTION: deletes everything)
gcloud projects delete beneai-hackathon
```

---

## Part 9: Production Considerations (Post-Hackathon)

### Security
- [ ] Add authentication (JWT tokens)
- [ ] Restrict CORS to specific domains
- [ ] Enable Cloud Armor (DDoS protection)
- [ ] Rotate OpenAI API key regularly
- [ ] Use Secret Manager (not env vars)

### Scaling
- [ ] Increase max-instances for traffic spikes
- [ ] Add Redis for distributed caching
- [ ] Use Cloud Load Balancer
- [ ] Implement connection pooling

### Monitoring
- [ ] Set up Cloud Monitoring dashboards
- [ ] Configure alerts (error rate, latency, costs)
- [ ] Integrate Sentry for error tracking
- [ ] Add custom metrics (advice quality, user satisfaction)

---

## Useful Commands Reference

```bash
# Deploy with all options
gcloud run deploy beneai-backend \
  --source ./backend \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 10 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --set-env-vars ENVIRONMENT=production \
  --set-env-vars OPENAI_API_KEY=$OPENAI_API_KEY

# View service details
gcloud run services describe beneai-backend --region us-central1

# Stream logs
gcloud run services logs tail beneai-backend --region us-central1

# Update environment variable
gcloud run services update beneai-backend \
  --region us-central1 \
  --update-env-vars OPENAI_MODEL=gpt-4-turbo

# Scale service
gcloud run services update beneai-backend \
  --region us-central1 \
  --min-instances 1 \
  --max-instances 20

# Delete service
gcloud run services delete beneai-backend --region us-central1
```

---

## Support

### Documentation
- **Cloud Run:** https://cloud.google.com/run/docs
- **FastAPI:** https://fastapi.tiangolo.com/
- **Chrome Extensions:** https://developer.chrome.com/docs/extensions/

### Troubleshooting
- **Cloud Run Logs:** `gcloud run services logs tail beneai-backend`
- **Extension Console:** Chrome DevTools > Console (F12)
- **OpenAI Status:** https://status.openai.com/

### Contact
For hackathon-related questions, contact your team lead.
