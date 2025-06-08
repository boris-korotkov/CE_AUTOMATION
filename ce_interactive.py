import cv2
import os
import time
import ce_actions # We need this to take the initial screenshot

# --- State variables for mouse callbacks ---
class MouseState:
    def __init__(self):
        self.point = None
        self.region = None
        self.start_point = None
        self.end_point = None
        self.is_dragging = False

def get_coords_from_click(adb_id):
    """
    Takes a screenshot, displays it, and waits for the user to click.
    Returns the (x, y) coordinates of the click.
    """
    screenshot_path = ce_actions.take_screenshot(adb_id)
    if not screenshot_path:
        print("ERROR: Could not get screenshot from device.")
        return None

    img = cv2.imread(screenshot_path)
    if img is None:
        print(f"ERROR: Could not read image file at {screenshot_path}")
        return None

    state = MouseState()
    window_name = "Click to select a point, then press any key to continue"

    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            state.point = (x, y)
            # Draw a circle on the image to give user feedback
            cv2.circle(img, (x, y), 5, (0, 255, 0), -1) # Green dot
            cv2.circle(img, (x, y), 7, (0, 0, 0), 1)   # Black outline
            cv2.imshow(window_name, img)
            print(f"Point selected: {state.point}")

    cv2.imshow(window_name, img)
    cv2.setMouseCallback(window_name, mouse_callback)
    
    print("\nINFO: A window has appeared. Click on it to select your desired coordinates.")
    cv2.waitKey(0)  # Wait indefinitely for any key press
    cv2.destroyAllWindows()
    
    os.remove(screenshot_path) # Clean up the full screenshot
    return state.point

def get_region_from_drag(adb_id):
    """
    Takes a screenshot, displays it, and lets the user drag to select a region.
    Returns the region as (x, y, w, h) and saves the cropped image.
    """
    screenshot_path = ce_actions.take_screenshot(adb_id)
    if not screenshot_path:
        print("ERROR: Could not get screenshot from device.")
        return None

    img_original = cv2.imread(screenshot_path)
    if img_original is None:
        print(f"ERROR: Could not read image file at {screenshot_path}")
        return None

    img_clone = img_original.copy()
    state = MouseState()
    window_name = "Click and drag to select a region, then press any key"

    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            state.start_point = (x, y)
            state.is_dragging = True
        elif event == cv2.EVENT_MOUSEMOVE:
            if state.is_dragging:
                # Draw the rectangle on a clone for live feedback
                img_feedback = img_original.copy()
                cv2.rectangle(img_feedback, state.start_point, (x, y), (0, 255, 0), 2)
                cv2.imshow(window_name, img_feedback)
        elif event == cv2.EVENT_LBUTTONUP:
            state.is_dragging = False
            state.end_point = (x, y)
            
            # Draw final rectangle
            cv2.rectangle(img_clone, state.start_point, state.end_point, (0, 255, 0), 2)
            cv2.imshow(window_name, img_clone)
            
            # Calculate final region (x, y, w, h)
            x1, y1 = state.start_point
            x2, y2 = state.end_point
            x = min(x1, x2)
            y = min(y1, y2)
            w = abs(x1 - x2)
            h = abs(y1 - y2)
            
            if w > 0 and h > 0:
                state.region = (x, y, w, h)
                print(f"Region selected: X={x}, Y={y}, W={w}, H={h}")
                
                # Save the captured region for inspection
                captured_area = img_original[y:y+h, x:x+w]
                save_path = os.path.join("temp", f"captured_region_{int(time.time())}.png")
                cv2.imwrite(save_path, captured_area)
                print(f"Captured region saved to: {save_path}")

    cv2.imshow(window_name, img_clone)
    cv2.setMouseCallback(window_name, mouse_callback)

    print("\nINFO: A window has appeared. Click and drag to select a region.")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    os.remove(screenshot_path) # Clean up the full screenshot
    return state.region