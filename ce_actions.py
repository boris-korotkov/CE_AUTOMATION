import subprocess
import logging
import os
import time
import cv2
import numpy as np
import pytesseract
import win32com.client as win32
import easyocr
from ce_config import load_general_config
from sklearn.cluster import DBSCAN

TEMP_DIR = "temp"
RESOURCES_DIR = "resources"

general_config = load_general_config()
SAVE_DEBUG_IMAGES = general_config.get('save_debug_images', False)

if general_config.get('tesseract_path'):
    pytesseract.pytesseract.tesseract_cmd = general_config['tesseract_path']

EASYOCR_READERS = {}

def initialize_easyocr(lang_code='en'):
    global EASYOCR_READERS
    if lang_code not in EASYOCR_READERS:
        logging.info(f"Initializing EasyOCR for language: '{lang_code}'...")
        try:
            EASYOCR_READERS[lang_code] = easyocr.Reader([lang_code])
            logging.info(f"EasyOCR for '{lang_code}' initialized.")
        except Exception as e:
            logging.error(f"Failed to initialize EasyOCR for '{lang_code}': {e}"); EASYOCR_READERS[lang_code] = None
    return EASYOCR_READERS.get(lang_code)

def take_screenshot(adb_id):
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
        logging.error(f"Failed to take screenshot on {adb_id}: {e.stderr.decode()}"); return None

def click(adb_id, x, y):
    logging.info(f"Clicking at ({x}, {y}) on {adb_id}")
    subprocess.run(f"adb -s {adb_id} shell input tap {x} {y}", shell=True)
    logging.debug("Click sent. Pausing for 1 second.")
    time.sleep(1)

def scroll(adb_id, x, y, direction, distance):
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

def compare_with_image(adb_id, language, instance_name, workflow_name, x, y, w, h, image_name, threshold=0.85):
    logging.debug(f"Comparing screen region ({x},{y},{w},{h}) with image '{image_name}' at threshold {threshold}")
    screenshot_path = take_screenshot(adb_id)
    if not screenshot_path: return False
    template_path = os.path.join(RESOURCES_DIR, language, image_name)
    if not os.path.exists(template_path): logging.error(f"Template image not found: {template_path}"); return False
    screen_img = cv2.imread(screenshot_path)
    template_img = cv2.imread(template_path)
    if screen_img is None or template_img is None: logging.error("Could not read screenshot or template image."); return False
    region = screen_img[y:y+h, x:x+w]
    template_h, template_w, _ = template_img.shape
    region_h, region_w, _ = region.shape
    if region_h < template_h or region_w < template_w:
        logging.error(f"OpenCV Error Prevention: Search region ({region_w}x{region_h}) is smaller than template '{image_name}' ({template_w}x{template_h}).")
        return False
    if SAVE_DEBUG_IMAGES:
        filename = f"{instance_name}_{workflow_name}_compare_image_({x},{y},{w},{h}).png"
        cv2.imwrite(os.path.join(TEMP_DIR, filename), region)
    res = cv2.matchTemplate(region, template_img, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(res)
    logging.debug(f"Image match score: {max_val:.2f} (Threshold: {threshold})")
    return max_val >= threshold

def compare_with_text(adb_id, language, instance_name, workflow_name,  x, y, w, h, expected_text):
    logging.debug(f"Comparing screen region ({x},{y},{w},{h}) with text '{expected_text}' using Tesseract.")
    screenshot_path = take_screenshot(adb_id)
    if not screenshot_path: return False
    screen_img = cv2.imread(screenshot_path)
    if screen_img is None: logging.error("Could not read screenshot."); return False
    region = screen_img[y:y+h, x:x+w]
    if SAVE_DEBUG_IMAGES:
        filename_input = f"{instance_name}_{workflow_name}_tesseract_input_({x},{y},{w},{h}).png"
        cv2.imwrite(os.path.join(TEMP_DIR, filename_input), region)
    scale_factor = 3
    resized = cv2.resize(region, (int(region.shape[1] * scale_factor), int(region.shape[0] * scale_factor)), interpolation=cv2.INTER_LANCZOS4)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    contrast_enhanced = clahe.apply(gray)
    _, thresh = cv2.threshold(contrast_enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = np.ones((2,2), np.uint8)
    processed_image = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    if SAVE_DEBUG_IMAGES:
        filename_processed = f"{instance_name}_{workflow_name}_tesseract_processed_({x},{y},{w},{h}).png"
        cv2.imwrite(os.path.join(TEMP_DIR, filename_processed), processed_image)
    try:
        custom_config = r'--oem 1 --psm 7'
        ocr_text = pytesseract.image_to_string(processed_image, config=custom_config).strip()
        logging.debug(f"Tesseract detected text: '{ocr_text}'")
        return expected_text.lower() in ocr_text.lower()
    except Exception as e:
        logging.error(f"An error occurred during Tesseract OCR: {e}"); return False

def compare_with_any_image(adb_id, language, instance_name, workflow_name, x, y, w, h, image_names, min_match_count=10):
    logging.debug(f"Feature-matching screen region ({x},{y},{w},{h}) with ANY of images: {image_names}")
    orb = cv2.ORB_create()
    screenshot_path = take_screenshot(adb_id)
    if not screenshot_path: return False
    screen_img = cv2.imread(screenshot_path, cv2.IMREAD_GRAYSCALE)
    if screen_img is None: logging.error("Could not read screenshot."); return False
    region_of_interest = screen_img[y:y+h, x:x+w]
    if SAVE_DEBUG_IMAGES:
        filename = f"{instance_name}_{workflow_name}_compare_any_image_({x},{y},{w},{h}).png"
        cv2.imwrite(os.path.join(TEMP_DIR, filename), region_of_interest)
    keypoints_roi, descriptors_roi = orb.detectAndCompute(region_of_interest, None)
    if descriptors_roi is None: logging.debug("No features found in screen region to compare against."); return False
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    for image_name in image_names:
        template_path = os.path.join(RESOURCES_DIR, language, image_name)
        if not os.path.exists(template_path): logging.warning(f"Template image not found, skipping: {template_path}"); continue
        template_img = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        if template_img is None: logging.warning(f"Could not read template image, skipping: {template_path}"); continue
        keypoints_template, descriptors_template = orb.detectAndCompute(template_img, None)
        if descriptors_template is None: logging.warning(f"No features in template '{image_name}', skipping."); continue
        matches = bf.match(descriptors_template, descriptors_roi)
        logging.debug(f"Found {len(matches)} feature matches for '{image_name}'. Required: {min_match_count}.")
        if len(matches) >= min_match_count:
            logging.info(f"SUCCESS: Sufficient feature match found for '{image_name}'.")
            return True
    logging.info("No match found for any provided images using feature matching.")
    return False

def compare_with_features(adb_id, language, instance_name, workflow_name, x, y, w, h, image_name, min_match_count=10):
    logging.debug(f"Comparing screen region ({x},{y},{w},{h}) with image '{image_name}' using feature matching.")
    orb = cv2.ORB_create()
    template_path = os.path.join(RESOURCES_DIR, language, image_name)
    if not os.path.exists(template_path): logging.error(f"Template image not found: {template_path}"); return False
    template_img = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if template_img is None: logging.error(f"Could not read template image: {template_path}"); return False
    keypoints_template, descriptors_template = orb.detectAndCompute(template_img, None)
    if descriptors_template is None: logging.error(f"Could not find any features in template image '{image_name}'."); return False
    screenshot_path = take_screenshot(adb_id)
    if not screenshot_path: return False
    screen_img = cv2.imread(screenshot_path, cv2.IMREAD_GRAYSCALE)
    if screen_img is None: logging.error("Could not read screenshot."); return False
    region_of_interest = screen_img[y:y+h, x:x+w]
    if SAVE_DEBUG_IMAGES:
        filename = f"{instance_name}_{workflow_name}_compare_features_({x},{y},{w},{h}).png"
        cv2.imwrite(os.path.join(TEMP_DIR, filename), region_of_interest)
    keypoints_roi, descriptors_roi = orb.detectAndCompute(region_of_interest, None)
    if descriptors_roi is None: logging.debug("No features found in the screen region."); return False
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(descriptors_template, descriptors_roi)
    matches = sorted(matches, key=lambda x: x.distance)
    logging.info(f"Found {len(matches)} feature matches. Required: {min_match_count}.")
    if len(matches) >= min_match_count:
        logging.info(f"SUCCESS: Found sufficient feature matches for '{image_name}'.")
        return True
    else:
        logging.info(f"FAILURE: Not enough feature matches for '{image_name}'.")
        return False

def compare_with_text_easyocr(adb_id, language, instance_name, workflow_name, x, y, w, h, expected_text):
    reader = initialize_easyocr(language)
    if reader is None: logging.error(f"EasyOCR reader for '{language}' could not be initialized."); return False
    logging.debug(f"Comparing screen region ({x},{y},{w},{h}) with text '{expected_text}' using EasyOCR ({language}).")
    screenshot_path = take_screenshot(adb_id)
    if not screenshot_path: return False
    screen_img = cv2.imread(screenshot_path)
    if screen_img is None: logging.error("Could not read screenshot."); return False
    region = screen_img[y:y+h, x:x+w]
    if SAVE_DEBUG_IMAGES:
        filename = f"{instance_name}_{workflow_name}_compare_easyocr_({x},{y},{w},{h}).png"
        cv2.imwrite(os.path.join(TEMP_DIR, filename), region)
    try:
        results = reader.readtext(region)
        detected_texts = [text for (bbox, text, prob) in results]
        for text in detected_texts:
            logging.debug(f"EasyOCR ({language}) detected: '{text}'")
            if expected_text.lower() in text.lower():
                logging.info(f"EasyOCR SUCCESS: Found '{expected_text}' in detected text '{text}'.")
                return True
        logging.info(f"EasyOCR did not find '{expected_text}'. Detected texts were: {detected_texts}")
        return False
    except Exception as e:
        logging.error(f"An error occurred during EasyOCR processing: {e}"); return False

def get_coords_from_image(adb_id, language, instance_name, workflow_name, image_name, threshold=0.85):
    """
    Finds a template image on the screen and returns the coordinates of its center.
    Returns (x, y) tuple on success, or None on failure.
    """
    logging.debug(f"Searching for image '{image_name}' to get its coordinates.")
    screenshot_path = take_screenshot(adb_id)
    if not screenshot_path:
        return None

    template_path = os.path.join(RESOURCES_DIR, language, image_name)
    if not os.path.exists(template_path):
        logging.error(f"Template image not found: {template_path}")
        return None

    screen_img = cv2.imread(screenshot_path, cv2.IMREAD_GRAYSCALE)
    template_img = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)

    if screen_img is None or template_img is None:
        logging.error("Could not read screenshot or template image for coordinate finding.")
        return None

    # Get the dimensions of the template
    template_h, template_w = template_img.shape

    # Perform template matching
    res = cv2.matchTemplate(screen_img, template_img, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)

    logging.debug(f"Coordinate search for '{image_name}' match score: {max_val:.2f} (Threshold: {threshold})")

    if max_val >= threshold:
        # max_loc is the top-left corner of the match
        # Calculate the center of the found region
        center_x = max_loc[0] + template_w // 2
        center_y = max_loc[1] + template_h // 2
        logging.info(f"Found '{image_name}' at coordinates: ({center_x}, {center_y})")
        return (center_x, center_y)
    else:
        logging.warning(f"Could not find image '{image_name}' on screen with sufficient confidence.")
        return None

# Add this function to ce_actions.py

def get_all_coords_from_image(adb_id, language, instance_name, workflow_name, image_name, threshold=0.85):
    """
    Finds ALL occurrences of a template image on the screen that meet a threshold.
    Returns a list of (x, y) tuples. The list is empty if no matches are found.
    The list is sorted from top-to-bottom, then left-to-right.
    """
    logging.debug(f"Searching for ALL occurrences of image '{image_name}'.")
    screenshot_path = take_screenshot(adb_id)
    if not screenshot_path:
        return []

    template_path = os.path.join(RESOURCES_DIR, language, image_name)
    if not os.path.exists(template_path):
        logging.error(f"Template image not found: {template_path}")
        return []

    # Read images in color for drawing, but we'll match in grayscale
    screen_img_color = cv2.imread(screenshot_path)
    screen_img = cv2.cvtColor(screen_img_color, cv2.COLOR_BGR2GRAY)
    template_img = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)

    if screen_img is None or template_img is None:
        logging.error("Could not read screenshot or template image for coordinate finding.")
        return []

    template_h, template_w = template_img.shape
    res = cv2.matchTemplate(screen_img, template_img, cv2.TM_CCOEFF_NORMED)
    
    # Find all locations where the match score is above the threshold
    locations = np.where(res >= threshold)
    
    # Zip the locations into (x, y) pairs
    points = list(zip(*locations[::-1])) # Switch from (row, col) to (x, y)
    
    if not points:
        logging.info(f"No occurrences of '{image_name}' found with threshold >= {threshold}.")
        return []

    # --- Non-Maximum Suppression ---
    # Group overlapping rectangles together to find the true centers
    rectangles, _ = cv2.groupRectangles(
        [ (pt[0], pt[1], template_w, template_h) for pt in points ], 
        groupThreshold=1, 
        eps=0.5
    )

    # Calculate the center of each unique, non-overlapping rectangle found
    centers = []
    for (x, y, w, h) in rectangles:
        # --- THIS IS THE FIX ---
        # Explicitly cast the numpy types to standard Python integers
        center_x = int(x + w // 2)
        center_y = int(y + h // 2)
        centers.append((center_x, center_y))
        if SAVE_DEBUG_IMAGES:
             # Draw a rectangle on the color screenshot for debugging
             cv2.rectangle(screen_img_color, (x, y), (x + w, y + h), (0, 255, 0), 2)
             cv2.putText(screen_img_color, f"({center_x},{center_y})", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    if SAVE_DEBUG_IMAGES and centers:
        image_name_safe = image_name.replace('.','_')
        filename = f"{instance_name}_{workflow_name}_{image_name_safe}.png"
        cv2.imwrite(os.path.join(TEMP_DIR, filename), screen_img_color)
        logging.debug(f"Saved debug image with all found matches to {filename}")

    # Sort the centers from top-to-bottom, then left-to-right for predictable order
    centers.sort(key=lambda p: (p[1], p[0]))

    logging.info(f"Found {len(centers)} occurrences of '{image_name}'. Coords: {centers}")
    return centers

def get_coords_from_features(adb_id, language, instance_name, workflow_name, image_name, min_match_count=10):
    """
    Finds a template image on the screen using feature matching (ORB) and returns
    the coordinates of its center. Ideal for animated or slightly scaled/rotated elements.
    Returns (x, y) tuple on success, or None on failure.
    """
    logging.debug(f"Feature-searching for image '{image_name}' to get its coordinates.")
    
    # 1. Load template and find its features
    template_path = os.path.join(RESOURCES_DIR, language, image_name)
    if not os.path.exists(template_path):
        logging.error(f"Template image not found: {template_path}")
        return None
    
    template_img = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if template_img is None:
        logging.error(f"Could not read template image: {template_path}")
        return None

    # --- IMPROVEMENT 1: Increase the number of features to detect ---
    # We look for more features to get a higher chance of a good match on small templates.
    orb = cv2.ORB_create(nfeatures=5000) 
    keypoints_template, descriptors_template = orb.detectAndCompute(template_img, None)
    
    if descriptors_template is None:
        logging.error(f"Could not find any features in template image '{image_name}'.")
        return None

    # 2. Take screenshot and find its features
    screenshot_path = take_screenshot(adb_id)
    if not screenshot_path: return None
    
    screen_img = cv2.imread(screenshot_path, cv2.IMREAD_GRAYSCALE)
    if screen_img is None:
        logging.error("Could not read screenshot for feature matching.")
        return None
        
    keypoints_screen, descriptors_screen = orb.detectAndCompute(screen_img, None)
    
    if descriptors_screen is None:
        logging.warning("No features found on the screen to compare against.")
        return None

    # 3. Match features between template and screenshot
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    all_matches = bf.knnMatch(descriptors_template, descriptors_screen, k=2)

    # Apply ratio test to find good matches
    good_matches = []
    try:
        # --- IMPROVEMENT 2: Relax the ratio test slightly ---
        # A value of 0.8 is less strict than 0.75 and can help with similar-looking images.
        ratio_thresh = 0.8 
        for m, n in all_matches:
            if m.distance < ratio_thresh * n.distance:
                good_matches.append(m)
    except ValueError:
        logging.debug("Not enough matches to perform ratio test. Likely no match.")
        return None

    logging.info(f"Found {len(good_matches)} good feature matches. Required: {min_match_count}.")
    
    # 4. If enough matches are found, find the object's location
    if len(good_matches) >= min_match_count:
        src_pts = np.float32([keypoints_template[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([keypoints_screen[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        
        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        
        if M is None:
            logging.warning("Could not compute homography matrix. Matches may be inconsistent.")
            return None
            
        h, w = template_img.shape
        pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
        dst = cv2.perspectiveTransform(pts, M)
        
        center_x = int(np.mean(dst[:, 0, 0]))
        center_y = int(np.mean(dst[:, 0, 1]))
        
        logging.info(f"SUCCESS: Located '{image_name}' via features at center: ({center_x}, {center_y})")
        
        if SAVE_DEBUG_IMAGES:
            debug_img = cv2.polylines(cv2.imread(screenshot_path), [np.int32(dst)], True, (0, 255, 0), 3, cv2.LINE_AA)
            cv2.circle(debug_img, (center_x, center_y), 10, (0, 0, 255), -1)
            # filename = f"DEBUG_feature_coords_{image_name.replace('.','_')}_{int(time.time())}.png"
            filename = f"{instance_name}_{workflow_name}_feature_coords_{image_name.replace('.','_')}.png"
            cv2.imwrite(os.path.join(TEMP_DIR, filename), debug_img)
            logging.debug(f"Saved feature coordinate debug image to {filename}")

        return (center_x, center_y)
    else:
        logging.info(f"FAILURE: Not enough good feature matches for '{image_name}'.")
        return None

def get_all_coords_from_features(adb_id, language, instance_name, workflow_name, image_name, min_match_count=7, eps=50, min_samples=5):
    """
    Finds ALL occurrences of a template image on the screen using feature matching and clustering.
    Ideal for finding multiple instances of animated or scaled/rotated elements.
    Returns a list of (x, y) tuples, sorted top-to-bottom. Returns an empty list if none are found.

    - min_match_count: Minimum "good" feature matches required to even attempt clustering.
    - eps: The maximum distance between two points for them to be considered as in the same neighborhood (DBSCAN parameter).
    - min_samples: The number of samples in a neighborhood for a point to be considered as a core point (DBSCAN parameter).
    """
    logging.debug(f"Feature-searching for ALL occurrences of image '{image_name}'.")

    # 1. Load template and find its features
    template_path = os.path.join(RESOURCES_DIR, language, image_name)
    if not os.path.exists(template_path):
        logging.error(f"Template image not found: {template_path}"); return []
    template_img = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if template_img is None:
        logging.error(f"Could not read template image: {template_path}"); return []

    orb = cv2.ORB_create(nfeatures=5000)
    keypoints_template, descriptors_template = orb.detectAndCompute(template_img, None)
    if descriptors_template is None:
        logging.error(f"No features in template '{image_name}'."); return []

    # 2. Take screenshot and find its features
    screenshot_path = take_screenshot(adb_id)
    if not screenshot_path: return []
    screen_img_color = cv2.imread(screenshot_path) # For drawing debug output
    screen_img = cv2.cvtColor(screen_img_color, cv2.COLOR_BGR2GRAY)
    if screen_img is None:
        logging.error("Could not read screenshot."); return []
    keypoints_screen, descriptors_screen = orb.detectAndCompute(screen_img, None)
    if descriptors_screen is None:
        logging.warning("No features found on screen."); return []

    # 3. Find all good matches
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    all_matches = bf.knnMatch(descriptors_template, descriptors_screen, k=2)
    good_matches = []
    try:
        for m, n in all_matches:
            if m.distance < 0.8 * n.distance:
                good_matches.append(m)
    except ValueError:
        pass # Not enough matches

    logging.info(f"Found {len(good_matches)} total good feature matches. Required: {min_match_count}.")
    if len(good_matches) < min_match_count:
        logging.info("Not enough good matches to proceed with clustering."); return []

    # 4. Get the locations of the good matches on the SCREEN
    matched_points = np.float32([keypoints_screen[m.trainIdx].pt for m in good_matches])
    if len(matched_points) < min_samples:
        logging.info(f"Not enough matched points ({len(matched_points)}) for DBSCAN clustering (min_samples={min_samples})."); return []


    # 5. Use DBSCAN to cluster these points.
    # 'eps' is a critical parameter to tune. It's roughly the max pixel distance within a single object.
    # 'min_samples' is also important. It's the minimum number of matched features to form a "dense" object.
    db = DBSCAN(eps=eps, min_samples=min_samples).fit(matched_points)
    labels = db.labels_
    
    unique_labels = set(labels)
    centers = []
    
    # 6. Calculate the center of each found cluster
    for k in unique_labels:
        if k == -1:
            # -1 represents noisy outliers that don't belong to any cluster
            continue
        
        class_member_mask = (labels == k)
        cluster_points = matched_points[class_member_mask]
        
        # Calculate the center of the cluster by averaging the coordinates
        center_x = int(np.mean(cluster_points[:, 0]))
        center_y = int(np.mean(cluster_points[:, 1]))
        centers.append((center_x, center_y))

        if SAVE_DEBUG_IMAGES:
            # Draw a circle around the cluster for debugging
            cv2.circle(screen_img_color, (center_x, center_y), int(eps), (0, 255, 0), 2)
            cv2.putText(screen_img_color, f"Cluster {k}", (center_x, center_y - int(eps)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    if SAVE_DEBUG_IMAGES and centers:
        # filename = f"DEBUG_all_feature_matches_{image_name.replace('.','_')}_{int(time.time())}.png"
        filename = f"{instance_name}_{workflow_name}_all_feature_matches_{image_name.replace('.','_')}.png"
        cv2.imwrite(os.path.join(TEMP_DIR, filename), screen_img_color)
        logging.debug(f"Saved all-feature-matches debug image to {filename}")

    # 7. Sort the centers for predictable order
    centers.sort(key=lambda p: (p[1], p[0]))
    
    logging.info(f"Clustered into {len(centers)} instances of '{image_name}'. Coords: {centers}")
    return centers

def send_email(subject, body):
    recipient = general_config.get('recipient_email')
    if not recipient: logging.warning("No recipient_email configured in instances.ini. Cannot send email."); return
    logging.info(f"Sending email to {recipient}: '{subject}'")
    try:
        outlook = win32.Dispatch('outlook.application')
        mail = outlook.CreateItem(0)
        mail.To = recipient; mail.Subject = subject; mail.Body = body
        mail.Send()
    except Exception as e:
        logging.error(f"Failed to send email via Outlook: {e}")

def emergency_exit(message):
    logging.critical(f"EMERGENCY EXIT: {message}")
    send_email("CRITICAL ERROR in CE_AUTOMATION", message)
    os._exit(1)