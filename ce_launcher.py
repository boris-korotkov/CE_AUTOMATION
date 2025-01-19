import subprocess
import logging
import os
import signal

def get_emulator_process_name(emulator_type):
    """
    Returns the main process name for the given emulator type.
    :param emulator_type: The type of emulator ("Nox" or "BlueStacks").
    :return: The main process name as a string.
    """
    if emulator_type == "Nox":
        return ["Nox.exe", "NoxVMHandle.exe"]
    elif emulator_type == "BlueStacks":
        return ["HD-Player.exe"]
    else:
        raise ValueError(f"Unknown emulator type: {emulator_type}")

def launch_instance(name, command):
    """
    Launches a specific emulator instance using the provided command.
    :param name: Name of the instance.
    :param command: Command to launch the emulator instance.
    :return: Subprocess instance for the launched emulator.
    """
    logging.info(f"Launching instance: {name}")
    if os.name == 'nt':  # Windows
        process = subprocess.Popen(command, shell=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    else:  # Unix-based systems
        process = subprocess.Popen(command, shell=True, preexec_fn=os.setsid)
    
    return process

def terminate_instance(process, emulator_type):
    """
    Terminates the running emulator instance and its child processes.
    :param process: The subprocess instance to terminate.
    :param emulator_type: The type of emulator ("Nox" or "BlueStacks").
    """
    try:
        logging.info(f"Attempting to terminate instance with PID: {process.pid}")
        process_names = get_emulator_process_name(emulator_type)

        # Terminate all processes related to the emulator
        if os.name == 'nt':  # Windows
            for process_name in process_names:
                logging.info(f"Looking for processes named {process_name}")
                subprocess.run(f"taskkill /F /IM {process_name}", shell=True)
        else:
            # Use Unix-based termination if needed
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)

        logging.info(f"All {emulator_type} processes terminated successfully.")
    except Exception as e:
        logging.error(f"Failed to terminate the {emulator_type} instance: {e}")


