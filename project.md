Project Name: CE_AUTOMATION

Product Requirements Document

Purpose: 
I want to automate daily routine and weekly event playing in Clone Evolution mobile game.
Th automation is to work on a regular computer with Windows 11 OS and with an Android Emulator installed.
The program has to by in Python and is to support BlueStacks and Nox emulators  as well as  multiple languages available in my game interface.

Product overview:
The product should allow me to run the different workflows. Each workflow represents an INI file with Emulator instances list and scenario items. A separate scenario list is to reside in the resources folder under a sub-folder which represent a language.
I plan to create a final executable file and run it with a workflow name as an argument.
The program is to start Emulator instances and execute the defined scenarios.
All events are to be logged and each run is to create a log file with the timestamp in the logs sub-folder.

Stakeholders / Users: 
Myself or/nad users from the game community

Assumptions and Constraints :
The game UI remains relatively static between versions.
Outlook must be installed and configured on the system.

In-Scope Must Features:
1. The program shouldn't impact the user's work at the computer.
Thus, the interaction with running emulator isntance is to be done via  (Android Debug Bridge) ADB protocol. The port number for each instance as well as instance start command with instance name will be defined in the workflow.ini for each instance
An exanple of workflow.ini file is below.
[EmulatorType]
Preferred = bluestacks
[CE_2024_5]
nox_command = "C:\Program Files\Nox\bin\Nox.exe" -clone:Nox_15 -startPackage:com.feelingtouch.clonewar
bluestacks_command = "C:\Program Files\BlueStacks_nxt\HD-Player.exe" --instance Rvc64_14 --cmd launchAppWithBsx --package "com.feelingtouch.clonewar"
adb_port = 5695
language = en
scenario = Supply_Depot_Farming, Guild_Event_Check
[Adidas]
nox_command = "C:\Program Files\Nox\bin\Nox.exe" -clone:Nox_1 -startPackage:com.feelingtouch.clonewar
bluestacks_command = "C:\Program Files\BlueStacks_nxt\HD-Player.exe" --instance Rvc64_5 --cmd launchAppWithBsx --package "com.feelingtouch.clonewar"
adb_port = 5605
language = ru
scenario = Supply_Depot_Farming, Guild_Event_Check
2. After instance is started is has to run a series of clicks, screen area captures, and captured areas assessment described in the scenarios file which can can either INI, YAML, or JSON. 
3. The commands should follow a pre-defined patterns and should allow new commands if needed. The command examples with expected actions are below. All coordinates are to be relative to the emulator window. 
3a. delay(10) - pause execution for 10 second; 
3b. click(100,200) - click on point with coordinates x=100 and y=200; 
3c. compare_with_text(200,300, 80, 20, 'Guild') - capture a window area with top left corner coordinates x=200 and y=300, with width =80 and height=20, convert the captured area to text and compare the converted text with 'Guild'. The command result should return either True or False
3d. compare_with_image(200,300, 80, 20, '\resources\en\bullets.jpg', 0.85) - capture a window area with top left corner coordinates x=200 and y=300, with width =80 and height=20, match the captured area with the image located in '\resources\en\bullets.jpg' with matching accuracy threshold=0.85. The command result should return either True or False
3e. scroll(100,100, 'left',200) - scroll screen on emulator window left with the starting point when mouse was pressed down at coordinates x=100 and y=100 and the movement was for 200 pixels.
3f. emergency_exit('the instance is not responding') - execution of the scenario is stopped, the program is stopped, the error message 'the instance is not responding' is sent to a pre-defined user's email via local Outlook.
3g. send_email('a kun is jumped to a new island') - send an email to the pre-defined user's email via local Outlook with the message 'a kun is jumped to a new island'.
4. I need to be able to create if-else and loop logic in the workflow. An example of one scenario item can look like this:
scenarios:
  - name: Supply_Depot_Farming
    description: Collect resources from the supply depot by refreshing until a specific item appears.
    steps:
      - scroll: [250, 250, left, 200]
      - if:
          condition: compare_with_text(200,300, 80, 20, 'Supply Depot')
          then:
            - click: [100, 200]
            - delay: 2
            - set: { counter: 0 }
            - while:
                condition: "not compare_with_image(100,150,50,50,'\\resources\\en\\3red_blueprints.jpg',0.85) and counter < 10"
                do:
                  - click: [300, 450]
                  - delay: 2
                  - increment: counter
            - if:
                condition: compare_with_image(100,150,50,50,'\\resources\\en\\3red_blueprints.jpg',0.85)
                then:
                  - click: [270, 600]
                  - delay: 2
                  - if:
                      condition: compare_with_text(200,300,80,20,'Buy')
                      then:
                        - click: [400, 500]
                        - delay: 2
                        - if:
                            condition: compare_with_text(400,350,180,50,'Claim')
                            then:
                              - click: [400, 500]
                              - delay: 2
            - if:
                condition: compare_with_image(20,20,100,100,'\\resources\\en\\back-arrow.jpg',0.85)
                then:
                  - click: [25, 25]

  - name: Guild_Event_Check
    steps:
      - scroll: [100, 100, up, 150]
      - if:
          condition: compare_with_text(150, 200, 100, 30, 'Guild Event')
          then:
            - click: [150, 200]
            - delay: 3
            - if:
                condition: compare_with_text(300, 400, 200, 50, 'Event Active')
                then:
                  - send_email: 'Guild Event is active now!'

The above 'Supply Depot Farming' scenario represent a user story when the user scrolls left the screen on the opened emulator, clicks on the area with visible 'Supply deport' text, if there is no 3 red blueprints found an a shelf at certain place (100,150), a user click on Refresh button (270,600) until this rare game resource is appeared at the defind coordinates, but no more than 10 times because each click costs a game currency.
If 3 red blueprints resource found, click on it, blick Buy in the opened window and them confirm clicking on Claim button in the next opened window to finilize a purchase. click on back-arrow in the top-left window corner to exit from 'Supply deport'.

5. The program should log all events in a log file with timestamp in the name.
6. The captured area is to be stored in the program location. In case of the error or misinterpretation of recognized text or picture I will be able to see what was captured.
7. If emulator window is not responding certain time, the instance is to be restarted and the scenario is to be continued from the place where it was stopped.
8. The compare_with_image method in the scenario is to compare captured area with saved image not exactly, but approximatly because the saved image will be captured manually and captured area may be different by approximatly 10-20 pixel. Ideally, it would be nice to have the matching accuracy requirement adjustable by user in the scenario or in the program code. I'll try to manually find a value that works.
9. Since the programn is to maintain multiple game interace language, I believe scenario YAML file is to be defined for each language and resides in a sub-folder with language name. E.g., 'en', 'ru', etc. This folder will not only inlude scenario file but also pre-saved images that can also be different for different game interface language.

In-Scope optional Features:
20. There is a hot key to pause script execution, resume and stop. Ideally they have to be defined in program ini file to allow user to change them if needed. The hotkeys should not overlap with the most popular Window hot keys like CTRL+C, CTRIL+V, or CTRL+S. For example we can use CTRL+P for pause, CTRL+R for resume and CTRL+H for stop program execution.
21. Scenario variables are stored in a global context dictionary during execution. They can be created, modified, and used in conditions.
Example:
- set: { last_kun_change_time: datetime.now() }
- capture_text: [100, 100, 50, 20, current_kun_count]
- if:
    condition: "${current_kun_count} != ${previous_kun_count}"
    then:
      - calculate: { time_diff: "datetime.now() - last_kun_change_time" }
      - send_email: "Kun count changed to ${current_kun_count} after ${time_diff.seconds} seconds."
22. Some game events may have text displied with a minor angle to the left or to the right. Ideally, compare_with_text function should be able to handle that. If not, I will have to use compare_with_image instead.

Non-Functional Requirements: 
30. The program is to be terminal window program with execution messages visible in the terminal window. After program is finished there is no need to keep the terminal window open because log file will have all displayed messages included.
31. The program should be compatible with Windows 10 and windows 11
32. After  program is finished all used libraries shoudln't be updated to avoid any failure in the future due to library changes
33. The version of Bluestacks I plan to use as my preferred emulator type is 5.22.51.10.38. A potential Nox version 7.0.6.1
34. An example of log file. File name: CE_robot_2025-05-19_23-06-13.log
File content:
2025-05-19 23:06:13,859 - INFO - Logging setup complete.
2025-05-19 23:06:13,860 - INFO - Loading preferred emulator type from the INI file.
2025-05-19 23:06:13,861 - INFO - Preferred emulator type: bluestacks
2025-05-19 23:06:13,861 - INFO - Loading instances from the INI file.
2025-05-19 23:06:13,862 - INFO - Loading preferred emulator type from the INI file.
2025-05-19 23:06:13,863 - INFO - Loaded 2 valid instances.
2025-05-19 23:06:13,863 - INFO - Launching instance: CE_2024_5 | Language: en | Scenarios: farm_campaign, fight_on_arena
2025-05-19 23:06:13,863 - INFO - Launching instance: CE_2024_5
2025-05-19 23:06:13,871 - INFO - Connecting ADB to 127.0.0.1:5695 for instance CE_2024_5...
2025-05-19 23:06:25,656 - INFO - ADB connected to 127.0.0.1:5695.
2025-05-19 23:06:25,656 - INFO - ADB connected to 127.0.0.1:5695 for instance CE_2024_5.
2025-05-19 23:06:25,656 - INFO - Executing scenario: farm_campaign for instance: CE_2024_5
2025-05-19 23:06:25,656 - INFO - Executing scenario: fight_on_arena for instance: CE_2024_5
2025-05-19 23:07:59,079 - INFO - Attempting to terminate instance with PID: 3768
2025-05-19 23:07:59,080 - INFO - Looking for processes named HD-Player.exe
2025-05-19 23:07:59,357 - INFO - All bluestacks processes terminated successfully.
2025-05-19 23:07:59,358 - INFO - Launching instance: Adidas | Language: ru | Scenarios: farm_campaign, collect_rewards
2025-05-19 23:07:59,358 - INFO - Launching instance: Adidas
2025-05-19 23:07:59,368 - INFO - Connecting ADB to 127.0.0.1:5605 for instance Adidas...
2025-05-19 23:08:11,129 - INFO - ADB connected to 127.0.0.1:5605.
2025-05-19 23:08:11,130 - INFO - ADB connected to 127.0.0.1:5605 for instance Adidas.
2025-05-19 23:08:11,130 - INFO - Executing scenario: farm_campaign for instance: Adidas
2025-05-19 23:08:11,130 - INFO - Executing scenario: collect_rewards for instance: Adidas
2025-05-19 23:10:09,706 - INFO - Attempting to terminate instance with PID: 2704
2025-05-19 23:10:09,706 - INFO - Looking for processes named HD-Player.exe
2025-05-19 23:10:10,023 - INFO - All bluestacks processes terminated successfully.
2025-05-19 23:10:10,024 - INFO - Script ended.
