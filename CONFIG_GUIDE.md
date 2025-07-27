# Configuration Guide for instances.ini

This file is the central configuration hub for the automation bot. It's divided into sections, each controlling a different aspect of the script's behavior.

### Example `instances.ini`
```ini
[General]
recipient_email = your_email@example.com
tesseract_path = C:\\Program Files\\Tesseract-OCR\\tesseract.exe
emulator_boot_time = 150
log_level = DEBUG
game_load_check_image = Guild.png
game_load_check_threshold = 0.85
save_debug_images = True

[EmulatorType]
Preferred = bluestacks

[Workflows]
daily_tasks = Send_flowers_to_friends,Daily_rewards,Campaign_farming
weekend_event = Weekend_Boss_Event,Special_Arena

[RunOrder]
order = Adidas,CE_2024_1,CE_2024_2
start_from = CE_2024_1
active_set = daily_tasks

[Hotkeys]
pause_resume = ctrl+shift+p
emergency_stop = ctrl+shift+h

[Adidas]
bluestacks_command = "C:\Program Files\BlueStacks_nxt\HD-Player.exe" --instance Rvc64_5 --cmd launchAppWithBsx --package "com.feelingtouch.clonewar"
adb_port = 5605
language = en
```

---

### Section Breakdown

#### `[General]`
Global settings that apply to the entire script.
*   `recipient_email`: The email address for sending notifications.
*   `tesseract_path`: The full, absolute path to your `tesseract.exe` file. Use double backslashes `\\`.
*   `emulator_boot_time`: The number of seconds to wait for an emulator instance to fully boot and load the game before the script tries to connect.
*   `log_level`: The verbosity of the logs. Valid options: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
*   `game_load_check_image`: The filename of an image (located in `resources/<lang>/`) that the script will look for to confirm the game has loaded successfully.
*   `game_load_check_threshold`: The accuracy threshold (0.0 to 1.0) for the `game_load_check_image`.
*   `save_debug_images`: If `True`, the script will save screenshots in the `temp` folder for every image recognition task, showing what it found (or didn't find). This is extremely useful for debugging but should be set to `False` for normal runs.

#### `[EmulatorType]`
*   `Preferred`: The emulator you are using. Valid options are `bluestacks` or `nox`. The script will use the corresponding `_command` from the instance sections.

#### `[Workflows]`
A centralized place to define sets of workflows.
*   Each key (e.g., `daily_tasks`) is a custom name for a set.
*   The value is a comma-separated list of scenario names from your YAML file(s).

#### `[RunOrder]`
Controls the execution flow when running in standard mode.
*   `order`: A comma-separated list of the instance names (from the sections below) in the exact order you want them to run.
*   `start_from`: (Optional) If you want to resume a long run, enter an instance name here. The script will skip all instances before it in the `order` list.
*   `active_set`: The name of the workflow set (from the `[Workflows]` section) that will be executed for all instances in this run.

#### `[Hotkeys]`
*   `pause_resume`: The key combination to pause/resume the script.
*   `emergency_stop`: The key combination to immediately terminate the script.

#### Instance Sections (e.g., `[Adidas]`)
Define one section for each emulator instance you want to automate. The section name (e.g., `Adidas`) is the unique identifier for that instance.
*   `bluestacks_command` / `nox_command`: The full command-line string to launch this specific emulator instance.
*   `adb_port`: The ADB port number assigned to this instance. This is how the script communicates with it.
*   `language`: The two-letter language code (e.g., `en`, `es`) that tells the script which subfolder inside `resources/` to use for images and workflows.