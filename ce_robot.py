import logging
import time
import os
import sys
from ce_config import load_instances, load_emulator_type, connect_adb_to_instance
from ce_launcher import launch_instance, terminate_instance
from ce_workflow_engine import WorkflowEngine

def setup_logging():
    """Sets up logging for the script."""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    if not os.path.exists('temp'):
        os.makedirs('temp')

    log_filename = f"logs/CE_robot_{time.strftime('%Y-%m-%d_%H-%M-%S')}.log"
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info("Logging setup complete.")

def main():
    """Main function to execute emulator instance automation."""
    setup_logging()
    
    try:
        emulator_type = load_emulator_type()
        logging.info(f"Preferred emulator type: {emulator_type}")
        
        instances = load_instances()
        
        for name, details in instances.items():
            command = details.get(f"{emulator_type}_command")
            language = details.get("language")
            workflows = details.get("workflows", [])
            process = None
            
            if not command:
                logging.warning(f"Skipping instance '{name}' - No command found for emulator type '{emulator_type}'.")
                continue
            
            try:
                logging.info(f"--- Processing instance: {name} | Language: {language} | Workflows: {', '.join(workflows)} ---")
                process = launch_instance(name, command)
                if not process:
                    logging.error(f"Failed to launch process for instance {name}. Skipping.")
                    continue

                # Wait for emulator to boot
                logging.info("Waiting 100 seconds for emulator to boot before connecting ADB...")
                time.sleep(100)
                
                adb_id = connect_adb_to_instance(name, logger=logging)
                if adb_id:
                    logging.info(f"Successfully connected ADB to {adb_id} for instance {name}.")
                    
                    engine = WorkflowEngine(adb_id, language)
                    for workflow_name in workflows:
                        engine.run_workflow(workflow_name)
                else:
                    logging.error(f"Could not connect ADB for instance {name}. Skipping workflows.")
            
            except Exception as e:
                logging.error(f"An unexpected error occurred while processing instance {name}: {e}", exc_info=True)
            
            finally:
                if process:
                    logging.info(f"--- Finished processing instance {name}. Terminating. ---")
                    terminate_instance(process, emulator_type)
                    # Give time for processes to close before starting the next one
                    time.sleep(10)
    
    except Exception as e:
        logging.critical(f"A critical error occurred in the main script: {e}", exc_info=True)
    
    finally:
        logging.info("Script finished.")

if __name__ == "__main__":
    main()