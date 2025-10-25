# BeneAI Performance Testing - Quick Start Guide

## 🎯 What This Framework Does

Test BeneAI's end-to-end pipeline performance by:
1. Processing a constant test video through multiple parameter configurations
2. Measuring **latency**, **throughput**, and **accuracy** for each configuration
3. Comparing results to find optimal settings for your use case
4. Generating visualizations and recommendations

## ⚡ 5-Minute Setup

### Step 1: Install Dependencies (1 min)

```bash
cd testing
pip install -r requirements.txt
```

### Step 2: Add Your Test Video (1 min)

```bash
# Copy your video to the videos directory
cp /path/to/your/test_video.mp4 videos/test_video.mp4
```

**Tip**: Use a 15-30 second video with clear facial expressions for best results.

### Step 3: Create Ground Truth Annotations (2-3 min)

```bash
# Copy the template
cp ground_truth_template.json videos/test_video_annotations.json

# Edit the file (use any text editor)
nano videos/test_video_annotations.json
```

**Quick annotation example:**
```json
{
  "video": "test_video.mp4",
  "fps": 30,
  "annotations": [
    {"timestamp": 2.0, "emotion": "Curiosity", "investor_state": "evaluative", "confidence": 0.9},
    {"timestamp": 5.0, "emotion": "Interest", "investor_state": "receptive", "confidence": 0.95},
    {"timestamp": 8.0, "emotion": "Contemplation", "investor_state": "evaluative", "confidence": 0.8}
  ]
}
```

Add an annotation every 2-5 seconds where emotions are clearly visible.

### Step 4: Start Backend (30 sec)

```bash
# In a separate terminal
cd ../backend
python -m uvicorn app.main:app --reload
```

Verify at http://localhost:8000

### Step 5: Run the Notebook (30 sec)

```bash
jupyter notebook performance_test.ipynb
```

**In the notebook:**
1. Run all cells in order (Cell → Run All)
2. Wait for tests to complete (progress bar shows status)
3. Review results and visualizations
4. Check `results/` directory for exported files

## 📊 What You'll Get

### Immediate Results

- **Performance tables**: Latency, throughput, accuracy for each configuration
- **Visual charts**:
  - Latency by frame rate, resolution, complexity
  - Throughput vs target FPS
  - Accuracy by parameters
  - Confusion matrix showing emotion detection accuracy
  - Latency vs accuracy tradeoff

### Recommendations

The notebook automatically identifies:
- **Lowest latency** config (best for real-time responsiveness)
- **Highest accuracy** config (best for precision)
- **Best balanced** config (⭐ recommended for production)
- **Highest throughput** config (best for batch processing)

### Example Output

```
Best Balanced Configuration:
  fps3_res480x360_q60_mc1_conf0.5

Metrics:
  Latency: 387ms avg (p95: 455ms)
  Throughput: 2.89 fps
  F1 Score: 0.847

Recommendation: Use this for production deployment
```

## 🔧 Configuration Options

### Quick Test (3-5 minutes)

Test a small subset first:

```python
# In notebook Section 4
RUN_SUBSET = True
SUBSET_CONFIGS = TEST_CONFIGS[::20]  # ~7 tests
```

### Full Test (20-40 minutes)

Test all configurations:

```python
# In notebook Section 4
RUN_ALL_TESTS = True  # ~135 tests
```

### Custom Parameters

Edit the parameter grid in Section 1:

```python
PARAM_GRID = {
    'frame_rates': [2, 3, 5],  # Your specific rates
    'resolutions': [(480, 360)],  # Single resolution
    'mediapipe_complexities': [1],  # Medium only
    'mediapipe_confidences': [0.5]  # Default only
}
# This creates only 3 test configurations
```

## 📈 Interpreting Results

### Good Latency
- **< 300ms**: Excellent (feels instant)
- **300-500ms**: Good (acceptable for real-time)
- **500-1000ms**: Fair (noticeable delay)
- **> 1000ms**: Poor (too slow for real-time)

### Good Accuracy (F1 Score)
- **> 0.85**: Excellent
- **0.75-0.85**: Good
- **0.65-0.75**: Fair
- **< 0.65**: Needs improvement

### Throughput
- Should be close to target FPS
- If throughput << target FPS, system is struggling

## 🐛 Common Issues

### "Cannot connect to backend"
```bash
# Check if backend is running
curl http://localhost:8000
# If not, start it:
cd ../backend && python -m uvicorn app.main:app --reload
```

### "Video file not found"
```bash
# Verify video exists
ls -la videos/
# Update path in notebook Section 1:
CONFIG['video_path'] = 'videos/your_video.mp4'
```

### "No accuracy metrics"
- Ground truth file is optional
- Tests run performance-only without it
- To add accuracy metrics, create annotations file

### Tests are slow
- Use shorter video (15-30 seconds)
- Test subset first (RUN_SUBSET = True)
- Reduce parameter grid

## 🎓 Tips for Best Results

### Annotation Tips
1. **Watch once through** - Note timestamps of clear emotions
2. **Be specific** - Use exact Hume AI emotion names
3. **Annotate transitions** - Mark when emotions clearly change
4. **Add notes** - Document what facial cues you saw
5. **Be consistent** - Use same emotion for same expressions

### Testing Strategy
1. **Start small**: Run 3-5 configs first to verify everything works
2. **Review initial results**: Check if metrics make sense
3. **Adjust parameters**: Focus on promising ranges
4. **Run comprehensive**: Full grid once confident
5. **Test multiple videos**: Validate findings across different content

### Production Deployment
1. Use **"Best Balanced"** recommendation as starting point
2. A/B test with users if possible
3. Monitor real-world latency (may differ from test)
4. Re-test periodically as backend improves

## 📁 File Structure Summary

```
testing/
├── QUICKSTART.md              ← You are here
├── README.md                  ← Full documentation
├── performance_test.ipynb     ← Main notebook
├── test_utils.py              ← Helper functions
├── requirements.txt           ← Dependencies
├── ground_truth_template.json ← Annotation template
├── videos/
│   ├── test_video.mp4        ← Your video
│   └── test_video_annotations.json ← Your annotations
└── results/
    └── [auto-generated files]
```

## 🚀 Next Steps

1. **Run your first test**: Follow steps 1-5 above
2. **Review results**: Check visualizations and recommendations
3. **Apply to production**: Update your deployment config
4. **Iterate**: Test with different videos, refine parameters
5. **Monitor**: Track real-world performance

## 💡 Use Cases

### Scenario 1: "I want the fastest possible response"
- Review "Lowest Latency" recommendation
- Expect some accuracy tradeoff
- Good for live demos where responsiveness matters most

### Scenario 2: "I need the most accurate emotion detection"
- Review "Highest Accuracy" recommendation
- Accept higher latency if needed
- Good for analysis/research where precision is critical

### Scenario 3: "I want good balance for production"
- Use "Best Balanced" recommendation ⭐
- Optimizes for both speed and accuracy
- **Recommended starting point**

### Scenario 4: "I'm processing recorded videos in batch"
- Review "Highest Throughput" recommendation
- Latency less important than volume
- Good for offline analysis

## 📞 Need Help?

1. Check **troubleshooting** in README.md
2. Review notebook comments and markdown cells
3. Inspect test_utils.py for implementation details
4. Check BeneAI backend logs for errors

---

**Happy testing! 🎉**

Questions? Check the full README.md for detailed documentation.
