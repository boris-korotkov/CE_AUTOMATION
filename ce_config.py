import configparser
import logging

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
