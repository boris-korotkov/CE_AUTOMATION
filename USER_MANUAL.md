# CE Automation - Workflow Command Reference

This document provides a complete reference for all commands and functions available for use in your `workflows.yaml` files.

## Basic Structure

Each workflow file consists of one or more scenarios. A scenario is a named sequence of steps that the robot will execute in order.

```yaml
scenarios:
  - name: Your_Scenario_Name
    description: A brief explanation of what this scenario does.
    steps:
      # ... A list of commands goes here ...
      - click: [100, 200]
      - delay: 5
```

---

## I. Action Commands

These are the primary commands that perform an action within the emulator. They are always used as a single-line step.

### `click`
Simulates a tap on the screen at a specific coordinate.

-   **Syntax:** `click: [x, y]`
-   **Parameters:**
    -   `x`: The horizontal coordinate (from the left edge).
    -   `y`: The vertical coordinate (from the top edge).
-   **Example:**
    ```yaml
    - click: [60, 680] # Click on the "Friends" icon
    ```

### `scroll`
Simulates a swipe gesture on the screen.

-   **Syntax:** `scroll: [x, y, direction, distance]`
-   **Parameters:**
    -   `x`, `y`: The starting coordinates for the swipe.
    -   `direction`: The direction of the swipe. Must be one of `up`, `down`, `left`, or `right`.
    -   `distance`: The length of the swipe in pixels.
-   **Example:**
    ```yaml
    - scroll: [500, 800, up, 400] # Scroll the friends list up from the middle-bottom of the screen
    ```

### `delay`
Pauses the execution of the script for a specified number of seconds.

-   **Syntax:** `delay: seconds`
-   **Parameters:**
    -   `seconds`: The duration of the pause in seconds (can be a decimal, e.g., `0.5`).
-   **Example:**
    ```yaml
    - delay: 3 # Wait 3 seconds for the next screen to load
    ```

### `log`
Prints a message to the console and the log file. Useful for debugging and tracking progress.

-   **Syntax:** `log: "Your message here"`
-   **Parameters:**
    -   A string containing the message to be logged. You can embed variables using `{{ variable_name }}`.
-   **Example:**
    ```yaml
    - log: "Starting the supply depot farming. Attempt #{{counter}}"
    ```

### `send_email`
Sends an email notification using the configured Outlook account.

-   **Syntax:** `send_email: "Your message here"`
-   **Parameters:**
    -   A string containing the body of the email.
-   **Example:**
    ```yaml
    - send_email: "Guild Event is now active! Please check the game."
    ```

### `emergency_exit`
Immediately stops the entire automation script and sends a critical error email.

-   **Syntax:** `emergency_exit: "Error message"`
-   **Parameters:**
    -   A string explaining the reason for the emergency stop.
-   **Example:**
    ```yaml
    - emergency_exit: "Game has crashed and cannot be recovered."
    ```

---

## II. Variable & Context Commands

These commands allow you to store and manipulate internal variables within a scenario, which is essential for loops and complex logic.

### `set`
Creates or overwrites a variable in the scenario's context.

-   **Syntax:** `set: { variable_name: value }`
-   **Example:**
    ```yaml
    - set: { counter: 0 } # Initialize a loop counter
    - set: { target_found: false } # Initialize a boolean flag
    ```

### `increment`
Adds 1 to a numeric variable. If the variable doesn't exist, it is created with a value of 1.

-   **Syntax:** `increment: variable_name`
-   **Example:**
    ```yaml
    - increment: counter # Increases the value of 'counter' by 1
    ```

---

## III. Control Flow Commands

These commands control the logic of your scenario, allowing for conditional execution and loops.

### `if / else`
Executes a block of steps only if a condition is met. An optional `else` block can be executed if the condition is not met.

-   **Syntax:**
    ```yaml
    - if:
        condition: "your_condition_here"
        then:
          # ... steps to run if condition is true ...
        else:
          # ... (optional) steps to run if condition is false ...
    ```
-   **Example:**
    ```yaml
    - if:
        condition: compare_with_text(400, 350, 180, 50, 'Claim')
        then:
          - log: "Claim button found. Clicking it."
          - click: [490, 375]
        else:
          - log: "Claim button not found. Moving on."
    ```

### `while`
Repeatedly executes a block of steps as long as a condition remains true.

-   **Syntax:**
    ```yaml
    - while:
        condition: "your_condition_here"
        do:
          # ... steps to repeat while the condition is true ...
    ```
-   **Example:**
    ```yaml
    - while:
        condition: "counter < 10 and not target_found"
        do:
          - log: "Searching for target..."
          - # ... more steps ...
          - increment: counter
    ```

---

## IV. Conditional Functions

These functions are used **exclusively inside the `condition:` string** of an `if` or `while` block. They return `True` or `False`.

### `compare_with_image`
Captures a region of the screen and compares it to a template image file.

-   **Syntax:** `compare_with_image(x, y, w, h, 'image_filename.png', threshold)`
-   **Parameters:**
    -   `x`, `y`, `w`, `h`: The coordinates, width, and height of the screen region to capture.
    -   `'image_filename.png'`: The name of the template image. This file must be located in the appropriate language resource folder (e.g., `resources/en/`).
    -   `threshold` (optional): The matching accuracy, from `0.0` to `1.0`. A higher value means a stricter match. Defaults to `0.85`.
-   **Example:**
    ```yaml
    condition: "compare_with_image(20, 20, 100, 100, 'back-arrow.png', 0.9)"
    ```

### `compare_with_text`
Captures a region of the screen, converts it to text using OCR, and checks if it contains the expected text. The comparison is case-insensitive.

-   **Syntax:** `compare_with_text(x, y, w, h, 'expected text')`
-   **Parameters:**
    -   `x`, `y`, `w`, `h`: The coordinates, width, and height of the screen region to capture.
    -   `'expected text'`: The text to search for within the captured region.
-   **Example:**
    ```yaml
    condition: "compare_with_text(297, 565, 156, 34, 'Claim All')"
    ```

### Combining Conditions
You can combine multiple conditions using standard logical operators: `and`, `or`, and `not`.

-   **Example:**
    ```yaml
    condition: "not compare_with_image(100,100,50,50,'error.png') and counter < 5"
    ```

---

## V. Best Practices & Tips

-   **Use Comments:** Use the `#` character to add comments to your steps. This makes your scenarios much easier to understand and maintain.
-   **Use the Tester:** Use `ce_tester.py` to find exact coordinates and regions. Options `7` (Get Coordinates) and `8` (Select Region) are your best friends for building accurate workflows. The image captured by option `8` can be used directly as a template for `compare_with_image`.
-   **Descriptive Naming:** Give your template images and scenarios descriptive names (e.g., `button_confirm_purchase.png` instead of `img1.png`).
-   **Indentation is Key:** YAML relies on strict indentation. Use a text editor that supports YAML to avoid errors. All steps in a block (`steps:`, `then:`, `do:`) must have the same level of indentation.