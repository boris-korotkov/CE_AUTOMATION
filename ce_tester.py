import argparse
import os
import sys
import time
import logging
import subprocess # We need this for the new connection logic
import ce_actions
import ce_interactive
from ce_workflow_engine import WorkflowEngine

# --- CONFIGURATION ---
DEFAULT_ADB_ID = "127.0.0.1:5685" #2024.4
# DEFAULT_ADB_ID = "127.0.0.1:5695" #2024.5
# DEFAULT_ADB_ID = "127.0.0.1:5605" #Adidas
DEFAULT_LANGUAGE = "en"
# Set the name of the scenario from workflows.yaml you want to test with option 9
DEFAULT_TEST_SCENARIO = "Daily_rewards" # <-- ADDED CONFIGURATION
# ---------------------

def get_coords(prompt="Enter coordinates as X,Y: "):
    while True:
        try:
            val = input(prompt)
            x, y = map(int, val.split(','))
            return x, y
        except ValueError:
            print("Invalid format. Please use X,Y (e.g., 100,200)")

def get_region(prompt="Enter region as X,Y,Width,Height: "):
    while True:
        try:
            val = input(prompt)
            x, y, w, h = map(int, val.split(','))
            return x, y, w, h
        except ValueError:
            print("Invalid format. Please use X,Y,W,H (e.g., 50,100,80,25)")

def print_menu():
    """Prints the main menu of available commands."""
    print("\n" + "="*50)
    print("      Clone Evolution Interactive Tester")
    print("="*50)
    print("--- Send Commands to Emulator ---")
    print("1. Click at specified coordinates (x, y)")
    print("2. Compare region with Image")
    print("3. Compare region with Text")
    print("4. Scroll")
    print("--- Get Info from Emulator (Interactive) ---")
    print("7. Get Coordinates by Clicking on Window")
    print("8. Select Region by Dragging on Window")
    print("--- Workflow Testing ---") # <-- ADDED SECTION
    print(f"9. Run Test Scenario ('{DEFAULT_TEST_SCENARIO}')") # <-- ADDED OPTION
    print("--- Utility ---")
    print("5. Delay (pause)")
    print("6. Take Full Screenshot")
    print("exit - Quit the tester")
    print("-"*50)

def main(adb_id, language):
    """Main interactive loop for the tester."""
    if not os.path.exists('temp'):
        os.makedirs('temp')

    print(f"\nTester connected to ADB device: {adb_id}")
    print(f"Using language for resources: '{language}'")
    
    while True:
        print_menu()
        choice = input("Enter your choice: ").strip().lower()

        try:
            if choice == '1':
                x, y = get_coords()
                ce_actions.click(adb_id, x, y)
                print(f"Action Sent: Clicked at ({x}, {y})")

            elif choice == '2':
                x, y, w, h = get_region()
                img_name = input("Enter template image filename (e.g., back-arrow.png): ")
                threshold_str = input("Enter match threshold [0.0-1.0] (default 0.85): ")
                threshold = float(threshold_str) if threshold_str else 0.85
                
                result = ce_actions.compare_with_image(adb_id, language, x, y, w, h, img_name, threshold)
                print(f"\n--- RESULT ---\nMatch found: {result}\n----------------")
                print("INFO: The captured screen area was saved to 'temp/last_capture.png' for inspection.")
            
            elif choice == '3':
                x, y, w, h = get_region()
                text = input("Enter the text to search for: ")
                
                result = ce_actions.compare_with_text(adb_id, language, x, y, w, h, text)
                print(f"\n--- RESULT ---\nMatch found: {result}\n----------------")
                print("INFO: The captured screen area was saved to 'temp/last_capture.png' for inspection.")

            elif choice == '4':
                x, y = get_coords("Enter scroll start coordinates as X,Y: ")
                direction = input("Enter direction (up, down, left, right): ").lower()
                if direction not in ['up', 'down', 'left', 'right']:
                    print("Invalid direction.")
                    continue
                distance_str = input("Enter scroll distance in pixels (e.g., 300): ")
                distance = int(distance_str)
                
                ce_actions.scroll(adb_id, x, y, direction, distance)
                print(f"Action Sent: Scrolled {direction} by {distance}px.")

            elif choice == '5':
                delay_str = input("Enter delay in seconds: ")
                delay = float(delay_str)
                print(f"Pausing for {delay} seconds...")
                time.sleep(delay)
                print("...resuming.")

            elif choice == '6':
                path = ce_actions.take_screenshot(adb_id)
                if path:
                    print(f"Full screenshot saved to: {path}")
                else:
                    print("Failed to take screenshot.")
            
            elif choice == '7':
                coords = ce_interactive.get_coords_from_click(adb_id)
                if coords:
                    print(f"\n--- COORDINATES CAPTURED ---\nResult: {coords[0]},{coords[1]}\n----------------------------")
                else:
                    print("Could not get coordinates.")

            elif choice == '8':
                region = ce_interactive.get_region_from_drag(adb_id)
                if region:
                    print(f"\n--- REGION CAPTURED ---\nResult: {region[0]},{region[1]},{region[2]},{region[3]}\n-----------------------")
                    print("The captured image has been saved in the 'temp' folder for you to inspect.")
                else:
                    print("Could not get region.")
            
            # --- ADDED SCENARIO EXECUTION ---
            elif choice == '9':
                if not DEFAULT_TEST_SCENARIO:
                    print("\nERROR: No test scenario is defined. Edit 'DEFAULT_TEST_SCENARIO' at the top of the script.")
                    continue
                
                print(f"\n--- Starting Scenario: {DEFAULT_TEST_SCENARIO} ---")
                try:
                    engine = WorkflowEngine(adb_id, language)
                    engine.run_workflow(DEFAULT_TEST_SCENARIO)
                    print(f"--- Scenario Finished: {DEFAULT_TEST_SCENARIO} ---")
                except Exception as e:
                    print(f"\nAN ERROR OCCURRED DURING SCENARIO EXECUTION: {e}")
            
            elif choice == 'exit':
                print("Exiting tester.")
                break
            
            else:
                print("Invalid choice, please try again.")

        except Exception as e:
            print(f"\nAn error occurred: {e}")
            print("Please check your inputs and try again.")


if __name__ == "__main__":
    # --- THIS STARTUP LOGIC IS NOW SIMPLIFIED ---
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    adb_id_to_use = DEFAULT_ADB_ID
    language_to_use = DEFAULT_LANGUAGE

    if not adb_id_to_use:
        print("\nERROR: DEFAULT_ADB_ID is not set in the script's CONFIGURATION section.")
        sys.exit(1)
        
    print(f"Attempting to connect to device: {adb_id_to_use}")
    is_connected = False
    try:
        # Step 1: Attempt to connect
        connect_result = subprocess.run(f"adb connect {adb_id_to_use}", shell=True, check=True, capture_output=True, text=True)
        if "failed to connect" in connect_result.stdout or "unable to connect" in connect_result.stdout:
            # This handles cases where the port is wrong or the emulator isn't listening
            pass
        
        # Step 2: Verify connection by checking 'adb devices'
        time.sleep(1) # Give ADB a moment to register the device
        for _ in range(3): # Try for a few seconds
            devices_result = subprocess.run("adb devices", shell=True, capture_output=True, text=True)
            if adb_id_to_use in devices_result.stdout and 'device' in devices_result.stdout:
                 is_connected = True
                 break
            time.sleep(1)

    except FileNotFoundError:
        print("\nFATAL: 'adb' command not found. Please ensure ADB is installed and in your system's PATH.")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn unexpected error occurred during ADB connection: {e}")
        sys.exit(1)

    # If connection is successful, start the main program. Otherwise, exit with an error.
    if is_connected:
        main(adb_id_to_use, language_to_use)
    else:
        print("\nFATAL: Could not connect to the emulator device.")
        print("Please ensure the following:")
        print("1. The emulator is running.")
        print("2. ADB debugging is enabled in the emulator's settings.")
        print(f"3. The DEFAULT_ADB_ID ('{adb_id_to_use}') at the top of the script is correct.")
        sys.exit(1)