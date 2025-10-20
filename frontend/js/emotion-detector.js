/**
 * Emotion Detector
 * Rule-based emotion detection from MediaPipe facial landmarks
 */

class EmotionDetector {
    constructor() {
        this.emotionHistory = [];
        this.currentEmotion = 'neutral';
        this.confidence = 0;
    }

    /**
     * Detect emotion from facial landmarks
     * @param {Object} landmarks - MediaPipe landmarks
     * @returns {Object} - {emotion: string, confidence: number}
     */
    detect(landmarks) {
        if (!landmarks || landmarks.length === 0) {
            return { emotion: 'neutral', confidence: 0 };
        }

        // Extract key facial features
        const smile = this.detectSmile(landmarks);
        const frown = this.detectFrown(landmarks);
        const eyebrowRaise = this.detectEyebrowRaise(landmarks);
        const eyeClose = this.detectEyeClose(landmarks);

        debug('Features:', { smile, frown, eyebrowRaise, eyeClose });

        // Rule-based classification
        let emotion = 'neutral';
        let confidence = 0.5;

        if (smile > CONFIG.EMOTION_THRESHOLDS.smile) {
            emotion = 'positive';
            confidence = Math.min(smile, 0.95);
        } else if (frown > CONFIG.EMOTION_THRESHOLDS.frown) {
            emotion = 'concerned';
            confidence = Math.min(frown, 0.9);
        } else if (eyebrowRaise > CONFIG.EMOTION_THRESHOLDS.eyebrowRaise) {
            emotion = 'surprised';
            confidence = Math.min(eyebrowRaise, 0.85);
        } else if (eyeClose > (1 - CONFIG.EMOTION_THRESHOLDS.eyeClose)) {
            emotion = 'disengaged';
            confidence = 0.7;
        }

        // Smooth with history
        this.emotionHistory.push(emotion);
        if (this.emotionHistory.length > CONFIG.PROCESSING.emotionSmoothingWindow) {
            this.emotionHistory.shift();
        }

        // Get most common emotion in window
        const smoothedEmotion = this.getMostCommon(this.emotionHistory);

        this.currentEmotion = smoothedEmotion;
        this.confidence = confidence;

        return {
            emotion: smoothedEmotion,
            confidence: confidence
        };
    }

    /**
     * Detect smile based on mouth corner positions
     */
    detectSmile(landmarks) {
        // Mouth corners: 61 (right), 291 (left)
        // Mouth center bottom: 17
        const rightMouth = landmarks[61];
        const leftMouth = landmarks[291];
        const mouthBottom = landmarks[17];

        if (!rightMouth || !leftMouth || !mouthBottom) return 0;

        // Calculate upward movement of corners relative to bottom
        const rightRise = mouthBottom.y - rightMouth.y;
        const leftRise = mouthBottom.y - leftMouth.y;

        const smileIntensity = (rightRise + leftRise) / 2;

        // Normalize to 0-1 range (empirically tuned)
        return Math.max(0, Math.min(1, smileIntensity * 20));
    }

    /**
     * Detect frown based on mouth position
     */
    detectFrown(landmarks) {
        // Mouth corners: 61 (right), 291 (left)
        // Upper lip center: 13
        const rightMouth = landmarks[61];
        const leftMouth = landmarks[291];
        const upperLip = landmarks[13];

        if (!rightMouth || !leftMouth || !upperLip) return 0;

        // Calculate downward movement
        const rightDrop = rightMouth.y - upperLip.y;
        const leftDrop = leftMouth.y - upperLip.y;

        const frownIntensity = (rightDrop + leftDrop) / 2;

        // Normalize
        return Math.max(0, Math.min(1, frownIntensity * 15));
    }

    /**
     * Detect eyebrow raise (surprise/interest)
     */
    detectEyebrowRaise(landmarks) {
        // Right eyebrow: 70
        // Left eyebrow: 300
        // Nose bridge (reference): 168
        const rightBrow = landmarks[70];
        const leftBrow = landmarks[300];
        const noseBridge = landmarks[168];

        if (!rightBrow || !leftBrow || !noseBridge) return 0;

        // Calculate distance between eyebrows and nose
        const rightDistance = noseBridge.y - rightBrow.y;
        const leftDistance = noseBridge.y - leftBrow.y;

        const raiseIntensity = (rightDistance + leftDistance) / 2;

        // Normalize
        return Math.max(0, Math.min(1, raiseIntensity * 10));
    }

    /**
     * Detect eye closure (disengagement/fatigue)
     */
    detectEyeClose(landmarks) {
        // Right eye: top 159, bottom 145
        // Left eye: top 386, bottom 374
        const rightTop = landmarks[159];
        const rightBottom = landmarks[145];
        const leftTop = landmarks[386];
        const leftBottom = landmarks[374];

        if (!rightTop || !rightBottom || !leftTop || !leftBottom) return 0;

        // Calculate eye openness
        const rightOpen = rightBottom.y - rightTop.y;
        const leftOpen = leftBottom.y - leftTop.y;

        const avgOpen = (rightOpen + leftOpen) / 2;

        // Normalize (smaller value = more closed)
        const openness = Math.max(0, Math.min(1, avgOpen * 50));

        return 1 - openness; // Return closeness instead
    }

    /**
     * Get most common element in array
     */
    getMostCommon(arr) {
        if (arr.length === 0) return 'neutral';

        const counts = {};
        let maxCount = 0;
        let mostCommon = arr[0];

        arr.forEach(item => {
            counts[item] = (counts[item] || 0) + 1;
            if (counts[item] > maxCount) {
                maxCount = counts[item];
                mostCommon = item;
            }
        });

        return mostCommon;
    }

    /**
     * Reset detector state
     */
    reset() {
        this.emotionHistory = [];
        this.currentEmotion = 'neutral';
        this.confidence = 0;
    }
}

// Export
window.EmotionDetector = EmotionDetector;
