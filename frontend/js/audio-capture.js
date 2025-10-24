/**
 * Audio Capture
 * Captures audio from microphone and sends chunks for speech-to-text
 * Uses MediaRecorder API for reliable audio streaming
 */

class AudioCapture {
    constructor() {
        this.mediaRecorder = null;
        this.audioStream = null;
        this.isCapturing = false;
        this.onChunkReady = null;

        // Audio chunk settings
        this.chunkInterval = 2000; // 2 seconds per chunk
        this.captureTimer = null;

        // Metrics tracking
        this.chunksProcessed = 0;
        this.totalDuration = 0;
    }

    /**
     * Initialize audio capture
     */
    async initialize() {
        try {
            console.log('🎤 [AudioCapture] Requesting microphone access...');

            // Request microphone access
            this.audioStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,  // Mono audio
                    sampleRate: 16000,  // 16kHz optimal for speech
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            console.log('✅ [AudioCapture] Microphone access granted!');
            console.log('   Audio tracks:', this.audioStream.getAudioTracks().length);

            // Log track settings
            const track = this.audioStream.getAudioTracks()[0];
            if (track) {
                const settings = track.getSettings();
                console.log('   Track settings:', {
                    sampleRate: settings.sampleRate,
                    channelCount: settings.channelCount,
                    deviceId: settings.deviceId
                });
            }

            // Check MediaRecorder support
            if (!MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
                console.warn('⚠️ audio/webm not supported, trying audio/mp4');
                if (!MediaRecorder.isTypeSupported('audio/mp4')) {
                    throw new Error('No supported audio format');
                }
            }

            // Create MediaRecorder
            const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
                ? 'audio/webm;codecs=opus'
                : 'audio/mp4';

            console.log(`📼 [AudioCapture] Creating MediaRecorder with ${mimeType}`);

            this.mediaRecorder = new MediaRecorder(this.audioStream, {
                mimeType: mimeType,
                audioBitsPerSecond: 16000  // Low bitrate for speech
            });

            this.setupRecorderHandlers();

            console.log('✅ [AudioCapture] Audio capture initialized successfully');
            debug('Audio capture initialized');
            return true;

        } catch (error) {
            console.error('❌ [AudioCapture] Failed to initialize:', error);
            console.error('   Error name:', error.name);
            console.error('   Error message:', error.message);
            return false;
        }
    }

    /**
     * Set up MediaRecorder event handlers
     */
    setupRecorderHandlers() {
        let audioChunks = [];

        this.mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        this.mediaRecorder.onstop = () => {
            if (audioChunks.length > 0) {
                this.processAudioChunks(audioChunks);
                audioChunks = [];  // Reset for next chunk
            }
        };

        this.mediaRecorder.onerror = (event) => {
            console.error('MediaRecorder error:', event.error);
        };
    }

    /**
     * Start capturing audio
     */
    start(onChunkCallback) {
        if (!this.mediaRecorder) {
            console.error('MediaRecorder not initialized');
            return false;
        }

        this.onChunkReady = onChunkCallback;
        this.isCapturing = true;
        this.chunksProcessed = 0;

        // Start recording
        this.mediaRecorder.start();

        // Set up interval to stop/restart recording for chunks
        this.captureTimer = setInterval(() => {
            if (this.isCapturing && this.mediaRecorder.state === 'recording') {
                // Stop current recording (triggers onstop → processes chunk)
                this.mediaRecorder.stop();

                // Start new recording for next chunk
                setTimeout(() => {
                    if (this.isCapturing) {
                        this.mediaRecorder.start();
                    }
                }, 50);  // Small delay to ensure clean chunk boundaries
            }
        }, this.chunkInterval);

        debug('Audio capture started');
        return true;
    }

    /**
     * Stop capturing audio
     */
    stop() {
        this.isCapturing = false;

        if (this.captureTimer) {
            clearInterval(this.captureTimer);
            this.captureTimer = null;
        }

        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.stop();
        }

        debug('Audio capture stopped');
    }

    /**
     * Process audio chunks and convert to base64
     */
    async processAudioChunks(chunks) {
        try {
            // Create blob from chunks
            const mimeType = this.mediaRecorder.mimeType;
            const audioBlob = new Blob(chunks, { type: mimeType });

            // Track duration (approximate)
            const duration = this.chunkInterval / 1000;
            this.totalDuration += duration;
            this.chunksProcessed++;

            console.log(`🔊 [AudioCapture] Chunk #${this.chunksProcessed}: ${audioBlob.size} bytes, ${duration}s`);

            // DIAGNOSTIC: Check if blob has actual audio data
            if (audioBlob.size === 0) {
                console.warn(`⚠️ [AudioCapture] Chunk #${this.chunksProcessed} has ZERO bytes! Microphone may not be capturing.`);
            } else if (audioBlob.size < 100) {
                console.warn(`⚠️ [AudioCapture] Chunk #${this.chunksProcessed} very small (${audioBlob.size} bytes) - likely silence`);
            } else {
                console.log(`   ✓ Size looks good (${(audioBlob.size/1024).toFixed(2)} KB)`);
            }

            debug(`Processing audio chunk ${this.chunksProcessed} (${duration}s, ${audioBlob.size} bytes)`);

            // Convert to base64
            const base64Audio = await this.blobToBase64(audioBlob);
            console.log(`   → Base64 length: ${base64Audio.length} chars`);

            // Send to callback if provided
            if (this.onChunkReady) {
                this.onChunkReady({
                    base64: base64Audio,
                    mimeType: mimeType,
                    duration: duration,
                    size: audioBlob.size,
                    chunkNumber: this.chunksProcessed
                });
            }

        } catch (error) {
            console.error('❌ [AudioCapture] Error processing chunk:', error);
        }
    }

    /**
     * Convert Blob to base64
     */
    blobToBase64(blob) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();

            reader.onloadend = () => {
                // Remove data URL prefix (data:audio/webm;base64,)
                const base64 = reader.result.split(',')[1];
                resolve(base64);
            };

            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    }

    /**
     * Get capture metrics
     */
    getMetrics() {
        return {
            chunksProcessed: this.chunksProcessed,
            totalDuration: this.totalDuration,
            isCapturing: this.isCapturing
        };
    }

    /**
     * Clean up resources
     */
    cleanup() {
        this.stop();

        if (this.audioStream) {
            this.audioStream.getTracks().forEach(track => track.stop());
            this.audioStream = null;
        }

        this.mediaRecorder = null;
        debug('Audio capture cleaned up');
    }
}

// Export
window.AudioCapture = AudioCapture;
