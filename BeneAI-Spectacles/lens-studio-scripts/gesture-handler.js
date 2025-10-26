// BeneAI Spectacles - Gesture Handler Script for Lens Studio
// Handles gesture controls for the AR interface

const global = globalThis;

// Gesture recognition states
const GESTURE_STATES = {
    NONE: 0,
    TAP: 1,
    SWIPE_LEFT: 2,
    SWIPE_RIGHT: 3,
    SWIPE_UP: 4,
    SWIPE_DOWN: 5,
    PINCH: 6
};

// Gesture handler class
class GestureHandler {
    constructor() {
        this.currentGesture = GESTURE_STATES.NONE;
        this.gestureStartTime = 0;
        this.gestureThreshold = 0.3; // 300ms threshold
        this.setupGestureDetection();
    }
    
    setupGestureDetection() {
        // Initialize hand tracking for gesture recognition
        print("Setting up gesture detection...");
        
        // In real implementation, this would use Spectacles' hand tracking
        this.simulateGestureInput();
    }
    
    simulateGestureInput() {
        // Simulate gesture input for demo purposes
        const gestures = [
            GESTURE_STATES.TAP,
            GESTURE_STATES.SWIPE_LEFT,
            GESTURE_STATES.SWIPE_RIGHT,
            GESTURE_STATES.SWIPE_UP,
            GESTURE_STATES.SWIPE_DOWN
        ];
        
        // Simulate random gestures every 10 seconds for demo
        setInterval(() => {
            const randomGesture = gestures[Math.floor(Math.random() * gestures.length)];
            this.handleGesture(randomGesture);
        }, 10000);
    }
    
    handleGesture(gesture) {
        this.currentGesture = gesture;
        this.gestureStartTime = Date.now();
        
        switch (gesture) {
            case GESTURE_STATES.TAP:
                this.handleTap();
                break;
            case GESTURE_STATES.SWIPE_LEFT:
                this.handleSwipeLeft();
                break;
            case GESTURE_STATES.SWIPE_RIGHT:
                this.handleSwipeRight();
                break;
            case GESTURE_STATES.SWIPE_UP:
                this.handleSwipeUp();
                break;
            case GESTURE_STATES.SWIPE_DOWN:
                this.handleSwipeDown();
                break;
            case GESTURE_STATES.PINCH:
                this.handlePinch();
                break;
        }
        
        print(`Gesture detected: ${this.getGestureName(gesture)}`);
    }
    
    handleTap() {
        // Toggle emotion display visibility
        if (global.emotionDisplay) {
            const currentOpacity = global.emotionDisplay.getOpacity();
            global.emotionDisplay.setOpacity(currentOpacity > 0.5 ? 0.3 : 1.0);
            print("Toggled emotion display visibility");
        }
        
        // Send tap gesture to mobile app
        if (global.bleManager) {
            global.bleManager.sendToMobile({
                type: 'gesture_input',
                gesture: 'tap',
                timestamp: Date.now()
            });
        }
    }
    
    handleSwipeLeft() {
        // Previous emotion state
        print("Swipe left: Previous emotion state");
        
        if (global.bleManager) {
            global.bleManager.sendToMobile({
                type: 'gesture_input',
                gesture: 'swipe_left',
                timestamp: Date.now()
            });
        }
    }
    
    handleSwipeRight() {
        // Next emotion state
        print("Swipe right: Next emotion state");
        
        if (global.bleManager) {
            global.bleManager.sendToMobile({
                type: 'gesture_input',
                gesture: 'swipe_right',
                timestamp: Date.now()
            });
        }
    }
    
    handleSwipeUp() {
        // Increase display size
        if (global.emotionDisplay) {
            const currentSize = global.emotionDisplay.getFontSize();
            global.emotionDisplay.setFontSize(Math.min(currentSize * 1.1, 0.12));
            print("Increased display size");
        }
    }
    
    handleSwipeDown() {
        // Decrease display size
        if (global.emotionDisplay) {
            const currentSize = global.emotionDisplay.getFontSize();
            global.emotionDisplay.setFontSize(Math.max(currentSize * 0.9, 0.04));
            print("Decreased display size");
        }
    }
    
    handlePinch() {
        // Toggle coaching advice display
        if (global.adviceDisplay) {
            const currentOpacity = global.adviceDisplay.getOpacity();
            global.adviceDisplay.setOpacity(currentOpacity > 0.5 ? 0.3 : 1.0);
            print("Toggled coaching advice display");
        }
    }
    
    getGestureName(gesture) {
        const names = {
            [GESTURE_STATES.NONE]: "None",
            [GESTURE_STATES.TAP]: "Tap",
            [GESTURE_STATES.SWIPE_LEFT]: "Swipe Left",
            [GESTURE_STATES.SWIPE_RIGHT]: "Swipe Right",
            [GESTURE_STATES.SWIPE_UP]: "Swipe Up",
            [GESTURE_STATES.SWIPE_DOWN]: "Swipe Down",
            [GESTURE_STATES.PINCH]: "Pinch"
        };
        return names[gesture] || "Unknown";
    }
    
    // Get current gesture state
    getCurrentGesture() {
        return this.currentGesture;
    }
    
    // Check if gesture is active
    isGestureActive() {
        return this.currentGesture !== GESTURE_STATES.NONE;
    }
}

// Initialize gesture handler
const gestureHandler = new GestureHandler();

// Export for global access
global.gestureHandler = gestureHandler;
global.GESTURE_STATES = GESTURE_STATES;

print("Gesture handler initialized!");
print("Available gestures: Tap, Swipe (4 directions), Pinch");


