/**
 * Audio Analyzer
 * Analyzes speech using Web Audio API and Web Speech API
 */

class AudioAnalyzer {
    constructor() {
        this.audioContext = null;
        this.analyzer = null;
        this.recognition = null;
        this.isListening = false;

        // Metrics
        this.transcript = '';
        this.wordCount = 0;
        this.startTime = null;
        this.speakingTime = 0;
        this.silenceTime = 0;
        this.fillerWordCount = 0;
        this.volumeLevel = 0;

        // Buffers
        this.transcriptBuffer = [];
        this.volumeBuffer = [];

        // Error handling with exponential backoff
        this.restartAttempts = 0;
        this.maxRestartAttempts = 3;
        this.restartDelay = 1000; // Start with 1 second
        this.speechAvailable = true; // Track if speech recognition is available
    }

    /**
     * Initialize audio analysis
     */
    async initialize() {
        try {
            // Get microphone stream
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            // Set up Web Audio API
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const source = this.audioContext.createMediaStreamSource(stream);
            this.analyzer = this.audioContext.createAnalyser();
            this.analyzer.fftSize = 2048;
            source.connect(this.analyzer);

            // Set up Web Speech API
            this.setupSpeechRecognition();

            debug('Audio analyzer initialized');
            return true;
        } catch (error) {
            console.error('Failed to initialize audio:', error);
            return false;
        }
    }

    /**
     * Set up Web Speech Recognition
     */
    setupSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            console.warn('Speech Recognition not supported');
            return;
        }

        this.recognition = new SpeechRecognition();
        this.recognition.lang = CONFIG.SPEECH.lang;
        this.recognition.continuous = CONFIG.SPEECH.continuous;
        this.recognition.interimResults = CONFIG.SPEECH.interimResults;
        this.recognition.maxAlternatives = CONFIG.SPEECH.maxAlternatives;

        this.recognition.onstart = () => {
            // Reset restart attempts on successful start
            this.restartAttempts = 0;
            this.speechAvailable = true;
            debug('Speech recognition started successfully');
        };

        this.recognition.onresult = (event) => {
            const last = event.results.length - 1;
            const text = event.results[last][0].transcript;

            if (event.results[last].isFinal) {
                this.transcriptBuffer.push(text);
                this.wordCount += text.split(' ').length;

                // Keep only last 30 seconds of transcript (rough estimate)
                if (this.transcriptBuffer.length > 30) {
                    this.transcriptBuffer.shift();
                }

                this.transcript = this.transcriptBuffer.join(' ');
                this.countFillerWords(text);

                debug('Speech recognized:', text);
            }
        };

        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);

            // Handle network errors with backoff
            if (event.error === 'network') {
                this.restartAttempts++;
                console.warn(`Speech recognition network error (attempt ${this.restartAttempts}/${this.maxRestartAttempts})`);

                if (this.restartAttempts >= this.maxRestartAttempts) {
                    this.isListening = false;
                    this.speechAvailable = false;
                    console.warn('⚠️ Speech recognition unavailable after multiple attempts. Continuing with emotion-only analysis.');
                    debug('Speech recognition disabled due to repeated network errors');
                }
            }
            // Handle other errors that should stop recognition
            else if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
                this.isListening = false;
                this.speechAvailable = false;
                console.error('Speech recognition not allowed. Please check microphone permissions.');
            }
        };

        this.recognition.onend = () => {
            // Auto-restart with exponential backoff if still listening
            if (this.isListening && this.speechAvailable) {
                if (this.restartAttempts < this.maxRestartAttempts) {
                    // Calculate exponential backoff delay
                    const delay = this.restartDelay * Math.pow(2, this.restartAttempts);
                    debug(`Restarting speech recognition in ${delay}ms (attempt ${this.restartAttempts + 1})`);

                    setTimeout(() => {
                        if (this.isListening) {
                            try {
                                this.recognition.start();
                            } catch (error) {
                                console.error('Failed to restart speech recognition:', error);
                            }
                        }
                    }, delay);
                } else {
                    debug('Speech recognition not restarting (max attempts reached)');
                }
            }
        };
    }

    /**
     * Start listening
     */
    start() {
        if (!this.audioContext || !this.recognition) {
            console.error('Audio not initialized');
            return;
        }

        this.isListening = true;
        this.startTime = Date.now();
        this.recognition.start();

        // Start volume monitoring
        this.monitorVolume();

        debug('Audio analysis started');
    }

    /**
     * Stop listening
     */
    stop() {
        this.isListening = false;

        if (this.recognition) {
            this.recognition.stop();
        }

        debug('Audio analysis stopped');
    }

    /**
     * Monitor volume levels
     */
    monitorVolume() {
        if (!this.isListening) return;

        const dataArray = new Uint8Array(this.analyzer.frequencyBinCount);
        this.analyzer.getByteTimeDomainData(dataArray);

        // Calculate RMS (Root Mean Square) for volume
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
            const normalized = (dataArray[i] - 128) / 128;
            sum += normalized * normalized;
        }
        const rms = Math.sqrt(sum / dataArray.length);

        this.volumeLevel = rms;
        this.volumeBuffer.push(rms);

        // Keep buffer size manageable
        if (this.volumeBuffer.length > 100) {
            this.volumeBuffer.shift();
        }

        // Continue monitoring
        requestAnimationFrame(() => this.monitorVolume());
    }

    /**
     * Count filler words in text
     */
    countFillerWords(text) {
        const lowerText = text.toLowerCase();
        CONFIG.SPEECH_THRESHOLDS.fillerWords.forEach(filler => {
            const regex = new RegExp(`\\b${filler}\\b`, 'g');
            const matches = lowerText.match(regex);
            if (matches) {
                this.fillerWordCount += matches.length;
            }
        });
    }

    /**
     * Get current metrics
     */
    getMetrics() {
        const elapsedMinutes = this.startTime ?
            (Date.now() - this.startTime) / 60000 : 0;

        const wordsPerMinute = elapsedMinutes > 0 ?
            Math.round(this.wordCount / elapsedMinutes) : 0;

        const avgVolume = this.volumeBuffer.length > 0 ?
            this.volumeBuffer.reduce((a, b) => a + b, 0) / this.volumeBuffer.length :
            0;

        // Calculate pause frequency (rough estimate based on volume)
        const silenceThreshold = 0.01;
        const silentFrames = this.volumeBuffer.filter(v => v < silenceThreshold).length;
        const pauseFrequency = this.volumeBuffer.length > 0 ?
            silentFrames / this.volumeBuffer.length : 0;

        return {
            wordsPerMinute,
            fillerWords: {
                total: this.fillerWordCount,
                breakdown: {} // Could be expanded
            },
            pauseFrequency: Math.round(pauseFrequency * 100) / 100,
            volumeLevel: Math.round(avgVolume * 100) / 100,
            energyLevel: Math.round(avgVolume * 100) / 100,
            speakingTime: elapsedMinutes * 60,
            recentTranscript: this.transcript.slice(-500) // Last 500 chars
        };
    }

    /**
     * Reset metrics
     */
    reset() {
        this.transcript = '';
        this.wordCount = 0;
        this.startTime = null;
        this.fillerWordCount = 0;
        this.transcriptBuffer = [];
        this.volumeBuffer = [];
    }
}

// Export
window.AudioAnalyzer = AudioAnalyzer;
