// BeneAI Spectacles - Emotion Display Script
// This script handles the AR overlay display of emotion states and coaching advice

const global = globalThis;

// Emotion state configuration
const EMOTION_STATES = {
    interested: { emoji: "😊", color: [0, 1, 0], name: "Interested" },
    skeptical: { emoji: "🤔", color: [1, 0.5, 0], name: "Skeptical" },
    concerned: { emoji: "😟", color: [1, 0, 0], name: "Concerned" },
    confused: { emoji: "😕", color: [1, 1, 0], name: "Confused" },
    bored: { emoji: "😴", color: [0.5, 0.5, 0.5], name: "Bored" },
    neutral: { emoji: "😐", color: [0.8, 0.8, 0.8], name: "Neutral" }
};

// Create AR overlay elements
const emotionDisplay = global.scene.create("Text");
const adviceDisplay = global.scene.create("Text");
const confidenceBar = global.scene.create("Rectangle");

// Position elements in user's field of view
emotionDisplay.setPosition(0, 0.15, -0.8);
adviceDisplay.setPosition(0, -0.15, -0.8);
confidenceBar.setPosition(0, 0.1, -0.8);

// Configure text properties
emotionDisplay.setText("BeneAI Ready");
emotionDisplay.setFontSize(0.08);
emotionDisplay.setColor(1, 1, 1);

adviceDisplay.setText("Starting coaching session...");
adviceDisplay.setFontSize(0.06);
adviceDisplay.setColor(0.7, 0.7, 0.7);

// Configure confidence bar
confidenceBar.setSize(0.3, 0.02);
confidenceBar.setColor(0.2, 0.2, 0.2);

// BLE Communication Manager
class BLEManager {
    constructor() {
        this.isConnected = false;
        this.setupBLE();
    }
    
    setupBLE() {
        // Initialize BLE connection to mobile app
        print("Initializing BLE connection...");
        this.isConnected = true; // Simulated for demo
    }
    
    send(data) {
        if (this.isConnected) {
            print("Sending to mobile app:", JSON.stringify(data));
            // In real implementation, this would send via BLE
        }
    }
    
    onReceive(callback) {
        this.receiveCallback = callback;
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

// Handle BLE communication
bleManager.onReceive(function(data) {
    if (data.type === 'emotion_update') {
        updateEmotionDisplay(data.emotionData);
    } else if (data.type === 'coaching_advice') {
        updateAdviceDisplay(data.advice);
    }
});

// Simulate emotion data for testing
function simulateEmotionData() {
    const states = Object.keys(EMOTION_STATES);
    const randomState = states[Math.floor(Math.random() * states.length)];
    const confidence = 0.5 + Math.random() * 0.5;
    
    const emotionData = {
        dominantState: randomState,
        confidence: confidence,
        timestamp: Date.now()
    };
    
    updateEmotionDisplay(emotionData);
    
    // Simulate coaching advice
    const advice = `Try to maintain ${randomState} energy level`;
    updateAdviceDisplay(advice);
}

// Start simulation for demo
print("BeneAI Spectacles Lens initialized!");
print("Starting emotion simulation...");

// Simulate data every 3 seconds
setInterval(simulateEmotionData, 3000);

// Export functions for external use
global.updateEmotionDisplay = updateEmotionDisplay;
global.updateAdviceDisplay = updateAdviceDisplay;
global.bleManager = bleManager;
