# BeneAI Performance Testing Framework

This directory contains a comprehensive testing framework for evaluating BeneAI's end-to-end pipeline performance, including latency, throughput, and emotion detection accuracy.

## 📁 Directory Structure

```
testing/
├── README.md                       # This file
├── performance_test.ipynb          # Main testing notebook
├── test_utils.py                   # Helper functions and utilities
├── requirements.txt                # Python dependencies
├── ground_truth_template.json      # Template for manual annotations
├── videos/                         # Place test videos here
│   └── test_video.mp4             # Your test video
│   └── test_video_annotations.json # Ground truth annotations
└── results/                        # Test results (auto-generated)
    ├── test_results_YYYYMMDD_HHMMSS.csv
    ├── test_results_detailed_YYYYMMDD_HHMMSS.json
    ├── latency_analysis_YYYYMMDD_HHMMSS.png
    ├── throughput_analysis_YYYYMMDD_HHMMSS.png
    ├── accuracy_analysis_YYYYMMDD_HHMMSS.png
    ├── confusion_matrix_YYYYMMDD_HHMMSS.png
    └── recommendations_YYYYMMDD_HHMMSS.txt
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd testing
pip install -r requirements.txt
```

### 2. Prepare Your Test Video

Place your test video in the `videos/` directory:

```bash
cp /path/to/your/video.mp4 videos/test_video.mp4
```

### 3. Create Ground Truth Annotations

Copy the template and annotate your video:

```bash
cp ground_truth_template.json videos/test_video_annotations.json
```

Edit `test_video_annotations.json` and add emotion annotations at key timestamps:

```json
{
  "video": "test_video.mp4",
  "fps": 30,
  "annotations": [
    {
      "timestamp": 2.5,
      "emotion": "Curiosity",
      "investor_state": "evaluative",
      "confidence": 0.9,
      "notes": "Clear eyebrow raise and forward lean"
    },
    ...
  ]
}
```

**Annotation Guidelines:**
- Annotate every 2-5 seconds for comprehensive coverage
- Use clear, observable emotions from the Hume AI emotion set
- Include `investor_state`: receptive, positive, evaluative, skeptical, or neutral
- Add `notes` describing the facial cues you observed
- Set `confidence` (0.0-1.0) based on how clear the emotion is

### 4. Start the BeneAI Backend

Make sure your backend is running:

```bash
cd ../backend
python -m uvicorn app.main:app --reload
```

Verify it's accessible at `http://localhost:8000`

### 5. Run the Notebook

```bash
jupyter notebook performance_test.ipynb
```

Or use Jupyter Lab:

```bash
jupyter lab performance_test.ipynb
```

## 📊 What the Notebook Tests

### Performance Metrics

1. **Latency**
   - Average time from frame send to emotion response
   - p50, p95, p99 percentiles
   - Broken down by parameter configuration

2. **Throughput**
   - Frames processed per second
   - Comparison vs target frame rate
   - Impact of resolution and complexity

3. **Accuracy** (requires ground truth)
   - Precision, Recall, F1 score
   - Per-emotion and overall metrics
   - Confusion matrix
   - Temporal alignment with ±0.5s tolerance

### Parameter Grid

The notebook tests combinations of:

- **Frame Rates**: 1, 2, 3, 5, 10 FPS
- **Resolutions**: 320×240, 480×360, 640×480
- **MediaPipe Complexity**: 0 (fast), 1 (medium), 2 (accurate)
- **MediaPipe Confidence**: 0.3, 0.5, 0.7

**Total configurations**: ~135 tests (can be subset for faster iteration)

## 📈 Outputs

### CSV Results

`test_results_YYYYMMDD_HHMMSS.csv` contains:
- Configuration parameters
- Performance metrics (latency, throughput)
- Accuracy metrics (precision, recall, F1)

### Detailed JSON

`test_results_detailed_YYYYMMDD_HHMMSS.json` includes:
- Full emotion results for each frame
- Complete configuration details
- Per-frame latency measurements

### Visualizations

- **Latency Analysis**: Boxplots by frame rate, resolution, complexity
- **Throughput Analysis**: Target vs actual FPS, distributions
- **Accuracy Analysis**: F1 scores by parameter, precision/recall scatter
- **Confusion Matrix**: Emotion detection accuracy breakdown
- **Tradeoff Charts**: Latency vs accuracy scatter with Pareto optimal

### Recommendations

`recommendations_YYYYMMDD_HHMMSS.txt` provides:
- **Lowest Latency** config (for responsiveness)
- **Highest Accuracy** config (for precision)
- **Best Balanced** config (recommended for production)
- **Highest Throughput** config (for batch processing)

## 🔧 Customization

### Testing a Subset of Configurations

In the notebook, modify Section 4:

```python
# Option 1: Run all tests
RUN_ALL_TESTS = False

# Option 2: Run every Nth config (faster iteration)
RUN_SUBSET = True
SUBSET_CONFIGS = TEST_CONFIGS[::10]  # Every 10th

# Option 3: Run specific indices
RUN_SPECIFIC = False
SPECIFIC_INDICES = [0, 10, 20, 30]
```

### Adjusting Parameter Grid

Modify Section 1 configuration:

```python
PARAM_GRID = {
    'frame_rates': [2, 5],  # Test fewer rates
    'resolutions': [(480, 360)],  # Single resolution
    'jpeg_qualities': [60],
    'mediapipe_complexities': [1],  # Only medium
    'mediapipe_confidences': [0.5]  # Only default
}
```

### Changing Backend URL

Update in Section 1:

```python
CONFIG = {
    'backend_url': 'ws://your-backend.com:8000/ws',
    ...
}
```

## 🎯 Use Cases

### 1. Finding Optimal Production Settings

Run all tests with ground truth to find the best balanced configuration for your use case:

```python
RUN_ALL_TESTS = True
```

Review the "Best Balanced Configuration" recommendation.

### 2. Testing New Video Content

Test with different videos to ensure consistent performance:

```python
CONFIG['video_path'] = 'videos/investor_pitch_v2.mp4'
CONFIG['ground_truth_path'] = 'videos/investor_pitch_v2_annotations.json'
```

### 3. Debugging Performance Issues

Run quick subset tests to diagnose problems:

```python
RUN_SUBSET = True
SUBSET_CONFIGS = TEST_CONFIGS[::20]  # Fast 5-10 tests
```

### 4. Comparing Parameter Changes

Test specific configurations before/after backend changes:

```python
RUN_SPECIFIC = True
SPECIFIC_INDICES = [15, 30, 45]  # Known good configs
```

## 🐛 Troubleshooting

### "Cannot connect to backend"

**Problem**: WebSocket connection fails

**Solution**:
1. Verify backend is running: `curl http://localhost:8000`
2. Check backend logs for errors
3. Ensure WebSocket endpoint is `/ws`
4. Try `ws://127.0.0.1:8000/ws` instead of `localhost`

### "Video file not found"

**Problem**: Can't load test video

**Solution**:
1. Verify file exists: `ls -la videos/`
2. Check file path in notebook config
3. Ensure video is readable: `file videos/test_video.mp4`

### "Ground truth file not found"

**Problem**: Annotations file missing

**Solution**:
1. Copy template: `cp ground_truth_template.json videos/test_video_annotations.json`
2. Edit with your annotations
3. Tests will run without accuracy metrics if file is missing (performance only)

### "Tests are very slow"

**Problem**: Each test takes too long

**Solution**:
1. Use shorter test video (10-30 seconds ideal)
2. Run subset of configurations first
3. Reduce frame rates in parameter grid
4. Check backend isn't overwhelmed (CPU/memory)

### "Accuracy metrics are very low"

**Problem**: Poor F1 scores across all configs

**Solution**:
1. Review ground truth annotations for accuracy
2. Check timestamp alignment (±0.5s tolerance)
3. Verify emotion names match Hume AI emotion set
4. Use more annotations (every 2-5 seconds recommended)
5. Check video quality (lighting, face visibility)

## 📚 Key Files

### `test_utils.py`

Contains helper classes:
- `TestConfig`: Configuration for a single test
- `VideoProcessor`: Extract and encode video frames
- `BeneAIClient`: WebSocket communication with backend
- `GroundTruth`: Load and manage annotations
- `MetricsCalculator`: Calculate performance and accuracy metrics
- `run_single_test()`: Execute a complete test run
- `aggregate_results()`: Combine results into DataFrame

### `ground_truth_template.json`

Reference format for manual annotations:

```json
{
  "video": "video_name.mp4",
  "fps": 30,
  "annotations": [
    {
      "timestamp": 2.5,
      "emotion": "Curiosity",
      "investor_state": "evaluative",
      "confidence": 0.9,
      "notes": "Observable cues"
    }
  ]
}
```

## 🎓 Best Practices

### Annotation Quality

- **Be Consistent**: Use the same emotion labels throughout
- **Be Specific**: Choose the most specific emotion (e.g., "Curiosity" not just "Interest")
- **Be Objective**: Annotate what you observe, not what you think they feel
- **Document Cues**: Use notes field to record facial expressions

### Testing Strategy

1. **Start Small**: Test 3-5 configs first to verify setup
2. **Iterate**: Review initial results, adjust parameters
3. **Go Comprehensive**: Run full grid once confident
4. **Validate**: Test multiple videos to ensure consistency

### Result Interpretation

- **Latency < 500ms**: Good for real-time applications
- **F1 Score > 0.7**: Acceptable accuracy
- **F1 Score > 0.8**: Good accuracy
- **Throughput ≈ Target FPS**: System keeping up with frame rate

## 🤝 Contributing

Found issues or improvements? Please update:
1. Add new metrics in `MetricsCalculator`
2. Add new visualizations in notebook Section 6
3. Document changes in this README

## 📞 Support

For issues:
1. Check troubleshooting section above
2. Review BeneAI main documentation
3. Check backend logs for errors
4. Open issue in BeneAI repository

---

**Happy Testing! 🚀**
