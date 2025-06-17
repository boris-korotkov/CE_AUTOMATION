import logging
import time
import os
import sys
import threading
from datetime import datetime
from ce_config import load_instances, load_emulator_type, connect_adb_to_instance, load_run_order, load_general_config, load_hotkey_config
from ce_launcher import launch_instance, terminate_instance
from ce_workflow_engine import WorkflowEngine
import ce_actions
from ce_hotkeys import setup_hotkey_listener

# ... (setup_logging and check_for_pause_or_stop functions are unchanged) ...
pause_event = threading.Event()
stop_event = threading.Event()

def setup_logging(log_level_str='INFO'):
    log_level = getattr(logging, log_level_str, logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(log_level)
    for handler in logger.handlers[:]: logger.removeHandler(handler)
    log_filename = f"logs/CE_robot_{time.strftime('%Y-%m-%d_%H-%M-%S')}.log"
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logging.info("Logging setup complete.")
    logging.info(f"Global log level set to: {log_level_str}")

def check_for_pause_or_stop():
    while pause_event.is_set(): time.sleep(0.5)
    if stop_event.is_set(): logging.critical("Emergency stop signal received. Terminating script."); sys.exit("Emergency stop activated by user.")


def main():
    """Main function to execute emulator instance automation."""
    general_settings = load_general_config()
    hotkeys_config = load_hotkey_config()
    log_level = general_settings.get('log_level')
    emulator_boot_time = general_settings.get('emulator_boot_time')
    
    # Load all global check parameters
    check_region_str = general_settings.get("game_load_check_region")
    check_image = general_settings.get("game_load_check_image")
    check_text = general_settings.get("game_load_check_text")
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
        
        run_order, start_from = load_run_order()

        if not run_order:
            logging.info("No specific run order found. Processing all instances.")
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
            workflows = details.get("workflows", [])
            
            if not command:
                logging.warning(f"Skipping instance '{name}' - No command found for emulator type '{emulator_type}'.")
                continue

            instance_ready = False
            final_process = None
            final_adb_id = None
            
            for attempt in range(1, MAX_LAUNCH_ATTEMPTS + 1):
                check_for_pause_or_stop()
                logging.info(f"--- Processing instance: {name} (Attempt {attempt}/{MAX_LAUNCH_ATTEMPTS}) ---")
                process = None
                try:
                    process = launch_instance(name, command)
                    if not process:
                        logging.error(f"Failed to launch process for instance {name}. Retrying if possible.")
                        time.sleep(15)
                        continue
                    logging.info(f"Waiting {emulator_boot_time} seconds for emulator to boot and game to load...")
                    time.sleep(emulator_boot_time)
                    check_for_pause_or_stop()
                    adb_id = connect_adb_to_instance(name, logger=logging)
                    if not adb_id:
                        logging.warning(f"Could not connect ADB for instance {name} on attempt {attempt}.")
                        terminate_instance(process, emulator_type)
                        time.sleep(15)
                        continue
                    logging.info(f"Successfully connected ADB to {adb_id}. Verifying game screen...")
                    check_for_pause_or_stop()
                    
                    is_loaded = False
                    # --- THIS IS THE DUAL VERIFICATION LOGIC BLOCK ---
                    # Check if at least the region is defined
                    if check_region_str and (check_image or check_text):
                        try:
                            check_region = tuple(map(int, check_region_str.split(',')))
                            
                            # Try image check first (more reliable)
                            if check_image and ce_actions.compare_with_image(adb_id, language, *check_region, check_image, check_threshold):
                                logging.info("Game load verification successful (Image Match).")
                                is_loaded = True
                            # If image fails, try text check
                            elif check_text and ce_actions.compare_with_text(adb_id, language, *check_region, check_text):
                                logging.info("Game load verification successful (Text Match).")
                                is_loaded = True
                            else:
                                logging.warning("Game load verification FAILED (Neither image nor text matched).")
                        except (ValueError, TypeError) as e:
                            logging.error(f"Invalid format for 'game_load_check_region' in [General] section: {e}. Skipping check.")
                            is_loaded = True # Skip check if format is wrong
                    else:
                        logging.info("Global game load verification parameters are incomplete. Skipping check.")
                        is_loaded = True
                    
                    if is_loaded:
                        instance_ready = True
                        final_process = process
                        final_adb_id = adb_id
                        break
                    else:
                        ce_actions.send_email(subject=f"CE Automation Alert: Instance {name} Failed Verification", body=f"Instance '{name}' failed the game load check on attempt {attempt}.\nThe script will try to relaunch it.")
                        terminate_instance(process, emulator_type)
                        logging.info("Waiting 15 seconds before next attempt...")
                        time.sleep(15)
                except Exception as e:
                    logging.error(f"An unexpected error occurred during launch attempt {attempt} for {name}: {e}", exc_info=True)
                    if process:
                        terminate_instance(process, emulator_type)
            
            if instance_ready:
                try:
                    engine = WorkflowEngine(final_adb_id, language, name)
                    
                    start_time = datetime.now()
                    logging.info(f"--- Starting all workflows for instance '{name}' ---")

                    for workflow_name in workflows:
                        check_for_pause_or_stop()
                        engine.run_workflow(workflow_name)
                    
                    end_time = datetime.now()
                    duration = end_time - start_time
                    
                    total_seconds = int(duration.total_seconds())
                    minutes, seconds = divmod(total_seconds, 60)
                    logging.info(f"--- All workflows for instance '{name}' completed. Total duration: {minutes}m {seconds}s ---")

                except Exception as e:
                    logging.error(f"An error occurred during workflow execution for {name}: {e}", exc_info=True)
                finally:
                    logging.info(f"--- Finished processing instance {name}. Terminating. ---")
                    if final_process:
                        terminate_instance(final_process, emulator_type)
            else:
                logging.critical(f"--- FAILED to launch and verify instance {name} after {MAX_LAUNCH_ATTEMPTS} attempts. Skipping. ---")
                ce_actions.send_email(subject=f"CE Automation FAILURE: Instance {name} Could Not Be Launched", body=f"The automation script failed to launch and verify the instance '{name}' after {MAX_LAUNCH_ATTEMPTS} attempts.\n\nThe script will now skip this instance and continue with the next one in the run order.")
    
    except SystemExit as e:
        logging.info(f"Script exiting cleanly: {e}")
    except Exception as e:
        logging.critical(f"A critical error occurred in the main script: {e}", exc_info=True)
    
    finally:
        logging.info("Script finished.")

if __name__ == "__main__":
    main()