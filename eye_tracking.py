import cv2
import numpy as np

class EyeTracker:
    def __init__(self):
        self.looking_away_threshold = 0.3
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        
    def detect_gaze_direction(self, face_landmarks, frame_shape):
        if face_landmarks is None or len(face_landmarks) == 0:
            return "no_face", 0.0
        
        # Simplified gaze detection
        return "looking_forward", 0.1
    
    def is_looking_at_screen(self, face_landmarks, frame_shape):
        direction, confidence = self.detect_gaze_direction(face_landmarks, frame_shape)
        return direction == "looking_forward", confidence
