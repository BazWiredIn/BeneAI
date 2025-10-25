# BeneAI Performance Testing Framework - Summary

## ✅ What Was Created

A comprehensive testing framework for iteratively testing and optimizing BeneAI's emotion detection pipeline.

### Core Files

1. **`performance_test.ipynb`** (35.8 KB)
   - Main Jupyter notebook with 7 sections
   - Automated parameter sweep testing
   - Real-time progress tracking
   - Rich visualizations and analysis
   - Export capabilities

2. **`test_utils.py`** (19.9 KB)
   - `VideoProcessor`: Extract and encode video frames
   - `BeneAIClient`: WebSocket communication with backend
   - `GroundTruth`: Load and validate annotations
   - `MetricsCalculator`: Calculate latency, throughput, accuracy
   - `TestConfig`, `EmotionResult`, `TestResult`: Data classes
   - `run_single_test()`: Execute complete test run
   - `aggregate_results()`: Combine results into DataFrame

3. **`ground_truth_template.json`** (2.8 KB)
   - Comprehensive annotation format specification
   - Example annotations with all fields
   - Emotion reference guide
   - Validation notes

4. **`requirements.txt`** (620 B)
   - All Python dependencies with versions
   - Jupyter, OpenCV, WebSockets
   - pandas, numpy, scikit-learn
   - matplotlib, seaborn, plotly
   - Progress tracking with tqdm

### Documentation

5. **`README.md`** (9.6 KB)
   - Complete framework documentation
   - Directory structure explanation
   - Quick start guide
   - Detailed parameter descriptions
   - Troubleshooting section
   - Best practices
   - Use cases

6. **`QUICKSTART.md`** (7.4 KB)
   - 5-minute setup guide
   - Step-by-step instructions
   - Configuration examples
   - Results interpretation
   - Common issues and solutions
   - Production deployment tips

7. **`SUMMARY.md`** (This file)
   - High-level overview
   - File descriptions
   - Testing capabilities
   - Getting started

### Supporting Structure

8. **`videos/`** directory
   - Place for test videos
   - `.gitkeep` to track in git
   - Instructions in `.gitkeep`

9. **`results/`** directory
   - Auto-generated test results
   - `.gitignore` (don't commit results)
   - `README.md` explaining output files

## 🎯 What It Does

### Testing Capabilities

1. **End-to-End Pipeline Testing**
   - Processes test video through complete BeneAI pipeline
   - Simulates real frontend → backend → LLM flow
   - Measures performance at each step

2. **Parameter Sweep**
   - Tests ~135 parameter combinations (customizable)
   - **Frame Rates**: 1, 2, 3, 5, 10 FPS
   - **Resolutions**: 320×240, 480×360, 640×480
   - **MediaPipe Complexity**: 0 (fast), 1 (medium), 2 (accurate)
   - **MediaPipe Confidence**: 0.3, 0.5, 0.7

3. **Performance Metrics**
   - **Latency**: avg, p50, p95, p99 (milliseconds)
   - **Throughput**: Frames per second
   - **Per-frame timing**: Individual latency measurements

4. **Accuracy Metrics** (with ground truth)
   - **Overall**: Accuracy, Precision, Recall, F1 Score
   - **Per-emotion**: Individual class performance
   - **Confusion Matrix**: Detailed error analysis
   - **Temporal Alignment**: ±0.5s tolerance for matching

5. **Visualization**
   - Latency distributions by parameter
   - Throughput analysis charts
   - Accuracy heatmaps
   - Confusion matrices
   - Latency vs accuracy tradeoffs
   - Parameter impact analysis

6. **Recommendations**
   - Lowest latency configuration
   - Highest accuracy configuration
   - Best balanced configuration (recommended)
   - Highest throughput configuration

## 🚀 Quick Start

### Minimal Setup (5 minutes)

```bash
# 1. Install dependencies
cd testing
pip install -r requirements.txt

# 2. Add test video
cp /path/to/video.mp4 videos/test_video.mp4

# 3. Create annotations
cp ground_truth_template.json videos/test_video_annotations.json
# Edit with your annotations (every 2-5 seconds)

# 4. Start backend (separate terminal)
cd ../backend && python -m uvicorn app.main:app --reload

# 5. Run notebook
jupyter notebook performance_test.ipynb
# Then: Cell → Run All
```

### First Test Run (3-5 configs, ~2-3 minutes)

```python
# In notebook Section 4:
RUN_SUBSET = True
SUBSET_CONFIGS = TEST_CONFIGS[:3]  # Just first 3
```

### Full Test Run (~135 configs, 20-40 minutes)

```python
# In notebook Section 4:
RUN_ALL_TESTS = True
```

## 📊 Expected Outputs

### Files Generated (per test run)

```
results/
├── test_results_20251025_120000.csv              # Tabular results
├── test_results_detailed_20251025_120000.json    # Complete data
├── latency_analysis_20251025_120000.png          # Latency charts
├── throughput_analysis_20251025_120000.png       # Throughput charts
├── accuracy_analysis_20251025_120000.png         # Accuracy charts
├── latency_accuracy_tradeoff_20251025_120000.png # Tradeoff scatter
├── confusion_matrix_20251025_120000.png          # Confusion matrix
└── recommendations_20251025_120000.txt           # Best configs
```

### Key Insights You'll Get

1. **Optimal Configuration** for your use case:
   ```
   Best Balanced: fps3_res480x360_q60_mc1_conf0.5
   - Latency: 387ms avg
   - F1 Score: 0.847
   - Throughput: 2.89 fps
   ```

2. **Parameter Impact Analysis**:
   - Frame rate impact on latency
   - Resolution impact on accuracy
   - MediaPipe complexity tradeoffs
   - Confidence threshold effects

3. **Production Recommendations**:
   - Configuration for real-time use
   - Configuration for batch processing
   - Configuration for maximum accuracy

## 🔧 Customization

### Test Fewer Configurations (Faster)

```python
# Quick 5-test run
PARAM_GRID = {
    'frame_rates': [2, 5],
    'resolutions': [(480, 360)],
    'jpeg_qualities': [60],
    'mediapipe_complexities': [1],
    'mediapipe_confidences': [0.5]
}
# Creates 2 tests (2 frame rates × 1 resolution × 1 quality × 1 complexity × 1 confidence)
```

### Focus on Specific Parameters

```python
# Test only frame rates
PARAM_GRID = {
    'frame_rates': [1, 2, 3, 5, 10],
    'resolutions': [(480, 360)],  # Fixed
    'jpeg_qualities': [60],  # Fixed
    'mediapipe_complexities': [1],  # Fixed
    'mediapipe_confidences': [0.5]  # Fixed
}
# Creates 5 tests
```

### Test Multiple Videos

```python
# Run for video 1
CONFIG['video_path'] = 'videos/pitch_v1.mp4'
CONFIG['ground_truth_path'] = 'videos/pitch_v1_annotations.json'
# Run all cells

# Then change and run again
CONFIG['video_path'] = 'videos/pitch_v2.mp4'
CONFIG['ground_truth_path'] = 'videos/pitch_v2_annotations.json'
# Run all cells again
```

## 📈 Understanding Results

### Latency Benchmarks
- **< 300ms**: Excellent (feels instant)
- **300-500ms**: Good (real-time capable)
- **500-1000ms**: Fair (noticeable but usable)
- **> 1000ms**: Poor (too slow)

### Accuracy Benchmarks (F1 Score)
- **> 0.85**: Excellent
- **0.75-0.85**: Good (production-ready)
- **0.65-0.75**: Fair (needs tuning)
- **< 0.65**: Poor (investigate issues)

### Throughput
- Should be close to target FPS
- If much lower → system is struggling

## 🎓 Best Practices

### For Accurate Results

1. **Use consistent test video**
   - 15-30 seconds ideal
   - Clear facial expressions
   - Good lighting and visibility
   - Representative of real use cases

2. **Quality annotations**
   - Annotate every 2-5 seconds
   - Use specific emotion names
   - Be consistent throughout
   - Document what you observe

3. **Systematic testing**
   - Start with small subset (3-5 configs)
   - Verify everything works
   - Run comprehensive sweep
   - Test multiple videos for validation

### For Production Deployment

1. **Choose "Best Balanced"** as starting point
2. **Validate** with real-world testing
3. **Monitor** actual performance metrics
4. **Re-test** periodically as system improves
5. **A/B test** if possible with users

## 🐛 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Backend not connecting | Check it's running at `http://localhost:8000` |
| Video file not found | Place in `videos/` and update path in notebook |
| Slow tests | Use shorter video, test subset, reduce parameters |
| Low accuracy | Review annotations, check timestamps, verify emotions |
| No accuracy metrics | Ground truth file needed (optional) |

See README.md for detailed troubleshooting.

## 🔬 Technical Details

### Architecture

```
Notebook (testing/performance_test.ipynb)
    ↓
VideoProcessor (test_utils.py)
    ↓ Extract frames at target FPS
    ↓ Encode as JPEG
    ↓
BeneAIClient (test_utils.py)
    ↓ Send via WebSocket
    ↓
Backend (localhost:8000/ws)
    ↓ Hume AI analysis
    ↓ Emotion detection
    ↓ Interval aggregation
    ↓
← Emotion response
    ↓
MetricsCalculator (test_utils.py)
    ↓ Calculate latency, throughput
    ↓ Compare with ground truth
    ↓ Generate metrics
    ↓
Results & Visualizations
```

### Data Flow

1. **Frame Extraction**: OpenCV → numpy array
2. **Encoding**: PIL → JPEG → base64
3. **Transmission**: WebSocket JSON message
4. **Processing**: Backend Hume AI → emotion analysis
5. **Response**: JSON with emotion, state, confidence
6. **Metrics**: sklearn for accuracy, numpy for performance
7. **Visualization**: matplotlib, seaborn for charts

## 📚 File Reference

| File | Purpose | Size |
|------|---------|------|
| `performance_test.ipynb` | Main notebook | 35.8 KB |
| `test_utils.py` | Helper functions | 19.9 KB |
| `ground_truth_template.json` | Annotation format | 2.8 KB |
| `requirements.txt` | Dependencies | 620 B |
| `README.md` | Full documentation | 9.6 KB |
| `QUICKSTART.md` | Quick start guide | 7.4 KB |

## 🎯 Next Steps

1. **Read QUICKSTART.md** for setup instructions
2. **Prepare test video** and annotations
3. **Run first test** with small subset
4. **Review results** and visualizations
5. **Run comprehensive tests** with full parameter grid
6. **Apply recommendations** to production

## 💡 Use Cases

### Research & Development
- Compare emotion detection algorithms
- Optimize system parameters
- Benchmark performance improvements
- Validate accuracy claims

### Production Deployment
- Find optimal configuration
- Validate real-world performance
- Set SLAs and expectations
- Monitor degradation over time

### Quality Assurance
- Regression testing after changes
- Validate accuracy on new content
- Compare versions
- Document performance characteristics

---

## 🎉 You're Ready!

The testing framework is complete and ready to use. Start with QUICKSTART.md for a 5-minute setup, or dive into README.md for comprehensive documentation.

**Questions?** All documentation is included in the `testing/` directory.

**Happy testing! 🚀**
