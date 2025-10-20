# BeneAI Installation Guide for Judges

**Time Required:** 5 minutes
**Browser:** Google Chrome (required)

---

## Quick Install (3 Steps)

### Step 1: Download Extension (30 seconds)

**Option A: From USB Drive**
- Copy `beneai-extension.zip` from provided USB drive to your computer
- Extract the ZIP file (right-click → Extract All)

**Option B: From GitHub** (if internet available)
```bash
# Download from: https://github.com/your-org/BeneAI/releases/latest
# Or clone repo:
git clone https://github.com/your-org/BeneAI.git
cd BeneAI/extension
```

### Step 2: Load Extension in Chrome (2 minutes)

1. **Open Chrome Extensions Page**
   - Type `chrome://extensions` in address bar and press Enter
   - Or: Menu (⋮) → More Tools → Extensions

2. **Enable Developer Mode**
   - Look for toggle in top-right corner
   - Switch it ON (should turn blue)

3. **Load Unpacked Extension**
   - Click "Load unpacked" button
   - Navigate to the extracted `beneai-extension` folder
   - Select the folder and click "Select Folder"

4. **Verify Installation**
   - You should see "BeneAI" tile appear
   - Green status indicator
   - Version 1.0.0

![Installation Screenshot](https://via.placeholder.com/600x300?text=Chrome+Extensions+Page)

### Step 3: Grant Permissions (2 minutes)

When you first use BeneAI, Chrome will ask for permissions:

- **Camera & Microphone:** Required to analyze your video call
- **Tab Capture:** Required to access video stream
- **Storage:** Required to save your preferences

Click "Allow" for each permission.

**Note:** BeneAI processes everything locally in your browser. No video or audio is uploaded to servers.

---

## Try It Out!

### Quick Test (2 minutes)

1. **Join a Test Call**
   - Go to: https://meet.google.com/new
   - Click "Join now"
   - Allow camera and microphone access

2. **Look for BeneAI Overlay**
   - Small widget should appear in bottom-right corner
   - Shows your current emotional state
   - Click to expand for more details

3. **Test Emotion Detection**
   - Smile → Should detect "positive"
   - Frown → Should detect "concerned"
   - Raise eyebrows → Should detect "surprised"

4. **Test Speech Analysis**
   - Start talking
   - Speak very quickly without pausing
   - You should see advice appear: "Slow down to 140 WPM"

**If you see the overlay and it responds to your expressions, it's working! 🎉**

---

## Detailed Instructions (If You Need More Help)

### For Windows Users

1. **Download and Extract**
   ```
   1. Download beneai-extension.zip
   2. Right-click → "Extract All..."
   3. Choose destination (e.g., Desktop)
   4. Click "Extract"
   ```

2. **Open Chrome Extensions**
   ```
   1. Open Google Chrome
   2. Press Ctrl+Shift+E (shortcut)
   OR
   1. Click three dots menu (⋮) in top-right
   2. More tools → Extensions
   ```

3. **Load Extension**
   ```
   1. Toggle "Developer mode" ON (top-right)
   2. Click "Load unpacked" (top-left)
   3. Navigate to extracted folder
   4. Select the "extension" folder
   5. Click "Select Folder"
   ```

### For Mac Users

1. **Download and Extract**
   ```
   1. Download beneai-extension.zip
   2. Double-click to extract
   3. Move to convenient location (e.g., Desktop)
   ```

2. **Open Chrome Extensions**
   ```
   1. Open Google Chrome
   2. Press Cmd+Shift+E (shortcut)
   OR
   1. Chrome menu → More Tools → Extensions
   ```

3. **Load Extension**
   ```
   1. Toggle "Developer mode" ON (top-right)
   2. Click "Load unpacked" (top-left)
   3. Navigate to extracted folder
   4. Select the "extension" folder
   5. Click "Open"
   ```

### For Linux Users

1. **Download and Extract**
   ```bash
   unzip beneai-extension.zip -d ~/Desktop/beneai-extension
   ```

2. **Open Chrome Extensions**
   - Navigate to `chrome://extensions`

3. **Load Extension**
   - Enable Developer mode
   - Load unpacked
   - Select `~/Desktop/beneai-extension`

---

## Troubleshooting

### Problem: "Load unpacked" button is grayed out

**Solution:** You need to enable "Developer mode" first
- Look for toggle switch in top-right corner of chrome://extensions page
- Click it to turn ON (should become blue)
- "Load unpacked" button should now be clickable

---

### Problem: Extension loads but doesn't work on Google Meet

**Solution:** Refresh the Google Meet page
- Close the Meet tab
- Open new tab and go to https://meet.google.com/new
- Join call again
- Extension should now activate

---

### Problem: Permission denied errors

**Solution:** Grant all requested permissions
1. Click extension icon in Chrome toolbar
2. Click "Permissions" or "Manage extensions"
3. Ensure all permissions are enabled:
   - ✓ Read and change all your data on websites
   - ✓ Use your microphone
   - ✓ Use your camera
   - ✓ Communicate with cooperating websites

---

### Problem: Overlay doesn't appear

**Checklist:**
- [ ] Extension is installed and enabled (green indicator)
- [ ] You're on a supported video platform (Google Meet, Zoom Web, Teams)
- [ ] Camera and microphone are active in the call
- [ ] You've refreshed the page after installing extension
- [ ] Check browser console (F12) for error messages

**Still not working?**
- Try restarting Chrome completely
- Ensure you're using Google Chrome (not Chromium, Brave, or Edge)
- Check that backend service is running (ask team)

---

### Problem: "Failed to load extension" error

**Common Causes:**

1. **Wrong folder selected**
   - Make sure you select the `extension` folder, not the parent folder
   - The folder should contain `manifest.json` file

2. **Manifest file error**
   - Ensure you extracted the ZIP completely
   - Don't modify any files before loading

3. **Chrome version too old**
   - Update Chrome to latest version (Settings → About Chrome)
   - BeneAI requires Chrome 88+

---

## Permissions Explained

BeneAI requests these permissions:

| Permission | Why We Need It | What We Do With It |
|------------|----------------|-------------------|
| **Camera** | Analyze facial expressions | Processed locally, never uploaded |
| **Microphone** | Analyze speech patterns | Processed locally, never uploaded |
| **Tab Capture** | Access video call stream | Only active during video calls |
| **Storage** | Save preferences | Store settings like "show/hide overlay" |
| **Host Permissions** | Work on Meet/Zoom/Teams | Only active on video call sites |

**Privacy Promise:**
- ✅ All video processing happens in your browser
- ✅ We never record or store your video/audio
- ✅ Only anonymized metrics sent to backend (e.g., "user looks concerned")
- ✅ No personally identifiable information collected

---

## Uninstalling

If you want to remove BeneAI:

1. Go to `chrome://extensions`
2. Find "BeneAI"
3. Click "Remove"
4. Confirm deletion

All data is removed immediately.

---

## System Requirements

- **Browser:** Google Chrome 88+ (latest recommended)
- **OS:** Windows 10+, macOS 10.14+, Linux (any modern distro)
- **RAM:** 4GB minimum (8GB recommended)
- **Internet:** Required for backend API calls
- **Camera:** Any webcam (built-in or external)
- **Microphone:** Any microphone (built-in or external)

---

## Supported Video Platforms

| Platform | Status | Notes |
|----------|--------|-------|
| Google Meet | ✅ Fully Supported | Best experience |
| Zoom Web App | ✅ Fully Supported | Must use web version, not desktop app |
| Microsoft Teams Web | ✅ Fully Supported | Web version only |
| Zoom Desktop App | ⚠️ Limited | Screen capture required, slower |
| Teams Desktop App | ⚠️ Limited | Screen capture required, slower |
| Skype | ❌ Not Supported | Future roadmap |
| Slack Huddles | ❌ Not Supported | Future roadmap |

---

## Getting Help

### During Hackathon Demo

- Ask the presenting team member for assistance
- They can demonstrate on their laptop if yours has issues

### After Demo

- **GitHub Issues:** https://github.com/your-org/BeneAI/issues
- **Email:** team@beneai.com
- **Documentation:** Full docs at https://beneai.com/docs

---

## What to Expect During Demo

### First Launch (30 seconds)
- Extension icon appears in toolbar
- Loading MediaPipe models (~2MB download)
- "BeneAI initialized" notification

### During Call (Real-time)
- Small overlay widget in corner
- Updates every 2-3 seconds
- Emotion indicator (color-coded)
- Speech metrics (WPM, pauses, filler words)
- Coaching advice streams in word-by-word

### Performance
- **Latency:** <500ms from detection to advice
- **CPU Usage:** ~10-15% (MediaPipe processing)
- **Memory:** ~100-150MB (models + processing)
- **Network:** ~1KB per update (minimal)

---

## Advanced Options (Optional)

### Customize Settings

Click extension icon in toolbar to:
- Toggle overlay on/off
- Adjust sensitivity (how often advice appears)
- Change overlay position
- Enable/disable specific features

### Developer Console

For technical users:
1. Press F12 to open Chrome DevTools
2. Go to Console tab
3. Look for `[BeneAI]` logs
4. Can see real-time metrics and debug info

---

## Feedback

We'd love to hear what you think!

**Quick Survey** (2 minutes):
https://forms.gle/your-survey-link

**What to share:**
- Did it work on first try?
- Was installation easy?
- Did advice seem helpful?
- Any bugs or issues?
- Feature suggestions?

---

## Thank You!

Thanks for trying BeneAI! We hope it helps you nail your next high-stakes video call.

**Built by:** [Your Team Name]
**Hackathon:** [Hackathon Name]
**Date:** October 2024

**Questions? Ask us at the booth!** 🚀

---

## Quick Reference Card

```
┌─────────────────────────────────────────┐
│         BENEAI QUICK REFERENCE          │
├─────────────────────────────────────────┤
│ Install:                                │
│  1. chrome://extensions                 │
│  2. Enable "Developer mode"             │
│  3. Load unpacked → select folder       │
├─────────────────────────────────────────┤
│ Use:                                    │
│  1. Join Google Meet call               │
│  2. Look for overlay in corner          │
│  3. Smile/frown to test                 │
│  4. Talk to get pacing feedback         │
├─────────────────────────────────────────┤
│ Troubleshoot:                           │
│  • Refresh page after install           │
│  • Grant all permissions                │
│  • Check F12 console for errors         │
├─────────────────────────────────────────┤
│ Help:                                   │
│  • Ask team member at booth             │
│  • See full docs in QUICKSTART.md       │
└─────────────────────────────────────────┘
```

---

*This guide is designed to be printed and handed out at the hackathon demo booth.*
