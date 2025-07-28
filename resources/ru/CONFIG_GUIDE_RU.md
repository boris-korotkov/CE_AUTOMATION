# Руководство по конфигурации (instances.ini)

Этот файл является центральным узлом конфигурации для бота автоматизации. Он разделен на секции, каждая из которых контролирует определенный аспект поведения скрипта.

### Пример `instances.ini`
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

### Описание секций

#### `[General]`
Глобальные настройки, которые применяются ко всему скрипту.
*   `recipient_email`: Адрес электронной почты для отправки уведомлений.
*   `tesseract_path`: Полный, абсолютный путь к вашему файлу `tesseract.exe`. Используйте двойные обратные слэши `\\`.
*   `emulator_boot_time`: Количество секунд ожидания полной загрузки эмулятора и игры перед тем, как скрипт попытается подключиться.
*   `log_level`: Уровень детализации логов. Допустимые значения: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
*   `game_load_check_image`: Имя файла изображения (из папки `resources/<lang>/`), которое скрипт будет искать для подтверждения успешной загрузки игры.
*   `game_load_check_threshold`: Порог точности (от 0.0 до 1.0) для `game_load_check_image`.
*   `save_debug_images`: Если `True`, скрипт будет сохранять скриншоты в папку `temp` для каждой задачи распознавания, показывая, что было найдено (или не найдено). Это очень полезно для отладки, но для обычных запусков лучше установить `False`.

#### `[EmulatorType]`
*   `Preferred`: Эмулятор, который вы используете. Допустимые значения: `bluestacks` или `nox`. Скрипт будет использовать соответствующую `_command` из секций инстансов.

#### `[Workflows]`
Централизованное место для определения наборов сценариев.
*   Каждый ключ (например, `daily_tasks`) — это ваше собственное имя для набора.
*   Значение — это список имен сценариев из вашего YAML-файла, разделенных запятыми.

#### `[RunOrder]`
Управляет потоком выполнения в стандартном режиме.
*   `order`: Список имен инстансов (из секций ниже), разделенных запятыми, в том порядке, в котором вы хотите их запустить.
*   `start_from`: (Опционально) Если вы хотите возобновить длинный запуск, введите здесь имя инстанса. Скрипт пропустит все инстансы, предшествующие ему в списке `order`.
*   `active_set`: Имя набора сценариев (из секции `[Workflows]`), который будет выполняться для всех инстансов в этом запуске.

#### `[Hotkeys]`
*   `pause_resume`: Комбинация клавиш для приостановки/возобновления выполнения скрипта.
*   `emergency_stop`: Комбинация клавиш для немедленной остановки скрипта.

#### Секции инстансов (например, `[Adidas]`)
Определите одну секцию для каждого инстанса эмулятора, который вы хотите автоматизировать. Имя секции (например, `Adidas`) является уникальным идентификатором этого инстанса.
*   `bluestacks_command` / `nox_command`: Полная строка командной строки для запуска этого конкретного инстанса эмулятора.
*   `adb_port`: Номер порта ADB, назначенный этому инстансу. Так скрипт общается с ним.
*   `language`: Двухбуквенный код языка (например, `en`, `ru`), который указывает скрипту, какую подпапку внутри `resources/` использовать для изображений и сценариев.