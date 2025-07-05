import argparse
import os
import sys
import time
import logging
import subprocess
from ce_config import load_instances, connect_adb_to_instance
import ce_actions
import ce_interactive
from ce_workflow_engine import WorkflowEngine

# --- CONFIGURATION ---
DEFAULT_INSTANCE_NAME = "ComradB"
DEFAULT_TEST_SCENARIO = "Supply_Depot_Farming"
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
    menu_items = {
        "1": "Click at specified coordinates (x, y)",
        "2": "Compare w/ Image (Template Match)",
        "3": "Compare w/ Image (Feature Match - ORB)",
        "4": "Compare w/ Text (Tesseract)",
        "5": "Compare w/ Text (EasyOCR)",
        "6": "Scroll",
        "7": "Get Coordinates by Clicking on Window",
        "8": "Select Region by Dragging on Window",
        "9": "Get Coordinates from Image (Anchor Finding)",
        "10": "Get Coords from Features (Animated Anchor)", # <-- NEW
        "11": "Run a Test Scenario" # <-- RENUMBERED
    }
    print("\n" + "="*50)
    print("      Clone Evolution Interactive Tester")
    print("="*50)
    for key, value in menu_items.items():
        print(f"{key}. {value}")
    print("exit - Quit the tester")
    print("-"*50)

def main(adb_id, language, instance_name):
    """Main interactive loop for the tester."""
    if not os.path.exists('temp'):
        os.makedirs('temp')

    print(f"\nSuccessfully connected to instance '{instance_name}' (device: {adb_id})")
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
                img_name = input("Enter template image filename: ")
                threshold = float(input("Enter match threshold [0.0-1.0] (default 0.85): ") or 0.85)
                result = ce_actions.compare_with_image(adb_id, language, instance_name, x, y, w, h, img_name, threshold)
                print(f"\n--- TEMPLATE MATCH RESULT ---\nMatch found: {result}\n---------------------------")

            elif choice == '3':
                x, y, w, h = get_region()
                img_name = input("Enter template image filename: ")
                min_matches = int(input("Enter minimum feature matches required (default 10): ") or 10)
                result = ce_actions.compare_with_features(adb_id, language, instance_name, x, y, w, h, img_name, min_matches)
                print(f"\n--- FEATURE MATCH RESULT ---\nMatch found: {result}\n--------------------------")

            elif choice == '4':
                x, y, w, h = get_region()
                text = input("Enter the text to search for: ")
                result = ce_actions.compare_with_text(adb_id, language, instance_name, x, y, w, h, text)
                print(f"\n--- TESSERACT RESULT ---\nMatch found: {result}\n----------------")

            elif choice == '5':
                x, y, w, h = get_region()
                text = input("Enter the text to search for: ")
                result = ce_actions.compare_with_text_easyocr(adb_id, language, instance_name, x, y, w, h, text)
                print(f"\n--- EASYOCR RESULT ---\nMatch found: {result}\n----------------")

            elif choice == '6':
                x, y = get_coords("Enter scroll start coordinates as X,Y: ")
                direction = input("Enter direction (up, down, left, right): ").lower()
                distance = int(input("Enter scroll distance in pixels (e.g., 300): "))
                ce_actions.scroll(adb_id, x, y, direction, distance)
                print(f"Action Sent: Scrolled {direction} by {distance}px.")

            elif choice == '7':
                coords = ce_interactive.get_coords_from_click(adb_id)
                if coords: print(f"\n--- COORDINATES CAPTURED ---\nResult: {coords[0]},{coords[1]}\n----------------------------")

            elif choice == '8':
                region = ce_interactive.get_region_from_drag(adb_id)
                if region: print(f"\n--- REGION CAPTURED ---\nResult: {region[0]},{region[1]},{region[2]},{region[3]}\n-----------------------")

            elif choice == '9':
                img_name = input("Enter template image filename to find: ")
                threshold = float(input("Enter match threshold [0.0-1.0] (default 0.85): ") or 0.85)
                coords = ce_actions.get_coords_from_image(adb_id, language, img_name, threshold)
                if coords:
                    print(f"\n--- COORDINATES CAPTURED (from Image) ---\nResult: {coords[0]},{coords[1]}\n-----------------------------------------")
                else:
                    print(f"\n--- RESULT ---\nImage '{img_name}' not found on screen.\n--------------")

            # --- NEW FUNCTIONALITY ---
            elif choice == '10':
                img_name = input("Enter template image filename to find: ")
                min_matches = int(input("Enter minimum feature matches required (default 10): ") or 10)
                coords = ce_actions.get_coords_from_features(adb_id, language, img_name, min_matches)
                if coords:
                    print(f"\n--- COORDINATES CAPTURED (from Features) ---\nResult: {coords[0]},{coords[1]}\n--------------------------------------------")
                else:
                    print(f"\n--- RESULT ---\nImage '{img_name}' not found on screen using feature matching.\n--------------")

            # --- RENUMBERED ---
            elif choice == '11':
                user_input = input(f"Enter scenario name to run (default: {DEFAULT_TEST_SCENARIO}): ").strip()
                scenario_to_run = user_input or DEFAULT_TEST_SCENARIO
                if not scenario_to_run: print("\nERROR: No scenario name provided."); continue
                print(f"\n--- Starting Scenario: {scenario_to_run} for instance {instance_name} ---")
                engine = WorkflowEngine(adb_id, language, instance_name)
                engine.run_workflow(scenario_to_run)
                print(f"--- Scenario Finished: {scenario_to_run} ---")
            
            elif choice == 'exit':
                print("Exiting tester.")
                break
            
            else:
                print("Invalid choice, please try again.")

        except Exception as e:
            print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    # ... (This startup logic is unchanged) ...
    parser = argparse.ArgumentParser(description="Interactive tester for Clone Evolution automation actions.", formatter_class=argparse.RawTextHelpFormatter, usage="python %(prog)s [instance_name]")
    parser.add_argument("instance_name", nargs='?', default=None, help="The instance name from instances.ini (e.g., 'Adidas').")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    instance_name_to_use = args.instance_name or DEFAULT_INSTANCE_NAME
    if not instance_name_to_use: print("\nERROR: Instance name is not set."); sys.exit(1)
    print(f"Using instance: '{instance_name_to_use}'")
    all_instances = load_instances()
    if instance_name_to_use not in all_instances: print(f"\nERROR: Instance '{instance_name_to_use}' not found in instances.ini."); sys.exit(1)
    language_to_use = all_instances[instance_name_to_use].get('language', 'en')
    print(f"Attempting to connect to instance '{instance_name_to_use}' via ADB...")
    adb_id_to_use = connect_adb_to_instance(instance_name_to_use, logger=logging.getLogger())
    if adb_id_to_use:
        main(adb_id_to_use, language_to_use, instance_name_to_use)
    else:
        print("\nFATAL: Could not connect to the emulator instance.")
        sys.exit(1)