// Configuration
const CONFIG = {
    // Backend WebSocket URL
    // Change this to your Cloud Run URL after deployment
    BACKEND_URL: 'ws://localhost:8000/ws',

    // MediaPipe Configuration
    MEDIAPIPE: {
        modelComplexity: 1,  // 0, 1, or 2 (higher = more accurate but slower)
        minDetectionConfidence: 0.5,
        minTrackingConfidence: 0.5,
        maxNumFaces: 1,
        refineLandmarks: true,
        enableFaceOval: true
    },

    // Video Configuration
    VIDEO: {
        width: 480,  // Reduced from 640 for faster encoding (still plenty for emotion detection)
        height: 360,  // Reduced from 480 for faster encoding
        facingMode: 'user',
        frameRate: 30
    },

    // Processing Configuration
    PROCESSING: {
        targetFPS: 2,  // Target 2 frames per second for emotion analysis (reduced for latency)
        updateInterval: 2000,  // Send updates every 2 seconds
        emotionSmoothingWindow: 5  // Average over last 5 frames
    },

    // Speech Recognition Configuration
    SPEECH: {
        lang: 'en-US',
        continuous: true,
        interimResults: true,
        maxAlternatives: 1
    },

    // Emotion Thresholds
    EMOTION_THRESHOLDS: {
        smile: 0.6,
        frown: 0.5,
        eyebrowRaise: 0.7,
        eyeClose: 0.3
    },

    // Speech Analysis Thresholds
    SPEECH_THRESHOLDS: {
        targetWPM: 140,
        minWPM: 120,
        maxWPM: 160,
        targetPauseFreq: 0.25,
        fillerWords: ['um', 'uh', 'like', 'you know', 'basically', 'actually', 'literally']
    },

    // Debug
    DEBUG: true
};

// Utility function for logging
function debug(...args) {
    if (CONFIG.DEBUG) {
        console.log('[BeneAI]', ...args);

        // Also log to debug panel if it exists
        const debugLog = document.getElementById('debug-log');
        if (debugLog) {
            const timestamp = new Date().toLocaleTimeString();
            const message = args.map(arg =>
                typeof arg === 'object' ? JSON.stringify(arg) : arg
            ).join(' ');

            const logEntry = document.createElement('div');
            logEntry.textContent = `[${timestamp}] ${message}`;
            debugLog.appendChild(logEntry);

            // Keep only last 50 entries
            while (debugLog.children.length > 50) {
                debugLog.removeChild(debugLog.firstChild);
            }

            // Auto-scroll to bottom
            debugLog.scrollTop = debugLog.scrollHeight;
        }
    }
}

// Export
window.CONFIG = CONFIG;
window.debug = debug;
