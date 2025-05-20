import configparser
import logging
import subprocess
import time

def load_emulator_type():
    """
    Reads the preferred emulator type from the INI file.
    """
    logging.info("Loading preferred emulator type from the INI file.")
    config = configparser.ConfigParser()
    config.read("workflow.ini")
    
    return config.get("EmulatorType", "Preferred", fallback="BlueStacks").strip()

def load_instances():
    """
    Reads the INI file and loads emulator instance details.
    Returns a dictionary with instance attributes.
    """
    logging.info("Loading instances from the INI file.")
    config = configparser.ConfigParser()
    config.read("workflow.ini")
    
    instances = {}
    emulator_type = load_emulator_type().lower()
    
    for section in config.sections():
        if section == "EmulatorType":
            continue
        
        instance_name = section
        instances[instance_name] = {"name": instance_name}
        
        for key, value in config[section].items():
            key_lower = key.lower()
            print(f"Processing key: {key_lower} with value: {value}")
            if key_lower in ["nox_command", "bluestacks_command"]:
                instances[instance_name][key_lower] = value.strip()
            elif key_lower == "language":
                instances[instance_name]["language"] = value.strip()
            elif key_lower == "scenario":
                instances[instance_name]["scenario"] = [s.strip() for s in value.split(",") if s.strip()]
        
        # Ensure correct command key is available
        emulator_command_key = f"{emulator_type}_command"
        instances[instance_name]["command"] = instances[instance_name].get(emulator_command_key, None)
    
    logging.info(f"Loaded {len(instances)} valid instances.")
    return instances

def connect_adb_to_instance(instance_name, logger=None):
    """
    Connects ADB to the emulator instance using the mapped port from workflow.ini.
    Returns the adb_id (e.g., 127.0.0.1:5605) if successful, else None.
    """
    port = get_adb_port_for_instance(instance_name)
    if not port:
        if logger:
            logger.warning(f"No ADB port mapping found for instance {instance_name}.")
        return None
    adb_id = f"127.0.0.1:{port}"
    try:
        if logger:
            logger.info(f"Connecting ADB to {adb_id} for instance {instance_name}...")
        subprocess.run(f"adb connect {adb_id}", shell=True, check=True)
        # Wait for device to appear in adb devices
        for _ in range(30):
            result = subprocess.run("adb devices", shell=True, capture_output=True, text=True)
            if adb_id in result.stdout:
                if logger:
                    logger.info(f"ADB connected to {adb_id}.")
                return adb_id
            time.sleep(1)
        if logger:
            logger.error(f"ADB device {adb_id} not detected after waiting.")
    except Exception as e:
        if logger:
            logger.error(f"ADB connection failed for {adb_id}: {e}")
    return None

def get_adb_port_for_instance(instance_name):
    """
    Returns the ADB port for a given instance name from workflow.ini.
    """
    config = configparser.ConfigParser()
    config.read("workflow.ini")
    if instance_name in config:
        port = config[instance_name].get("adb_port")
        if port:
            try:
                return int(port)
            except ValueError:
                logging.warning(f"Invalid adb_port value for {instance_name}: {port}")
    return None
