import cv2
import face_recognition
import os
import time
import stat
import platform
import subprocess
from collections import deque
from datetime import datetime, timedelta
from pynput import mouse, keyboard

# Global variable to track user activity
last_activity_time = datetime.now()

def on_activity(*args, **kwargs):
    global last_activity_time
    last_activity_time = datetime.now()

# Set up mouse and keyboard listeners
mouse_listener = mouse.Listener(on_move=on_activity, on_click=on_activity, on_scroll=on_activity)
keyboard_listener = keyboard.Listener(on_press=on_activity)

mouse_listener.start()
keyboard_listener.start()

def lock_screen():
    """Locks the screen based on the OS."""
    try:
        if os.name == "posix":  # macOS or Linux
            if "darwin" in os.uname().sysname.lower():  # macOS
                os.system('osascript -e \'tell application "System Events" to keystroke "q" using {command down, control down}\'')
            else:  # Linux
                os.system("xdg-screensaver lock")
        elif os.name == "nt":  # Windows
            os.system("rundll32.exe user32.dll, LockWorkStation")
        print("[INFO] Screen locked due to no match.")
    except Exception as e:
        print(f"[ERROR] Failed to lock screen: {e}")

def ensure_write_permissions(directory):
    """Ensure the script has write permissions for the given directory."""
    if not os.access(directory, os.W_OK):
        try:
            os.chmod(directory, stat.S_IWUSR | stat.S_IRUSR | stat.S_IXUSR)
            print(f"[INFO] Write permissions granted for directory: {directory}")
        except Exception as e:
            print(f"[ERROR] Failed to set write permissions for directory: {directory}, {e}")
            exit(1)

def check_face(reference_face_encodings, video_capture, tolerance=1.0):
    """Checks for a face match using the camera."""
    ret, frame = video_capture.read()
    if not ret:
        print("[ERROR] Failed to capture frame.")
        return False

    # Adjust brightness of the video capture
    frame = adjust_brightness(frame, value=30)

    # Display the frame for debugging
    cv2.imshow('Captured Frame', frame)
    cv2.waitKey(1)

    # Convert frame to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)

    if not face_locations:
        print("[WARNING] No faces detected.")
        return False

    # Encode faces and compare
    try:
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(reference_face_encodings, face_encoding, tolerance=tolerance)
            if any(matches):
                print("[INFO] Face match found!")
                return True
    except Exception as e:
        print(f"[ERROR] Error in face encoding or comparison: {e}")

    print("[WARNING] No face match found.")
    return False

def adjust_brightness(image, value=30):
    """Adjust the brightness of an image."""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    v = cv2.add(v, value)
    v[v > 255] = 255
    v[v < 0] = 0
    final_hsv = cv2.merge((h, s, v))
    image = cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)
    return image

def take_pictures(video_capture, script_dir):
    """Takes three pictures with 5 seconds interval and adjusts brightness."""
    picture_paths = []
    for i in range(1, 4):
        ret, frame = video_capture.read()
        if ret:
            # Adjust brightness
            frame = adjust_brightness(frame, value=30)
            image_path = os.path.join(script_dir, f"photo{i}.jpg")
            try:
                cv2.imwrite(image_path, frame)
                picture_paths.append(image_path)
                print(f"[INFO] Picture {i} saved as {image_path}")
            except Exception as e:
                print(f"[ERROR] Failed to save picture {i}: {e}")
        else:
            print(f"[ERROR] Failed to capture picture {i}")
        time.sleep(5)
    return picture_paths

def load_reference_encodings(picture_paths):
    """Loads face encodings from the given picture paths."""
    reference_face_encodings = []
    for image_path in picture_paths:
        if os.path.exists(image_path):
            reference_image = face_recognition.load_image_file(image_path)
            face_encodings = face_recognition.face_encodings(reference_image)
            if len(face_encodings) == 0:
                print(f"[ERROR] No faces found in the image: {image_path}")
                return None
            reference_face_encoding = face_encodings[0]
            reference_face_encodings.append(reference_face_encoding)
        else:
            print(f"[INFO] {image_path} does not exist.")
            return None
    return reference_face_encodings

def prevent_idle():
    """Prevent the screen from going idle by simulating a control key press."""
    if platform.system() == "Darwin":  # macOS
        os.system('osascript -e \'tell application "System Events" to key code 59\'')  # 59 is the key code for the control key

def check_user_match(previous_reference_encodings, video_capture):
    """Check if the current user matches the previous reference."""
    return check_face(previous_reference_encodings, video_capture)

def get_available_cameras():
    """Detect available cameras."""
    available_cameras = []
    index = 0
    while True:
        video_capture = cv2.VideoCapture(index)
        if not video_capture.isOpened():
            break
        available_cameras.append(index)
        video_capture.release()
        index += 1
    return available_cameras

def main():
    """Main loop for periodic face checking."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    check_interval = 12  # Check every 12 seconds

    # Ensure the script has write permissions for the directory
    ensure_write_permissions(script_dir)

    # Detect available cameras
    cam_indices = get_available_cameras()
    if not cam_indices:
        print("[ERROR] No available cameras found.")
        return

    print(f"[INFO] Available cameras: {cam_indices}")

    # Load previous reference pictures
    previous_picture_paths = [
        os.path.join(script_dir, "photo1.jpg"),
        os.path.join(script_dir, "photo2.jpg"),
        os.path.join(script_dir, "photo3.jpg"),
    ]
    previous_reference_encodings = load_reference_encodings(previous_picture_paths)
    
    # Check if the previous reference encodings are existing
    if previous_reference_encodings is None:
        print("[ERROR] No previous reference pictures found. Taking new reference pictures...")
        for cam_index in cam_indices:
            video_capture = cv2.VideoCapture(cam_index)
            if video_capture.isOpened():
                previous_picture_paths = take_pictures(video_capture, script_dir)
                previous_reference_encodings = load_reference_encodings(previous_picture_paths)
                if previous_reference_encodings is not None:
                    break
        if previous_reference_encodings is None:
            print("[ERROR] Failed to load new reference face encodings.")
            return

    print("[INFO] Previous reference pictures loaded successfully.")

    # Flag to indicate if new pictures have been taken and reference updated
    reference_updated = False

    # Check if the current user matches the previous reference at the start
    for cam_index in cam_indices:
        video_capture = cv2.VideoCapture(cam_index)
        if video_capture.isOpened() and check_user_match(previous_reference_encodings, video_capture):
            print("[INFO] User matched with previous reference. Overriding old reference pictures.")
            previous_picture_paths = take_pictures(video_capture, script_dir)
            previous_reference_encodings = load_reference_encodings(previous_picture_paths)
            if previous_reference_encodings is None:
                print("[ERROR] Failed to load new reference face encodings.")
                return
            reference_updated = True
            break

    screen_locked = False
    mismatch_count = 0
    MAX_CONSECUTIVE_MISMATCHES = 3  # Lock screen after 3 consecutive mismatches

    # Track the times when the screen was locked
    lock_times = deque(maxlen=3)

    try:
        while True:
            print("[INFO] Starting face check...")
            face_detected = False
            for cam_index in cam_indices:
                video_capture = cv2.VideoCapture(cam_index)
                if video_capture.isOpened():
                    if check_face(previous_reference_encodings, video_capture):
                        face_detected = True
                        break
                    else:
                        print(f"[INFO] No face detected with camera {cam_index}. Switching to the next camera.")
                else:
                    print(f"[ERROR] Failed to open camera {cam_index}.")
            
            if not face_detected:
                mismatch_count += 1
                print(f"[WARNING] Mismatch count: {mismatch_count}/{MAX_CONSECUTIVE_MISMATCHES}")
                if mismatch_count >= MAX_CONSECUTIVE_MISMATCHES:
                    lock_screen()
                    screen_locked = True
                    lock_times.append(datetime.now())
                    break

                # Wait only 3 seconds after a mismatch
                print("[INFO] Waiting for 3 seconds before the next mismatch check...")
                time.sleep(3)
            else:
                print("[INFO] Face matched. Resetting mismatch count.")
                mismatch_count = 0  # Reset mismatch count on successful match

                # Check if there was recent user activity
                if (datetime.now() - last_activity_time).total_seconds() > 10:
                    # Prevent the screen from going idle
                    prevent_idle()
                else:
                    print("[INFO] User is active. Skipping prevent idle.")

                time.sleep(2)

                video_capture.release()

                # Wait 12 seconds before the next check after a match
                print("[INFO] Waiting for 12 seconds before the next check...")
                time.sleep(check_interval)

            time.sleep(2)  # Wait 2 seconds before the next check

        # If the screen was locked, skip taking new pictures after unlocking
        if screen_locked:
            print("[INFO] Screen was locked. Skipping taking new pictures after unlocking.")
            return

        # Check if the screen was locked three times within a minute
        if len(lock_times) == 3 and (datetime.now() - lock_times[0]) < timedelta(minutes=1):
            print("[INFO] Screen was locked three times within a minute. Waiting for 3 minutes before checking again.")
            time.sleep(3 * 60)  # Wait for 3 minutes

    finally:
        print("[INFO] Exiting...")
        cv2.destroyAllWindows()  # Close all OpenCV windows

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}")