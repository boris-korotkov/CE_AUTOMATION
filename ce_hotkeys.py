import keyboard
import logging
import ce_actions

def setup_hotkey_listener(pause_event, stop_event, hotkeys_config):
    """
    Sets up global hotkeys to control the script's execution.
    This runs in a separate thread and communicates via Event objects.
    """
    
    def toggle_pause():
        """Flips the state of the pause_event."""
        if pause_event.is_set():
            pause_event.clear()
            logging.info("--- SCRIPT RESUMED ---")
        else:
            logging.info("--- SCRIPT PAUSED (Press hotkey again to resume) ---")
            pause_event.set()

    def emergency_stop():
        """Sets the stop_event to signal the main loop to exit."""
        if not stop_event.is_set():
            logging.critical("--- EMERGENCY STOP HOTKEY PRESSED! ---")
            ce_actions.send_email(
                subject="CE Automation: EMERGENCY STOP ACTIVATED",
                body="The emergency stop hotkey was pressed. The script will terminate after the current action."
            )
            stop_event.set()

    try:
        pause_key = hotkeys_config.get('pause_resume')
        stop_key = hotkeys_config.get('emergency_stop')

        keyboard.add_hotkey(pause_key, toggle_pause)
        keyboard.add_hotkey(stop_key, emergency_stop)
        
        logging.info("Hotkey listener started successfully.")

    except Exception as e:
        logging.error(f"Failed to set up hotkey listener: {e}")
        logging.warning("You may need to run this script with administrator privileges for hotkeys to work.")