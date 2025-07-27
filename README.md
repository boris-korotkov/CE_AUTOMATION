# Mobile Game Automation Framework (Clone Evolution Example)

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Overview

This project is a powerful and flexible framework for automating repetitive tasks in mobile games running on a PC via an Android emulator. By leveraging computer vision and a sophisticated workflow engine, it can perform complex, multi-step actions, saving you time and ensuring consistent execution of daily routines across multiple game accounts.

While this framework can be adapted for any mobile game, the current implementation and workflows are tailored for **Clone Evolution**.

### Benefits of Automation
*   **Time Efficiency:** Automate daily chores, resource collection, and event participation across all your accounts in a fraction of the time.
*   **Consistency:** The bot performs actions with pixel-perfect precision, eliminating human error.
*   **Multi-Account Management:** Seamlessly launch, run tasks on, and close multiple game instances in a predefined order.
*   **Multi-Emulator Support:** The framework is designed to work with different emulators. Although primarily tested with **BlueStacks**, it includes configuration options for **Nox** and can be extended.

## Key Features
*   **Anchor-Based Computer Vision:** Uses OpenCV to dynamically find UI elements (buttons, icons, etc.) on the screen, making it resilient to ads, resolution changes, and minor UI shifts.
*   **Advanced Image Recognition:** Supports both fast template matching for static elements and robust feature matching for animated or inconsistent elements.
*   **Sophisticated Workflow Engine:** Uses simple YAML files to define complex, multi-step scenarios with loops, conditional logic, and variables.
*   **Centralized Workflow Management:** Define workflow sets once and apply them to all instances, making configuration clean and easy to manage.
*   **Interactive Tester Script:** A powerful command-line tool (`ce_tester.py`) for debugging, finding coordinates, and testing image recognition on the fly.
*   **Hotkeys & Notifications:** Supports global hotkeys to pause/resume or stop the script, and can send email notifications for critical events.

## Technology Stack
*   **Language:** Python 3
*   **Computer Vision:** OpenCV, NumPy
*   **OCR:** Tesseract, EasyOCR
*   **Workflow Engine:** PyYAML, Jinja2
*   **Emulator Interaction:** Android Debug Bridge (ADB)
*   **Dependencies:** scikit-learn, PyWin32, keyboard

---

## Getting Started

### Prerequisites
Before you begin, ensure you have the following installed and configured:

1.  **Python:** Version 3.9 or higher.
2.  **Android Emulator:** **BlueStacks 5** is recommended and tested.
3.  **Tesseract OCR:** This is required for text detection.
    *   Download the installer from the official [Tesseract GitHub repository](https://github.com/UB-Mannheim/tesseract/wiki).
    *   During installation, **make sure to add Tesseract to your system's PATH variable**. This is a crucial step.
    *   After installation, update the `tesseract_path` in `instances.ini` to point to `tesseract.exe`.
4.  **Android Debug Bridge (ADB):** ADB is required to communicate with the emulator. It usually comes bundled with BlueStacks. Ensure that the directory containing `HD-Adb.exe` (usually in the BlueStacks installation folder) is added to your system's PATH.

### Installation
1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd <your-repository-folder>
    ```

2.  **Create and activate a Python virtual environment (recommended):**
    ```bash
    # Create the environment
    python -m venv venv

    # Activate it (Windows)
    venv\Scripts\activate
    ```

3.  **Install the required Python packages:**
    ```bash
    pip install -r requirements.txt
    ```

---

## Configuration
All configuration is handled in the `instances.ini` file. This includes emulator paths, instance details, and which workflows to run.

**For a detailed guide on every setting, please see the [Configuration Guide](CONFIG_GUIDE.md).**

---

## Usage

### Running the Main Bot (`ce_robot.py`)
This script runs the full automation sequence.

**1. Standard Run:**
Uses the `[RunOrder]` and `[Workflows]` sections from `instances.ini`.
```bash
python ce_robot.py
```

**2. Target Specific Instances:**
Ignores `[RunOrder]` and runs only the specified instances.
```bash
python ce_robot.py Adidas CE_2024_1
```

**3. Run with a Custom Workflow File:**
Uses a specific YAML file for the run. Ideal for testing or special tasks.
```bash
python ce_robot.py -wf "resources/en/special_tasks.yaml"
```

### Testing with the Interactive Tester (`ce_tester.py`)
This script provides a menu-driven interface to test individual actions without running a full workflow. It's essential for creating new automation scenarios.

**To run:**
```bash
# Make sure your virtual environment is active
python ce_tester.py <instance_name>

# Example:
python ce_tester.py Adidas
```
You will be presented with a menu of options to find coordinates, test image matching (both static and feature-based), and run single scenarios.

---

## Creating Workflows
Automation logic is defined in YAML files (e.g., `resources/en/workflows.yaml`).

**For a complete command reference and guide to writing workflows, please see the [User Manual & Command Reference](USER_MANUAL.html).**

---

## Creating an Executable
You can package the script into a single `.exe` file using **PyInstaller**. This allows you to run the bot without needing a Python installation.

1.  **Install PyInstaller:**
    ```bash
    pip install pyinstaller
    ```

2.  **Run the PyInstaller command:**
    This command packages the main script and correctly includes your necessary resource files and configurations. Run it from your project's root directory.
    ```bash
    pyinstaller --noconsole --onefile --name "CE_Robot" ^
    --add-data "instances.ini;." ^
    --add-data "workflows.yaml;." ^
    --add-data "resources;resources" ^
    ce_robot.py
    ```
    *   `--noconsole`: Prevents the command prompt from opening when you run the `.exe`.
    *   `--onefile`: Packages everything into a single executable.
    *   `--add-data`: This is critical. It tells PyInstaller to bundle your configuration and resource files.
    *   The final `.exe` will be located in the `dist` folder.