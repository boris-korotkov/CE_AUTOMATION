import subprocess
import time
import random
from PIL import Image
import logging
from ce_launcher import launch_instance, terminate_instance

def send_adb_command(adb_id, command):
    """
    Sends an ADB command to the specified emulator instance.
    """
    try:
        full_command = f'adb -s {adb_id} {command}'
        logging.info(f"Executing ADB command: {full_command}")
        result = subprocess.run(full_command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        logging.error(f"ADB command failed: {e}")
        return None

def click_on_screen(adb_id, x, y):
    """
    Simulates a click on the screen at the specified coordinates.
    """
    command = f"shell input tap {x} {y}"
    send_adb_command(adb_id, command)

def take_screenshot(adb_id, output_file):
    """
    Takes a screenshot of the emulator screen and saves it to the specified file.
    """
    temp_file = "/sdcard/temp_screenshot.png"
    send_adb_command(adb_id, f"shell screencap -p {temp_file}")
    send_adb_command(adb_id, f"pull {temp_file} {output_file}")
    send_adb_command(adb_id, f"shell rm {temp_file}")

def crop_screenshot(input_file, output_file, x, y, width, height):
    """
    Crops a region from the screenshot and saves it to a new file.
    """
    with Image.open(input_file) as img:
        left = max(0, x - width // 2)
        top = max(0, y - height // 2)
        right = left + width
        bottom = top + height
        cropped = img.crop((left, top, right, bottom))
        cropped.save(output_file)

def wait_for_adb_device():
    """
    Waits for an ADB device to appear.
    """
    logging.info("Waiting for ADB device...")
    for _ in range(60):  # Wait up to 60 seconds
        logging.info("Retrying ADB connection...")
        subprocess.run("adb connect 127.0.0.1:5605", shell=True, check=False)
        result = subprocess.run("adb devices", shell=True, capture_output=True, text=True)
        if "127.0.0.1:5605" in result.stdout:
            logging.info("ADB device detected.")
            return "127.0.0.1:5605"  # Return the ADB ID
        time.sleep(1)
    raise RuntimeError("No ADB device detected after waiting.")

def wait_for_emulator_ready(adb_id):
    """
    Waits for the emulator to be fully loaded and ready.
    """
    logging.info("Waiting for emulator to be ready...")
    for _ in range(60):  # Wait up to 60 seconds
        result = subprocess.run(f"adb -s {adb_id} shell getprop sys.boot_completed", shell=True, capture_output=True, text=True)
        if result.stdout.strip() == "1":
            logging.info("Emulator is ready.")
            return
        time.sleep(1)
    raise RuntimeError("Emulator did not become ready within the expected time.")

def main():
    instance_name = "Adidas"  # Replace with the desired instance name
    emulator_type = "bluestacks"  # Replace with the desired emulator type

    # Ensure the command is properly quoted
    command = '"C:\\Program Files\\BlueStacks_nxt\\HD-Player.exe" --instance Rvc64_5'

    # Start the emulator instance
    logging.info(f"Starting emulator instance: {instance_name}")
    process = launch_instance(instance_name, command)

    try:
        # Manually connect ADB to the BlueStacks instance
        logging.info("Connecting ADB to BlueStacks instance at 127.0.0.1:5605")
        subprocess.run("adb connect 127.0.0.1:5605", shell=True, check=True)

        # Wait for the emulator to be detected by ADB
        adb_id = wait_for_adb_device()

        # Wait for the emulator to be ready
        wait_for_emulator_ready(adb_id)

        # Start the game using ADB
        package_name = "com.feelingtouch.clonewar"
        logging.info("Starting the game...")
        send_adb_command(adb_id, f"shell monkey -p {package_name} -c android.intent.category.LAUNCHER 1")

        # Wait for the game to load
        time.sleep(120)  # Adjust the wait time as needed

        # Generate random coordinates for the click
        x = random.randint(100, 800)  # Adjust based on screen resolution
        y = random.randint(100, 800)

        # Perform the click
        logging.info(f"Clicking on coordinates: ({x}, {y})")
        click_on_screen(adb_id, x, y)

        # Take a screenshot
        screenshot_file = "screenshot.png"
        take_screenshot(adb_id, screenshot_file)

        # Crop the area around the click
        cropped_file = "cropped_screenshot.png"
        crop_screenshot(screenshot_file, cropped_file, x, y, 100, 100)

        logging.info(f"Click performed at ({x}, {y}). Screenshot saved as {cropped_file}.")
    finally:
        # Terminate the emulator instance
        if process:
            terminate_instance(process, emulator_type)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
