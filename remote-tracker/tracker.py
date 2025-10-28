import sys
import time
import psutil
from pynput import mouse, keyboard

# Platform-specific imports
if sys.platform == "win32":
    import win32gui
    import win32process
elif sys.platform == "darwin":
    from AppKit import NSWorkspace
elif sys.platform.startswith("linux"):
    from Xlib import display

# --- CONFIGURATION ---
IDLE_THRESHOLD_SECONDS = 120  # 2 minutes. Change as needed.

# --- STATE MANAGEMENT ---
# A simple dictionary to hold the timestamp of the last detected activity.
# This is a simple way to share state between our listener threads and the main thread.
last_activity = {'time': time.time()}

# --- LISTENER CALLBACKS ---
def on_activity(*args):
    """A callback function that updates the last activity time."""
    last_activity['time'] = time.time()

# --- CORE FUNCTIONS (from Step 1) ---
def get_active_window_title():
    """Gets the process name of the currently active window."""
    # (This function is the same as in the previous step)
    active_window_name = None
    try:
        if sys.platform == "win32":
            hwnd = win32gui.GetForegroundWindow()
            pid = win32process.GetWindowThreadProcessId(hwnd)[1]
            active_window_name = psutil.Process(pid).name()
        elif sys.platform == "darwin":
            active_window_name = NSWorkspace.sharedWorkspace().activeApplication()['NSApplicationName']
        elif sys.platform.startswith("linux"):
            d = display.Display()
            root = d.screen().root
            window_id = root.get_full_property(d.intern_atom('_NET_ACTIVE_WINDOW'), 0).value[0]
            window = d.create_resource_object('window', window_id)
            pid = window.get_full_property(d.intern_atom('_NET_WM_PID'), 0).value[0]
            active_window_name = psutil.Process(pid).name()
    except Exception:
        return None
    return active_window_name

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    print("Starting activity tracker with idle detection...")
    print(f"User will be marked as IDLE after {IDLE_THRESHOLD_SECONDS} seconds of inactivity.")
    print("Press Ctrl+C to stop.")

    # Setup and start the listeners in the background.
    # We listen for mouse moves, clicks, and scrolls, and keyboard presses.
    mouse_listener = mouse.Listener(on_move=on_activity, on_click=on_activity, on_scroll=on_activity)
    keyboard_listener = keyboard.Listener(on_press=on_activity)
    
    mouse_listener.start()
    keyboard_listener.start()

    try:
        while True:
            active_app = get_active_window_title()
            
            # Check if the user is idle
            time_since_last_activity = time.time() - last_activity['time']
            is_idle = time_since_last_activity > IDLE_THRESHOLD_SECONDS
            
            status = "IDLE" if is_idle else "ACTIVE"
            
            print(f"Status: {status} | Active App: {active_app or 'None'}")
            
            time.sleep(5)
    except KeyboardInterrupt:
        print("\nStopping tracker...")
        mouse_listener.stop()
        keyboard_listener.stop()
        print("Tracker stopped.")