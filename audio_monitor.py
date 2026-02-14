import numpy as np
import threading
import time

class AudioMonitor:
    def __init__(self, threshold=0.5):
        self.threshold = threshold
        self.is_monitoring = False
        self.suspicious_audio_detected = False
        
    def calculate_audio_level(self, audio_data):
        # Calculate RMS (Root Mean Square) of audio signal
        if len(audio_data) == 0:
            return 0
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        rms = np.sqrt(np.mean(audio_array**2))
        normalized_rms = rms / 32768.0  # Normalize to 0-1 range
        return normalized_rms
    
    def detect_voice(self, audio_data):
        audio_level = self.calculate_audio_level(audio_data)
        
        if audio_level > self.threshold:
            self.suspicious_audio_detected = True
            return True, audio_level
        
        self.suspicious_audio_detected = False
        return False, audio_level
    
    def start_monitoring(self):
        self.is_monitoring = True
        
    def stop_monitoring(self):
        self.is_monitoring = False
    
    def get_status(self):
        return {
            'is_monitoring': self.is_monitoring,
            'suspicious_detected': self.suspicious_audio_detected
        }
