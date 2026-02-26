import cv2
import numpy as np

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# MediaPipe Face Mesh landmark indices for eyes and irises
# Reference: https://github.com/google/mediapipe/blob/master/mediapipe/modules/face_geometry/data/canonical_face_model_uv_visualization.png
# ─────────────────────────────────────────────────────────────────────────────

# Outer corners of each eye
LEFT_EYE_OUTER  = 33
LEFT_EYE_INNER  = 133
RIGHT_EYE_OUTER = 362
RIGHT_EYE_INNER = 263

# Top and bottom of each eye (for openness/blink detection)
LEFT_EYE_TOP    = 159
LEFT_EYE_BOTTOM = 145
RIGHT_EYE_TOP   = 386
RIGHT_EYE_BOTTOM = 374

# Iris centres (only available when refine_landmarks=True in FaceMesh)
LEFT_IRIS_CENTER  = 468
RIGHT_IRIS_CENTER = 473

# How far the iris can deviate from eye centre before flagging as "looking away"
# Range is 0.0 (centre) to 1.0 (fully to one side). 0.35 is a reasonable threshold.
GAZE_THRESHOLD = 0.35

# Minimum eye openness ratio — below this is considered a blink (not a gaze violation)
BLINK_THRESHOLD = 0.15


class EyeTracker:
    def __init__(self):
        self.looking_away_threshold = GAZE_THRESHOLD

        if not MEDIAPIPE_AVAILABLE:
            # Fallback cascade for basic eye detection
            self._eye_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_eye.xml'
            )
            print("EyeTracker: MediaPipe not available, using basic fallback")

    # ──────────────────────────────────────────────────────────────────────
    # Public API (same signatures as before — app.py needs no changes)
    # ──────────────────────────────────────────────────────────────────────

    def is_looking_at_screen(self, face_landmarks, frame_shape):
        """
        Returns (is_looking: bool, confidence: float).
        face_landmarks is a MediaPipe NormalizedLandmarkList from FaceMesh.
        """
        if face_landmarks is None:
            return False, 0.0

        if not MEDIAPIPE_AVAILABLE:
            # Fallback: if we got any landmarks, assume looking forward
            return True, 0.5

        direction, confidence = self.detect_gaze_direction(face_landmarks, frame_shape)
        return direction == "looking_forward", confidence

    def detect_gaze_direction(self, face_landmarks, frame_shape):
        """
        Analyses iris position relative to eye corners to determine gaze direction.
        Returns: (direction: str, confidence: float)
        direction is one of: 'looking_forward', 'looking_left', 'looking_right',
                             'looking_up', 'looking_down', 'eyes_closed', 'no_face'
        """
        if face_landmarks is None:
            return "no_face", 0.0

        if not MEDIAPIPE_AVAILABLE:
            return "looking_forward", 0.5

        try:
            landmarks = face_landmarks.landmark
            total = len(landmarks)

            # Check if iris landmarks are available (requires refine_landmarks=True)
            has_iris = total > LEFT_IRIS_CENTER

            if not has_iris:
                # Fallback: face is detected but no iris data — assume forward
                return "looking_forward", 0.4

            # ── Check for blink (eyes closed) ────────────────────────────
            left_openness = self._eye_openness(landmarks, LEFT_EYE_TOP, LEFT_EYE_BOTTOM,
                                                LEFT_EYE_OUTER, LEFT_EYE_INNER)
            right_openness = self._eye_openness(landmarks, RIGHT_EYE_TOP, RIGHT_EYE_BOTTOM,
                                                 RIGHT_EYE_OUTER, RIGHT_EYE_INNER)
            avg_openness = (left_openness + right_openness) / 2

            if avg_openness < BLINK_THRESHOLD:
                return "eyes_closed", 0.9  # Blink — don't flag as looking away

            # ── Horizontal gaze (left/right) ─────────────────────────────
            left_ratio  = self._iris_horizontal_ratio(landmarks,
                                                       LEFT_IRIS_CENTER,
                                                       LEFT_EYE_OUTER,
                                                       LEFT_EYE_INNER)
            right_ratio = self._iris_horizontal_ratio(landmarks,
                                                       RIGHT_IRIS_CENTER,
                                                       RIGHT_EYE_INNER,   # Note: swapped for right eye
                                                       RIGHT_EYE_OUTER)
            avg_h_ratio = (left_ratio + right_ratio) / 2

            # ── Vertical gaze (up/down) ───────────────────────────────────
            left_v_ratio  = self._iris_vertical_ratio(landmarks,
                                                       LEFT_IRIS_CENTER,
                                                       LEFT_EYE_TOP,
                                                       LEFT_EYE_BOTTOM)
            right_v_ratio = self._iris_vertical_ratio(landmarks,
                                                       RIGHT_IRIS_CENTER,
                                                       RIGHT_EYE_TOP,
                                                       RIGHT_EYE_BOTTOM)
            avg_v_ratio = (left_v_ratio + right_v_ratio) / 2

            # ── Classify gaze direction ───────────────────────────────────
            # Ratios are 0.0–1.0. 0.5 = centre.
            h_deviation = abs(avg_h_ratio - 0.5)
            v_deviation = abs(avg_v_ratio - 0.5)

            if h_deviation > self.looking_away_threshold:
                direction = "looking_left" if avg_h_ratio < 0.5 else "looking_right"
                confidence = min(1.0, h_deviation * 2)
                return direction, round(confidence, 3)

            if v_deviation > self.looking_away_threshold:
                direction = "looking_up" if avg_v_ratio < 0.5 else "looking_down"
                confidence = min(1.0, v_deviation * 2)
                return direction, round(confidence, 3)

            # Iris is near centre — student is looking at screen
            confidence = 1.0 - max(h_deviation, v_deviation) * 2
            return "looking_forward", round(max(0.0, confidence), 3)

        except (IndexError, AttributeError) as e:
            # Landmark data incomplete — don't flag as violation
            return "looking_forward", 0.3

    # ──────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────

    def _iris_horizontal_ratio(self, landmarks, iris_idx, left_corner_idx, right_corner_idx):
        """
        Returns how far the iris is between the left and right eye corners.
        0.0 = fully left, 0.5 = centre, 1.0 = fully right.
        """
        iris_x  = landmarks[iris_idx].x
        left_x  = landmarks[left_corner_idx].x
        right_x = landmarks[right_corner_idx].x

        eye_width = abs(right_x - left_x)
        if eye_width < 1e-6:
            return 0.5  # Avoid division by zero

        ratio = (iris_x - min(left_x, right_x)) / eye_width
        return max(0.0, min(1.0, ratio))

    def _iris_vertical_ratio(self, landmarks, iris_idx, top_idx, bottom_idx):
        """
        Returns how far the iris is between the top and bottom of the eye.
        0.0 = fully up, 0.5 = centre, 1.0 = fully down.
        """
        iris_y  = landmarks[iris_idx].y
        top_y   = landmarks[top_idx].y
        bot_y   = landmarks[bottom_idx].y

        eye_height = abs(bot_y - top_y)
        if eye_height < 1e-6:
            return 0.5

        ratio = (iris_y - min(top_y, bot_y)) / eye_height
        return max(0.0, min(1.0, ratio))

    def _eye_openness(self, landmarks, top_idx, bottom_idx, outer_idx, inner_idx):
        """
        Returns eye openness as a ratio of height/width.
        Near 0 = closed, ~0.3+ = open.
        """
        height = abs(landmarks[top_idx].y - landmarks[bottom_idx].y)
        width  = abs(landmarks[outer_idx].x - landmarks[inner_idx].x)

        if width < 1e-6:
            return 0.0
        return height / width