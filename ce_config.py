import configparser
import logging
import subprocess
import time

CONFIG_FILE = "instances.ini"

config = configparser.ConfigParser()
try:
    if not config.read(CONFIG_FILE):
        logging.error(f"Configuration file '{CONFIG_FILE}' not found or is empty.")
except configparser.Error as e:
    logging.error(f"Error parsing configuration file '{CONFIG_FILE}': {e}")
    pass

def get_config():
    return config

def load_general_config():
    """Loads settings from the [General] section."""
    settings = {
        'recipient_email': config.get('General', 'recipient_email', fallback=None),
        'tesseract_path': config.get('General', 'tesseract_path', fallback=None),
        'emulator_boot_time': config.getint('General', 'emulator_boot_time', fallback=45),
        'log_level': config.get('General', 'log_level', fallback='INFO').strip().upper(),
        'save_debug_images': config.getboolean('General', 'save_debug_images', fallback=False),
        'game_load_check_region': config.get('General', 'game_load_check_region', fallback=None),
        'game_load_check_image': config.get('General', 'game_load_check_image', fallback=None),
        'game_load_check_text': config.get('General', 'game_load_check_text', fallback=None),
        'game_load_check_threshold': config.getfloat('General', 'game_load_check_threshold', fallback=0.85)
    }
    return settings

def load_emulator_type():
    # ... (This function is unchanged) ...
    logging.info("Loading preferred emulator type from the INI file.")
    return config.get("EmulatorType", "Preferred", fallback="bluestacks").strip().lower()

def load_instances():
    # ... (This function is unchanged) ...
    logging.info("Loading instances from the INI file.")
    instances = {}
    for section in config.sections():
        if section in ["EmulatorType", "General", "RunOrder", "Hotkeys"]:
            continue
        details = {
            "name": section,
            "nox_command": config.get(section, "nox_command", fallback="").strip(),
            "bluestacks_command": config.get(section, "bluestacks_command", fallback="").strip(),
            "adb_port": config.get(section, "adb_port", fallback="").strip(),
            "language": config.get(section, "language", fallback="en").strip(),
            "workflows": [s.strip() for s in config.get(section, "workflows", fallback="").split(",") if s.strip()],
        }
        instances[section] = details
    logging.info(f"Loaded {len(instances)} valid instances.")
    return instances

# ... (The rest of the file: connect_adb_to_instance, load_run_order, load_hotkey_config remains exactly the same) ...
def connect_adb_to_instance(instance_name, logger=logging):
    if not config.has_section(instance_name): logger.error(f"Instance '{instance_name}' not found in {CONFIG_FILE}."); return None
    port = config.get(instance_name, "adb_port", fallback=None)
    if not port: logger.warning(f"No ADB port mapping found for instance {instance_name} in {CONFIG_FILE}."); return None
    adb_id = f"127.0.0.1:{port}"
    try:
        logger.info(f"Connecting ADB to {adb_id} for instance {instance_name}...")
        subprocess.run(f"adb disconnect {adb_id}", shell=True, capture_output=True)
        time.sleep(1)
        connect_result = subprocess.run(f"adb connect {adb_id}", shell=True, check=True, capture_output=True, text=True)
        if "unable to connect" in connect_result.stdout.lower() or "failed to connect" in connect_result.stdout.lower():
             logger.error(f"ADB connection command failed for {adb_id}."); return None
        for _ in range(15):
            result = subprocess.run("adb devices", shell=True, capture_output=True, text=True)
            if adb_id in result.stdout and "device" in result.stdout:
                logger.info(f"ADB device {adb_id} is connected and ready."); return adb_id
            time.sleep(1)
        logger.error(f"ADB device {adb_id} not detected after waiting.")
    except Exception as e:
        logger.error(f"ADB connection failed for {adb_id}: {e}")
    return None

def load_run_order():
    logging.info("Loading run order from [RunOrder] section.")
    order_list, start_instance = [], None
    if config.has_section("RunOrder"):
        order_str = config.get("RunOrder", "order", fallback="").strip()
        if order_str: order_list = [name.strip() for name in order_str.split(',') if name.strip()]
        start_instance = config.get("RunOrder", "start_from", fallback=None)
        if start_instance: start_instance = start_instance.strip()
    logging.info(f"Run order: {order_list}")
    logging.info(f"Starting from: {start_instance if start_instance else 'the beginning'}")
    return order_list, start_instance

def load_hotkey_config():
    hotkeys = {'pause_resume': 'ctrl+p', 'emergency_stop': 'ctrl+h'}
    if config.has_section("Hotkeys"):
        hotkeys['pause_resume'] = config.get("Hotkeys", "pause_resume", fallback='ctrl+p').strip()
        hotkeys['emergency_stop'] = config.get("Hotkeys", "emergency_stop", fallback='ctrl+h').strip()
    logging.info(f"Hotkeys loaded: Pause/Resume on '{hotkeys['pause_resume']}', Stop on '{hotkeys['emergency_stop']}'")
    return hotkeys