/**
 * WebSocket Client
 * Handles communication with backend
 */

class WebSocketClient {
    constructor() {
        this.ws = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.onAdviceCallback = null;
        this.onEmotionCallback = null;

        // Heartbeat/keepalive to prevent connection timeout
        this.pingInterval = null;
        this.pingIntervalMs = 25000; // Send ping every 25 seconds
    }

    /**
     * Connect to backend
     */
    connect() {
        return new Promise((resolve, reject) => {
            try {
                this.ws = new WebSocket(CONFIG.BACKEND_URL);

                this.ws.onopen = () => {
                    this.isConnected = true;
                    this.reconnectAttempts = 0;
                    debug('WebSocket connected');

                    // Start heartbeat/keepalive ping
                    this.startHeartbeat();

                    resolve();
                };

                this.ws.onmessage = (event) => {
                    this.handleMessage(JSON.parse(event.data));
                };

                this.ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    reject(error);
                };

                this.ws.onclose = () => {
                    this.isConnected = false;
                    this.stopHeartbeat();
                    debug('WebSocket closed');
                    this.attemptReconnect();
                };

            } catch (error) {
                reject(error);
            }
        });
    }

    /**
     * Handle incoming messages
     */
    handleMessage(message) {
        debug('Received:', message.type);

        switch (message.type) {
            case 'connection':
                debug('Connected to server:', message.message);
                break;

            case 'pong':
                debug('Pong received');
                break;

            case 'advice_start':
                this.currentAdvice = '';
                this.showAdviceLoading(true);
                break;

            case 'advice_chunk':
                this.currentAdvice += message.chunk;
                if (this.onAdviceCallback) {
                    this.onAdviceCallback(this.currentAdvice, false);
                }
                break;

            case 'advice_complete':
                this.showAdviceLoading(false);
                if (this.onAdviceCallback) {
                    this.onAdviceCallback(message.full_text, true);
                }
                debug('Advice complete:', message.metadata);
                break;

            case 'emotion_result':
                // Handle emotion detection result from Hume AI
                if (this.onEmotionCallback) {
                    this.onEmotionCallback(message);
                }
                debug('Emotion result:', message.investor_state, message.confidence);
                break;

            case 'interval_complete':
                // Handle 1-second interval completion
                if (this.onIntervalCallback) {
                    this.onIntervalCallback(message.interval);
                }
                debug('Interval complete:', message.interval.investor_state);
                break;

            case 'llm_context_update':
                // Handle LLM coaching advice (every 4-5 seconds)
                if (this.onCoachingCallback) {
                    this.onCoachingCallback(message);
                }
                debug('Coaching advice:', message.coaching_advice);
                break;

            case 'emotion_error':
                console.error('Emotion detection error:', message.message);
                break;

            case 'error':
                console.error('Server error:', message.message);
                this.showError(message.message);
                break;

            case 'status':
                debug('Status:', message.message);
                break;

            default:
                debug('Unknown message type:', message.type);
        }
    }

    /**
     * Send parameters to backend
     */
    sendParameters(emotion, speechMetrics) {
        if (!this.isConnected) {
            debug('Not connected, skipping send');
            return;
        }

        const payload = {
            type: 'parameters',
            timestamp: Date.now(),
            data: {
                emotion: {
                    label: emotion.emotion,
                    confidence: emotion.confidence,
                    landmarks_detected: true,
                    face_count: 1
                },
                speech: speechMetrics
            }
        };

        debug('Sending parameters:', payload);
        this.ws.send(JSON.stringify(payload));
    }

    /**
     * Send video frame for emotion detection
     */
    sendVideoFrame(frameData) {
        if (!this.isConnected) {
            debug('Not connected, skipping frame send');
            return;
        }

        const payload = {
            type: 'video_frame',
            timestamp: Date.now(),
            data: frameData
        };

        // Note: Sending large base64 strings can be slow
        // Consider compression or optimization if needed
        this.ws.send(JSON.stringify(payload));
        debug('Video frame sent');
    }

    /**
     * Send speech metrics to backend
     */
    sendSpeechMetrics(metrics) {
        if (!this.isConnected) {
            debug('Not connected, skipping speech metrics');
            return;
        }

        const payload = {
            type: 'speech_metrics',
            timestamp: Date.now(),
            metrics: metrics
        };

        this.ws.send(JSON.stringify(payload));
        debug('Speech metrics sent:', {
            wordsPerMinute: metrics.wordsPerMinute,
            wordCount: metrics.recentTranscript ? metrics.recentTranscript.split(' ').length : 0
        });
    }

    /**
     * Send ping
     */
    ping() {
        if (!this.isConnected) return;

        const payload = {
            type: 'ping',
            timestamp: Date.now()
        };

        this.ws.send(JSON.stringify(payload));
    }

    /**
     * Attempt reconnection
     */
    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            this.showError('Connection lost. Please refresh the page.');
            return;
        }

        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

        debug(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

        setTimeout(() => {
            this.connect().catch(err => {
                console.error('Reconnection failed:', err);
            });
        }, delay);
    }

    /**
     * Set callback for advice updates
     */
    onAdvice(callback) {
        this.onAdviceCallback = callback;
    }

    /**
     * Set callback for emotion updates
     */
    onEmotion(callback) {
        this.onEmotionCallback = callback;
    }

    /**
     * Set callback for interval updates
     */
    onInterval(callback) {
        this.onIntervalCallback = callback;
    }

    /**
     * Set callback for coaching updates
     */
    onCoaching(callback) {
        this.onCoachingCallback = callback;
    }

    /**
     * Send audio chunk for speech-to-text (Deepgram)
     */
    sendAudioChunk(audioData) {
        if (!this.isConnected) {
            console.warn('⚠️ [WebSocket] Not connected, skipping audio chunk');
            debug('Not connected, skipping audio chunk');
            return;
        }

        console.log(`📤 [WebSocket] Sending audio chunk #${audioData.chunkNumber}`);
        console.log(`   Size: ${audioData.size} bytes, Duration: ${audioData.duration}s`);
        console.log(`   Base64 length: ${audioData.base64.length} chars`);

        const payload = {
            type: 'audio_chunk',
            timestamp: Date.now(),
            data: {
                audio: audioData.base64,
                mimeType: audioData.mimeType,
                duration: audioData.duration,
                chunkNumber: audioData.chunkNumber
            }
        };

        this.ws.send(JSON.stringify(payload));
        console.log(`   ✅ Sent via WebSocket successfully`);
        debug(`Audio chunk sent: #${audioData.chunkNumber} (${audioData.size} bytes, ${audioData.duration}s)`);
    }

    /**
     * Send transcribed text with timestamps (for Hume language analysis)
     */
    sendTranscribedText(text, timestamp, words = null) {
        if (!this.isConnected) {
            debug('Not connected, skipping transcript send');
            return;
        }

        const payload = {
            type: 'transcribed_text',
            data: {
                text: text,
                timestamp: timestamp,
                words: words || []  // Optional word-level timestamps
            }
        };

        this.ws.send(JSON.stringify(payload));
        debug('Transcribed text sent:', text.substring(0, 50));
    }

    /**
     * Show loading state for advice
     */
    showAdviceLoading(show) {
        const loading = document.getElementById('advice-loading');
        if (loading) {
            loading.style.display = show ? 'block' : 'none';
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        const adviceContent = document.getElementById('advice-content');
        if (adviceContent) {
            adviceContent.innerHTML = `<span style="color: #ef4444;">Error: ${message}</span>`;
        }
    }

    /**
     * Start heartbeat/keepalive ping
     */
    startHeartbeat() {
        // Clear any existing interval
        this.stopHeartbeat();

        // Send ping periodically to keep connection alive
        this.pingInterval = setInterval(() => {
            if (this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN) {
                const pingPayload = {
                    type: 'ping',
                    timestamp: Date.now()
                };
                this.ws.send(JSON.stringify(pingPayload));
                console.log('🔄 [WebSocket] Heartbeat ping sent');
            }
        }, this.pingIntervalMs);

        console.log(`✓ [WebSocket] Heartbeat started (every ${this.pingIntervalMs/1000}s)`);
    }

    /**
     * Stop heartbeat/keepalive ping
     */
    stopHeartbeat() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
            console.log('⏹ [WebSocket] Heartbeat stopped');
        }
    }

    /**
     * Disconnect
     */
    disconnect() {
        if (this.ws) {
            this.isConnected = false;
            this.stopHeartbeat();
            this.ws.close();
        }
    }
}

// Export
window.WebSocketClient = WebSocketClient;
