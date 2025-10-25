/**
 * Video Processor
 * Captures video frames and sends to backend for emotion detection
 * Uses Web Worker for non-blocking JPEG encoding to reduce latency
 */

class VideoProcessor {
    constructor() {
        this.stream = null;
        this.isProcessing = false;
        this.frameCount = 0;
        this.captureInterval = null;
        this.onFrameCaptureCallback = null;
        this.videoElement = null;
        this.canvasElement = null;
        this.canvasCtx = null;

        // Web Worker for non-blocking encoding
        this.encodingWorker = null;
        this.workerReady = false;
        this.pendingFrames = 0;  // Track frames being encoded
        this.maxPendingFrames = 2;  // Drop frames if encoding backs up

        // Initialize Web Worker
        this.initWorker();
    }

    /**
     * Initialize Web Worker for encoding
     */
    initWorker() {
        try {
            this.encodingWorker = new Worker('js/video-worker.js');

            this.encodingWorker.addEventListener('message', (event) => {
                const { type, frameData, frameNumber, size, error } = event.data;

                switch (type) {
                    case 'ready':
                        debug('Video encoding worker ready');
                        break;

                    case 'initialized':
                        this.workerReady = true;
                        debug('Video encoding worker initialized');
                        break;

                    case 'encoded':
                        // Frame encoded successfully
                        this.pendingFrames--;
                        debug(`Frame ${frameNumber} encoded (${(size / 1024).toFixed(1)}KB, ${this.pendingFrames} pending)`);

                        // Call the callback with encoded frame data
                        if (this.onFrameCaptureCallback) {
                            this.onFrameCaptureCallback(frameData);
                        }
                        break;

                    case 'error':
                        this.pendingFrames--;
                        console.error('Worker encoding error:', error);
                        break;
                }
            });

            this.encodingWorker.addEventListener('error', (error) => {
                console.error('Worker error:', error);
            });

        } catch (error) {
            console.error('Failed to initialize Web Worker:', error);
            debug('Web Worker not supported, falling back to synchronous encoding');
        }
    }

    /**
     * Initialize webcam
     */
    async initialize(videoElement, canvasElement) {
        debug('Initializing webcam...');

        this.videoElement = videoElement;
        this.canvasElement = canvasElement;
        this.canvasCtx = canvasElement.getContext('2d');

        try {
            // Request webcam access
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: CONFIG.VIDEO.width,
                    height: CONFIG.VIDEO.height,
                    facingMode: 'user'
                },
                audio: false
            });

            // Attach stream to video element
            this.videoElement.srcObject = this.stream;
            await this.videoElement.play();

            debug('Webcam initialized');

            // Initialize worker with video dimensions (once video is ready)
            if (this.encodingWorker && this.videoElement.videoWidth > 0) {
                this.encodingWorker.postMessage({
                    type: 'init',
                    data: {
                        width: this.videoElement.videoWidth,
                        height: this.videoElement.videoHeight
                    }
                });
            }

        } catch (error) {
            console.error('Failed to initialize webcam:', error);
            throw new Error('Could not access webcam: ' + error.message);
        }
    }

    /**
     * Start capturing frames
     */
    async start() {
        if (!this.stream) {
            throw new Error('Video processor not initialized');
        }

        this.isProcessing = true;

        // Start capturing frames at configured rate (exactly 3 FPS)
        const captureRate = CONFIG.PROCESSING.targetFPS ?
            1000 / CONFIG.PROCESSING.targetFPS :
            333; // ~3 FPS default

        this.captureInterval = setInterval(() => {
            if (this.isProcessing) {
                this.captureFrame();
            }
        }, captureRate);

        debug('Video frame capture started');
    }

    /**
     * Stop capturing frames
     */
    stop() {
        this.isProcessing = false;

        if (this.captureInterval) {
            clearInterval(this.captureInterval);
            this.captureInterval = null;
        }

        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }

        // Terminate worker
        if (this.encodingWorker) {
            this.encodingWorker.terminate();
            this.encodingWorker = null;
            this.workerReady = false;
            debug('Video encoding worker terminated');

            // Re-initialize worker for next start
            this.initWorker();
        }

        debug('Video frame capture stopped');
    }

    /**
     * Capture a frame and send to worker for encoding
     * Uses async createImageBitmap to avoid blocking main thread
     */
    async captureFrame() {
        try {
            // Frame dropping: skip if too many frames pending encoding
            if (this.pendingFrames >= this.maxPendingFrames) {
                debug(`Dropping frame ${this.frameCount + 1} (${this.pendingFrames} frames pending encoding)`);
                return;
            }

            // Resize canvas to match video (for local preview)
            this.canvasElement.width = this.videoElement.videoWidth;
            this.canvasElement.height = this.videoElement.videoHeight;

            // Draw current video frame to canvas (for local preview)
            this.canvasCtx.drawImage(
                this.videoElement,
                0, 0,
                this.canvasElement.width,
                this.canvasElement.height
            );

            this.frameCount++;

            // Use Web Worker for encoding if available
            if (this.encodingWorker && this.workerReady) {
                // Create ImageBitmap from video (async, but fast)
                const imageBitmap = await createImageBitmap(this.videoElement);

                // Send to worker for encoding (non-blocking)
                this.pendingFrames++;
                this.encodingWorker.postMessage({
                    type: 'encode',
                    data: {
                        imageBitmap: imageBitmap,
                        quality: 0.6,  // JPEG quality
                        frameNumber: this.frameCount
                    }
                }, [imageBitmap]);  // Transfer ImageBitmap (zero-copy)

                debug(`Frame ${this.frameCount} sent to worker (${this.pendingFrames} pending)`);

            } else {
                // Fallback: synchronous encoding (if worker not available)
                const frameData = this.canvasElement.toDataURL('image/jpeg', 0.6);

                if (this.onFrameCaptureCallback) {
                    this.onFrameCaptureCallback(frameData);
                }

                debug(`Frame ${this.frameCount} captured (sync fallback)`);
            }

        } catch (error) {
            console.error('Error capturing frame:', error);
        }
    }

    /**
     * Set callback for frame capture
     */
    onFrameCapture(callback) {
        this.onFrameCaptureCallback = callback;
    }

    /**
     * Draw emotion overlay on canvas (optional visual feedback)
     */
    drawEmotionOverlay(emotionData) {
        if (!emotionData || !emotionData.detected) {
            return;
        }

        const ctx = this.canvasCtx;
        const rect = emotionData.face_rectangle;

        if (rect) {
            // Draw bounding box
            ctx.strokeStyle = '#10b981';
            ctx.lineWidth = 3;
            ctx.strokeRect(
                rect.left,
                rect.top,
                rect.right - rect.left,
                rect.bottom - rect.top
            );

            // Draw emotion label
            ctx.fillStyle = '#10b981';
            ctx.font = '16px sans-serif';
            ctx.fillText(
                `${emotionData.emotion} (${(emotionData.confidence * 100).toFixed(0)}%)`,
                rect.left,
                rect.top - 10
            );
        }
    }
}

// Export
window.VideoProcessor = VideoProcessor;
