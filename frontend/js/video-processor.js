/**
 * Video Processor
 * Captures video frames and sends to backend for Luxand emotion detection
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

        debug('Video frame capture stopped');
    }

    /**
     * Capture a frame and send to backend
     */
    captureFrame() {
        try {
            // Resize canvas to match video
            this.canvasElement.width = this.videoElement.videoWidth;
            this.canvasElement.height = this.videoElement.videoHeight;

            // Draw current video frame to canvas
            this.canvasCtx.drawImage(
                this.videoElement,
                0, 0,
                this.canvasElement.width,
                this.canvasElement.height
            );

            // Convert canvas to base64 JPEG
            const frameData = this.canvasElement.toDataURL('image/jpeg', 0.8);

            // Callback with frame data
            if (this.onFrameCaptureCallback) {
                this.onFrameCaptureCallback(frameData);
            }

            this.frameCount++;
            debug(`Frame ${this.frameCount} captured`);

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
