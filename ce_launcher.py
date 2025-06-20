import subprocess
import logging
import os
import signal
import time

def launch_instance(name, command):
    """
    Launches a specific emulator instance using the provided command.
    """
    logging.info(f"Launching instance: {name}")

    try:
        # Using CREATE_NEW_PROCESS_GROUP is crucial for targeted termination on Windows
        if os.name == 'nt':
            process = subprocess.Popen(command, shell=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
            process = subprocess.Popen(command, shell=True, preexec_fn=os.setsid)
        logging.info(f"Instance '{name}' launched with PID: {process.pid}")
        return process
    except Exception as e:
        logging.error(f"Failed to launch instance {name}: {e}")
        return None

def terminate_instance(process, adb_id):
    """
    Terminates a specific running emulator instance.
    First, it tries a graceful shutdown via ADB.
    As a fallback, it terminates the process by its PID.
    """
    if not process:
        logging.warning("Terminate called but no process object was provided.")
        return

    logging.info(f"Attempting to terminate instance (PID: {process.pid}, ADB ID: {adb_id}).")

    # --- Primary Method: Graceful shutdown via ADB ---
    if adb_id:
        try:
            logging.info(f"Sending shutdown command to {adb_id} via ADB...")
            # The 'reboot -p' command tells the Android system to power off
            subprocess.run(f"adb -s {adb_id} reboot -p", shell=True, check=True, capture_output=True, timeout=15)
            logging.info(f"ADB shutdown command sent successfully to {adb_id}.")
            # Give the emulator a moment to process the shutdown and close its window
            time.sleep(5)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logging.warning(f"ADB shutdown command for {adb_id} failed or timed out: {e}. Proceeding to fallback termination.")
        except Exception as e:
            logging.error(f"An unexpected error occurred during ADB shutdown for {adb_id}: {e}")

    # --- Fallback Method: Terminate by Process ID ---
    # Check if the process is still running before trying to kill it
    if process.poll() is None:
        logging.info(f"Process {process.pid} is still running. Using fallback termination...")
        try:
            if os.name == 'nt':  # Windows
                # /T terminates child processes, /F forces termination
                subprocess.run(f"taskkill /PID {process.pid} /T /F", shell=True, check=True, capture_output=True)
                logging.info(f"Successfully terminated process with PID {process.pid} and its children.")
            else:  # Unix-based systems
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                logging.info(f"Successfully sent SIGTERM to process group with PGID {os.getpgid(process.pid)}.")
            # Final check to confirm termination
            process.wait(timeout=5)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logging.error(f"Failed to terminate process with PID {process.pid}: {e.stderr.decode() if hasattr(e, 'stderr') else e}")
        except Exception as e:
             logging.error(f"An unexpected error occurred during fallback termination of PID {process.pid}: {e}")
    else:
        logging.info(f"Instance with PID {process.pid} has already terminated.")