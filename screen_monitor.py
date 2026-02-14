import time
from datetime import datetime

class ScreenMonitor:
    def __init__(self):
        self.tab_switches = 0
        self.last_focus_time = datetime.now()
        self.is_focused = True
        self.focus_lost_events = []
        
    def detect_tab_switch(self):
        # This will be triggered by JavaScript in the frontend
        self.tab_switches += 1
        self.is_focused = False
        self.focus_lost_events.append({
            'timestamp': datetime.now(),
            'type': 'tab_switch'
        })
        
    def detect_window_blur(self):
        self.is_focused = False
        self.focus_lost_events.append({
            'timestamp': datetime.now(),
            'type': 'window_blur'
        })
        
    def detect_window_focus(self):
        self.is_focused = True
        self.last_focus_time = datetime.now()
        
    def get_statistics(self):
        return {
            'total_tab_switches': self.tab_switches,
            'is_focused': self.is_focused,
            'focus_lost_count': len(self.focus_lost_events),
            'events': self.focus_lost_events
        }
    
    def reset(self):
        self.tab_switches = 0
        self.focus_lost_events = []
        self.is_focused = True
