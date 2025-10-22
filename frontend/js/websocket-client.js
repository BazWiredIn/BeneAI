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
                // Handle emotion detection result from Luxand
                if (this.onEmotionCallback) {
                    this.onEmotionCallback(message);
                }
                debug('Emotion result:', message.investor_state, message.confidence);
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
     * Disconnect
     */
    disconnect() {
        if (this.ws) {
            this.isConnected = false;
            this.ws.close();
        }
    }
}

// Export
window.WebSocketClient = WebSocketClient;
