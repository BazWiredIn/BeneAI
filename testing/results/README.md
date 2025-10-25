# Test Results Directory

This directory contains the outputs from performance testing runs.

## Generated Files

Each test run creates files with timestamp suffix `YYYYMMDD_HHMMSS`:

### CSV Results
- `test_results_YYYYMMDD_HHMMSS.csv` - Tabular results for all test configurations

### JSON Results
- `test_results_detailed_YYYYMMDD_HHMMSS.json` - Complete results with frame-level data

### Visualizations
- `latency_analysis_YYYYMMDD_HHMMSS.png` - Latency breakdown by parameters
- `throughput_analysis_YYYYMMDD_HHMMSS.png` - Throughput analysis charts
- `accuracy_analysis_YYYYMMDD_HHMMSS.png` - Accuracy metrics by parameters
- `latency_accuracy_tradeoff_YYYYMMDD_HHMMSS.png` - Latency vs accuracy scatter
- `confusion_matrix_YYYYMMDD_HHMMSS.png` - Emotion detection confusion matrix

### Recommendations
- `recommendations_YYYYMMDD_HHMMSS.txt` - Configuration recommendations

## Note

Results are gitignored by default to avoid committing large files.
To share results, export specific files manually.
