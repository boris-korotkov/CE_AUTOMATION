import subprocess
import logging
import os
import signal

def get_emulator_process_name(emulator_type):
    """
    Returns the main process name for the given emulator type.
    """
    if emulator_type == "nox":
        return ["Nox.exe", "NoxVMHandle.exe"]
    elif emulator_type == "bluestacks":
        return ["HD-Player.exe"]
    else:
        raise ValueError(f"Unknown emulator type: {emulator_type}")

def launch_instance(name, command):
    """
    Launches a specific emulator instance using the provided command.
    """
    logging.info(f"Launching instance: {name}")

    try:
        if os.name == 'nt':  # Windows
            process = subprocess.Popen(command, shell=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        else:  # Unix-based systems
            process = subprocess.Popen(command, shell=True, preexec_fn=os.setsid)
        return process
    except Exception as e:
        logging.error(f"Failed to launch instance {name}: {e}")
        return None

def terminate_instance(process, emulator_type):
    """
    Terminates the running emulator instance and its child processes.
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


