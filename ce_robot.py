from ce_config import load_instances, load_emulator_type, connect_adb_to_instance
from ce_launcher import launch_instance, terminate_instance
import logging
import time

def setup_logging():
    """Sets up logging for the script."""
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    log_filename = f"logs/CE_robot_{time.strftime('%Y-%m-%d_%H-%M-%S')}.log"
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.INFO)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logging.info("Logging setup complete.")

def main():
    """Main function to execute emulator instance automation."""
    setup_logging()
    
    try:
        emulator_type = load_emulator_type()
        logging.info(f"Preferred emulator type: {emulator_type}")
        print(f"Using Emulator Type: {emulator_type}")
        
        instances = load_instances()
        
        for name, details in instances.items():
            command = details.get(f"{emulator_type.lower()}_command")
            language = details.get("language", "en")
            scenarios = details.get("scenario", [])
            process = None
            
            if not command:
                logging.warning(f"Skipping instance {name} - No command found for {emulator_type}.")
                continue
            
            try:
                logging.info(f"Launching instance: {name} | Language: {language} | Scenarios: {', '.join(scenarios)}")
                process = launch_instance(name, command)

                # Connect ADB to the emulator instance
                adb_id = connect_adb_to_instance(name, logger=logging)
                if adb_id:
                    logging.info(f"ADB connected to {adb_id} for instance {name}.")
                else:
                    logging.warning(f"ADB connection failed for instance {name}.")

                for scenario in scenarios:
                    logging.info(f"Executing scenario: {scenario} for instance: {name}")
                    # TODO: Implement scenario execution logic
                
                input(f"Press Enter to close {name} and proceed to the next instance...")
            except Exception as e:
                logging.error(f"Error with instance {name}: {e}")
            finally:
                if process:
                    terminate_instance(process, emulator_type)
    
    except Exception as e:
        logging.critical(f"Critical error in automation: {e}")
    finally:
        logging.info("Script ended.")

if __name__ == "__main__":
    main()
