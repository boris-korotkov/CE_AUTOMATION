import configparser
import logging
import subprocess
import time

# Corrected to use your specified filename. This is the only change.
CONFIG_FILE = "instances.ini" 

# Read the configuration file once at the module level
config = configparser.ConfigParser()
# Check if the file exists before reading to prevent an empty config object on file-not-found
try:
    if not config.read(CONFIG_FILE):
        logging.error(f"Configuration file '{CONFIG_FILE}' not found or is empty.")
except configparser.Error as e:
    logging.error(f"Error parsing configuration file '{CONFIG_FILE}': {e}")
    # Exit or handle as appropriate if the config is essential for the app to start
    # For this script, we'll let individual functions handle the missing data
    pass


def get_config():
    """Returns the pre-read config object."""
    return config

def load_general_config():
    """Loads settings from the [General] section."""
    settings = {
        'recipient_email': config.get('General', 'recipient_email', fallback=None),
        'tesseract_path': config.get('General', 'tesseract_path', fallback=None)
    }
    return settings

def load_emulator_type():
    """Reads the preferred emulator type from the INI file."""
    logging.info("Loading preferred emulator type from the INI file.")
    return config.get("EmulatorType", "Preferred", fallback="bluestacks").strip().lower()

def load_instances():
    """
    Reads the INI file and loads emulator instance details.
    Returns a dictionary with instance attributes.
    """
    logging.info("Loading instances from the INI file.")
    instances = {}
    
    for section in config.sections():
        if section in ["EmulatorType", "General"]:
            continue
        
        details = {
            "name": section,
            "nox_command": config.get(section, "nox_command", fallback="").strip(),
            "bluestacks_command": config.get(section, "bluestacks_command", fallback="").strip(),
            "adb_port": config.get(section, "adb_port", fallback="").strip(),
            "language": config.get(section, "language", fallback="en").strip(),
            "workflows": [s.strip() for s in config.get(section, "workflows", fallback="").split(",") if s.strip()]
        }
        instances[section] = details
    
    logging.info(f"Loaded {len(instances)} valid instances.")
    return instances

def connect_adb_to_instance(instance_name, logger=logging):
    """
    Connects ADB to the emulator instance using the mapped port from instances.ini.
    Returns the adb_id (e.g., 127.0.0.1:5605) if successful, else None.
    """
    if not config.has_section(instance_name):
        logger.error(f"Instance '{instance_name}' not found in {CONFIG_FILE}.")
        return None
        
    port = config.get(instance_name, "adb_port", fallback=None)
    if not port:
        logger.warning(f"No ADB port mapping found for instance {instance_name} in {CONFIG_FILE}.")
        return None

    adb_id = f"127.0.0.1:{port}"
    try:
        logger.info(f"Connecting ADB to {adb_id} for instance {instance_name}...")
        subprocess.run(f"adb disconnect {adb_id}", shell=True, capture_output=True)
        time.sleep(1)
        connect_result = subprocess.run(f"adb connect {adb_id}", shell=True, check=True, capture_output=True, text=True)
        if "unable to connect" in connect_result.stdout.lower() or "failed to connect" in connect_result.stdout.lower():
             logger.error(f"ADB connection command failed for {adb_id}.")
             return None
        
        for _ in range(15):
            result = subprocess.run("adb devices", shell=True, capture_output=True, text=True)
            if adb_id in result.stdout and "device" in result.stdout:
                logger.info(f"ADB device {adb_id} is connected and ready.")
                return adb_id
            time.sleep(1)
            
        logger.error(f"ADB device {adb_id} not detected after waiting.")

    except Exception as e:
        logger.error(f"ADB connection failed for {adb_id}: {e}")
    
    return None