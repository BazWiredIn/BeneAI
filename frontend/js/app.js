/**
 * BeneAI Main Application
 */

class BeneAI {
    constructor() {
        this.videoProcessor = new VideoProcessor();
        this.audioCapture = new AudioCapture();  // NEW: Deepgram-based audio capture
        this.wsClient = new WebSocketClient();
        this.isRunning = false;
        this.updateInterval = null;

        // Store latest emotion data from Hume AI
        this.latestEmotion = {
            investorState: 'neutral',
            primaryEmotion: 'neutral',
            confidence: 0,
            allEmotions: {}
        };

        // Data collection tracking
        this.dataStats = {
            framesSent: 0,
            emotionsReceived: 0,
            intervalsReceived: 0,
            coachingAdviceReceived: 0,
            audioChunksSent: 0  // NEW: Track audio chunks
        };

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
            outputCanvas: document.getElementById('output-canvas'),
            debugLog: document.getElementById('debug-log')
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

            // Initialize audio capture (Deepgram)
            const audioReady = await this.audioCapture.initialize();
            if (!audioReady) {
                throw new Error('Failed to initialize audio capture');
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
                this.dataStats.framesSent++;
                this.logDataCollection('Frame sent', { count: this.dataStats.framesSent });
            });

            // Set up emotion result callback from backend
            this.wsClient.onEmotion((emotionResult) => {
                this.dataStats.emotionsReceived++;

                // Store latest emotion data
                if (emotionResult.detected) {
                    this.latestEmotion = {
                        investorState: emotionResult.investor_state || 'neutral',
                        primaryEmotion: emotionResult.emotion || 'neutral',
                        confidence: emotionResult.confidence || 0,
                        allEmotions: emotionResult.all_emotions || {}
                    };

                    this.logDataCollection('Emotion received', {
                        state: this.latestEmotion.investorState,
                        emotion: this.latestEmotion.primaryEmotion,
                        confidence: this.latestEmotion.confidence.toFixed(2),
                        count: this.dataStats.emotionsReceived
                    });
                }

                this.updateEmotionUI(emotionResult);

                // Optional: Draw overlay on canvas
                if (emotionResult.detected) {
                    this.videoProcessor.drawEmotionOverlay(emotionResult);
                }
            });

            // Set up interval completion callback
            this.wsClient.onInterval((intervalData) => {
                this.dataStats.intervalsReceived++;
                this.logDataCollection('Interval complete', {
                    state: intervalData.investor_state,
                    words: intervalData.words ? intervalData.words.length : 0,
                    count: this.dataStats.intervalsReceived
                });
            });

            // Set up coaching advice callback
            this.wsClient.onCoaching((coachingData) => {
                this.dataStats.coachingAdviceReceived++;
                this.logDataCollection('Coaching advice', {
                    advice: coachingData.coaching_advice,
                    state: coachingData.investor_state,
                    count: this.dataStats.coachingAdviceReceived
                });

                // Update UI with coaching advice
                if (this.elements.adviceContent) {
                    this.elements.adviceContent.textContent = coachingData.coaching_advice;
                }
            });

            // Start audio capture with callback
            this.elements.statusText.textContent = 'Starting audio capture...';
            this.audioCapture.start((audioData) => {
                // Send audio chunk to backend via WebSocket
                this.wsClient.sendAudioChunk(audioData);
                this.dataStats.audioChunksSent++;
                this.logDataCollection('Audio chunk sent', {
                    chunk: audioData.chunkNumber,
                    size: audioData.size,
                    duration: audioData.duration,
                    total: this.dataStats.audioChunksSent
                });
            });

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
        this.audioCapture.stop();
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

            // Note: Audio chunks are sent automatically every 2 seconds via AudioCapture callback
            // Speech metrics (WPM, filler words) will come from Deepgram transcription in backend
            // This interval is mainly for UI updates now

            // Update audio capture metrics in UI
            const captureMetrics = this.audioCapture.getMetrics();
            debug(`Audio capture: ${captureMetrics.chunksProcessed} chunks, ${captureMetrics.totalDuration}s`);

        }, CONFIG.PROCESSING.updateInterval);

        debug('Periodic updates started');
    }

    /**
     * Log data collection to debug panel
     */
    logDataCollection(event, data) {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = `[${timestamp}] ${event}: ${JSON.stringify(data)}`;

        console.log(`📊 ${logEntry}`);

        // Update debug panel if it exists
        if (this.elements.debugLog) {
            const entry = document.createElement('div');
            entry.className = 'debug-entry';
            entry.textContent = logEntry;
            this.elements.debugLog.insertBefore(entry, this.elements.debugLog.firstChild);

            // Keep only last 20 entries
            while (this.elements.debugLog.children.length > 20) {
                this.elements.debugLog.removeChild(this.elements.debugLog.lastChild);
            }
        }

        // Update status text with stats
        if (this.elements.statusText && this.isRunning) {
            this.elements.statusText.textContent =
                `Active - Frames:${this.dataStats.framesSent} | ` +
                `Emotions:${this.dataStats.emotionsReceived} | ` +
                `Intervals:${this.dataStats.intervalsReceived} | ` +
                `Advice:${this.dataStats.coachingAdviceReceived}`;
        }
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

        // Coaching advice comes from LLM via WebSocket (no hardcoded suggestions)
    }

    /**
     * REMOVED: updateCoachingSuggestion (hardcoded advice)
     *
     * Coaching advice now comes exclusively from LLM (GPT-4) via WebSocket.
     * See onCoaching callback in start() method for LLM advice handling.
     */

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
