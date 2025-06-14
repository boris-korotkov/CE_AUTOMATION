import subprocess
import logging
import os
import time
import cv2
import numpy as np
import pytesseract
import win32com.client as win32
from ce_config import load_general_config

TEMP_DIR = "temp"
RESOURCES_DIR = "resources"
LAST_CAPTURE_PATH = os.path.join(TEMP_DIR, "last_capture.png")

# Configure pytesseract
general_config = load_general_config()
if general_config.get('tesseract_path'):
    pytesseract.pytesseract.tesseract_cmd = general_config['tesseract_path']

def take_screenshot(adb_id):
    # ... (This function is unchanged)
    device_path = "/sdcard/screen.png"
    local_path = os.path.join(TEMP_DIR, f"screenshot_{adb_id.replace(':', '_')}.png")
    try:
        subprocess.run(f"adb -s {adb_id} shell screencap -p {device_path}", check=True, shell=True, capture_output=True)
        subprocess.run(f"adb -s {adb_id} pull {device_path} {local_path}", check=True, shell=True, capture_output=True)
        subprocess.run(f"adb -s {adb_id} shell rm {device_path}", shell=True, capture_output=True)
        logging.debug("Screenshot taken. Pausing for 1 second.")
        time.sleep(1)
        return local_path
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to take screenshot on {adb_id}: {e.stderr.decode()}")
        return None

def click(adb_id, x, y):
    # ... (This function is unchanged)
    logging.info(f"Clicking at ({x}, {y}) on {adb_id}")
    subprocess.run(f"adb -s {adb_id} shell input tap {x} {y}", shell=True)
    logging.debug("Click sent. Pausing for 1 second.")
    time.sleep(1)

def scroll(adb_id, x, y, direction, distance):
    # ... (This function is unchanged)
    logging.info(f"Scrolling {direction} by {distance}px from ({x}, {y}) on {adb_id}")
    x2, y2 = x, y
    if direction == 'left': x2 = x - distance
    elif direction == 'right': x2 = x + distance
    elif direction == 'up': y2 = y - distance
    elif direction == 'down': y2 = y + distance
    duration_ms = 300
    subprocess.run(f"adb -s {adb_id} shell input swipe {x} {y} {x2} {y2} {duration_ms}", shell=True)
    logging.debug("Scroll sent. Pausing for 1 second.")
    time.sleep(1)

# --- THIS FUNCTION IS UPDATED WITH A SAFETY CHECK ---
def compare_with_image(adb_id, language, x, y, w, h, image_name, threshold=0.85):
    logging.debug(f"Comparing screen region ({x},{y},{w},{h}) with image '{image_name}' at threshold {threshold}")
    screenshot_path = take_screenshot(adb_id)
    if not screenshot_path:
        return False
        
    template_path = os.path.join(RESOURCES_DIR, language, image_name)
    if not os.path.exists(template_path):
        logging.error(f"Template image not found: {template_path}")
        return False

    screen_img = cv2.imread(screenshot_path)
    template_img = cv2.imread(template_path)
    
    if screen_img is None or template_img is None:
        logging.error("Could not read screenshot or template image.")
        return False
    
    region = screen_img[y:y+h, x:x+w]
    
    # --- NEW SAFETY CHECK ---
    # Get dimensions of the template and the region
    template_h, template_w, _ = template_img.shape
    region_h, region_w, _ = region.shape

    # Check if the search region is smaller than the template image
    if region_h < template_h or region_w < template_w:
        logging.error(f"OpenCV Error Prevention: The search region ({region_w}x{region_h}) is smaller than the template image '{image_name}' ({template_w}x{template_h}).")
        logging.error("Please ensure the w,h in your YAML are >= the dimensions of the template image.")
        return False
    # --- END OF SAFETY CHECK ---

    cv2.imwrite(LAST_CAPTURE_PATH, region)
    res = cv2.matchTemplate(region, template_img, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(res)
    
    logging.debug(f"Image match score: {max_val:.2f} (Threshold: {threshold})")
    return max_val >= threshold

# ... (The rest of the file is unchanged) ...
def compare_with_text(adb_id, language, x, y, w, h, expected_text):
    logging.debug(f"Comparing screen region ({x},{y},{w},{h}) with text '{expected_text}'")
    screenshot_path = take_screenshot(adb_id)
    if not screenshot_path: return False
    screen_img = cv2.imread(screenshot_path)
    if screen_img is None: logging.error("Could not read screenshot."); return False
    region = screen_img[y:y+h, x:x+w]
    cv2.imwrite(LAST_CAPTURE_PATH, region)
    try:
        gray_region = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        _, thresh_region = cv2.threshold(gray_region, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        ocr_text = pytesseract.image_to_string(thresh_region).strip()
        logging.debug(f"OCR detected text: '{ocr_text}'")
        return expected_text.lower() in ocr_text.lower()
    except pytesseract.TesseractNotFoundError:
        logging.critical("Tesseract is not installed or not in your PATH. Check tesseract_path in instances.ini."); emergency_exit("Tesseract is not configured.")
        return False
    except Exception as e:
        logging.error(f"An error occurred during OCR: {e}"); return False

def compare_with_any_image(adb_id, language, x, y, w, h, image_names, threshold=0.85):
    logging.debug(f"Comparing screen region ({x},{y},{w},{h}) with ANY of the images: {image_names}")
    screenshot_path = take_screenshot(adb_id)
    if not screenshot_path: return False
    screen_img = cv2.imread(screenshot_path)
    if screen_img is None: logging.error("Could not read screenshot."); return False
    region = screen_img[y:y+h, x:x+w]
    cv2.imwrite(LAST_CAPTURE_PATH, region)
    for image_name in image_names:
        template_path = os.path.join(RESOURCES_DIR, language, image_name)
        if not os.path.exists(template_path): logging.warning(f"Template image not found, skipping: {template_path}"); continue
        template_img = cv2.imread(template_path)
        if template_img is None: logging.warning(f"Could not read template image, skipping: {template_path}"); continue
        res = cv2.matchTemplate(region, template_img, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)
        logging.debug(f"Matching against '{image_name}', score: {max_val:.2f} (Threshold: {threshold})")
        if max_val >= threshold:
            logging.info(f"SUCCESS: Match found for '{image_name}'.")
            return True
    logging.info("No match found for any of the provided images.")
    return False

def send_email(subject, body):
    recipient = general_config.get('recipient_email')
    if not recipient: logging.warning("No recipient_email configured in instances.ini. Cannot send email."); return
    logging.info(f"Sending email to {recipient}: '{subject}'")
    try:
        outlook = win32.Dispatch('outlook.application')
        mail = outlook.CreateItem(0)
        mail.To = recipient
        mail.Subject = subject
        mail.Body = body
        mail.Send()
    except Exception as e:
        logging.error(f"Failed to send email via Outlook: {e}")

def emergency_exit(message):
    logging.critical(f"EMERGENCY EXIT: {message}")
    send_email("CRITICAL ERROR in CE_AUTOMATION", message)
    os._exit(1)