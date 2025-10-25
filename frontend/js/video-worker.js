/**
 * Video Encoding Worker
 * Handles JPEG encoding off the main thread to prevent blocking
 */

let offscreenCanvas = null;
let ctx = null;

// Initialize worker
self.addEventListener('message', async (event) => {
    const { type, data } = event.data;

    switch (type) {
        case 'init':
            // Initialize OffscreenCanvas with dimensions
            const { width, height } = data;
            offscreenCanvas = new OffscreenCanvas(width, height);
            ctx = offscreenCanvas.getContext('2d');

            self.postMessage({ type: 'initialized', success: true });
            break;

        case 'encode':
            // Encode frame to JPEG
            try {
                const { imageBitmap, quality, frameNumber } = data;

                // Draw ImageBitmap to OffscreenCanvas
                ctx.drawImage(imageBitmap, 0, 0);

                // Convert to JPEG blob (async, non-blocking)
                const blob = await offscreenCanvas.convertToBlob({
                    type: 'image/jpeg',
                    quality: quality || 0.6
                });

                // Convert blob to base64
                const base64 = await blobToBase64(blob);

                // Send encoded frame back to main thread
                self.postMessage({
                    type: 'encoded',
                    frameData: base64,
                    frameNumber: frameNumber,
                    size: blob.size
                });

                // Clean up ImageBitmap
                imageBitmap.close();

            } catch (error) {
                self.postMessage({
                    type: 'error',
                    error: error.message
                });
            }
            break;

        default:
            console.error('[Worker] Unknown message type:', type);
    }
});

/**
 * Convert Blob to base64 data URL
 */
function blobToBase64(blob) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
    });
}

// Signal worker is ready
self.postMessage({ type: 'ready' });
