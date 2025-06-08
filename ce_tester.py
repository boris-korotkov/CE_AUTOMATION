import argparse
import os
import sys
import time
import ce_actions
import ce_interactive  # Import the new interactive module

# --- CONFIGURATION ---
# DEFAULT_ADB_ID = "127.0.0.1:5695" #2024.5
DEFAULT_ADB_ID = "127.0.0.1:5685" #2024.4
DEFAULT_LANGUAGE = "en"
# ---------------------

def get_coords(prompt="Enter coordinates as X,Y: "):
    # ... (this function remains the same)
    while True:
        try:
            val = input(prompt)
            x, y = map(int, val.split(','))
            return x, y
        except ValueError:
            print("Invalid format. Please use X,Y (e.g., 100,200)")

def get_region(prompt="Enter region as X,Y,Width,Height: "):
    # ... (this function remains the same)
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
                print("\n--- RESULT ---")
                print(f"Match found: {result}")
                print("----------------")
                print("INFO: The captured screen area was saved to 'temp/last_capture.png' for inspection.")
            
            elif choice == '3':
                x, y, w, h = get_region()
                text = input("Enter the text to search for: ")
                
                result = ce_actions.compare_with_text(adb_id, language, x, y, w, h, text)
                print("\n--- RESULT ---")
                print(f"Match found: {result}")
                print("----------------")
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
            
            # --- NEW INTERACTIVE OPTIONS ---
            elif choice == '7':
                coords = ce_interactive.get_coords_from_click(adb_id)
                if coords:
                    print(f"\n--- COORDINATES CAPTURED ---")
                    print(f"Result: {coords[0]},{coords[1]}")
                    print(f"----------------------------")
                else:
                    print("Could not get coordinates.")

            elif choice == '8':
                region = ce_interactive.get_region_from_drag(adb_id)
                if region:
                    print(f"\n--- REGION CAPTURED ---")
                    print(f"Result: {region[0]},{region[1]},{region[2]},{region[3]}")
                    print(f"-----------------------")
                    print("The captured image has been saved in the 'temp' folder for you to inspect.")
                else:
                    print("Could not get region.")
            
            elif choice == 'exit':
                print("Exiting tester.")
                break
            
            else:
                print("Invalid choice, please try again.")

        except Exception as e:
            print(f"\nAn error occurred: {e}")
            print("Please check your inputs and try again.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Interactive tester for Clone Evolution automation actions.",
        formatter_class=argparse.RawTextHelpFormatter,
        usage="python %(prog)s [adb_id] [language]"
    )
    parser.add_argument(
        "adb_id", 
        nargs='?',
        default=None,
        help="The ADB device ID of the running emulator (e.g., '127.0.0.1:5605')."
    )
    parser.add_argument(
        "language", 
        nargs='?',
        default=None,
        help="The two-letter language code for resource paths (e.g., 'en', 'ru')."
    )
    
    args = parser.parse_args()

    if args.adb_id and args.language:
        print("Using command-line arguments for configuration.")
        adb_id_to_use = args.adb_id
        language_to_use = args.language
    else:
        print("Using default configuration from inside the script.")
        adb_id_to_use = DEFAULT_ADB_ID
        language_to_use = DEFAULT_LANGUAGE

    if not adb_id_to_use or not language_to_use:
        print("\nError: ADB ID or Language is not set.")
        print("Please either edit the CONFIGURATION section at the top of the script")
        print("or provide both values as command-line arguments.\n")
        parser.print_help()
        sys.exit(1)

    main(adb_id_to_use, language_to_use)