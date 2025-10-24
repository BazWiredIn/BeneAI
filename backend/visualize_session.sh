#!/bin/bash
#
# BeneAI Session Visualization Script
# Visualizes emotions, intervals, and LLM updates from session_data.json
#

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         BeneAI Session Visualization                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if session_data.json exists
if [ ! -f "session_data.json" ]; then
    echo "❌ Error: session_data.json not found!"
    echo ""
    echo "Please run a session first:"
    echo "  1. Start backend: python main.py"
    echo "  2. Open frontend: http://localhost:8080"
    echo "  3. Click 'Start Session' and run for 10-20 seconds"
    echo "  4. Stop session and run this script again"
    echo ""
    exit 1
fi

# Check if data file is empty
if [ ! -s "session_data.json" ]; then
    echo "❌ Error: session_data.json is empty!"
    echo ""
    echo "No data has been collected yet. Run a session first."
    echo ""
    exit 1
fi

echo "📊 Found session data file: session_data.json"
echo ""

# Run visualization with all features
echo "🎨 Generating visualizations..."
echo ""

python visualize_emotions.py session_data.json --trends --prompts

echo ""
echo "✅ Visualization complete!"
echo ""
echo "💡 Tip: Run with --output to save plots:"
echo "   ./visualize_session.sh output_dir/"
echo ""
