import argparse
import os
import sys
import time
import logging
import subprocess
from ce_config import load_instances, connect_adb_to_instance  # Added load_instances
import ce_actions
import ce_interactive
from ce_workflow_engine import WorkflowEngine

# --- CONFIGURATION ---
# Set the default INSTANCE NAME from instances.ini you want to test.
DEFAULT_INSTANCE_NAME = "CE_2024_1"
#DEFAULT_ADB_ID = "127.0.0.1:5605" #Adidas
#DEFAULT_ADB_ID = "127.0.0.1:5575" #Hidden Enemy
#DEFAULT_ADB_ID = "127.0.0.1:5585" #Comrad B
#DEFAULT_ADB_ID = "127.0.0.1:5595" #Charlie
DEFAULT_ADB_ID = "127.0.0.1:5655" #2024.1
#DEFAULT_ADB_ID = "127.0.0.1:5665" #2024.2
#DEFAULT_ADB_ID = "127.0.0.1:5675" #2024.3
#DEFAULT_ADB_ID = "127.0.0.1:5685" #2024.4
#DEFAULT_ADB_ID = "127.0.0.1:5695" #2024.5

# Set the DEFAULT scenario from workflows.yaml to be used if you press Enter at the prompt.
DEFAULT_TEST_SCENARIO = "Gene_Bank"
# ---------------------

def get_coords(prompt="Enter coordinates as X,Y: "):
    # ... (This function is unchanged) ...
    while True:
        try:
            val = input(prompt)
            x, y = map(int, val.split(','))
            return x, y
        except ValueError:
            print("Invalid format. Please use X,Y (e.g., 100,200)")

def get_region(prompt="Enter region as X,Y,Width,Height: "):
    # ... (This function is unchanged) ...
    while True:
        try:
            val = input(prompt)
            x, y, w, h = map(int, val.split(','))
            return x, y, w, h
        except ValueError:
            print("Invalid format. Please use X,Y,W,H (e.g., 50,100,80,25)")

def print_menu():
    # ... (This function is unchanged) ...
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
    print("--- Workflow Testing ---")
    print("9. Run a Test Scenario")
    print("--- Utility ---")
    print("5. Delay (pause)")
    print("6. Take Full Screenshot")
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
            # ... (Options 1-8 are unchanged) ...
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
                if direction not in ['up', 'down', 'left', 'right']: print("Invalid direction."); continue
                distance = int(input("Enter scroll distance in pixels (e.g., 300): "))
                ce_actions.scroll(adb_id, x, y, direction, distance)
                print(f"Action Sent: Scrolled {direction} by {distance}px.")
            elif choice == '5':
                delay = float(input("Enter delay in seconds: "))
                print(f"Pausing for {delay} seconds...")
                time.sleep(delay)
                print("...resuming.")
            elif choice == '6':
                path = ce_actions.take_screenshot(adb_id)
                if path: print(f"Full screenshot saved to: {path}")
                else: print("Failed to take screenshot.")
            elif choice == '7':
                coords = ce_interactive.get_coords_from_click(adb_id)
                if coords: print(f"\n--- COORDINATES CAPTURED ---\nResult: {coords[0]},{coords[1]}\n----------------------------")
                else: print("Could not get coordinates.")
            elif choice == '8':
                region = ce_interactive.get_region_from_drag(adb_id)
                if region: print(f"\n--- REGION CAPTURED ---\nResult: {region[0]},{region[1]},{region[2]},{region[3]}\n-----------------------")
                else: print("Could not get region.")
            
            # --- UPDATED SCENARIO EXECUTION ---
            elif choice == '9':
                user_input = input(f"Enter scenario name to run (default: {DEFAULT_TEST_SCENARIO}): ").strip()
                scenario_to_run = user_input or DEFAULT_TEST_SCENARIO

                if not scenario_to_run:
                    print("\nERROR: No scenario name provided and no default is set.")
                    continue
                
                print(f"\n--- Starting Scenario: {scenario_to_run} for instance {instance_name} ---")
                try:
                    # Initialize the engine with the instance name
                    engine = WorkflowEngine(adb_id, language, instance_name)
                    engine.run_workflow(scenario_to_run)
                    print(f"--- Scenario Finished: {scenario_to_run} ---")
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
    # --- UPDATED STARTUP LOGIC ---
    parser = argparse.ArgumentParser(
        description="Interactive tester for Clone Evolution automation actions.",
        formatter_class=argparse.RawTextHelpFormatter,
        usage="python %(prog)s [instance_name]"
    )
    parser.add_argument("instance_name", nargs='?', default=None, help="The instance name from instances.ini (e.g., 'Adidas').")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    instance_name_to_use = args.instance_name or DEFAULT_INSTANCE_NAME
    
    if not instance_name_to_use:
        print("\nERROR: Instance name is not set.")
        parser.print_help()
        sys.exit(1)
    
    print(f"Using instance: '{instance_name_to_use}'")
        
    all_instances = load_instances()
    if instance_name_to_use not in all_instances:
        print(f"\nERROR: Instance '{instance_name_to_use}' not found in instances.ini.")
        sys.exit(1)
    
    language_to_use = all_instances[instance_name_to_use].get('language', 'en')
    
    print(f"Attempting to connect to instance '{instance_name_to_use}' via ADB...")
    adb_id_to_use = connect_adb_to_instance(instance_name_to_use, logger=logging.getLogger())

    if adb_id_to_use:
        # Pass all three required parameters to the main function
        main(adb_id_to_use, language_to_use, instance_name_to_use)
    else:
        print("\nFATAL: Could not connect to the emulator instance.")
        print("Please ensure the following:")
        print("1. The correct emulator instance is running.")
        print(f"2. The instance name '{instance_name_to_use}' is correct in instances.ini.")
        print("3. The 'adb_port' for the instance is correct in instances.ini.")
        print("4. ADB is enabled in the emulator's settings.")
        sys.exit(1)