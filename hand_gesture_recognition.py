import cv2
import numpy as np

try:
    # Try the newer MediaPipe API
    import mediapipe as mp
    mediapipe_available = hasattr(mp, 'solutions')
    if mediapipe_available:
        # Use the traditional solutions API if available
        mp_hands = mp.solutions.hands
        mp_drawing = mp.solutions.drawing_utils
    else:
        # Try the newer tasks API
        from mediapipe.tasks import vision
        mediapipe_available = True
        mp_hands = None
        mp_drawing = None
except ImportError:
    mediapipe_available = False
    print("Warning: MediaPipe not available. Hand gesture recognition will be disabled.")

class HandGestureRecognizer:
    def __init__(self):
        self.use_traditional_api = mediapipe_available and hasattr(mp, 'solutions')
        
        if self.use_traditional_api:
            self.mp_hands = mp.solutions.hands
            self.mp_drawing = mp.solutions.drawing_utils
            self.hands = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=2,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.7
            )
        else:
            # For newer MediaPipe versions, we'll disable hand detection for now
            # as the implementation would be quite different
            self.mp_hands = None
            self.mp_drawing = None
            self.hands = None
        
    def detect_phone_usage(self, frame):
        """
        Detect if a person is holding a phone near their face
        This is a simplified version - in reality, you'd need more sophisticated pose estimation
        """
        if not mediapipe_available or not self.use_traditional_api:
            return False, None
            
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Get wrist and thumb tip coordinates
                wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
                thumb_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
                
                # Calculate distance between wrist and thumb tip
                distance = np.sqrt((wrist.x - thumb_tip.x)**2 + (wrist.y - thumb_tip.y)**2)
                
                # If distance is small, it might indicate holding something
                if distance < 0.05:  # Threshold value - needs tuning
                    return True, hand_landmarks
        
        return False, None
    
    def detect_raised_hand(self, frame):
        """
        Detect if a person has raised their hand (requesting help)
        """
        if not mediapipe_available or not self.use_traditional_api:
            return False, None
            
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Check if wrist is lower than fingertips (indicating raised hand)
                wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
                
                # Get finger tip positions
                finger_tips = [
                    hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP],
                    hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP],
                    hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP],
                    hand_landmarks.landmark[self.mp_hands.HandLandmark.RING_FINGER_TIP],
                    hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_TIP]
                ]
                
                # Check if all fingertips are higher than wrist (y-axis inverted in image)
                if all(finger_tip.y < wrist.y for finger_tip in finger_tips):
                    return True, hand_landmarks
        
        return False, None
    
    def draw_hand_landmarks(self, frame, hand_landmarks):
        """Draw hand landmarks on the frame"""
        if not mediapipe_available or not self.mp_drawing or not self.use_traditional_api:
            return
            
        self.mp_drawing.draw_landmarks(
            frame,
            hand_landmarks,
            self.mp_hands.HAND_CONNECTIONS
        )
        
    def process_frame(self, frame):
        """Process a frame and return detection results"""
        if not mediapipe_available or not self.use_traditional_api:
            return {
                'phone_detected': False,
                'raised_hand_detected': False,
                'frame': frame
            }
            
        phone_detected, phone_hand = self.detect_phone_usage(frame)
        raised_hand_detected, raised_hand = self.detect_raised_hand(frame)
        
        # Draw landmarks if hands are detected
        if phone_hand:
            self.draw_hand_landmarks(frame, phone_hand)
            cv2.putText(frame, "PHONE DETECTED!", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        if raised_hand:
            self.draw_hand_landmarks(frame, raised_hand)
            cv2.putText(frame, "RAISED HAND", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        return {
            'phone_detected': phone_detected,
            'raised_hand_detected': raised_hand_detected,
            'frame': frame
        }