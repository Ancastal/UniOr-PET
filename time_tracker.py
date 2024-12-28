from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Optional, Any
import streamlit as st

@dataclass
class EditingSession:
    start_time: datetime
    pause_time: Optional[datetime] = None
    total_paused_time: float = 0.0
    is_paused: bool = False
    last_activity: datetime = datetime.now()
    active_time: float = 0.0  # Track actual active editing time
    idle_time: float = 0.0
    is_pet_paused: bool = False  # New field for PET timer mode

    def to_dict(self) -> dict:
        return {
            'start_time': self.start_time,
            'pause_time': self.pause_time,
            'total_paused_time': self.total_paused_time,
            'is_paused': self.is_paused,
            'last_activity': self.last_activity,
            'active_time': self.active_time,
            'idle_time': self.idle_time,
            'is_pet_paused': self.is_pet_paused
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'EditingSession':
        return cls(
            start_time=data['start_time'],
            pause_time=data['pause_time'],
            total_paused_time=data['total_paused_time'],
            is_paused=data['is_paused'],
            last_activity=data.get('last_activity', datetime.now()),
            active_time=data.get('active_time', 0.0),
            idle_time=data.get('idle_time', 0.0),
            is_pet_paused=data.get('is_pet_paused', False)
        )

class TimeTracker:
    IDLE_THRESHOLD = 30  # 30 seconds idle threshold

    def __init__(self):
        self.sessions: Dict[int, EditingSession] = {}
        self.timer_mode: str = "current"  # "current" or "pet"
    
    def set_timer_mode(self, mode: str) -> None:
        """Set the timer mode (current or pet)"""
        self.timer_mode = mode
    
    def start_segment(self, segment_id: int) -> None:
        """Start tracking time for a segment"""
        current_time = datetime.now()
        if segment_id not in self.sessions:
            # Always start paused in PET mode
            is_pet_paused = self.timer_mode == "pet"
            self.sessions[segment_id] = EditingSession(
                start_time=current_time,
                last_activity=current_time,
                is_pet_paused=is_pet_paused,  # Start paused in PET mode
                is_paused=is_pet_paused  # Also set is_paused for PET mode
            )
        else:
            # If segment exists and we're in PET mode, ensure it's paused when switching to it
            if self.timer_mode == "pet":
                session = self.sessions[segment_id]
                if not session.is_pet_paused:
                    session.is_pet_paused = True
                    session.is_paused = True
                    session.pause_time = current_time
    
    def pause_segment(self, segment_id: int) -> None:
        """Pause time tracking for a segment"""
        if segment_id in self.sessions and not self.sessions[segment_id].is_paused:
            session = self.sessions[segment_id]
            current_time = datetime.now()
            
            # Calculate and add active time before pausing
            time_since_last = (current_time - session.last_activity).total_seconds()
            if time_since_last <= self.IDLE_THRESHOLD or not st.session_state.get('idle_timer_enabled', True):
                session.active_time += time_since_last
            
            session.pause_time = current_time
            session.is_paused = True
            session.last_activity = current_time
    
    def resume_segment(self, segment_id: int) -> None:
        """Resume time tracking for a segment"""
        if segment_id in self.sessions and self.sessions[segment_id].is_paused:
            session = self.sessions[segment_id]
            current_time = datetime.now()
            
            # Only resume if not in PET mode or if explicitly started in PET mode
            if self.timer_mode != "pet" or not session.is_pet_paused:
                if session.pause_time:
                    pause_duration = (current_time - session.pause_time).total_seconds()
                    session.total_paused_time += pause_duration
                
                session.is_paused = False
                session.pause_time = None
                session.last_activity = current_time
    
    def update_activity(self, segment_id: int) -> None:
        """Update activity tracking"""
        if segment_id in self.sessions:
            session = self.sessions[segment_id]
            current_time = datetime.now()
            
            if not session.is_paused:
                time_since_last = (current_time - session.last_activity).total_seconds()
                
                if st.session_state.get('idle_timer_enabled', True):
                    if time_since_last > self.IDLE_THRESHOLD:
                        # Add to idle time
                        session.idle_time += (time_since_last - self.IDLE_THRESHOLD)
                    else:
                        # Add to active time
                        session.active_time += time_since_last
                else:
                    # When idle timer is disabled, all time is active time
                    session.active_time += time_since_last
            
            session.last_activity = current_time

    def get_editing_time(self, segment_id: int) -> float:
        """Get actual editing time (excluding idle and paused time)"""
        if segment_id not in self.sessions:
            return 0.0
        
        session = self.sessions[segment_id]
        
        # If not paused, add time since last activity
        if not session.is_paused:
            current_time = datetime.now()
            time_since_last = (current_time - session.last_activity).total_seconds()
            if time_since_last <= self.IDLE_THRESHOLD or not st.session_state.get('idle_timer_enabled', True):
                return session.active_time + time_since_last
        
        return session.active_time

    def to_dict(self) -> dict:
        """Convert TimeTracker to dictionary for MongoDB storage"""
        return {
            'sessions': {
                str(k): v.to_dict() for k, v in self.sessions.items()
            }
        }

    @classmethod
    def from_dict(cls, data: dict, timer_mode: str = None) -> 'TimeTracker':
        """Create TimeTracker instance from dictionary data"""
        tracker = cls()
        if timer_mode:
            tracker.set_timer_mode(timer_mode)
        
        if data and 'sessions' in data:
            tracker.sessions = {
                int(k): EditingSession.from_dict(v) 
                for k, v in data['sessions'].items()
            }
        return tracker

    def check_idle_time(self, segment_id: int) -> None:
        """Periodic idle time check"""
        if not st.session_state.get('idle_timer_enabled', True):
            return
            
        if segment_id in self.sessions:
            session = self.sessions[segment_id]
            if not session.is_paused:
                current_time = datetime.now()
                time_since_last = (current_time - session.last_activity).total_seconds()
                
                if time_since_last > self.IDLE_THRESHOLD:
                    # Only count new idle time
                    new_idle = time_since_last - self.IDLE_THRESHOLD
                    if new_idle > session.idle_time:
                        additional_idle = new_idle - session.idle_time
                        session.idle_time = new_idle
                        
                        # Only show warning for significant idle time
                        if additional_idle >= 60:  # Show warning for 1+ minute
                            minutes = int(additional_idle // 60)
                            seconds = int(additional_idle % 60)
                            time_msg = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
                            st.warning(f"⚠️ Idle time detected: {time_msg}", icon="⚠️")

    def pause_pet_timer(self, segment_id: int) -> None:
        """Pause the PET timer for a segment"""
        if segment_id in self.sessions and self.timer_mode == "pet":
            session = self.sessions[segment_id]
            session.is_pet_paused = True
            self.pause_segment(segment_id)
    
    def start_pet_timer(self, segment_id: int) -> None:
        """Start the PET timer for a segment"""
        if segment_id in self.sessions and self.timer_mode == "pet":
            session = self.sessions[segment_id]
            session.is_pet_paused = False
            self.resume_segment(segment_id)
    
    def is_pet_timer_paused(self, segment_id: int) -> bool:
        """Check if PET timer is paused for a segment"""
        return segment_id in self.sessions and self.sessions[segment_id].is_pet_paused