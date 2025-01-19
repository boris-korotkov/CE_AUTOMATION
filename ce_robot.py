from ce_config import load_instances, load_language, load_emulator_type
from ce_launcher import launch_instance, terminate_instance
from datetime import datetime
import logging

import logging

def setup_logging():
    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Create a log file handler
    log_filename = f"automation_log_{time.strftime('%Y-%m-%d_%H-%M-%S')}.log"
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.INFO)

    # Create a console (stream) handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # Show DEBUG messages in the console

    # Create a formatter and add it to both handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logging.info("Logging setup complete.")

# Call setup_logging() at the beginning of your script
setup_logging()


def main():
    """
    Main function to execute emulator instance automation.
    """
    setup_logging()

    try:
        # User selects emulator type
        emulator_type = load_emulator_type()
        logging.info(f"Preferred emulator type: {emulator_type}")
        print(f"Using Emulator Type: {emulator_type}")
        
        # Load preferred language
        language = load_language()
        logging.info(f"Preferred language: {language}")
        print(f"Selected Language: {language}")

        # Load instances from the INI file
        instances = load_instances(emulator_type)
        
        # Process each instance
        for name, command in instances.items():
            process = None
            try:
                logging.info(f"Using language: {language} for instance: {name}")
                process = launch_instance(name, command)
                input(f"Press Enter to close {name} and proceed to the next instance...")
            except Exception as e:
                logging.error(f"Error with instance {name}: {e}")
            finally:
                if process:
                    terminate_instance(process,emulator_type)

    except Exception as e:
        logging.critical(f"Critical error in automation: {e}")
    finally:
        logging.info("Script ended.")

if __name__ == "__main__":
    main()
