// BeneAI Spectacles - Emotion Display Script for Lens Studio
// This script handles the AR overlay display of emotion states and coaching advice

const global = globalThis;

// Emotion state configuration (matching your Hume AI states)
const EMOTION_STATES = {
    skeptical: { 
        emoji: "🤔", 
        color: [0, 0.4, 1], // Orange
        name: "SKEPTICAL",
        description: "Address concerns with concrete data"
    },
    evaluative: { 
        emoji: "🧠", 
        color: [1, 1, 0], // Yellow
        name: "THINKING",
        description: "They're analyzing - provide more details"
    },
    receptive: { 
        emoji: "😊", 
        color: [0, 1, 0], // Green
        name: "INTERESTED",
        description: "Great! They're engaged - keep momentum"
    },
    positive: { 
        emoji: "🎉", 
        color: [0, 1, 1], // Cyan
        name: "EXCITED",
        description: "Excellent! They're enthusiastic - close deal"
    },
    neutral: { 
        emoji: "😐", 
        color: [0.8, 0.8, 0.8], // Gray
        name: "NEUTRAL",
        description: "Create more emotional connection"
    }
};

// Create AR overlay elements
const emotionDisplay = global.scene.create("Text");
const adviceDisplay = global.scene.create("Text");
const confidenceBar = global.scene.create("Rectangle");
const stateIndicator = global.scene.create("Circle");

// Position elements in user's field of view (Spectacles-optimized)
emotionDisplay.setPosition(0, 0.2, -0.6);
adviceDisplay.setPosition(0, -0.2, -0.6);
confidenceBar.setPosition(0, 0.1, -0.6);
stateIndicator.setPosition(0.3, 0.3, -0.5);

// Configure text properties
emotionDisplay.setText("BeneAI Ready");
emotionDisplay.setFontSize(0.08);
emotionDisplay.setColor(1, 1, 1);

adviceDisplay.setText("Starting analysis...");
adviceDisplay.setFontSize(0.06);
adviceDisplay.setColor(0.7, 0.7, 0.7);

// Configure confidence bar
confidenceBar.setSize(0.3, 0.02);
confidenceBar.setColor(0.2, 0.2, 0.2);

// Configure state indicator circle
stateIndicator.setRadius(0.05);
stateIndicator.setColor(0.8, 0.8, 0.8);

// BLE Communication Manager for mobile app
class BLEManager {
    constructor() {
        this.isConnected = false;
        this.mobileDeviceId = null;
        this.messageQueue = [];
        this.setupBLE();
    }
    
    setupBLE() {
        print("Initializing BLE connection to mobile app...");
        // In real implementation, this would initialize actual BLE
        this.simulateConnection();
    }
    
    simulateConnection() {
        // Simulate BLE connection for demo
        setTimeout(() => {
            this.isConnected = true;
            this.mobileDeviceId = "mobile-device-001";
            print("BLE connected to mobile app:", this.mobileDeviceId);
            this.processMessageQueue();
        }, 2000);
    }
    
    sendToMobile(data) {
        if (this.isConnected) {
            print("Sending to mobile app:", JSON.stringify(data));
            // In real implementation, this would send via BLE
            this.simulateMobileResponse(data);
        } else {
            this.messageQueue.push(data);
            print("Message queued, waiting for connection...");
        }
    }
    
    simulateMobileResponse(data) {
        // Simulate mobile app processing and response
        setTimeout(() => {
            if (data.type === 'emotion_data') {
                this.simulateEmotionProcessing(data);
            }
        }, 1000);
    }
    
    simulateEmotionProcessing(data) {
        // Simulate emotion processing response from mobile app
        const response = {
            type: 'emotion_processed',
            emotionData: {
                dominantState: data.emotionData.dominantState,
                confidence: data.emotionData.confidence + 0.1,
                timestamp: Date.now()
            }
        };
        
        this.receiveFromMobile(response);
    }
    
    receiveFromMobile(data) {
        print("Received from mobile app:", JSON.stringify(data));
        
        switch (data.type) {
            case 'emotion_processed':
                this.handleEmotionUpdate(data.emotionData);
                break;
            case 'coaching_advice':
                this.handleCoachingAdvice(data.advice);
                break;
        }
    }
    
    handleEmotionUpdate(emotionData) {
        updateEmotionDisplay(emotionData);
    }
    
    handleCoachingAdvice(advice) {
        updateAdviceDisplay(advice);
    }
    
    processMessageQueue() {
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            this.sendToMobile(message);
        }
    }
}

// Initialize BLE manager
const bleManager = new BLEManager();

// Emotion display functions
function updateEmotionDisplay(emotionData) {
    const state = emotionData.dominantState;
    const config = EMOTION_STATES[state] || EMOTION_STATES.neutral;
    
    // Update emotion display
    emotionDisplay.setText(`${config.emoji} ${config.name}`);
    emotionDisplay.setColor(config.color[0], config.color[1], config.color[2]);
    
    // Update state indicator
    stateIndicator.setColor(config.color[0], config.color[1], config.color[2]);
    
    // Update confidence bar
    const confidence = emotionData.confidence || 0.5;
    const barWidth = confidence * 0.3;
    confidenceBar.setSize(barWidth, 0.02);
    
    // Color based on confidence
    const confidenceColor = confidence > 0.7 ? [0, 1, 0] : 
                           confidence > 0.4 ? [1, 1, 0] : [1, 0, 0];
    confidenceBar.setColor(confidenceColor[0], confidenceColor[1], confidenceColor[2]);
    
    print(`Emotion updated: ${state} (${Math.round(confidence * 100)}%)`);
}

function updateAdviceDisplay(advice) {
    adviceDisplay.setText(advice);
    adviceDisplay.setColor(0, 1, 0); // Green for advice
    
    print(`Coaching advice: ${advice}`);
}

// Gesture handling
function handleGesture(gesture) {
    switch (gesture) {
        case 'tap':
            // Toggle display visibility
            const currentOpacity = emotionDisplay.getOpacity();
            emotionDisplay.setOpacity(currentOpacity > 0.5 ? 0.3 : 1.0);
            adviceDisplay.setOpacity(currentOpacity > 0.5 ? 0.3 : 1.0);
            break;
        case 'swipe_left':
            // Previous emotion state
            print("Swipe left: Previous emotion state");
            break;
        case 'swipe_right':
            // Next emotion state
            print("Swipe right: Next emotion state");
            break;
    }
}

// Export functions for external use
global.updateEmotionDisplay = updateEmotionDisplay;
global.updateAdviceDisplay = updateAdviceDisplay;
global.handleGesture = handleGesture;
global.bleManager = bleManager;

print("BeneAI Spectacles Lens initialized!");
print("Waiting for mobile app connection...");


