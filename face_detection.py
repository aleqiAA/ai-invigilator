import cv2
import numpy as np

# MediaPipe is imported lazily so the app still starts if it's not installed
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("Warning: MediaPipe not installed. Run: pip install mediapipe")


class FaceDetector:
    def __init__(self):
        if MEDIAPIPE_AVAILABLE:
            # Face Detection — fast, accurate, works at angles
            # model_selection=0: short range (within 2m) — ideal for exam webcams
            self._mp_face_detection = mp.solutions.face_detection
            self._face_detection = self._mp_face_detection.FaceDetection(
                model_selection=0,
                min_detection_confidence=0.6
            )

            # Face Mesh — 468 landmarks for accurate gaze tracking
            self._mp_face_mesh = mp.solutions.face_mesh
            self._face_mesh = self._mp_face_mesh.FaceMesh(
                max_num_faces=4,          # Detect up to 4 faces (catches multiple people)
                refine_landmarks=True,    # Enables iris landmarks for gaze tracking
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )

            self._mp_drawing = mp.solutions.drawing_utils
            print("FaceDetector: MediaPipe loaded successfully")
        else:
            # Fallback to Haar Cascade if MediaPipe is not installed
            self._face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            print("FaceDetector: Falling back to Haar Cascade (install MediaPipe for better accuracy)")

        # Hand gesture recognizer (unchanged)
        try:
            from hand_gesture_recognition import HandGestureRecognizer
            self._hand_recognizer = HandGestureRecognizer()
            self._hand_gestures_enabled = True
        except ImportError:
            self._hand_gestures_enabled = False
            print("Warning: Hand gesture recognition not available. Install MediaPipe.")

        # Cache the last face mesh result so EyeTracker can use it
        # without running face mesh twice per frame
        self._last_mesh_results = None

    # ──────────────────────────────────────────────────────────────────────
    # Face detection
    # ──────────────────────────────────────────────────────────────────────

    def detect_faces(self, frame):
        """
        Detects faces in a frame.
        Returns: (face_count, detections)
        detections is a list of (x, y, w, h) bounding boxes — same format
        as before so draw_detections() and app.py need no changes.
        """
        if MEDIAPIPE_AVAILABLE:
            return self._detect_faces_mediapipe(frame)
        else:
            return self._detect_faces_haar(frame)

    def _detect_faces_mediapipe(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self._face_detection.process(rgb)

        detections = []
        if results.detections:
            h, w = frame.shape[:2]
            for detection in results.detections:
                bbox = detection.location_data.relative_bounding_box
                # Convert relative coordinates to pixel coordinates
                x = max(0, int(bbox.xmin * w))
                y = max(0, int(bbox.ymin * h))
                bw = min(int(bbox.width * w), w - x)
                bh = min(int(bbox.height * h), h - y)
                detections.append((x, y, bw, bh))

        return len(detections), detections

    def _detect_faces_haar(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self._face_cascade.detectMultiScale(gray, 1.3, 5)
        face_list = list(faces) if len(faces) > 0 else []
        return len(face_list), face_list

    # ──────────────────────────────────────────────────────────────────────
    # Face mesh landmarks (used by EyeTracker)
    # ──────────────────────────────────────────────────────────────────────

    def get_face_landmarks(self, frame):
        """
        Returns MediaPipe face mesh results for the first detected face.
        EyeTracker uses this for gaze detection.
        Also caches the result so it's only computed once per frame.
        """
        if not MEDIAPIPE_AVAILABLE:
            # Fallback: return Haar face regions for basic compatibility
            _, faces = self._detect_faces_haar(frame)
            return faces if len(faces) > 0 else None

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self._face_mesh.process(rgb)
        self._last_mesh_results = results  # Cache for draw_detections

        if results.multi_face_landmarks:
            return results.multi_face_landmarks[0]  # Return first face landmarks
        return None

    # ──────────────────────────────────────────────────────────────────────
    # Hand detection (unchanged — uses existing HandGestureRecognizer)
    # ──────────────────────────────────────────────────────────────────────

    def detect_hands(self, frame):
        if not self._hand_gestures_enabled:
            return {'phone_detected': False, 'raised_hand_detected': False, 'frame': frame}
        try:
            return self._hand_recognizer.process_frame(frame)
        except Exception as e:
            print(f"Hand detection error: {e}")
            return {'phone_detected': False, 'raised_hand_detected': False, 'frame': frame}

    # ──────────────────────────────────────────────────────────────────────
    # Student identity verification (improved with MediaPipe)
    # ──────────────────────────────────────────────────────────────────────

    def verify_student(self, frame, reference_image_path):
        """
        Verifies exactly one face is present in frame.
        Future improvement: add face embedding comparison against reference photo.
        """
        face_count, _ = self.detect_faces(frame)
        return face_count == 1

    # ──────────────────────────────────────────────────────────────────────
    # Drawing
    # ──────────────────────────────────────────────────────────────────────

    def draw_detections(self, frame, detections):
        """
        Draws bounding boxes around detected faces.
        Uses green for exactly 1 face, red for 0 or multiple.
        """
        face_count = len(detections) if detections else 0

        if face_count == 1:
            color = (0, 255, 0)   # Green — normal
            label = "Student"
        elif face_count == 0:
            color = (0, 0, 255)   # Red — no face
            label = "No Face"
        else:
            color = (0, 0, 255)   # Red — multiple faces
            label = f"{face_count} Faces!"

        if detections:
            for (x, y, w, h) in detections:
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                cv2.putText(frame, label, (x, y - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        return frame

    # ──────────────────────────────────────────────────────────────────────
    # Cleanup
    # ──────────────────────────────────────────────────────────────────────

    def close(self):
        if MEDIAPIPE_AVAILABLE:
            self._face_detection.close()
            self._face_mesh.close()