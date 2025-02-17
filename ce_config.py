import configparser
import logging

def load_emulator_type():
    """
    Reads the preferred emulator type from the INI file.
    :return: Preferred emulator type as a string.
    """
    logging.info("Loading preferred emulator type from the INI file.")
    config = configparser.ConfigParser()
    config.read("instances.ini")
    
    if "EmulatorType" not in config:
        logging.warning("No 'EmulatorType' section found in INI file. Defaulting to 'Nox'.")
        return "Nox"
    
    return config["EmulatorType"].get("Preferred", "Nox")

def load_instances(emulator_type="Nox"):
    """
    Reads the INI file and loads emulator instance details based on the emulator type.
    :param emulator_type: The type of emulator ("Nox" or "BlueStacks").
    :return: Dictionary of instance names and commands.
    """
    logging.info(f"Loading {emulator_type} instances from the INI file.")
    config = configparser.ConfigParser()
    config.read("instances.ini")
    
    section = f"{emulator_type}Instances"
    if section not in config:
        logging.error(f"No '{section}' section found in INI file.")
        raise KeyError(f"Missing '{section}' section in INI file.")
    
    instances = {}
    for key in config[section]:
        if key.endswith('_command'):
            instance_name = key.replace('_command', '')
            command = config[section][key]
            language_key = f"{instance_name}_language"
            language = config[section].get(language_key, 'en')  # Default to 'en' if not specified
            instances[instance_name] = {"command": command, "language": language}
    

    # instances = config[section]
    # if not instances:
    #     logging.error(f"No {emulator_type} instances found in the INI file.")
    #     raise ValueError(f"{section} section is empty or improperly configured.")
    
    logging.info(f"Found {len(instances)} {emulator_type} instances.")
    return instances

def load_language():
    """
    Reads the preferred language from the INI file.
    :return: Preferred language as a string.
    """
    logging.info("Loading preferred language from the INI file.")
    config = configparser.ConfigParser()
    config.read("instances.ini")
    
    if "Language" not in config:
        logging.warning("No 'Language' section found in INI file. Defaulting to English.")
        return "English"
    
    return config["Language"].get("Preferred", "English")
