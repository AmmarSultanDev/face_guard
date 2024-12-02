import cv2
import face_recognition
import os
import time
import stat

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

def take_pictures(video_capture, script_dir):
    """Takes three pictures with 5 seconds interval."""
    picture_paths = []
    for i in range(1, 4):
        ret, frame = video_capture.read()
        if ret:
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

def main():
    """Main loop for periodic face checking."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cam_index = 0
    check_interval = 12  # Check every 12 seconds
    video_capture = cv2.VideoCapture(cam_index)
    if not video_capture.isOpened():
        print("[ERROR] Failed to open the built-in camera.")
        return

    # Ensure the script has write permissions for the directory
    ensure_write_permissions(script_dir)

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
        previous_picture_paths = take_pictures(video_capture, script_dir)
        previous_reference_encodings = load_reference_encodings(previous_picture_paths)
        if previous_reference_encodings is None:
            print("[ERROR] Failed to load new reference face encodings.")
            return

    # Compare new video picture with previous reference pictures
    print("[INFO] Comparing new video picture with previous reference pictures...")
    if not check_face(previous_reference_encodings, video_capture):
        lock_screen()
        return

    # Take new pictures and make them the new reference
    print("[INFO] Taking new reference pictures...")
    new_picture_paths = take_pictures(video_capture, script_dir)
    new_reference_encodings = load_reference_encodings(new_picture_paths)
    if new_reference_encodings is None:
        print("[ERROR] Failed to load new reference face encodings.")
        return

    print("[INFO] New reference pictures matched successfully.")
    video_capture.release()

    mismatch_count = 0
    MAX_CONSECUTIVE_MISMATCHES = 3  # Lock screen after 3 consecutive mismatches

    while True:
        print("[INFO] Starting face check...")
        video_capture = cv2.VideoCapture(cam_index)
        if not video_capture.isOpened():
            print("[ERROR] Failed to open the built-in camera.")
            break

        # Add a delay before checking the face
        time.sleep(2)

        if not check_face(new_reference_encodings, video_capture):
            mismatch_count += 1
            print(f"[WARNING] Mismatch count: {mismatch_count}/{MAX_CONSECUTIVE_MISMATCHES}")
            if mismatch_count >= MAX_CONSECUTIVE_MISMATCHES:
                lock_screen()
                break

            # Wait only 3 seconds after a mismatch
            print("[INFO] Waiting for 3 seconds before the next mismatch check...")
            time.sleep(3)
        else:
            print("[INFO] Face matched. Resetting mismatch count.")
            mismatch_count = 0  # Reset mismatch count on successful match

            time.sleep(2)

            video_capture.release()

            # Wait 12 seconds before the next check after a match
            print("[INFO] Waiting for 12 seconds before the next check...")
            time.sleep(check_interval)

        time.sleep(2)  # Wait 2 seconds before the next check

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}")