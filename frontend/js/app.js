/**
 * BeneAI Main Application
 */

class BeneAI {
    constructor() {
        this.videoProcessor = new VideoProcessor();
        this.audioAnalyzer = new AudioAnalyzer();
        this.wsClient = new WebSocketClient();
        this.isRunning = false;
        this.updateInterval = null;

        // UI Elements
        this.elements = {
            startBtn: document.getElementById('start-btn'),
            stopBtn: document.getElementById('stop-btn'),
            status: document.getElementById('status'),
            statusText: document.getElementById('status-text'),
            emotion: document.getElementById('emotion'),
            emotionConfidence: document.getElementById('emotion-confidence'),
            wpm: document.getElementById('wpm'),
            fillerCount: document.getElementById('filler-count'),
            pauseFreq: document.getElementById('pause-freq'),
            adviceContent: document.getElementById('advice-content'),
            webcam: document.getElementById('webcam'),
            outputCanvas: document.getElementById('output-canvas')
        };

        this.initializeUI();
    }

    /**
     * Initialize UI and event listeners
     */
    initializeUI() {
        this.elements.startBtn.addEventListener('click', () => this.start());
        this.elements.stopBtn.addEventListener('click', () => this.stop());

        // Set up WebSocket advice callback
        this.wsClient.onAdvice((advice, isComplete) => {
            this.elements.adviceContent.textContent = advice;
        });

        debug('UI initialized');
    }

    /**
     * Start the application
     */
    async start() {
        debug('Starting BeneAI...');

        try {
            // Update UI
            this.elements.startBtn.disabled = true;
            this.elements.statusText.textContent = 'Initializing...';

            // Initialize video processor
            await this.videoProcessor.initialize(
                this.elements.webcam,
                this.elements.outputCanvas
            );

            // Initialize audio analyzer
            const audioReady = await this.audioAnalyzer.initialize();
            if (!audioReady) {
                throw new Error('Failed to initialize audio');
            }

            // Connect to backend
            this.elements.statusText.textContent = 'Connecting to backend...';
            await this.wsClient.connect();

            // Start video processing
            this.elements.statusText.textContent = 'Starting video analysis...';
            await this.videoProcessor.start();

            // Set up frame capture callback
            this.videoProcessor.onFrameCapture((frameData) => {
                // Send frame to backend via WebSocket
                this.wsClient.sendVideoFrame(frameData);
            });

            // Set up emotion result callback from backend
            this.wsClient.onEmotion((emotionResult) => {
                this.updateEmotionUI(emotionResult);

                // Optional: Draw overlay on canvas
                if (emotionResult.detected) {
                    this.videoProcessor.drawEmotionOverlay(emotionResult);
                }
            });

            // Start audio analysis
            this.elements.statusText.textContent = 'Starting audio analysis...';
            this.audioAnalyzer.start();

            // Start periodic updates
            this.startPeriodicUpdates();

            // Update UI
            this.isRunning = true;
            this.elements.status.classList.add('active');
            this.elements.statusText.textContent = 'Active - Analyzing...';
            this.elements.startBtn.disabled = true;
            this.elements.stopBtn.disabled = false;

            debug('BeneAI started successfully');

        } catch (error) {
            console.error('Failed to start:', error);
            this.elements.statusText.textContent = 'Error: ' + error.message;
            this.elements.startBtn.disabled = false;
            alert('Failed to start: ' + error.message);
        }
    }

    /**
     * Stop the application
     */
    stop() {
        debug('Stopping BeneAI...');

        this.isRunning = false;

        // Stop periodic updates
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }

        // Stop components
        this.videoProcessor.stop();
        this.audioAnalyzer.stop();
        this.wsClient.disconnect();

        // Update UI
        this.elements.status.classList.remove('active');
        this.elements.statusText.textContent = 'Stopped';
        this.elements.startBtn.disabled = false;
        this.elements.stopBtn.disabled = true;

        debug('BeneAI stopped');
    }

    /**
     * Start periodic updates to backend
     */
    startPeriodicUpdates() {
        this.updateInterval = setInterval(() => {
            if (!this.isRunning) return;

            // Get current metrics
            const speechMetrics = this.audioAnalyzer.getMetrics();
            const emotion = {
                emotion: this.videoProcessor.emotionDetector.currentEmotion,
                confidence: this.videoProcessor.emotionDetector.confidence
            };

            // Update speech UI
            this.updateSpeechUI(speechMetrics);

            // Send to backend
            this.wsClient.sendParameters(emotion, speechMetrics);

        }, CONFIG.PROCESSING.updateInterval);

        debug('Periodic updates started');
    }

    /**
     * Update emotion UI
     */
    updateEmotionUI(emotionResult) {
        if (!emotionResult.detected) {
            this.elements.emotion.textContent = 'No Face';
            this.elements.emotion.className = 'emotion-label neutral';
            this.elements.emotionConfidence.style.width = '0%';
            return;
        }

        // Display investor state (for demo scenario)
        const investorState = emotionResult.investor_state || 'neutral';
        const primaryEmotion = emotionResult.emotion || 'neutral';
        const confidence = emotionResult.confidence || 0;

        // Update emotion label with investor state
        this.elements.emotion.textContent =
            investorState.charAt(0).toUpperCase() + investorState.slice(1);

        // Update emotion class based on investor state
        this.elements.emotion.className = `emotion-label ${investorState}`;

        // Update confidence bar
        this.elements.emotionConfidence.style.width = `${confidence * 100}%`;

        // Optional: Add coaching suggestions based on investor state
        this.updateCoachingSuggestion(investorState, confidence);
    }

    /**
     * Update coaching suggestion overlay based on investor state
     */
    updateCoachingSuggestion(investorState, confidence) {
        // Map investor states to coaching suggestions for demo
        const suggestions = {
            'skeptical': '🔴 Investor seems doubtful. Focus on confident posture & clear tone.',
            'evaluative': '🟡 Investor is thinking. Slow down, articulate key wins concisely.',
            'receptive': '🟢 Investor is receptive. Maintain steady tone & confident eye contact.',
            'positive': '🟢 Investor is engaged! Continue with confidence.',
            'neutral': '⚪ Maintain professional demeanor.'
        };

        const suggestion = suggestions[investorState] || suggestions['neutral'];

        // Update advice if available
        if (confidence > 0.3) {
            this.elements.adviceContent.textContent = suggestion;
        }
    }

    /**
     * Update speech metrics UI
     */
    updateSpeechUI(metrics) {
        this.elements.wpm.textContent = metrics.wordsPerMinute;
        this.elements.fillerCount.textContent = metrics.fillerWords.total;
        this.elements.pauseFreq.textContent = `${Math.round(metrics.pauseFrequency * 100)}%`;

        // Color code WPM
        if (metrics.wordsPerMinute < CONFIG.SPEECH_THRESHOLDS.minWPM) {
            this.elements.wpm.style.color = '#f59e0b'; // Warning - too slow
        } else if (metrics.wordsPerMinute > CONFIG.SPEECH_THRESHOLDS.maxWPM) {
            this.elements.wpm.style.color = '#ef4444'; // Danger - too fast
        } else {
            this.elements.wpm.style.color = '#10b981'; // Success - good pace
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    debug('DOM ready, initializing BeneAI...');
    window.app = new BeneAI();
});
