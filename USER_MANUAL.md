# CE Automation - User Manual & Command Reference

This document provides a complete guide for configuring and writing automation workflows for the CE Automation script.

---

## I. Running the Robot

You can run the main script, `ce_robot.py`, in several ways from your command line. Open a terminal, navigate to the project directory, and use one of the following commands.

### Standard Mode
Runs the script according to the settings in `instances.ini`, using the `[RunOrder]` and `[Workflows]` sections.
```bash
python ce_robot.py
```

### Targeted Instance(s) Mode
Runs the script for one or more specific instances, ignoring the `[RunOrder]` section.
```bash
# Run only for the 'Adidas' instance
python ce_robot.py Adidas

# Run for 'Adidas' and 'CE_2024_1' in that order
python ce_robot.py Adidas CE_2024_1
```

### Custom Workflow File Mode
Uses a specific YAML file for the run instead of the default. This is perfect for testing or running special, one-off tasks. The path should be relative to the script's location.
```bash
# Use a special workflow file for the standard run order
python ce_robot.py -wf "resources/en/special_tasks.yaml"

# Combine with targeted instances
python ce_robot.py Adidas -wf "resources/en/test_expedition.yaml"
```

---

## II. Core Concepts & Configuration

### The Workflow File
All automation logic is written in YAML files (e.g., `workflows.yaml`). A file contains one or more **scenarios**. A scenario is a named sequence of **steps** that the robot executes in order.

### Centralized Workflows in `instances.ini`
To avoid duplicating workflow lists for every instance, you can define them centrally in `instances.ini`.
1.  **Remove** the `workflows = ...` line from your individual instance sections (e.g., `[Adidas]`).
2.  **Add a `[Workflows]` section** to define named sets of tasks (e.g., `daily_tasks`).
3.  **Add an `active_set` key** to your `[RunOrder]` section to choose which set to run.

```ini
[Workflows]
daily_tasks = Daily_rewards, Campaign_farming, Guild_activity
weekend_event = Weekend_Boss_Event, Special_Arena

[RunOrder]
order = Adidas, CE_2024_1
active_set = daily_tasks
```

### Anchor-Based Automation
This is the most important concept for creating reliable scripts. Instead of using fixed, hardcoded coordinates that can break when ads appear or the UI shifts, you should find a visual "anchor" on the screen first, and then perform actions relative to it.

```yaml
# The Brittle Way (Avoid This)
- click: [850, 690] # Fails if the Guild button moves

# The Robust Way (Use This)
- set:
    guild_button_coords: "{{ get_coords_from_image('guild_button.png') }}"
- if:
    condition: "guild_button_coords"
    then:
      - click: "{{ guild_button_coords }}"
```

---

## III. YAML Workflow Commands

### Action Commands
These commands perform a direct action in the emulator.

#### `click`
Simulates a tap on the screen.
```yaml
# Click a static, hardcoded coordinate
- click: [100, 250]
```

#### `scroll`
Simulates a swipe gesture.
```yaml
# Scroll up from the middle of the screen by 400 pixels
- scroll: [540, 700, "up", 400]
```

#### `delay`
Pauses the script. Essential for waiting for screens to load.
```yaml
# Wait 3.5 seconds for an animation to finish
- delay: 3.5
```

#### `log`
Prints a message to the console and log file.
```yaml
# Log the current progress
- log: "Starting attack #{{ attempt_counter }} in the Arena."
```

#### `send_email`
Sends a notification email to the address in `instances.ini`.
```yaml
# Send a notification that a rare event has started
- send_email: "The 'Galactic Conquest' event is now active!"
```

#### `emergency_exit`
Immediately stops the entire program. Use for unrecoverable errors.
```yaml
# Stop the script if a critical element is not found
- emergency_exit: "Could not find the 'Home' button. State is unrecoverable."
```

### Variable & Context Commands
These commands manage the script's internal memory (context).

#### `set`
Creates or updates a variable.
```yaml
# Initialize a counter variable to 0
- set:
    attack_counter: 0
```

#### `increment`
Adds 1 to a numeric variable.
```yaml
# Increment the counter after an attack
- increment: attack_counter
```

### Control Flow Commands
These commands control the script's logic.

#### `if / then / else`
Executes steps conditionally.
```yaml
- if:
    condition: "attack_counter < 5"
    then:
      - log: "Still have attacks left. Continuing."
    else:
      - log: "No attacks left. Exiting Arena."
```

#### `while / do`
Executes steps in a loop as long as a condition is true.
```yaml
- while:
    condition: "get_coords_from_image('claim_reward.png')"
    do:
      - log: "Found a reward to claim. Clicking it."
      - click: "{{ get_coords_from_image('claim_reward.png') }}"
      - delay: 2
```

---

## IV. Functions for Finding & Comparing
These functions are the "eyes" of the robot. They can be used with `set` to store a result, or directly inside a `condition` string.

> [!NOTE]
> The `len()` function can be used in templates to get the number of items found:
> `- log: "Found {{ len(all_buttons) }} buttons on the screen."`

### Static Object Detection (Template Matching)
Fast and precise. Use for UI elements that are **not** animated.

#### `get_coords_from_image('image.png', threshold)`
Finds the **single best match** for a static image and returns its center coordinates `(x, y)`.

#### `get_all_coords_from_image('image.png', threshold)`
Finds **all occurrences** of a static image and returns a **sorted list** of coordinates `[(x1, y1), ...]`, from top-to-bottom, left-to-right.

> [!NOTE]
> #### Targeting Specific Occurrences
> Because the returned list is sorted, you can reliably target specific items:
> - **Topmost Item:** Use index `[0]`.
> - **Bottommost Item:** Use index `[-1]`.
> ```yaml
> # Find all 'Claim' buttons and click the one lowest on the screen
> - set:
>     all_buttons: "{{ get_all_coords_from_image('claim_button.png') }}"
> - if:
>     condition: "all_buttons"
>     then:
>       - log: "Clicking the lowest of {{ len(all_buttons) }} buttons."
>       - click: "{{ all_buttons[-1] }}"
> ```

### Animated/Dynamic Object Detection (Feature Matching)
More robust. Use for elements that are **animated, scaled, or rotated**.

#### `get_coords_from_features('image.png', min_match_count)`
Finds the **single best match** for a dynamic/animated image and returns its center coordinates `(x, y)`.

#### `get_all_coords_from_features(...)`
Finds **all occurrences** of a dynamic/animated image and returns a sorted list of coordinates.
- **Syntax:** `get_all_coords_from_features('image.png', min_match_count, eps, min_samples)`

> [!NOTE]
> #### Targeting Specific Occurrences
> This function also returns a sorted list, so the same targeting logic applies:
> ```yaml
> # Find all animated cards and click the topmost one
> - set:
>     all_cards: "{{ get_all_coords_from_features('animated_card.png') }}"
> - if:
>     condition: "all_cards"
>     then:
>       - log: "Clicking the topmost of {{ len(all_cards) }} cards."
>       - click: "{{ all_cards[0] }}"
> ```

> [!WARNING]
> #### Tuning Feature Detection
> Feature-based functions require tuning to work reliably. Use `ce_tester.py` to experiment.
> - `min_match_count`: Minimum good feature matches required. Lower for small/simple images; raise to avoid false positives.
> - `eps`: Max pixel distance for points to be in the same object. A good start is half the template's width/height.
> - `min_samples`: Min features needed to form a valid object cluster. Lower for small objects.

### Text and Other Comparisons
These functions are for use inside a `condition:` string and return `True/False`.
- `compare_with_image(x, y, w, h, 'image.png', threshold)`
- `compare_with_any_image(x, y, w, h, ['img1.png', 'img2.png'])`
- `compare_with_text(x, y, w, h, 'expected text')`