# Awake.py Tutorial

This tutorial will guide you through the steps to set up and use `awake.py` to periodically check for face matches using your camera and lock the screen if no match is found.

## Prerequisites

- Python 3.6 or higher
- `pip` (Python package installer)
- [Miniconda](https://docs.conda.io/en/latest/miniconda.html) (optional but recommended for environment management)

## Installation

1. **Clone the repository** (if applicable):
    ```sh
    git clone <repository_url>
    cd <repository_directory>
    ```

2. **Create a virtual environment using Miniconda** (optional but recommended):
    ```sh
    conda create -n awake_env python=3.8
    conda activate awake_env
    ```

3. **Install the required packages**:
    ```sh
    pip install opencv-python face_recognition
    ```

## Usage

1. **Run the script**:
    ```sh
    python awake.py
    ```

2. **Script Behavior**:
    - The script will attempt to open the built-in camera.
    - It will ensure the script has write permissions for the directory.
    - It will load previous reference pictures (`photo1.jpg`, `photo2.jpg`, `photo3.jpg`) from the script directory.
    - If no previous reference pictures are found, it will take new reference pictures and use them as the reference.
    - It will compare the new video picture with the previous reference pictures.
    - If a face match is found, it will take new reference pictures and make them the new reference.
    - If no face match is found, it will lock the screen before continuing any other steps.
    - During periodic checks, if a face match is not found for a specified number of consecutive checks, it will lock the screen.

## Configuration

- **Face Matching Tolerance**: You can adjust the tolerance for face matching by modifying the `tolerance` parameter in the `check_face` function.
- **Check Interval**: You can adjust the interval between face checks by modifying the `check_interval` variable in the `main` function.
- **Maximum Consecutive Mismatches**: You can adjust the number of consecutive mismatches allowed before locking the screen by modifying the `MAX_CONSECUTIVE_MISMATCHES` variable in the `main` function.

## Troubleshooting

- **Camera Not Opening**: Ensure that your camera is properly connected and not being used by another application.
- **Permission Issues**: Ensure that the script has the necessary permissions to access the camera and write to the directory.
- **Face Not Detected**: Ensure that the lighting conditions are adequate and the camera is positioned correctly.

## Example Output

**Example Output**:
- `[INFO] Write permissions granted for directory: /path/to/script`
- `[INFO] Taking new reference pictures...`
- `[INFO] Picture 1 saved as /path/to/script/photo1.jpg`
- `[INFO] Picture 2 saved as /path/to/script/photo2.jpg`
- `[INFO] Picture 3 saved as /path/to/script/photo3.jpg`
- `[INFO] New reference pictures matched successfully.`
- `[INFO] Starting face check...`
- `[INFO] Face matched. Resetting mismatch count.`
- `[INFO] Waiting for 12 seconds before the next check...`

## License

This project is licensed under the CC0 1.0 UNIVERSAL - see the LICENSE file for details.

## Acknowledgments

- [OpenCV](https://opencv.org/)
- [face_recognition](https://github.com/ageitgey/face_recognition)
