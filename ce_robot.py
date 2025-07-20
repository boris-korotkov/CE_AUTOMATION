import logging
import time
import os
import sys
import threading
import argparse
import yaml
from datetime import datetime
from ce_config import load_instances, load_emulator_type, connect_adb_to_instance, load_run_order, load_general_config, load_hotkey_config
from ce_launcher import launch_instance, terminate_instance
from ce_workflow_engine import WorkflowEngine
import ce_actions
from ce_hotkeys import setup_hotkey_listener

# Global threading events for hotkeys
pause_event = threading.Event()
stop_event = threading.Event()

def setup_logging(log_level_str='INFO'):
    # Get the desired log level object (e.g., logging.INFO) from the config string
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    
    # Get the root logger
    logger = logging.getLogger()
    # Set the master gatekeeper level. All handlers will inherit this as their upper limit.
    logger.setLevel(log_level)
    
    # Remove any old handlers to prevent duplicate logging if this function is called again
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        
    # Ensure the 'logs' directory exists
    if not os.path.exists('logs'):
        os.makedirs('logs')
        
    log_filename = f"logs/CE_robot_{time.strftime('%Y-%m-%d_%H-%M-%S')}.log"
    
    # --- File Handler ---
    file_handler = logging.FileHandler(log_filename)
    # Set the file handler's level to match the config
    file_handler.setLevel(log_level) 
    
    # --- Console Handler ---
    console_handler = logging.StreamHandler(sys.stdout)
    # Set the console handler's level to also match the config
    console_handler.setLevel(log_level)

    # Create a single formatter and apply it to both handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add the configured handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # These initial messages will now respect the log level
    logging.info("Logging setup complete.")
    logging.info(f"Log file created at: {log_filename}")
    logging.info(f"Global log level for all handlers set to: {log_level_str}")

def check_for_pause_or_stop():
    while pause_event.is_set():
        logging.info("Script is paused. Press the hotkey again to resume.")
        time.sleep(1)
    if stop_event.is_set():
        logging.critical("Emergency stop signal received. Terminating script.")
        sys.exit("Emergency stop activated by user.")

def main():
    """Main function to execute emulator instance automation."""
    parser = argparse.ArgumentParser(description="Clone Evolution automation robot.")
    parser.add_argument("instance_names", nargs='*', help="One or more instance names to run (e.g., 'CE_2024_1'). Overrides run order from config.")
    parser.add_argument("-wf", "--workflow-file", default=None, help="Path to a custom YAML workflow file to run instead of the default.")
    args = parser.parse_args()

    general_settings = load_general_config()
    hotkeys_config = load_hotkey_config()
    log_level = general_settings.get('log_level')
    emulator_boot_time = general_settings.get('emulator_boot_time')
    
    check_image = general_settings.get("game_load_check_image")
    check_threshold = general_settings.get("game_load_check_threshold")
    
    setup_logging(log_level)
    
    hotkey_thread = threading.Thread(target=setup_hotkey_listener, args=(pause_event, stop_event, hotkeys_config), daemon=True)
    hotkey_thread.start()
    
    MAX_LAUNCH_ATTEMPTS = 3
    
    try:
        check_for_pause_or_stop()
        emulator_type = load_emulator_type()
        logging.info(f"Preferred emulator type: {emulator_type}")
        
        all_instances = load_instances()
        
        if args.instance_names:
            execution_list = args.instance_names
            logging.info(f"Processing instances specified on command line: {execution_list}")
        else:
            run_order, start_from = load_run_order()
            if not run_order:
                logging.info("No specific run order found. Processing all defined instances.")
                execution_list = list(all_instances.keys())
            else:
                execution_list = run_order
            if start_from and start_from in execution_list:
                try:
                    start_index = execution_list.index(start_from)
                    execution_list = execution_list[start_index:]
                    logging.info(f"Execution will begin from instance: '{start_from}'")
                except ValueError:
                    logging.warning(f"'start_from' instance '{start_from}' not in order list. Starting from beginning.")
        
        logging.info(f"Final execution list: {execution_list}")

        for name in execution_list:
            check_for_pause_or_stop()
            if name not in all_instances:
                logging.warning(f"Instance '{name}' from run order not found in instance definitions. Skipping.")
                continue
            
            details = all_instances[name]
            command = details.get(f"{emulator_type}_command")
            language = details.get("language")

            workflows_to_run = []
            if args.workflow_file:
                if not os.path.exists(args.workflow_file):
                    logging.error(f"Custom workflow file not found at path: {args.workflow_file}")
                    sys.exit(1)
                try:
                    with open(args.workflow_file, 'r') as f:
                        data = yaml.safe_load(f)
                        workflows_to_run = [s['name'] for s in data.get('scenarios', [])]
                    logging.info(f"Using custom workflow file: '{args.workflow_file}' with workflows: {workflows_to_run}")
                except Exception as e:
                    logging.error(f"Could not load/parse custom workflow file '{args.workflow_file}': {e}. Skipping instance.")
                    continue
            else:
                workflows_to_run = details.get("workflows", [])
            
            if not command:
                logging.warning(f"Skipping instance '{name}' - No command found for emulator type '{emulator_type}'.")
                continue

            instance_ready, final_process, final_adb_id = False, None, None
            
            for attempt in range(1, MAX_LAUNCH_ATTEMPTS + 1):
                check_for_pause_or_stop()
                logging.info(f"--- Processing instance: {name} (Attempt {attempt}/{MAX_LAUNCH_ATTEMPTS}) ---")
                process, adb_id = None, None
                try:
                    process = launch_instance(name, command)
                    if not process: continue
                    logging.info(f"Waiting {emulator_boot_time}s for emulator boot...")
                    time.sleep(emulator_boot_time)
                    check_for_pause_or_stop()
                    adb_id = connect_adb_to_instance(name, logger=logging)
                    
                    # --- THIS IS THE CORRECTED LINE ---
                    if not adb_id:
                        terminate_instance(process, adb_id)
                        time.sleep(15)
                        continue
                    
                    logging.info(f"Successfully connected ADB to {adb_id}. Verifying game screen...")
                    
                    is_loaded = False
                    if check_image:
                        if ce_actions.get_coords_from_image(adb_id, language,name, "Startup_Check", check_image, check_threshold):
                            logging.info("Game load verification successful (Image Found).")
                            is_loaded = True
                        else:
                            logging.warning(f"Image-based verification FAILED for '{check_image}'.")
                    else:
                        logging.info("Global game load verification image not configured. Skipping check.")
                        is_loaded = True

                    if is_loaded:
                        instance_ready, final_process, final_adb_id = True, process, adb_id
                        break
                    else:
                        ce_actions.send_email(f"CE Automation: {name} Failed Verification", f"Instance '{name}' failed game load check on attempt {attempt}.")
                        terminate_instance(process, adb_id)
                        time.sleep(15)
                except Exception as e:
                    logging.error(f"Unexpected error during launch of {name}: {e}", exc_info=True)
                    if process: terminate_instance(process, adb_id)
            
            if instance_ready:
                try:
                    engine = WorkflowEngine(final_adb_id, language, name, workflow_file=args.workflow_file)
                    start_time = datetime.now()
                    logging.info(f"--- Starting all workflows for instance '{name}' ---")
                    for workflow_name in workflows_to_run:
                        check_for_pause_or_stop()
                        engine.run_workflow(workflow_name)
                    duration = datetime.now() - start_time
                    logging.info(f"--- Workflows for '{name}' completed. Duration: {str(duration).split('.')[0]} ---")
                except Exception as e:
                    logging.error(f"Error during workflow execution for {name}: {e}", exc_info=True)
                finally:
                    logging.info(f"--- Finished processing instance {name}. Terminating. ---")
                    if final_process: terminate_instance(final_process, final_adb_id)
            else:
                logging.critical(f"--- FAILED to launch and verify instance {name} after {MAX_LAUNCH_ATTEMPTS} attempts. Skipping. ---")
                ce_actions.send_email(f"CE Automation FAILURE: {name} Could Not Launch", f"Failed to launch '{name}' after {MAX_LAUNCH_ATTEMPTS} attempts.")
    
    except SystemExit as e:
        logging.info(f"Script exiting cleanly: {e}")
    except Exception as e:
        logging.critical(f"A critical error occurred in the main script: {e}", exc_info=True)
    
    finally:
        logging.info("Script finished.")

if __name__ == "__main__":
    main()