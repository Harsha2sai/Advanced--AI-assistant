"""
Advanced System Skills Module
Includes: Screen recording, screen control, power management, and timers
"""

import cv2
import numpy as np
import os
import subprocess
import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
import pyautogui
from PIL import ImageGrab
import sys
import shutil
import re
import mss # Import mss
import uuid # Import uuid for collision-resistant IDs

if sys.platform != 'win32':
    raise ImportError("This module requires Windows platform")

import win32api
import win32con
import win32gui
logger = logging.getLogger(__name__)

class ScreenRecorder:
    """Screen recording functionality with OpenCV and FFmpeg"""
    def __init__(self):
        self._lock = threading.Lock()
        with self._lock:
            self.is_recording = False
            self.recording_thread = None
            self.video_writer = None
        self.fps = 20.0
        self.resolution = (1920, 1080)
        self.min_free_space_gb = 1.0 # Minimum 1 GB free space required
        self.sct: Optional[mss.mss.MSS] = None # Initialize mss instance
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitizes the filename by stripping directory components,
        validating characters, and enforcing a .mp4 extension.
        """
        # Strip directory components (use only basename)
        filename = os.path.basename(filename)

        # Validate filename against a safe whitelist of characters
        # (alphanumerics, hyphen, underscore, dot for extension)
        safe_chars_pattern = r'[^a-zA-Z0-9_\-\.]'
        filename = re.sub(safe_chars_pattern, '', filename)

        # Ensure it ends with .mp4
        if not filename.lower().endswith('.mp4'):
            filename += '.mp4'
        
        # Make filename unique to avoid overwrites
        base, ext = os.path.splitext(filename)
        counter = 1
        original_base = base
        while os.path.exists(filename):
            filename = f"{original_base}_{counter}{ext}"
            counter += 1

        return filename

    def _check_disk_space(self, path: str, required_space_gb: float) -> bool:
        """
        Checks if there is sufficient disk space at the given path.
        """
        try:
            total, used, free = shutil.disk_usage(path)
            free_gb = free / (1024**3)
            if free_gb < required_space_gb:
                logger.error(f"Insufficient disk space. Required: {required_space_gb:.2f} GB, Available: {free_gb:.2f} GB")
                return False
            return True
        except Exception as e:
            logger.error(f"Failed to check disk space: {e}")
            return False
        
    def start_recording(self, filename: Optional[str] = None, duration: int = 0) -> str:
        """Start screen recording"""
        with self._lock:
            if self.is_recording:
                return "Screen recording is already in progress"
            
        try:
            # Initialize mss instance
            self.sct = mss.mss()

            # Sanitize and validate filename
            if filename:
                filename = self._sanitize_filename(filename)
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = self._sanitize_filename(f"screen_recording_{timestamp}.mp4")

            # Check disk space before starting recording
            # Assuming recordings are saved in the current working directory
            if not self._check_disk_space(os.getcwd(), self.min_free_space_gb):
                return "Failed to start recording: Insufficient disk space."
            
            # Get screen resolution
            screen_size = pyautogui.size()
            self.resolution = (screen_size.width, screen_size.height)
            
            # Setup video writer
            # Pylance might incorrectly flag VideoWriter_fourcc as unknown, but it's valid at runtime.
            fourcc = cv2.VideoWriter_fourcc(*'mp4v') # type: ignore
            with self._lock:
                self.video_writer = cv2.VideoWriter(filename, fourcc, self.fps, self.resolution)
            
                if not self.video_writer.isOpened():
                    return "Failed to initialize video writer"
                
                self.is_recording = True
            
            # Start recording in separate thread
            self.recording_thread = threading.Thread(
                target=self._recording_worker,
                args=(duration,),
                daemon=True
            )
            self.recording_thread.start()
            
            duration_text = f" for {duration} seconds" if duration > 0 else ""
            logger.info(f"Screen recording started: {filename}")
            return f"Screen recording started{duration_text}. File: {filename}"
            
        except Exception as e:
            logger.error(f"Failed to start screen recording: {e}")
            return f"Failed to start screen recording: {e}"
    
    def _recording_worker(self, duration: int):
        """Worker thread for screen recording"""
        start_time = time.time()
        
        try:
            while True:
                if not self.is_recording:
                    break
                if self.sct: # Ensure sct is initialized
                    sct_img = self.sct.grab(self.sct.monitors[0]) # Grab primary monitor
                    # Convert to numpy array and then to BGR
                    frame = np.array(sct_img)
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    
                    # Write frame
                    with self._lock:
                        if self.video_writer: # Check if video_writer is still valid before writing
                            self.video_writer.write(frame)
                
                # Check duration limit
                if duration > 0 and (time.time() - start_time) >= duration:
                    break
                    
                # Control frame rate
                time.sleep(1.0 / self.fps)
                
        except Exception as e:
            logger.error(f"Recording error: {e}")
        finally:
            self._cleanup_recording()
    
    def stop_recording(self) -> str:
        """Stop screen recording"""
        with self._lock:
            if not self.is_recording:
                return "No screen recording in progress"
            
            self.is_recording = False
        
        # Wait for thread to finish
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=5.0)
        
        return "Screen recording stopped"
    
    def _cleanup_recording(self):
        """Clean up recording resources"""
        with self._lock:
            self.is_recording = False
            if self.video_writer:
                self.video_writer.release()
                self.video_writer = None
            if self.sct:
                self.sct.close() # Close mss instance
                self.sct = None

class PowerManager:
    """System power management with timer support"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self.scheduled_tasks = {}
    
    def _create_wrapped_callback(self, original_callback, task_id, *args, **kwargs):
        """
        Creates a wrapper for the timer callback that removes the task_id
        from scheduled_tasks upon completion or error.
        """
        def wrapped_callback():
            try:
                original_callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in scheduled task {task_id}: {e}")
            finally:
                with self._lock:
                    if task_id in self.scheduled_tasks:
                        del self.scheduled_tasks[task_id]
        return wrapped_callback

    def shutdown(self, delay: int = 0, message: str = "System shutdown initiated") -> str:
        """Shutdown system with optional delay"""
        try:
            if delay > 0:
                task_id = f"shutdown_{uuid.uuid4()}" # Use uuid4 for collision-resistant ID
                wrapped_func = self._create_wrapped_callback(self._execute_shutdown, task_id, message)
                timer = threading.Timer(delay, wrapped_func)
                timer.start()
                with self._lock:
                    self.scheduled_tasks[task_id] = timer
                return f"System will shutdown in {delay} seconds. Task ID: {task_id}"
            else:
                return self._execute_shutdown(message)
        except Exception as e:
            return f"Failed to schedule shutdown: {e}"

    def _execute_shutdown(self, message: str = "") -> str:
        """Execute system shutdown"""
        try:
            if message:
                subprocess.run(['shutdown', '/s', '/t', '0', '/c', message], check=True)
            else:
                subprocess.run(['shutdown', '/s', '/t', '0'], check=True)
            return "System shutdown initiated"
        except subprocess.CalledProcessError as e:
            return f"Shutdown failed: {e}"

    def restart(self, delay: int = 0, message: str = "System restart initiated") -> str:
        """Restart system with optional delay"""
        try:
            if delay > 0:
                task_id = f"restart_{uuid.uuid4()}" # Use uuid4 for collision-resistant ID
                wrapped_func = self._create_wrapped_callback(self._execute_restart, task_id, message)
                timer = threading.Timer(delay, wrapped_func)
                timer.start()
                with self._lock:
                    self.scheduled_tasks[task_id] = timer
                return f"System will restart in {delay} seconds. Task ID: {task_id}"
            else:
                return self._execute_restart(message)
        except Exception as e:
            return f"Failed to schedule restart: {e}"

    def sleep_system(self, delay: int = 0) -> str:
        """Put system to sleep with optional delay"""
        try:
            if delay > 0:
                task_id = f"sleep_{uuid.uuid4()}" # Use uuid4 for collision-resistant ID
                wrapped_func = self._create_wrapped_callback(self._execute_sleep, task_id)
                timer = threading.Timer(delay, wrapped_func)
                timer.start()
                with self._lock:
                    self.scheduled_tasks[task_id] = timer
                return f"System will sleep in {delay} seconds. Task ID: {task_id}"
            else:
                return self._execute_sleep()
        except Exception as e:
            return f"Failed to schedule sleep: {e}"

    def hibernate(self, delay: int = 0) -> str:
        """Hibernate system with optional delay"""
        try:
            if delay > 0:
                task_id = f"hibernate_{uuid.uuid4()}" # Use uuid4 for collision-resistant ID
                wrapped_func = self._create_wrapped_callback(self._execute_hibernate, task_id)
                timer = threading.Timer(delay, wrapped_func)
                timer.start()
                with self._lock:
                    self.scheduled_tasks[task_id] = timer
                return f"System will hibernate in {delay} seconds. Task ID: {task_id}"
            else:
                return self._execute_hibernate()
        except Exception as e:
            return f"Failed to schedule hibernate: {e}"

    def cancel_scheduled_task(self, task_id: str) -> str:
        """Cancel a scheduled power management task."""
        with self._lock:
            if task_id in self.scheduled_tasks:
                self.scheduled_tasks[task_id].cancel()
                del self.scheduled_tasks[task_id]
                return f"Scheduled task {task_id} cancelled"
            return f"Task {task_id} not found"
    
    def _execute_restart(self, message: str = "") -> str:
        """Execute system restart"""
        try:
            if message:
                subprocess.run(['shutdown', '/r', '/t', '0', '/c', message], check=True)
            else:
                subprocess.run(['shutdown', '/r', '/t', '0'], check=True)
            return "System restart initiated"
        except subprocess.CalledProcessError as e:
            return f"Restart failed: {e}"
    
    def _execute_sleep(self) -> str:
        """Execute system sleep"""
        try:
            subprocess.run(['rundll32.exe', 'powrprof.dll,SetSuspendState', '0', '1', '0'], check=True)
            return "System sleep initiated"
        except subprocess.CalledProcessError as e:
            return f"Sleep failed: {e}"
    
    def _execute_hibernate(self) -> str:
        """Execute system hibernate"""
        try:
            subprocess.run(['shutdown', '/h'], check=True)
            return "System hibernate initiated"
        except subprocess.CalledProcessError as e:
            return f"Hibernate failed: {e}"

class ScreenController:
    """Screen control functionality"""
    
    @staticmethod
    def blank_screen() -> str:
        """Turn off display/blank screen"""
        try:
            # Turn off monitor
            win32gui.SendMessage(win32con.HWND_BROADCAST, win32con.WM_SYSCOMMAND, 
                               win32con.SC_MONITORPOWER, 2)
            return "Screen blanked"
        except Exception as e:
            return f"Failed to blank screen: {e}"
    
    @staticmethod
    def wake_screen(move_mouse: bool = False) -> str:
        """
        Wake up display.
        Optionally moves the mouse slightly to ensure the screen wakes up,
        which can interfere with user input if not desired.
        """
        try:
            # Turn on monitor
            win32gui.SendMessage(win32con.HWND_BROADCAST, win32con.WM_SYSCOMMAND,
                               win32con.SC_MONITORPOWER, -1)
            # Move mouse slightly to ensure wake if requested
            if move_mouse:
                current_pos = pyautogui.position()
                pyautogui.moveTo(current_pos.x + 1, current_pos.y + 1)
                pyautogui.moveTo(current_pos.x, current_pos.y)
            return "Screen activated"
        except Exception as e:
            return f"Failed to wake screen: {e}"
    
    @staticmethod
    def lock_screen() -> str:
        """Lock the workstation"""
        try:
            subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'], check=True)
            return "Screen locked"
        except subprocess.CalledProcessError as e:
            return f"Failed to lock screen: {e}"

# Global instances
screen_recorder = ScreenRecorder()
power_manager = PowerManager()
screen_controller = ScreenController()

# Main skill functions for voice assistant integration
def start_screen_recording(duration: int = 0, filename: str = "") -> str:
    """Start screen recording"""
    return screen_recorder.start_recording(filename if filename else None, duration)

def stop_screen_recording() -> str:
    """Stop screen recording"""
    return screen_recorder.stop_recording()

def blank_screen() -> str:
    """Blank/turn off screen"""
    return screen_controller.blank_screen()

def wake_screen(move_mouse: bool = False) -> str:
    """Wake up screen"""
    return screen_controller.wake_screen(move_mouse)

def lock_screen() -> str:
    """Lock screen"""
    return screen_controller.lock_screen()

def shutdown_system(minutes: int = 0, seconds: int = 0) -> str:
    """Shutdown system with timer"""
    delay = (minutes * 60) + seconds
    return power_manager.shutdown(delay)

def restart_system(minutes: int = 0, seconds: int = 0) -> str:
    """Restart system with timer"""
    delay = (minutes * 60) + seconds
    return power_manager.restart(delay)

def sleep_system(minutes: int = 0, seconds: int = 0) -> str:
    """Put system to sleep with timer"""
    delay = (minutes * 60) + seconds
    return power_manager.sleep_system(delay)

def hibernate_system(minutes: int = 0, seconds: int = 0) -> str:
    """Hibernate system with timer"""
    delay = (minutes * 60) + seconds
    return power_manager.hibernate(delay)

def cancel_power_task(task_id: str) -> str:
    """Cancel scheduled power task"""
    return power_manager.cancel_scheduled_task(task_id)
