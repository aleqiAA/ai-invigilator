import cv2
import numpy as np

class FaceDetector:
    def __init__(self):
        # Use OpenCV's Haar Cascade for face detection
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Initialize hand gesture recognizer
        try:
            from hand_gesture_recognition import HandGestureRecognizer
            self.hand_gestureRecognizer = HandGestureRecognizer()
            self.hand_gestures_enabled = True
        except ImportError:
            print("Warning: Hand gesture recognition module not found. Install MediaPipe to enable this feature.")
            self.hand_gestures_enabled = False

    def detect_faces(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)

        face_count = len(faces)
        return face_count, faces

    def detect_hands(self, frame):
        """Detect hand gestures if the module is available"""
        if not self.hand_gestures_enabled:
            return {'phone_detected': False, 'raised_hand_detected': False, 'frame': frame}
        
        try:
            return self.hand_gestureRecognizer.process_frame(frame)
        except Exception as e:
            print(f"Hand detection error: {e}")
            return {'phone_detected': False, 'raised_hand_detected': False, 'frame': frame}

    def verify_student(self, frame, reference_image_path):
        face_count, _ = self.detect_faces(frame)
        return face_count == 1

    def get_face_landmarks(self, frame):
        # Return face regions for eye tracking
        _, faces = self.detect_faces(frame)
        return faces if len(faces) > 0 else None

    def draw_detections(self, frame, detections):
        if detections is not None and len(detections) > 0:
            for (x, y, w, h) in detections:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        return frame

    def close(self):
        pass
