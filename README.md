# PZ Backup
Backup your Project Zomboid installation to make it stable and safe from future updates. The tool will copy your current installation alongside your saves and mods to a new location, allowing you to launch a completely separate instance of the game. This way, you can continue playing on your current version without worrying about updates breaking your experience.

## Usage
> [!IMPORTANT]
> The tool will copy your current active mods of your installation, so make sure to enable mods on the main menu that you want to copy locally for your stable backup before you run the tool.

1. Download the latest release from the [releases page](
2. Run the executable
   - On Windows, run `PZBackup.exe`
   - On Linux, run `chmod +x PZBackup` to make it executable, then run `./PZBackup` (or double click)
3. It will open a UI with different parameters to fill in:
   - Select the [installation folder](https://pzwiki.net/wiki/Game_files#Accessing_the_game_files) of Project Zomboid (which contains the game files)
   - Select the [cache folder](https://pzwiki.net/wiki/Game_files#Cache_folder) of Project Zomboid (which contains your configurations, saves, etc.)
   - Select the folder which will hold the backup
   - Select the name of your backup (by default, it will be the current date and time)
4. Click the "Run Backup" button to start the backup process. The tool will log the progress in the log panel of the UI

Run the launch shortcut that was created in the backup folder to launch the game with the right configuration. 
> [!CAUTION]
> Make sure to not launch the game from the binaries and scripts inside `install`, as those will not have the right configuration !

## Technical details
The application will do the following steps to create a backup of your game:
- The most important one is to copy the game files to a new location. This will allow you to launch the game from that location without worrying about updates breaking your experience.
- It will copy your cache folder which holds your saves and configurations. This way, you can continue playing with your current saves and settings on the new installation, fully independent from the original one.
> [!CAUTION]
> This means that any changes to the original or to the copy will be fully independent from each other, so any parameters change, current active mod list, etc.
- It will copy your current active mods to the new installation cache folder. This way, you can continue playing with your current active mods on the new installation, that will not be affected by any update that may break your mods on the original installation.
- It will create a shortcut to launch the game inside that backup folder (`ProjectZomboid64.exe` on Windows, `projectzomboid.sh` on Linux). It will pass [two launch arguments](https://pzwiki.net/wiki/Startup_parameters#Game_arguments) to the game:
  - `-nosteam` to prevent the game from loading Workshop mods, and instead will only use the mods that were copied to the new installation cache folder.
  - `-cachedir=[path/to/the/new/cache/folder]` to tell the game to use the copy of the cache folder that was created earlier.